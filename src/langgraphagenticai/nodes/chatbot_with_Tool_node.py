from src.langgraphagenticai.state.state import State
from src.langgraphagenticai.utils.deduplication import deduplicate_tool_calls
from langchain_core.messages import SystemMessage, AIMessage
import json
import re
import logging
import os
from typing import Callable, Any, Dict, List

# Persistent probe store path (used to avoid re-executing identical probes across runs)
PERSISTENT_PROBES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "__blobstorage__", "executed_probes.json"))

def _load_persisted_probes() -> set:
    try:
        if os.path.exists(PERSISTENT_PROBES_PATH):
            with open(PERSISTENT_PROBES_PATH, "r") as f:
                data = json.load(f)
                return set(data or [])
    except Exception:
        pass
    return set()

def _write_persisted_probes(keys: set):
    try:
        os.makedirs(os.path.dirname(PERSISTENT_PROBES_PATH), exist_ok=True)
        with open(PERSISTENT_PROBES_PATH, "w") as f:
            json.dump(sorted(list(keys)), f)
    except Exception:
        pass

def _probe_key_from_tc(tc: Dict[str, Any]) -> str:
    """Return a normalized probe key for simple probes such as kubectl_get.
    Format: resourceType:namespace (namespace empty string if not provided)
    Returns empty string for non-probe tool calls.
    """
    if not isinstance(tc, dict):
        return ""
    name = tc.get("name", "")
    args = tc.get("args", {}) or {}
    if name and name == "kubectl_get":
        rt = args.get("resourceType") or args.get("resource") or args.get("resource_type") or ""
        ns = args.get("namespace") or args.get("ns") or ""
        return f"{str(rt).lower()}:{ns}"
    return ""

logger = logging.getLogger(__name__)


class ChatbotWithToolNode:

    def __init__(self, model, system_prompt):
        self.llm = model
        self.system_prompt = system_prompt

    def extract_and_create_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Convert model output into structured tool calls.

        Supports two formats commonly emitted by models:
        1) JSON objects inside markdown code blocks e.g. ```json {"name": "kubectl_get", "parameters": {...}} ```
        2) Plain-text function-style calls, e.g. kubectl_get(resourceType="namespaces") or kubectl_describe(resourceType="pod", name="x").

        The function will return a list of dicts with keys: 'id', 'name', 'args'.
        """
        tool_calls: List[Dict[str, Any]] = []

        # 1) Parse JSON code-blocks as before
        json_blocks = re.findall(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
        for i, json_str in enumerate(json_blocks):
            try:
                tool_data = json.loads(json_str)
                # Support both `name` and `function` keys emitted by different model styles
                if isinstance(tool_data, dict):
                    name = tool_data.get("name") or tool_data.get("function") or tool_data.get("tool")
                    params = tool_data.get("parameters") or tool_data.get("args") or {}
                    if name:
                        tool_calls.append({
                            "id": f"tool_json_{i}",
                            "name": name,
                            "args": params,
                        })
            except json.JSONDecodeError:
                logger.debug("Failed to parse JSON block #%d", i)

        # 2) Parse plain-text function-style tool invocations anywhere in the content
        # e.g. kubectl_get(resourceType="namespaces", name="default")
        func_pattern = re.findall(r'([a-zA-Z_]\w*)\s*\(\s*([^)]*)\)', content)
        for i, (fname, argstr) in enumerate(func_pattern):
            # Skip obvious false-positives such as Markdown links or common phrases by basic heuristic
            if fname.lower() in ("http", "https"):
                continue
            params = {}
            if argstr.strip():
                # Parse comma-separated key=value pairs; handle single/double quotes
                arg_pairs = re.findall(r"""(\w+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^,\)\s]+))""", argstr)
                for (k, v1, v2, v3) in arg_pairs:
                    value = v1 or v2 or v3
                    # Try to coerce numeric values
                    if isinstance(value, str) and value.isdigit():
                        value = int(value)
                    params[k] = value
            tool_calls.append({
                "id": f"tool_plain_{i}",
                "name": fname,
                "args": params,
            })

        # Deduplicate by (name, args) keeping first occurrence
        return deduplicate_tool_calls(tool_calls)


    def _sanitize_tool_call(self, tc: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and sanitize a parsed tool call.

        - Remove banned params (allNamespaces/output/name/kind)
        - Normalize common parameter names (resource_type -> resourceType)
        - Keep other args unchanged but return sanitized shape.
        """
        if not isinstance(tc, dict):
            return tc
        args = dict(tc.get("args", {}) or {})

        # Normalize keys
        if "resource_type" in args and "resourceType" not in args:
            args["resourceType"] = args.pop("resource_type")
        if "resource" in args and "resourceType" not in args:
            args["resourceType"] = args.pop("resource")

        # Remove banned keys
        for k in ["allNamespaces", "all_namespaces", "allnamespaces", "output", "name", "kind"]:
            if k in args:
                args.pop(k, None)

        sanitized = {"id": tc.get("id"), "name": tc.get("name"), "args": args}

        # If this probe was already executed in a previous run, skip it to avoid repeated probing
        try:
            persisted = _load_persisted_probes()
            probe_key = _probe_key_from_tc(sanitized)
            if probe_key and probe_key in persisted:
                # Returning None indicates caller should drop this tool call
                return None
        except Exception as e:
            logger.warning(f"Error checking persisted probes: {e}")

        return sanitized

    def _ensure_auditor_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Augment tool_calls for the Auditor use case to ensure istio-system checks.

        If the LLM omitted namespaced checks for pods/daemonsets in istio-system, add them.
        This prevents missed evidence when the model queries pods without namespaces.
        """
        # Copy to avoid mutating original
        augmented = list(tool_calls)

        def has_kubectl_get_for(resource_type: str, namespace: str = None):
            for tc in augmented:
                if tc.get("name") == "kubectl_get":
                    args = tc.get("args", {}) or {}
                    rt = args.get("resourceType") or args.get("resource_type") or args.get("resource")
                    ns = args.get("namespace") or args.get("ns")
                    if rt and str(rt).lower() == resource_type.lower():
                        if namespace is None:
                            return True
                        # Allow matching when namespace already present or when explicit None is requested
                        if ns == namespace:
                            return True
            return False

        def is_banned_call(tc: Dict[str, Any]):
            # Ban calls that include unsafe/forbidden params (we want strict kubectl_get/kubectl_describe use only)
            banned_keys = {"allNamespaces", "all_namespaces", "allnamespaces", "output", "name", "kind"}
            args = tc.get("args", {}) or {}
            return any(k in args for k in banned_keys)

        # Remove any banned calls silently (model may still suggest them, we ignore)
        augmented = [tc for tc in augmented if not is_banned_call(tc)]

        # Ensure namespaces are queried (helpful for detecting istio-system)
        persisted = _load_persisted_probes()
        if not has_kubectl_get_for("namespaces"):
            pk = f"namespaces:"
            if pk not in persisted:
                augmented.append({"id": "auto_namespaces", "name": "kubectl_get", "args": {"resourceType": "namespaces"}})

        # Ensure pods in istio-system
        if not has_kubectl_get_for("pods", namespace="istio-system"):
            pk = f"pods:istio-system"
            if pk not in persisted:
                augmented.append({"id": "auto_istio_pods", "name": "kubectl_get", "args": {"resourceType": "pods", "namespace": "istio-system"}})

        # Ensure daemonsets in istio-system
        if not has_kubectl_get_for("daemonsets", namespace="istio-system"):
            pk = f"daemonsets:istio-system"
            if pk not in persisted:
                augmented.append({"id": "auto_istio_daemonsets", "name": "kubectl_get", "args": {"resourceType": "daemonsets", "namespace": "istio-system"}})

        # Deduplicate again (by name and args)
        return deduplicate_tool_calls(augmented)


    def create_chatbot(self, tools, usecase: str) -> Callable[[State], Dict[str, List[AIMessage]]]:
        """Return a node function compatible with LangGraph StateGraph.

        The graph builder is expected to bind tools to the LLM before passing it in,
        so this function uses the provided LLM instance directly.

        Args:
            tools: tools list (unused directly here but available for compatibility)
            usecase: the selected use case string; attached to state for downstream nodes
        """
        llm = self.llm

        def chatbot_node(state: State):
            # Attach the current usecase to state for downstream nodes (best-effort)
            try:
                state["usecase"] = usecase
            except Exception:
                logger.debug("Unable to attach usecase to state")

            messages = state["messages"].copy()

            # Ensure the system prompt is first
            if not messages or not isinstance(messages[0], SystemMessage):
                messages.insert(0, SystemMessage(content=self.system_prompt))

            # For the Zero Trust Auditor use case we must enforce certain data collection rules
            # to ensure `istio-system` is always checked and kubectl_get is used for resources.
            # To do this we append a small, explicit instruction to the last user message so the
            # model is strongly guided to perform namespaced kubectl_get calls (including
            # namespace="istio-system" for pods/daemonsets). This keeps the model-driven
            # behavior but nudges it toward the required checks.
            try:
                last_message = messages[-1]
                # Only augment once: if the enforcement text is not already present, append it.
                enforcement_marker = "IMPORTANT: You MUST use the kubectl_get and kubectl_describe tools"
                usecase_lower = (usecase or "").lower()
                if (
                    usecase_lower
                    and "auditor" in usecase_lower
                    and "comprehensive" not in usecase_lower
                    and not isinstance(last_message, SystemMessage)
                ):
                    if enforcement_marker not in getattr(last_message, "content", ""):
                        enhanced_content = (
                            f"{last_message.content}\n\nIMPORTANT: You MUST use the kubectl_get and kubectl_describe tools to collect real cluster data. "
                            "When checking Pods or DaemonSets, ALWAYS run them with namespace=\"istio-system\" in addition to any other queries. "
                            "Do NOT return mock data or skip namespaced queries."
                        )
                        messages[-1] = type(last_message)(content=enhanced_content)
            except Exception:
                logger.debug("Could not augment last message for Auditor enforcement")

            # Invoke the LLM (assumed to be already bound to tools)
            response = llm.invoke(messages)
            # print(f"LLM Response: {response}")

            # If the model didn't return explicit tool_calls, try to extract JSON-based calls
            if not getattr(response, "tool_calls", []) and isinstance(response.content, str):
                tool_calls = self.extract_and_create_tool_calls(response.content)
                if tool_calls:
                    # sanitize tool calls to remove banned parameters, normalize keys, and drop any
                    # probe that was already executed in a previous run (to prevent re-probing)
                    sanitized = [self._sanitize_tool_call(tc) for tc in tool_calls]
                    # filter out any None entries that indicate dropped tool calls
                    sanitized = [s for s in sanitized if s is not None]
                    response = AIMessage(content=response.content, tool_calls=sanitized)
            
            # Filter out any tool calls that aren't in the bound tools list
            # This prevents hallucinated tools like "Control", "Settings", etc.
            existing_calls = getattr(response, "tool_calls", []) or []
            if existing_calls:
                valid_tool_names = {tool.name for tool in tools} if tools else set()
                filtered_calls = [
                    tc for tc in existing_calls 
                    if tc.get("name") in valid_tool_names
                ]
                if len(filtered_calls) != len(existing_calls):
                    # Some tool calls were invalid, update the response
                    response = AIMessage(content=response.content, tool_calls=filtered_calls)

            # Ensure that for the Auditor use case we always query istio-system for pods/daemonsets
            # if the model didn't explicitly do so. This avoids missing evidence when the model
            # issued pod/daemonset queries without namespaces or skipped them entirely.
            if usecase and "auditor" in usecase.lower():
                # Normalize existing tool_calls from the response
                existing = getattr(response, "tool_calls", []) or []
                augmented = self._ensure_auditor_tool_calls(existing)
                if len(augmented) != len(existing):
                    response = AIMessage(content=response.content, tool_calls=augmented)

            # NOTE: Assessment/synthesis is handled by a dedicated synthesizer node.
            # Chatbot node should only produce AI responses / tool_calls so the graph
            # can route: Chatbot -> Tools -> Synthesizer -> Chatbot/Output.

            return {"messages": [response]}

        return chatbot_node
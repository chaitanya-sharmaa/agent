"""
Graph executor module for running LangGraph workflows.
Handles graph streaming, tool result collection, and probe tracking.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional

from src.langgraphagenticai.core.probe_manager import ProbeManager
from src.langgraphagenticai.utils.cli_output_formatter import CLIOutputFormatter

logger = logging.getLogger(__name__)


class ToolResult:
    """Represents a single tool execution result."""

    def __init__(self, content: str, tool_name: Optional[str], tool_call_id: Optional[str]):
        self.content = content
        self.tool_name = tool_name
        self.tool_call_id = tool_call_id

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "output": self.content,
            "tool_name": self.tool_name,
            "tool_call_id": self.tool_call_id,
        }


class GraphExecutor:
    """Executes LangGraph workflows and collects results."""

    def __init__(
        self,
        formatter: CLIOutputFormatter,
        probe_manager: ProbeManager,
    ):
        """
        Initialize the graph executor.
        
        Args:
            formatter: CLI output formatter instance
            probe_manager: Probe manager for tracking executed probes
        """
        self.formatter = formatter
        self.probe_manager = probe_manager

    @staticmethod
    def _extract_probe_key(resource_type: str, namespace: str = "") -> str:
        """
        Extract a probe key from resource type and namespace.
        
        Args:
            resource_type: Type of Kubernetes resource
            namespace: Namespace (optional)
            
        Returns:
            Formatted probe key
        """
        rt_lower = str(resource_type).lower()
        ns = str(namespace).lower()
        return f"{rt_lower}:{ns}" if ns else f"{rt_lower}:"

    async def execute_graph(
        self,
        graph_obj,
        user_message: str,
        max_events: int = 200,
        stop_on_tool_names: Optional[Set[str]] = None,
        required_probe_prefixes: Optional[Set[str]] = None,
    ) -> Tuple[List[Dict], Set[str]]:
        """
        Execute a LangGraph and collect tool results.
        
        Args:
            graph_obj: Compiled LangGraph instance
            user_message: User input message for the graph
            max_events: Maximum events to process before stopping
            stop_on_tool_names: Set of tool names that trigger early stopping
            required_probe_prefixes: Probe prefixes that must be executed
            
        Returns:
            Tuple of (collected_tool_results, executed_probe_keys)
        """
        collected_tool_results = []
        tool_call_map = {}
        executed_probe_keys = set()
        event_count = 0

        print("\n" + "="*70)
        print("🔍 STARTING AUDIT - Executing LangGraph workflow")
        print("="*70)

        async for event in graph_obj.astream(
            {"messages": [("human", user_message)]},
            {"recursion_limit": 50},
        ):
            event_count += 1
            if event_count > max_events:
                print(f"\n⚠️  Max event iterations ({max_events}) reached; stopping.")
                logger.info("Max event iterations reached; stopping to avoid infinite loop.")
                break

            # Log LLM thinking
            if "chatbot" in event:
                print(f"\n📝 [Event {event_count}] LLM Processing...")
                for msg in event.get("chatbot", {}).get("messages", []):
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        print(f"   → Planning {len(msg.tool_calls)} tool call(s):")
                        for tc in msg.tool_calls:
                            tool_name = tc.get("name", "unknown")
                            args = tc.get("args", {})
                            rt = args.get("resourceType", "?")
                            ns = args.get("namespace", "all")
                            print(f"      • {tool_name}(resourceType='{rt}', namespace='{ns}')")
            
            # Log tool execution
            if "tools" in event:
                print(f"\n⚙️  [Event {event_count}] Executing Tools...")
                for msg in event.get("tools", {}).get("messages", []):
                    content = getattr(msg, "content", None)
                    tool_name = getattr(msg, "tool_name", None)
                    
                    if content and str(content).strip():
                        if "error" in str(content).lower() or "forbidden" in str(content).lower():
                            print(f"   ❌ {tool_name}: ERROR")
                            print(f"      {str(content)[:100]}...")
                        else:
                            lines = str(content).split("\n")
                            print(f"   ✓ {tool_name}: Got {len(lines)} lines of output")

            self.formatter.process_event(event)
            self._process_tool_calls(event, tool_call_map)
            self._process_tool_results(
                event,
                tool_call_map,
                collected_tool_results,
                executed_probe_keys,
                stop_on_tool_names,
            )

            if self._should_stop_early(executed_probe_keys, required_probe_prefixes):
                print(f"\n✅ All required probes executed ({len(executed_probe_keys)} probes)")
                logger.info("All required probes executed; stopping graph.")
                break

        print(f"\n" + "="*70)
        print(f"✅ AUDIT COMPLETE - Processed {event_count} events")
        print(f"   • Tools executed: {len(collected_tool_results)}")
        print(f"   • Probes collected: {len(executed_probe_keys)}")
        print("="*70)

        return collected_tool_results, executed_probe_keys

    def _process_tool_calls(self, event: dict, tool_call_map: dict) -> None:
        """
        Process tool call events and map them.
        
        Args:
            event: Event from graph stream
            tool_call_map: Dictionary to store tool call mappings
        """
        if "chatbot" not in event or not isinstance(event["chatbot"], dict):
            return

        for msg in event["chatbot"].get("messages", []):
            tcalls = getattr(msg, "tool_calls", None) or []
            for tc in tcalls:
                tc_id = tc.get("id")
                if tc_id:
                    tool_call_map[tc_id] = (tc.get("name"), tc.get("args", {}))

    def _process_tool_results(
        self,
        event: dict,
        tool_call_map: dict,
        collected_results: list,
        executed_probes: set,
        stop_on_tool_names: Optional[Set[str]],
    ) -> None:
        """
        Process tool result events.
        
        Args:
            event: Event from graph stream
            tool_call_map: Mapping of tool call IDs to names and args
            collected_results: List to append results to
            executed_probes: Set to track executed probe keys
            stop_on_tool_names: Set of tool names that trigger stopping
        """
        if "tools" not in event or not isinstance(event["tools"], dict):
            return

        for msg in event["tools"].get("messages", []):
            try:
                content = getattr(msg, "content", None)
                tool_name = getattr(msg, "name", None)
                tool_call_id = getattr(msg, "tool_call_id", None)

                if content:
                    collected_results.append(
                        ToolResult(content, tool_name, tool_call_id).to_dict()
                    )

                self._track_probe_execution(
                    tool_call_id, tool_call_map, executed_probes
                )

                if stop_on_tool_names and tool_name in stop_on_tool_names:
                    logger.info(f"Detected tool execution: {tool_name}; stopping.")

            except Exception as e:
                logger.warning(f"Error processing tool result: {e}")
                continue

    def _track_probe_execution(
        self,
        tool_call_id: Optional[str],
        tool_call_map: dict,
        executed_probes: set,
    ) -> None:
        """
        Track probe execution and persist the state.
        
        Args:
            tool_call_id: ID of the tool call
            tool_call_map: Mapping of tool calls to names and args
            executed_probes: Set to add executed probes to
        """
        if not tool_call_id or tool_call_id not in tool_call_map:
            return

        planned_name, planned_args = tool_call_map[tool_call_id]
        resource_type = (planned_args or {}).get("resourceType") or (
            planned_args or {}
        ).get("resource", "")
        namespace = (planned_args or {}).get("namespace", "")

        if resource_type:
            probe_key = self._extract_probe_key(resource_type, namespace)
            executed_probes.add(probe_key)
            self.probe_manager.add_probes({probe_key})

    @staticmethod
    def _should_stop_early(
        executed_probes: set,
        required_prefixes: Optional[Set[str]],
    ) -> bool:
        """
        Check if early stopping condition is met.
        
        Args:
            executed_probes: Set of executed probe keys
            required_prefixes: Required probe prefixes to execute
            
        Returns:
            True if all required probes have been executed
        """
        if not required_prefixes:
            return False

        probes_found = {p.split(":")[0] for p in executed_probes}
        return required_prefixes.issubset(probes_found)

import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.langgraphagenticai.nodes.chatbot_with_Tool_node import ChatbotWithToolNode


def test_ensure_auditor_tool_calls_adds_istio_checks():
    node = ChatbotWithToolNode(model=None, system_prompt="")
    # Tool calls missing namespaces and daemonsets
    existing = [
        {"id": "t1", "name": "kubectl_get", "args": {"resourceType": "pods"}},
    ]

    augmented = node._ensure_auditor_tool_calls(existing)

    # Expect at least pods in istio-system, daemonsets in istio-system and namespaces query
    names = {(tc["name"], tuple(sorted(tc.get("args", {}).items()))) for tc in augmented}

    assert any(tc for tc in augmented if tc.get("name") == "kubectl_get" and tc.get("args", {}).get("resourceType") == "namespaces")
    assert any(tc for tc in augmented if tc.get("name") == "kubectl_get" and tc.get("args", {}).get("resourceType") == "pods" and tc.get("args", {}).get("namespace") == "istio-system")
    assert any(tc for tc in augmented if tc.get("name") == "kubectl_get" and tc.get("args", {}).get("resourceType") == "daemonsets" and tc.get("args", {}).get("namespace") == "istio-system")

import os
import sys
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.langgraphagenticai.nodes.synthesizer_node import create_synthesizer_node
from langchain_core.messages import ToolMessage


def fake_tool_message(content, tool_call_id=None):
    # ToolMessage requires tool_call_id on construction; include a tool_name for UI clarity
    return ToolMessage(content=content, tool_call_id=tool_call_id, tool_name="kubectl_get")


def test_synthesizer_filters_error_outputs_and_dedups():
    node = create_synthesizer_node()

    # First call: include an error output and valid pods/daemonset outputs
    state = {
        "messages": [
            fake_tool_message('Error: Status is not a valid tool, try one of [kubectl_get, kubectl_describe].', tool_call_id="t1"),
            fake_tool_message('{"items": [{"kind": "Namespace", "metadata": {"name": "istio-system"}}]}', tool_call_id="t2"),
            fake_tool_message('{"items": [{"kind": "Pod", "metadata": {"name": "istio-ingressgateway-123", "namespace": "istio-system"}}]}', tool_call_id="t3"),
            fake_tool_message('{"items": [{"kind": "DaemonSet", "metadata": {"name": "ztunnel"}}]}', tool_call_id="t4"),
        ],
        "tool_results_cache": []
    }

    out1 = node(state)
    # First invocation should emit an assessment
    assert isinstance(out1, dict)
    assert "messages" in out1 and len(out1["messages"]) == 1
    content1 = out1["messages"][0].content
    assert "Zero Trust Security Assessment" in content1
    assert "ztunnel" in content1.lower()

    # Second call with identical inputs should not emit anything (dedup)
    out2 = node(state)
    assert out2 == {}

    # If we add a new valid tool output (e.g., a PeerAuthentication), a new assessment should be emitted
    state["messages"].append(fake_tool_message('{"items": [{"kind": "PeerAuthentication", "metadata": {"name": "default", "namespace": "istio-system"}, "spec": {"mtls": {"mode": "STRICT"}}}]}', tool_call_id="t5"))
    out3 = node(state)
    assert isinstance(out3, dict) and "messages" in out3 and len(out3["messages"]) == 1
    content3 = out3["messages"][0].content
    assert "Zero Trust Security Assessment" in content3
    assert content3 != content1

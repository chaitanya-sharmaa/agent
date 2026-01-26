from src.langgraphagenticai.nodes.synthesizer_node import create_synthesizer_node


def test_synthesizer_generates_assessment():
    node = create_synthesizer_node()
    # Provide minimal tool_results_cache; analyzer expects items but will handle
    state = {"tool_results_cache": [{"output": "items: []"}]}
    out = node(state)
    assert isinstance(out, dict)
    assert "messages" in out
    msgs = out["messages"]
    assert len(msgs) >= 1
    # The synthesizer prefixes content with header
    assert any("Zero Trust Security Assessment" in (getattr(m, "content", "") or "") for m in msgs)

import os
import sys
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer


def test_evidence_provenance_marking():
    analyzer = ZeroTrustAnalyzer()

    # Tool result that comes from an actual kubectl execution (has tool_call_id and tool_name)
    pods = {"items": [{"kind": "Pod", "metadata": {"name": "istiod-1", "namespace": "istio-system"}}]}
    # Tool result that is unverified (no tool_call_id / simulated LLM output)
    fake_pod = {"items": [{"kind": "Pod", "metadata": {"name": "fake-pod-xyz", "namespace": "istio-system"}}]}

    tool_results = [
        {"output": json.dumps(pods), "tool_call_id": "t-pods", "tool_name": "kubectl_get"},
        {"output": json.dumps(fake_pod)}
    ]

    report = analyzer.analyze_and_generate_report(tool_results)
    # Evidence should include the real pod with source and the fake one as unverified
    assert "istiod-1" in report
    assert "kubectl_get:t-pods" in report
    assert "fake-pod-xyz" in report
    assert "[unverified]" in report

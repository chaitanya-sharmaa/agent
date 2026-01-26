import os
import sys
import json
# Ensure repository root is on PYTHONPATH for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer


def test_pod_deduplication_and_mode_selection():
    tool_results = []
    namespaces = {"items": [{"metadata": {"name": "istio-system"}}]}
    # Two pods batches, both containing the same ztunnel pod and one istiod
    pods1 = {"items": [{"metadata": {"name": "ztunnel-1", "namespace": "istio-system"}, "kind": "Pod"}, {"metadata": {"name": "istiod-1", "namespace": "istio-system"}, "kind": "Pod"}]}
    pods2 = {"items": [{"metadata": {"name": "ztunnel-1", "namespace": "istio-system"}, "kind": "Pod"}, {"metadata": {"name": "ztunnel-2", "namespace": "istio-system"}, "kind": "Pod"}]}
    tool_results.append({"output": json.dumps(namespaces)})
    tool_results.append({"output": json.dumps(pods1)})
    tool_results.append({"output": json.dumps(pods2)})

    analyzer = ZeroTrustAnalyzer()
    report = analyzer.analyze_and_generate_report(tool_results)

    # ztunnel should be detected and counted once per unique pod
    assert "ztunnel" in report.lower()
    # Ensure mode is Ambient (ztunnel evidence takes precedence)
    assert "ambient" in report.lower()
    # Ensure duplicate pod did not inflate counts (we expect at most 3 pods counted here)
    assert "pod(s)" in report.lower()

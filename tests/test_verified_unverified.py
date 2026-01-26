import os
import sys
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer


def test_unverified_pod_does_not_claim_istio_installed():
    analyzer = ZeroTrustAnalyzer()

    # Only unverified pod evidence present (no tool_call_id/tool_name)
    tool_results = [
        {"output": json.dumps({"items": [{"kind": "Pod", "metadata": {"name": "istio-ingressgateway-XYZ", "namespace": "istio-system"}}]})}
    ]

    report = analyzer.analyze_and_generate_report(tool_results)
    # Expect the report to either indicate unverified evidence or no components found
    r = report.lower()
    assert ("unverified" in r) or ("no istio components found" in r)


def test_verified_daemonset_claims_istio_installed():
    analyzer = ZeroTrustAnalyzer()

    # Verified daemonset and unverified pod together: installation should be confirmed due to verified daemonset
    tool_results = [
        {"output": json.dumps({"items": [{"kind": "Pod", "metadata": {"name": "istio-ingressgateway-XYZ", "namespace": "istio-system"}}]})},
        {"output": json.dumps({"items": [{"kind": "DaemonSet", "metadata": {"name": "ztunnel"}}]}), "tool_call_id": "t1", "tool_name": "kubectl_get"}
    ]

    report = analyzer.analyze_and_generate_report(tool_results)
    assert "Found ztunnel daemonset" in report and "verified" in report

import json
import sys
import pathlib

# Ensure project src/ is importable when running tests from workspace root
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer


def test_integration_synthesizer_detects_istio_and_networkpolicy():
    # Simulate tool outputs (list of tool result dicts as used by analyzer)
    tool_results = []

    namespaces = {"items": [{"metadata": {"name": "default"}, "kind": "Namespace"}, {"metadata": {"name": "istio-system"}, "kind": "Namespace"}]}
    pods = {"items": [{"metadata": {"name": "istiod-abc123", "namespace": "istio-system"}, "kind": "Pod"}, {"metadata": {"name": "bookinfo-gateway-istio-5456", "namespace": "default"}, "kind": "Pod"}]}
    networkpolicies = {"items": [{"metadata": {"name": "default-deny", "namespace": "default"}, "kind": "NetworkPolicy", "spec": {}}]}

    tool_results.append({"output": json.dumps(namespaces)})
    tool_results.append({"output": json.dumps(pods)})
    tool_results.append({"output": json.dumps(networkpolicies)})

    analyzer = ZeroTrustAnalyzer()
    report = analyzer.analyze_and_generate_report(tool_results)

    assert "Istio installed" in report
    assert "Yes" in report or "Found" in report
    assert "NetworkPolicies" in report

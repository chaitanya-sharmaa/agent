import json
import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer


def test_ztunnel_detected_as_ambient_when_daemonset_present():
    tool_results = []
    namespaces = {"items": [{"metadata": {"name": "istio-system"}}]}
    daemonsets = {"items": [{"metadata": {"name": "ztunnel", "namespace": "istio-system"}, "kind": "DaemonSet"}]}
    tool_results.append({"output": json.dumps(namespaces)})
    tool_results.append({"output": json.dumps(daemonsets)})

    analyzer = ZeroTrustAnalyzer()
    report = analyzer.analyze_and_generate_report(tool_results)

    assert "Istio installed" in report
    assert "ztunnel" in report.lower() or "ambient" in report.lower()


def test_ztunnel_detected_as_ambient_when_pods_present():
    tool_results = []
    namespaces = {"items": [{"metadata": {"name": "istio-system"}}]}
    pods = {"items": [{"metadata": {"name": "ztunnel-bsjmx", "namespace": "istio-system"}, "kind": "Pod"}]}
    tool_results.append({"output": json.dumps(namespaces)})
    tool_results.append({"output": json.dumps(pods)})

    analyzer = ZeroTrustAnalyzer()
    report = analyzer.analyze_and_generate_report(tool_results)

    assert "Istio installed" in report
    assert "ztunnel" in report.lower() or "ambient" in report.lower()

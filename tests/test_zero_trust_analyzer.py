from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer


def test_istio_detected_from_namespaces_and_pods():
    analyzer = ZeroTrustAnalyzer()

    # Simulate tool results: namespaces show istio-system (top-level 'name' fields)
    namespaces_output = {
        "output": '{\n  "items": [\n    {"name": "default", "kind": "Namespace"},\n    {"name": "istio-system", "kind": "Namespace"}\n  ]\n}'
    }

    # Pods returned for default namespace but one pod name indicates istio
    pods_output = {
        "output": '{\n  "items": [\n    {"name": "bookinfo-gateway-istio-545686b59d-8wkcs", "namespace": "default", "kind": "Pod"}\n  ]\n}'
    }

    # No daemonsets or peer/authz/networkpolicies in this test
    tool_results = [namespaces_output, pods_output]

    report = analyzer.analyze_and_generate_report(tool_results)

    assert "Istio installed" in report
    # Expect yes because istio-system namespace exists
    assert "Istio installed" in report and "Yes" in report.split("Istio installed")[1]

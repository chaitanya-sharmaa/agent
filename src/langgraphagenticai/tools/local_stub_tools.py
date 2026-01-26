import asyncio
import json
from typing import List, Dict, Any

# Minimal stubs that mimic a kubectl_get tool response shape for testing
async def kubectl_get_stub(resourceType: str = None, name: str = None) -> Dict[str, Any]:
    """Stub implementation of kubectl_get for testing.

    Returns small realistic payloads for common resource types so the analyzer
    can detect Istio / mTLS / network policy state for offline testing.
    """
    # Return small realistic payloads for common resource types
    if resourceType == "namespaces":
        return {"items": [{"kind": "Namespace", "metadata": {"name": "default"}}, {"kind": "Namespace", "metadata": {"name": "istio-system"}}]}
    if resourceType == "pods":
        # Return a pod inside istio-system
        return {"items": [{"kind": "Pod", "metadata": {"name": "istio-ingressgateway-123", "namespace": "istio-system"}}]}
    if resourceType == "daemonsets":
        return {"items": [{"kind": "DaemonSet", "metadata": {"name": "ztunnel"}}]}
    if resourceType == "deployments":
        return {"items": [{"kind": "Deployment", "metadata": {"name": "istio-nginx"}}]}
    if resourceType == "networkpolicies":
        return {"items": []}
    # Generic fallback
    return {"items": []}

async def kubectl_describe_stub(resourceType: str = None, name: str = None) -> Dict[str, Any]:
    """Return a descriptive sample for a single resource or an empty not-found style result.

    For types we don't have explicit fixtures for, return an empty 'items' list so the analyzer
    treats the resource as absent instead of presenting a misleading record.
    """
    # Provide an explicit example for some known types
    if resourceType == "peerauthentication":
        # In many clusters PeerAuthentication resources are absent; return empty result
        return {"items": []}
    if resourceType == "authorizationpolicy":
        return {"items": []}
    # If name and resourceType provided and we know of it, return a small descriptive object
    if resourceType == "deployment" and name == "istio-nginx":
        return {"kind": "Deployment", "metadata": {"name": name}, "status": {"availableReplicas": 1}}
    if resourceType == "pod" and name and "istio" in name:
        return {"kind": "Pod", "metadata": {"name": name, "namespace": "istio-system"}, "status": {"phase": "Running"}}
    # Generic not-found style
    return {"items": []}


def make_stub_tools():
    """Return a list of Tool objects compatible with ToolNode.
    We create very lightweight Tool objects using langgraph.prebuilt.Tool wrapper if available,
    or fallback to plain callables in a dict that the ToolNode may accept.
    """
    try:
        from langgraph.prebuilt import Tool
        tools = [
            Tool(name="kubectl_get", func=kubectl_get_stub, description="Stub kubectl_get"),
            Tool(name="kubectl_describe", func=kubectl_describe_stub, description="Stub kubectl_describe"),
            Tool(name="upgrade_helm_chart", func=upgrade_helm_chart_stub, description="Stub upgrade_helm_chart"),
            Tool(name="install_helm_chart", func=install_helm_chart_stub, description="Stub install_helm_chart"),
        ]
        return tools
    except Exception:
        # Fall back to plain dict forms (ensure callables have names and docstrings so langchain StructuredTool.from_function succeeds)
        async def upgrade_helm_chart_stub(*args, **kwargs):
            """Stubbed upgrade helm chart callable used in fallback tool list."""
            return {"status": "ok", "action": "upgrade", "args": {"args": args, "kwargs": kwargs}}

        async def install_helm_chart_stub(*args, **kwargs):
            """Stubbed install helm chart callable used in fallback tool list."""
            return {"status": "ok", "action": "install", "args": {"args": args, "kwargs": kwargs}}

        return [
            {"name": "kubectl_get", "func": kubectl_get_stub},
            {"name": "kubectl_describe", "func": kubectl_describe_stub},
            {"name": "upgrade_helm_chart", "func": upgrade_helm_chart_stub},
            {"name": "install_helm_chart", "func": install_helm_chart_stub},
        ]

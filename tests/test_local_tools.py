import sys, os
# Ensure project root is on sys.path so tests can import 'src' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from src.langgraphagenticai.tools.kubernetes_tool import get_tools


def test_local_stubs_include_helm_tools():
    tools = asyncio.get_event_loop().run_until_complete(get_tools())
    # tools can be tool objects or dicts; normalize names
    names = set()
    for t in tools:
        if hasattr(t, "name"):
            names.add(getattr(t, "name"))
        elif isinstance(t, dict):
            names.add(t.get("name"))
    assert "upgrade_helm_chart" in names
    assert "install_helm_chart" in names

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    _HAS_MCP = True
except Exception:
    _HAS_MCP = False

from langgraph.prebuilt import ToolNode
import asyncio
import logging
from src.langgraphagenticai.tools.local_stub_tools import make_stub_tools
from src.langgraphagenticai.config.config_loader import get_config

logger = logging.getLogger(__name__)


async def get_tools():
    """
    Return the list of tools to be used. Prefer MCP-backed tools; if unavailable,
    return local stub tools to allow offline testing.
    """
    if _HAS_MCP:
        config = get_config()
        url = config.get_mcp_url()
        transport = config.get_mcp_transport()
        client = MultiServerMCPClient(
            {
                "kubernetes": {
                    "url": url,
                    "transport": transport,
                }
            }
        )
        tools = await client.get_tools()
        return tools

    logger.warning("langchain_mcp_adapters not available; using local stub tools for offline testing")
    # Return lightweight stubs usable by ToolNode
    return make_stub_tools()


def create_tool_node(tools):
    """Create and return a ToolNode; handle both real Tool objects and fallback dicts or callables.

    For dict fallbacks we convert them into simple async callables with a proper __name__ so
    LangGraph/ToolNode can accept them.
    """
    normalized = []
    for t in tools:
        # Already a callable/function: ensure it has a name
        if callable(t) and hasattr(t, "__name__"):
            normalized.append(t)
            continue

        # If it's a dict fallback, try to extract the callable
        if isinstance(t, dict) and "func" in t:
            func = t.get("func")
            name = t.get("name") or getattr(func, "__name__", None) or "unnamed_tool"

            # If the func exists, wrap if needed to guarantee correct signature/name
            if callable(func):
                # Ensure __name__ matches the expected tool name
                try:
                    func.__name__ = name
                except Exception:
                    # Some callables don't allow setting __name__; wrap instead
                    async def _wrapper(*args, __func=func, **kwargs):
                        if asyncio.iscoroutinefunction(__func):
                            return await __func(*args, **kwargs)
                        return __func(*args, **kwargs)
                    _wrapper.__name__ = name
                    normalized.append(_wrapper)
                    continue
                normalized.append(func)
                continue

        # Fallback: append as-is and let ToolNode raise a helpful error if unsupported
        normalized.append(t)

    return ToolNode(tools=normalized, handle_tool_errors=True)
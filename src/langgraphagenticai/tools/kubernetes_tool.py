from langchain_mcp_adapters.client import MultiServerMCPClient

from langgraph.prebuilt import ToolNode
import asyncio
import logging

from src.langgraphagenticai.config.config_loader import get_config

logger = logging.getLogger(__name__)


async def get_tools():
    """
    Return the list of MCP-backed tools.
    Requires langchain_mcp_adapters and accessible MCP server.
    Will raise an error if MCP tools cannot be loaded.
    """
    try:
        config = get_config()
        base_url = config.get_mcp_url()
        client = MultiServerMCPClient(
            {
                "kubernetes": {
                    "url": f"{base_url}/mcp",
                    "transport": "streamable_http",
                }
            }
        )
        tools = await client.get_tools()
        if not tools:
            raise ValueError("MCP server returned no tools")
        logger.info(f"✓ Loaded {len(tools)} tools from MCP server")
        return tools
    except ImportError as e:
        raise ImportError(
            f"langchain_mcp_adapters not available. Install with: "
            f"pip install langchain-mcp-adapters. Error: {e}"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Failed to load MCP tools from http://48.194.37.51:3001/mcp. "
            f"Ensure MCP server is running and accessible. Error: {e}"
        ) from e


def create_tool_node(tools):
    """Create and return a ToolNode with strict validation.
    
    Requires proper Tool objects from MCP. Does not support fallbacks or stubs.
    
    Args:
        tools: List of langchain Tool objects from MCP
        
    Returns:
        ToolNode configured to handle tool execution errors
        
    Raises:
        ValueError: If tools list is empty or contains invalid tools
    """
    if not tools:
        raise ValueError("No tools provided to create_tool_node")
    
    # Validate all tools are proper objects with required attributes
    for t in tools:
        if not hasattr(t, 'name') or not hasattr(t, 'func'):
            raise ValueError(
                f"Invalid tool object: {t}. "
                f"Tools must have 'name' and 'func' attributes from MCP. "
                f"Stubs and fallback callables are not supported."
            )
    
    logger.info(f"✓ Creating ToolNode with {len(tools)} MCP tools")
    return ToolNode(tools=tools, handle_tool_errors=True)
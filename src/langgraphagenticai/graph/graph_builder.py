"""GraphBuilder

Clean, documented builder for AgenticAI flows. Provides explicit methods to
construct independent, isolated graphs for each supported use case so future
changes to one flow won't impact another.

Now configuration-driven: reads prompts from config/prompts.yaml
"""

import asyncio
from langgraph.graph import StateGraph
from src.langgraphagenticai.state.state import State
from src.langgraphagenticai.nodes.chatbot_with_Tool_node import ChatbotWithToolNode
from src.langgraphagenticai.tools.kubernetes_tool import get_tools, create_tool_node
from langgraph.prebuilt import tools_condition
from src.langgraphagenticai.config.config_loader import get_config


class GraphBuilder:
    """Build and compile graphs for distinct use cases.

    Each public builder method returns a compiled graph instance that is
    isolated to the requested use case. The compiled graph has an attribute
    `_agenticai_model` attached (when possible) to help higher-level code
    spawn additional graphs using the same model instance (e.g. run AUDITOR
    pass even when the UI was started in CREATOR mode).
    
    Configuration is loaded from config/ directory, making this reusable
    across different MCP servers and workflows without code changes.
    """

    def __init__(self, model, config=None):
        self.llm = model
        self.config = config or get_config()

    async def _base_graph(self, system_prompt: str, workflow_id: str):
        """Create the common nodes (chatbot + tools) and compile the StateGraph.

        The chatbot node is bound to a model that has tools attached so it can
        produce tool_calls. The tools node is created from `get_tools` which
        uses MCP to fetch real tools from the Kubernetes server.
        """
        tools = await get_tools()
        tool_node = create_tool_node(tools)

        # Bind tools to the LLM so it can emit tool_calls
        llm_with_tools = self.llm.bind_tools(tools)
        workflow_name = self.config.get_workflow_name(workflow_id)
        chatbot_node = ChatbotWithToolNode(llm_with_tools, system_prompt).create_chatbot(tools, workflow_name)

        sg = StateGraph(State)
        sg.add_node("chatbot", chatbot_node)
        sg.add_node("tools", tool_node)
        sg.set_entry_point("chatbot")
        sg.add_conditional_edges("chatbot", tools_condition)

        compiled = sg.compile()
        try:
            setattr(compiled, "_agenticai_model", self.llm)
        except Exception:
            pass
        return compiled

    async def build_graph(self, workflow_id: str):
        """Build a graph for the specified workflow ID.
        
        Args:
            workflow_id: ID of the workflow (from config/prompts.yaml)
        
        Returns:
            Compiled LangGraph StateGraph
        
        Raises:
            ValueError: If workflow not found in configuration
        """
        system_prompt = self.config.get_workflow_system_prompt(workflow_id)
        return await self._base_graph(system_prompt, workflow_id)

    async def build_auditor_graph(self):
        """Return a compiled graph for the Zero Trust Auditor use case.
        Reads prompt from config/prompts.yaml::workflows.auditor.system_prompt
        """
        return await self.build_graph("auditor")

    async def build_creator_graph(self):
        """Return a compiled graph for the Zero Trust Creator use case.
        Reads prompt from config/prompts.yaml::workflows.creator.system_prompt
        """
        return await self.build_graph("creator")

    async def setup_graph(self, workflow_id: str):
        """Build graph for any configured workflow.
        
        Args:
            workflow_id: Workflow identifier or friendly name
        
        Returns:
            Compiled graph
        """
        # Support both workflow IDs and friendly names
        workflows = self.config.get_workflows()
        
        # Try direct ID lookup
        if workflow_id in workflows:
            return await self.build_graph(workflow_id)
        
        # Try by friendly name
        for wf_id, wf_config in workflows.items():
            if wf_config.get('name') == workflow_id:
                return await self.build_graph(wf_id)
        
        raise ValueError(f"Workflow not found: {workflow_id}")







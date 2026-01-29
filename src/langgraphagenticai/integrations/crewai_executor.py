"""
Crew AI Executor - Multi-agent orchestration via Crew AI.

Integrates Crew AI as an alternative execution engine to LangGraph.
Supports both single master agent and multi-agent collaboration with specialized agents.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional, Any
import asyncio
import os

try:
    from crewai import Agent, Task, Crew
    from crewai.llm import LLM
except ImportError:
    raise ImportError("crewai not found. Install with: pip install crewai crewai-tools")

from src.langgraphagenticai.core.probe_manager import ProbeManager
from src.langgraphagenticai.config.config_loader import ConfigLoader
from src.langgraphagenticai.utils.cli_output_formatter import CLIOutputFormatter

logger = logging.getLogger(__name__)


class CrewAIExecutor:
    """Execute workflows using Crew AI multi-agent orchestration."""

    def __init__(
        self,
        formatter: CLIOutputFormatter,
        probe_manager: ProbeManager,
        config: ConfigLoader,
        llm_model=None,  # LangChain LLM instance (not used; Crew AI creates its own)
    ):
        """
        Initialize Crew AI executor.
        
        Args:
            formatter: CLI output formatter instance
            probe_manager: Probe manager for tracking executed probes
            config: Configuration loader instance
            llm_model: LangChain LLM model instance (ignored; Crew AI manages LLM)
        """
        self.formatter = formatter
        self.probe_manager = probe_manager
        self.config = config
        self.tool_call_count = 0
        self.max_tool_calls = 100
        self.crew_llm = self._create_crew_llm()

    def _create_crew_llm(self) -> Optional[LLM]:
        """
        Create a Crew AI compatible LLM instance from configuration.
        
        Returns:
            Crew AI LLM instance or None
        """
        try:
            llm_config = self.config.get_llm_config()
            provider = llm_config.get('provider', 'ollama').lower()
            
            if provider == 'ollama':
                model = llm_config.get('model', 'mistral:latest')
                base_url = llm_config.get('endpoint', 'http://localhost:11434')
                
                # Create Crew AI compatible LLM for Ollama
                crew_llm = LLM(
                    model=model,
                    base_url=base_url,
                    temperature=llm_config.get('temperature', 0.3),
                )
                logger.info(f"✓ Initialized Crew AI LLM: {model} at {base_url}")
                return crew_llm
            
            elif provider == 'openai':
                model = llm_config.get('model', 'gpt-4')
                api_key = os.environ.get('OPENAI_API_KEY')
                
                if not api_key:
                    logger.warning("OPENAI_API_KEY not set; OpenAI provider will not work")
                    return None
                
                # Create Crew AI compatible LLM for OpenAI
                crew_llm = LLM(
                    model=model,
                    temperature=llm_config.get('temperature', 0.3),
                )
                logger.info(f"✓ Initialized Crew AI LLM: {model} (OpenAI)")
                return crew_llm
            
            else:
                logger.warning(f"Unsupported LLM provider: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create Crew AI LLM: {e}")
            return None

    def _create_master_agent(self, workflow_id: str) -> Agent:
        """
        Create the master/coordinator agent.
        
        Args:
            workflow_id: The workflow being executed
            
        Returns:
            Configured Crew AI Agent instance
        """
        master_config = self.config.get_crew_ai_master_agent()
        delegation_enabled = self.config.get_crew_ai_delegation_enabled()

        agent = Agent(
            role=master_config.get('role', 'Coordinator'),
            goal=master_config.get('goal', 'Execute tasks'),
            backstory=master_config.get('backstory', 'Helpful assistant'),
            verbose=True,
            allow_delegation=delegation_enabled,
            llm=self.crew_llm,  # ← Use Crew AI LLM
        )

        return agent

    def _create_specialized_agents(self, workflow_id: str) -> List[Agent]:
        """
        Create specialized agents for multi-agent collaboration.
        
        Args:
            workflow_id: The workflow being executed
            
        Returns:
            List of configured Agent instances
        """
        agents = []
        agent_configs = self.config.get_crew_ai_specialized_agents(workflow_id)
        
        for agent_config in agent_configs:
            agent = Agent(
                role=agent_config.get('role', 'Assistant'),
                goal=agent_config.get('goal', 'Help with tasks'),
                backstory=agent_config.get('backstory', 'Helpful assistant'),
                verbose=True,
                allow_delegation=False,  # Specialized agents don't delegate
                llm=self.crew_llm,  # ← Use Crew AI LLM
            )
            agents.append(agent)
        
        return agents

    def _create_workflow_tasks(
        self, 
        workflow_id: str, 
        user_message: str,
        master_agent: Agent,
        specialized_agents: List[Agent]
    ) -> List[Task]:
        """
        Create tasks for the workflow.
        
        Args:
            workflow_id: The workflow being executed
            user_message: Main user message
            master_agent: Master coordinator agent
            specialized_agents: List of specialized agents
            
        Returns:
            List of Task instances
        """
        tasks = []
        agent_configs = self.config.get_crew_ai_specialized_agents(workflow_id)
        
        # Create specialized agent tasks
        if specialized_agents and agent_configs:
            for i, (agent_config, agent) in enumerate(zip(agent_configs, specialized_agents)):
                agent_role = agent_config.get('role', 'Assistant')
                task_description = self._get_task_description(workflow_id, agent_config['id'], user_message)
                
                task = Task(
                    description=task_description,
                    agent=agent,
                    expected_output=f"{agent_role} findings and analysis",
                )
                tasks.append(task)
        
        # Create master task that coordinates and synthesizes results
        coordinator_task = Task(
            description=f"Coordinate and synthesize findings from all agents:\n{user_message}",
            agent=master_agent,
            expected_output="Final comprehensive analysis and recommendations",
        )
        tasks.append(coordinator_task)
        
        return tasks

    def _get_task_description(self, workflow_id: str, agent_id: str, user_message: str) -> str:
        """Get task description for a specialized agent."""
        if agent_id == "data_collector":
            return f"Collect comprehensive Kubernetes cluster data using available tools. {user_message}"
        elif agent_id == "security_analyzer":
            return f"Analyze security misconfigurations and vulnerabilities. {user_message}"
        elif agent_id == "compliance_checker":
            return f"Verify compliance with NIST, CIS, and NSA/CISA standards. {user_message}"
        elif agent_id == "policy_creator":
            return f"Create remediation policies and security configurations. {user_message}"
        else:
            return user_message

    async def execute_workflow(
        self,
        workflow_id: str,
        user_message: str,
        tools: List[Any],  # MCP tools
        max_tool_calls: Optional[int] = None,
    ) -> Tuple[List[Dict], Set[str]]:
        """
        Execute a workflow using Crew AI with multi-agent collaboration.
        
        Args:
            workflow_id: ID of workflow to execute
            user_message: User input message
            tools: List of MCP tools available
            max_tool_calls: Max tool calls before stopping (from config if not provided)
            
        Returns:
            Tuple of (tool_results, executed_probes)
        """
        if max_tool_calls is None:
            max_tool_calls = self.config.get_crew_ai_tool_budget(workflow_id)
        
        self.max_tool_calls = max_tool_calls
        self.tool_call_count = 0

        print("\n" + "=" * 70)
        print(f"🤖 CREW AI MULTI-AGENT EXECUTION - Workflow: {workflow_id}")
        print("=" * 70)

        collected_results = []
        executed_probes = set()

        try:
            # Create master agent
            master_agent = self._create_master_agent(workflow_id)
            print(f"\n✓ Master Agent: {master_agent.role}")

            # Create specialized agents
            specialized_agents = self._create_specialized_agents(workflow_id)
            if specialized_agents:
                print(f"✓ Specialized Agents ({len(specialized_agents)}):")
                agent_configs = self.config.get_crew_ai_specialized_agents(workflow_id)
                for agent, config in zip(specialized_agents, agent_configs):
                    print(f"  - {agent.role}")
            
            print(f"\nBudget: {max_tool_calls} tool calls")
            print(f"Max Iterations: {self.config.get_crew_ai_max_iterations()}")
            print(f"Delegation Enabled: {self.config.get_crew_ai_delegation_enabled()}")

            # Create tasks for all agents
            all_agents = [master_agent] + specialized_agents
            tasks = self._create_workflow_tasks(
                workflow_id, 
                user_message, 
                master_agent,
                specialized_agents
            )

            print(f"✓ Created {len(tasks)} tasks for agent coordination")

            # Create crew with all agents
            crew = Crew(
                agents=all_agents,
                tasks=tasks,
                verbose=True,
                max_iter=self.config.get_crew_ai_max_iterations(),
            )

            print(f"✓ Crew assembled: {len(all_agents)} agents, {len(tasks)} tasks")
            print(f"✓ Running crew execution...\n")

            # Run crew (synchronous call wrapped in async context)
            result = await asyncio.to_thread(crew.kickoff)

            print(f"\n✓ Crew execution completed")
            print(f"  Tool calls used: {self.tool_call_count}/{self.max_tool_calls}")
            print(f"  Agents acted: {len(all_agents)}")

            # Parse results from crew output
            if result:
                collected_results.append({
                    "tool_name": "crew_ai_multi_agent",
                    "output": str(result),
                    "tool_call_id": "crew_synthesis_task",
                })

            return collected_results, executed_probes

        except Exception as e:
            logger.error(f"Crew AI execution failed: {e}", exc_info=True)
            print(f"\n❌ Crew AI execution failed: {e}")
            raise

    @staticmethod
    def _extract_probe_key(resource_type: str, namespace: str = "") -> str:
        """Extract probe key from resource type and namespace."""
        rt_lower = str(resource_type).lower()
        ns = str(namespace).lower()
        return f"{rt_lower}:{ns}" if ns else f"{rt_lower}:"

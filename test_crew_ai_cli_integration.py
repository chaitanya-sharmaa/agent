#!/usr/bin/env python3
"""
Test script to verify multi-agent Crew AI integration with CLI.
This demonstrates running the auditor workflow with Crew AI multi-agent orchestration.
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.langgraphagenticai.config.config_loader import get_config
from src.langgraphagenticai.core.cli_orchestrator import CLIOrchestrator
from src.langgraphagenticai.core.graph_executor import GraphExecutor
from src.langgraphagenticai.core.probe_manager import ProbeManager
from src.langgraphagenticai.graph.graph_builder import GraphBuilder
from src.langgraphagenticai.LLMS.ollamallm import OllamaLLM
from src.langgraphagenticai.utils.cli_output_formatter import CLIOutputFormatter
from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer
from src.langgraphagenticai.utils.live_logger import get_live_logger

logger_obj = get_live_logger()

async def test_crew_ai_integration():
    """Test multi-agent Crew AI orchestration through CLI."""
    
    print("\n" + "=" * 70)
    print("MULTI-AGENT CREW AI INTEGRATION TEST")
    print("=".ljust(70, "="))
    
    try:
        # Load configuration
        config = get_config()
        execution_engine = config.get_execution_engine()
        
        print(f"\n📋 Configuration:")
        print(f"   Execution Engine: {execution_engine}")
        print(f"   Delegation Enabled: {config.get_crew_ai_delegation_enabled()}")
        print(f"   Memory Enabled: {config.get_crew_ai_memory_enabled()}")
        
        if execution_engine == "crew_ai":
            agents = config.get_crew_ai_specialized_agents("auditor")
            print(f"   Specialized Agents: {len(agents)}")
            for agent in agents:
                status = "✓" if agent.get('enabled', True) else "○"
                print(f"     {status} {agent.get('role')}")
        
        # Initialize components
        print(f"\n🔧 Initializing components...")
        llm_config = config.get_llm_config()
        model = OllamaLLM(llm_config).get_llm_model()
        
        if not model:
            print("❌ Failed to initialize LLM model")
            return False
        
        print("   ✓ LLM Model initialized")
        
        graph_builder = GraphBuilder(model, config)
        print("   ✓ Graph Builder created")
        
        probe_manager = ProbeManager("/tmp/executed_probes.json")
        formatter = CLIOutputFormatter(show_raw_output=True)
        executor = GraphExecutor(formatter, probe_manager)
        print("   ✓ Graph Executor created")
        
        analyzer = ZeroTrustAnalyzer()
        print("   ✓ Security Analyzer created")
        
        # Create orchestrator with LLM model for Crew AI
        print(f"\n🎯 Creating CLI Orchestrator with execution engine: {execution_engine}")
        orchestrator = CLIOrchestrator(
            graph_builder,
            executor,
            analyzer,
            config=config,
            llm_model=model
        )
        print(f"   ✓ Orchestrator created")
        print(f"   Execution Engine: {orchestrator.execution_engine}")
        
        if orchestrator.execution_engine == "crew_ai":
            if orchestrator.crew_ai_executor:
                print("   ✓ Crew AI executor initialized")
                print("   ✓ Ready for multi-agent orchestration")
            else:
                print("   ⚠ Crew AI executor not initialized")
                return False
        
        # Test workflow execution
        print(f"\n🚀 Testing {orchestrator.execution_engine} auditor workflow...")
        print("   (Note: This will attempt to connect to Kubernetes cluster)")
        print("   (Set KUBECONFIG or ensure kubectl is configured)")
        
        if orchestrator.execution_engine == "crew_ai":
            print("\n   Crew AI Agents will coordinate:")
            agents = config.get_crew_ai_specialized_agents("auditor")
            master = config.get_crew_ai_master_agent()
            print(f"   - Master Agent: {master.get('role')}")
            for agent in agents:
                if agent.get('enabled', True):
                    print(f"   - {agent.get('role')}")
        
        print("\n   Starting workflow execution...")
        print("   (This may take 1-5 minutes depending on cluster size)")
        print("   Press Ctrl+C to cancel")
        
        await orchestrator.run_auditor()
        
        print("\n✅ Workflow completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main entry point."""
    success = await test_crew_ai_integration()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ MULTI-AGENT CREW AI INTEGRATION TEST PASSED")
    else:
        print("❌ MULTI-AGENT CREW AI INTEGRATION TEST FAILED")
    print("=" * 70 + "\n")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())

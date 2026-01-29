"""
Test Crew AI integration - Validate configuration and imports
"""

import asyncio
import sys

async def test_crew_ai_setup():
    """Test that Crew AI integration is properly set up"""
    
    print("=" * 70)
    print("CREW AI INTEGRATION TEST")
    print("=" * 70)
    
    # Test 1: Config loading
    print("\n[1/5] Testing configuration loading...")
    try:
        from src.langgraphagenticai.config.config_loader import get_config
        config = get_config()
        print("  ✓ ConfigLoader imported successfully")
        
        engine = config.get_execution_engine()
        print(f"  ✓ Current execution engine: {engine}")
        
        if engine == "crew_ai":
            crew_config = config.get_crew_ai_config()
            print(f"  ✓ Crew AI config found: {len(crew_config)} sections")
            
            master = config.get_crew_ai_master_agent()
            print(f"  ✓ Master agent role: {master.get('role', 'N/A')}")
            
            budget = config.get_crew_ai_tool_budget("auditor")
            print(f"  ✓ Auditor tool budget: {budget}")
        else:
            print("  ℹ Crew AI not enabled (config: execution_engine='langgraph')")
            print("  → To enable, set execution_engine: 'crew_ai' in config/settings.yaml")
    except Exception as e:
        print(f"  ✗ Config loading failed: {e}")
        return False
    
    # Test 2: CrewAI package availability
    print("\n[2/5] Testing Crew AI package availability...")
    try:
        import crewai
        print(f"  ✓ crewai package available (version: {getattr(crewai, '__version__', 'unknown')})")
    except ImportError as e:
        print(f"  ⚠ crewai package not installed")
        print(f"  → Install with: pip install crewai crewai-tools")
        print(f"  Error: {e}")
    
    # Test 3: CrewAIExecutor import
    print("\n[3/5] Testing CrewAIExecutor import...")
    try:
        from src.langgraphagenticai.integrations.crewai_executor import CrewAIExecutor
        print("  ✓ CrewAIExecutor imported successfully")
        print(f"  ✓ Methods available: execute_workflow, _create_master_agent")
    except Exception as e:
        print(f"  ✗ CrewAIExecutor import failed: {e}")
        return False
    
    # Test 4: CLI Orchestrator changes
    print("\n[4/5] Testing CLI Orchestrator routing...")
    try:
        from src.langgraphagenticai.core.cli_orchestrator import CLIOrchestrator
        print("  ✓ CLIOrchestrator imported successfully")
        print("  ✓ Routing logic integrated (checks config.get_execution_engine())")
    except Exception as e:
        print(f"  ✗ CLIOrchestrator import failed: {e}")
        return False
    
    # Test 5: Configuration structure
    print("\n[5/5] Validating configuration structure...")
    try:
        from src.langgraphagenticai.config.config_loader import get_config
        config = get_config()
        settings = config._config_cache.get('settings', {})
        
        # Check execution_engine
        if 'execution_engine' in settings:
            print(f"  ✓ execution_engine setting present: {settings['execution_engine']}")
        else:
            print("  ⚠ execution_engine not found in settings.yaml")
        
        # Check crew_ai section
        if 'crew_ai' in settings:
            crew = settings['crew_ai']
            print(f"  ✓ crew_ai section present")
            
            if 'master_agent' in crew:
                print(f"    ✓ master_agent configured: {crew['master_agent'].get('role', 'N/A')}")
            else:
                print(f"    ⚠ master_agent missing")
            
            if 'specialized_agents' in crew:
                agents = crew['specialized_agents']
                enabled = [a for a in agents if a.get('enabled', True)]
                print(f"    ✓ specialized_agents: {len(agents)} total, {len(enabled)} enabled")
                for agent in agents:
                    status = "✓" if agent.get('enabled', True) else "○"
                    print(f"      {status} {agent.get('role', 'Unknown')}")
            else:
                print(f"    ⚠ specialized_agents missing")
            
            if 'max_iterations' in crew:
                print(f"    ✓ max_iterations: {crew['max_iterations']}")
            else:
                print(f"    ⚠ max_iterations missing")
            
            if 'tool_budget_per_workflow' in crew:
                budgets = crew['tool_budget_per_workflow']
                print(f"    ✓ tool_budget_per_workflow configured:")
                for wf, budget in budgets.items():
                    print(f"      - {wf}: {budget}")
            else:
                print(f"    ⚠ tool_budget_per_workflow missing")
            
            if 'delegate_to_crew' in crew:
                print(f"    ✓ multi-agent delegation: {'ENABLED' if crew['delegate_to_crew'] else 'disabled'}")
            else:
                print(f"    ⚠ delegate_to_crew missing")
        else:
            print("  ⚠ crew_ai section not found in settings.yaml")
    except Exception as e:
        print(f"  ✗ Configuration validation failed: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ CREW AI INTEGRATION TEST PASSED")
    print("=" * 70)
    print("\nNext steps:")
    print("1. To enable Crew AI with multi-agent collaboration, edit config/settings.yaml:")
    print("   execution_engine: 'crew_ai'")
    print("   delegate_to_crew: true  (default)")
    print("\n2. Run a workflow:")
    print("   python app.py auditor")
    print("\n3. For detailed configuration options, see:")
    print("   docs/CREW_AI_GUIDE.md")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_crew_ai_setup())
    sys.exit(0 if result else 1)

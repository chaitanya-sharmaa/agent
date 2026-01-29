"""
LangGraph AgenticAI Main Application Entry Point.

This module serves as the entry point for the application, supporting both
Streamlit UI and CLI modes with Zero Trust Kubernetes security auditing and deployment.

Configuration-driven: Reads workflow and MCP server settings from config/

Usage:
    # Run with Streamlit UI (default)
    python -m src.langgraphagenticai.main

    # Run in CLI mode (no UI)
    python -m src.langgraphagenticai.main --no-ui

    # Run specific workflow in CLI mode
    python -m src.langgraphagenticai.main --no-ui comprehensive_auditor
    python -m src.langgraphagenticai.main --no-ui creator
"""

import asyncio
import logging
import os
import sys

# Handle both direct execution and module import
if "src" not in sys.modules:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    # Try relative imports first (for Streamlit)
    from .core.cli_orchestrator import CLIOrchestrator
    from .core.cli_parser import CLIArgumentParser
    from .core.graph_executor import GraphExecutor
    from .core.probe_manager import ProbeManager
    from .core.ui_orchestrator import UIOrchestrator
    from .LLMS.ollamallm import OllamaLLM
    from .graph.graph_builder import GraphBuilder
    from .utils.cli_output_formatter import CLIOutputFormatter
    from .utils.zero_trust_analyzer import ZeroTrustAnalyzer
    from .utils.live_logger import get_live_logger
    from .config.config_loader import get_config
except ImportError:
    # Fall back to absolute imports (for python -m)
    from src.langgraphagenticai.core.cli_orchestrator import CLIOrchestrator
    from src.langgraphagenticai.core.cli_parser import CLIArgumentParser
    from src.langgraphagenticai.core.graph_executor import GraphExecutor
    from src.langgraphagenticai.core.probe_manager import ProbeManager
    from src.langgraphagenticai.core.ui_orchestrator import UIOrchestrator
    from src.langgraphagenticai.LLMS.ollamallm import OllamaLLM
    from src.langgraphagenticai.graph.graph_builder import GraphBuilder
    from src.langgraphagenticai.utils.cli_output_formatter import CLIOutputFormatter
    from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer
    from src.langgraphagenticai.utils.live_logger import get_live_logger
    from src.langgraphagenticai.config.config_loader import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
# Suppress module-level INFO chatter (live_logger handles user-facing info)
logger.setLevel(logging.WARNING)
# Silence verbose HTTP client logs in CLI runs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
# Quiet noisy MCP adapter chatter
logging.getLogger("langchain_mcp_adapters").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("mcp.client.streamable_http").setLevel(logging.WARNING)
live_logger = get_live_logger()

# Persistent probes file path
PERSISTENT_PROBES_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "__blobstorage__",
        "executed_probes.json",
    )
)


async def run_streamlit_ui() -> None:
    """
    Run the application with Streamlit UI.
    
    Configuration is loaded from config/
    
    Raises:
        Exception: If UI setup or execution fails
    """
    try:
        orchestrator = UIOrchestrator()
        await orchestrator.run_app()
    except Exception as e:
        logger.error(f"Error in Streamlit UI: {e}", exc_info=True)
        raise


async def run_cli() -> None:
    """
    Run the application in CLI mode.
    
    Handles:
    - Argument parsing
    - Configuration loading
    - Model initialization
    - Workflow selection from config
    - Execution orchestration
    - Output formatting
    
    Exits with code 1 on error.
    """
    try:
        # Load configuration first
        config = get_config()
        config.print_summary()
        
        # Parse command-line arguments
        arg_parser = CLIArgumentParser()
        run_without_ui, command = arg_parser.parse_args()
        # If UI flag not set, run with Streamlit
        if not run_without_ui:
            await run_streamlit_ui()
            return

        # CLI mode execution
        logger.info("Running in CLI mode")
        live_logger.info("🚀 Starting application in CLI mode...")

        # Determine workflow from args or prompt user
        if command:
            workflow_id = arg_parser.get_usecase_from_command(command)
        else:
            workflow_id = arg_parser.get_command_from_user()

        live_logger.info(f"Selected workflow: {workflow_id}")
        # Initialize core components and run workflow
        await _initialize_and_run(workflow_id, config)

    except Exception as e:
        logger.error(f"Error in CLI execution: {e}", exc_info=True)
        live_logger.error(f"Error in CLI execution: {e}")
        print(f"Error in CLI execution: {e}")
        sys.exit(1)


async def _initialize_and_run(usecase: str, config=None) -> None:
    """
    Initialize application components and run the workflow.
    
    Args:
        usecase: The workflow to execute (comprehensive_auditor or creator)
        config: Configuration loader instance
        
    Raises:
        Exception: If initialization or execution fails
    """
    if config is None:
        config = get_config()
    
    logger.info(f"Initializing for workflow: {usecase}")

    # Initialize LLM with config
    llm_config = config.get_llm_config()
    model = OllamaLLM(llm_config).get_llm_model()
    if not model:
        logger.error("Could not initialize LLM model")
        print("Error: Could not initialize LLM model")
        return

    # Initialize core components with config
    graph_builder = GraphBuilder(model, config)
    probe_manager = ProbeManager(PERSISTENT_PROBES_PATH)
    formatter = CLIOutputFormatter(show_raw_output=True)
    executor = GraphExecutor(formatter, probe_manager)
    analyzer = ZeroTrustAnalyzer()
    
    # Pass LLM model to orchestrator for Crew AI initialization
    orchestrator = CLIOrchestrator(
        graph_builder, 
        executor, 
        analyzer, 
        config=config,
        llm_model=model  # ← Pass LLM model for Crew AI executor
    )

    # Print execution header
    _print_execution_header(usecase, config)

    # Execute workflow based on usecase
    if "comprehensive" in usecase.lower():
        await orchestrator.run_comprehensive_auditor()
    elif "creator" in usecase.lower():
        await orchestrator.run_creator()
    else:
        logger.warning(f"Unknown workflow: {usecase}. Using comprehensive_auditor as default.")
        await orchestrator.run_comprehensive_auditor()

    # Print final output
    final_output = formatter.get_final_output()
    print("\nAI Response:")
    print("=" * 50)
    print(final_output)


def _print_execution_header(usecase: str, config=None) -> None:
    """
    Print execution header with usecase information.
    
    Args:
        usecase: The usecase being executed
        config: Configuration loader instance for workflow details
    """
    print(f"\n=== Executing: {usecase} ===")
    
    if config:
        # Try to get workflow description from config
        workflows = config.get_workflows()
        for wf_id, wf_config in workflows.items():
            if wf_config.get('name') == usecase:
                description = wf_config.get('description', '')
                if description:
                    print(f"Description: {description}")
                break
    
    print("\n=== LangGraph Execution Results ===\n")


async def main() -> None:
    """
    Main application entry point.
    
    Dispatches to CLI or UI mode based on arguments.
    """
    await run_cli()


if __name__ == "__main__":
    asyncio.run(main())




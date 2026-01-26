"""
UI orchestrator module for managing Streamlit UI workflows.
"""

import logging
import streamlit as st

from src.langgraphagenticai.LLMS.ollamallm import OllamaLLM
from src.langgraphagenticai.graph.graph_builder import GraphBuilder
from src.langgraphagenticai.ui.streamlitui.loadui import LoadStreamlitUI
from src.langgraphagenticai.ui.streamlitui.display_result import DisplayResultStreamlit
from src.langgraphagenticai.utils.live_logger import get_live_logger

logger = logging.getLogger(__name__)
live_logger = get_live_logger()


class UIOrchestrator:
    """Orchestrates Streamlit UI workflows."""

    async def run_app(self) -> None:
        """
        Load and run the LangGraph AgenticAI application with Streamlit UI.
        """
        try:
            # Set up session state for logs if not exists
            if 'logs' not in st.session_state:
                st.session_state.logs = []
            
            # Create container for logs
            st.subheader("📋 Live Execution Logs")
            log_placeholder = st.empty()
            
            # Setup live logger for Streamlit
            live_logger.setup_streamlit_logging(log_placeholder)
            live_logger.section("Execution Started")
            
            # Display UI controls
            ui = LoadStreamlitUI()
            user_input = ui.load_streamlit_ui()

            if not user_input:
                st.error("Error: Failed to load user input from the UI.")
                return

            # Only proceed if the submit button was clicked
            if not user_input.get("submit", False):
                st.info("👈 Select a usecase and click **Execute** to begin")
                return

            model = self._initialize_model(user_input)
            if not model:
                st.error("Error: LLM model could not be initialized")
                return

            usecase = user_input.get("selected_usecase")
            if not usecase:
                st.error("Error: No use case selected.")
                return
            
            live_logger.info(f"Running workflow: {usecase}")

            await self._setup_and_run_graph(model, usecase)
            live_logger.section("Execution Completed Successfully")

        except Exception as e:
            logger.error(f"Error in UI application: {e}", exc_info=True)
            live_logger.error(f"Execution failed with error: {e}")
            st.error(f"Error: Main application setup failed - {e}")

    @staticmethod
    def _initialize_model(user_input: dict):
        """
        Initialize the LLM model.
        
        Args:
            user_input: User configuration from UI
            
        Returns:
            Initialized LLM model or None
        """
        try:
            live_logger.info("🔧 Initializing LLM model...")
            obj_llm_config = OllamaLLM(user_controls_input=user_input)
            model = obj_llm_config.get_llm_model()
            live_logger.status("LLM model initialized successfully")
            return model
        except Exception as e:
            live_logger.error(f"Failed to initialize LLM model: {e}")
            logger.error(f"Failed to initialize LLM model: {e}")
            return None

    @staticmethod
    async def _setup_and_run_graph(model, usecase: str) -> None:
        """
        Set up the graph and run it.
        
        Args:
            model: Initialized LLM model
            usecase: Selected use case
        """
        try:
            live_logger.subsection(f"Setting up workflow: {usecase}")
            
            live_logger.info("📊 Building graph structure...")
            graph_builder = GraphBuilder(model)
            graph = await graph_builder.setup_graph(usecase)
            live_logger.status("Graph structure built successfully")
            
            live_logger.info("🚀 Running workflow...")
            await DisplayResultStreamlit(graph, usecase).display_result_on_ui()
            live_logger.status("Workflow execution completed")
            
        except Exception as e:
            live_logger.error(f"Error during graph setup: {e}")
            logger.error(f"Error during graph setup: {e}", exc_info=True)
            st.error(f"Error: Graph set up failed - see details below")
            st.exception(e)

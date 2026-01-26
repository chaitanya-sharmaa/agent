import streamlit as st
from src.langgraphagenticai.ui.uiconfigfile import Config

class LoadStreamlitUI:
    def __init__(self):
        self.config = Config()
        self.user_controls = {}

    def load_streamlit_ui(self):
        st.set_page_config(page_title=self.config.get_page_title(), layout="wide")
        st.header("LangGraph: Build Stateful Agentic AI Zero Trust for Microservice")

        with st.sidebar:
            # LLM Provider Selection
            llm_options = self.config.get_llm_options()
            selected_llm = st.selectbox("Select LLM", llm_options)
            self.user_controls["selected_llm"] = selected_llm

            if selected_llm == "Ollama":
                ollama_model_options = self.config.get_ollama_model_options()
                selected_ollama_model = st.selectbox("Select Model", ollama_model_options)
                self.user_controls["selected_ollama_model"] = selected_ollama_model

            # Use Case Selection
            usecase_options = self.config.get_usecase_options()
            selected_usecase = st.selectbox("Select Usecases", usecase_options)
            self.user_controls["selected_usecase"] = selected_usecase

            # Submit Button
            submit_button = st.button("Execute", type="primary")
            self.user_controls["submit"] = submit_button

        return self.user_controls

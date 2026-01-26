#!/usr/bin/env python3
"""
Streamlit App Entry Point for LangGraph AgenticAI

This file serves as the main entry point for running the application
via Streamlit GUI. It provides an easy way to launch the Streamlit
interface without using the --no-ui flag.

Usage:
    streamlit run app.py
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.langgraphagenticai.main import run_streamlit_ui

if __name__ == "__main__":
    # Run the Streamlit application
    asyncio.run(run_streamlit_ui())

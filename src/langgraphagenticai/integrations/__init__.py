"""
Integration modules for LangGraph Agentic CI/AI framework.

Provides alternative execution engines and external integrations:
- crewai_executor: Multi-agent orchestration via Crew AI
"""

from src.langgraphagenticai.integrations.crewai_executor import CrewAIExecutor

__all__ = ["CrewAIExecutor"]

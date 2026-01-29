"""
CLI argument parser module for handling command-line arguments.
"""

import argparse
from enum import Enum
from typing import Optional


class UseCaseType(Enum):
    """Available use case types."""

    CREATOR = "creator"
    COMPREHENSIVE_AUDITOR = "comprehensive_auditor"


class CLIArgumentParser:
    """Handles parsing and validation of CLI arguments."""

    def __init__(self):
        """Initialize the CLI argument parser."""
        self.parser = self._build_parser()

    @staticmethod
    def _build_parser() -> argparse.ArgumentParser:
        """
        Build the argument parser.
        
        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            description="LangGraph AgenticAI CLI for Kubernetes Zero Trust Security"
        )
        parser.add_argument(
            "--no-ui",
            action="store_true",
            help="Run in command-line mode without the Streamlit UI.",
        )

        subparsers = parser.add_subparsers(dest="command")
        subparsers.add_parser(
            "comprehensive_auditor",
            help="Run Comprehensive Security Auditor (deep analysis)",
        )
        subparsers.add_parser(
            "creator",
            help="Run Zero Trust Creator (audit + deploy + verify)",
        )
        
        return parser

    def parse_args(self) -> tuple[bool, Optional[str]]:
        """
        Parse command-line arguments.
        
        Returns:
            Tuple of (run_without_ui, command)
        """
        args = self.parser.parse_args()
        return args.no_ui, args.command

    @staticmethod
    def get_usecase_from_command(command: Optional[str]) -> str:
        """
        Convert CLI command to usecase string.
        
        Args:
            command: CLI command from arguments
            
        Returns:
            Usecase string (workflow ID)
        """
        if command and command.lower() in ("creator", "create"):
            return "creator"
        elif command and command.lower() in ("comprehensive_auditor", "comprehensive", "audit"):
            return "comprehensive_auditor"
        else:
            if command:
                print(f"Unknown command: '{command}'. Defaulting to comprehensive_auditor.")
            return "comprehensive_auditor"

    def get_command_from_user(self) -> str:
        """
        Prompt user for command if not provided.
        
        Returns:
            User-selected command
        """
        cmd = input("Enter command (comprehensive_auditor/creator): ").strip()
        return self.get_usecase_from_command(cmd)

"""CLI Output Formatter for LangGraph AgenticAI.

This module provides formatting utilities to extract and display
only the essential information from LangGraph execution events.
"""

from typing import Dict, Any, List
import json


class CLIOutputFormatter:
    """Formats LangGraph events for clean CLI output."""
    
    def __init__(self, show_raw_output=False):
        self.final_message = None
        self.tool_results = []
        self.all_events = []  # Store all events for raw output
        self.show_raw_output = show_raw_output
        
    def process_event(self, event: Dict[str, Any]) -> str:
        """Process a single event and return formatted output if needed.
        
        Args:
            event: The event dictionary from LangGraph
            
        Returns:
            Formatted string to display, or empty string if nothing to show
        """
        # Store all events for raw output if needed
        self.all_events.append(event)
        
        output = ""
        
        # Check for chatbot messages
        if "chatbot" in event and "messages" in event["chatbot"]:
            messages = event["chatbot"]["messages"]
            for message in messages:
                # Extract content from AIMessage
                if hasattr(message, "content") and message.content:
                    content = message.content
                    if content:  # Save any non-empty content
                        self.final_message = content
                    
        # Check for tool messages
        if "tools" in event and "messages" in event["tools"]:
            messages = event["tools"]["messages"]
            for message in messages:
                if hasattr(message, "content") and message.content:
                    # Tool messages contain list of content items
                    if isinstance(message.content, list):
                        for content_item in message.content:
                            if isinstance(content_item, dict) and "text" in content_item:
                                try:
                                    # Parse JSON content from tools
                                    tool_data = json.loads(content_item["text"])
                                    # Store the full tool result with output
                                    self.tool_results.append({"output": content_item["text"]})
                                except json.JSONDecodeError:
                                    # If not JSON, store as plain text
                                    self.tool_results.append({"output": content_item["text"]})
                                
        return output
    
    def get_final_output(self) -> str:
        """Get the final formatted output after processing all events.
        
        Returns:
            The final formatted message to display to the user
        """
        if self.show_raw_output:
            # Return raw tool results for multipurpose use
            return self._format_raw_output()
        
        if self.final_message:
            return f"\n{self.final_message}\n"
        elif self.tool_results:
            # If no final message but we have tool results, format them
            return self._format_tool_results()
        else:
            return "No results to display."
            
    def _format_tool_results(self) -> str:
        """Format tool results for display.
        
        Returns:
            Formatted tool results
        """
        output = "\nTool Results:\n"
        output += "=" * 50 + "\n"
        for i, result in enumerate(self.tool_results, 1):
            output += f"\n[Tool Output {i}]\n"
            if isinstance(result, dict):
                # Pretty print JSON data
                output += json.dumps(result, indent=2) + "\n"
            else:
                output += str(result) + "\n"
            output += "-" * 50 + "\n"
        return output
    
    def _format_raw_output(self) -> str:
        """Format raw output showing all events and tool results.
        
        Returns:
            Raw formatted output for multipurpose use
        """
        output = "\n=== LangGraph Execution Results ===\n\n"
        
        # Show tool results
        if self.tool_results:
            output += "Tool Outputs:\n"
            output += "-" * 50 + "\n"
            for i, result in enumerate(self.tool_results, 1):
                output += f"\n[Tool {i}]\n"
                if isinstance(result, dict):
                    output += json.dumps(result, indent=2) + "\n"
                else:
                    output += str(result) + "\n"
            output += "\n"
        
        # Show final AI message if available
        if self.final_message:
            output += "\nAI Response:\n"
            output += "=" * 50 + "\n"
            output += self.final_message + "\n"
        
        # Optionally show all events for debugging
        if not self.tool_results and not self.final_message:
            output += "\nAll Events (Debug):\n"
            output += "-" * 50 + "\n"
            for event in self.all_events:
                output += json.dumps(event, indent=2, default=str) + "\n\n"
        
        return output
    
    def get_tool_results(self) -> List[Any]:
        """Get raw tool results for programmatic access.
        
        Returns:
            List of tool results
        """
        return self.tool_results
    
    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events for programmatic access.
        
        Returns:
            List of all events
        """
        return self.all_events
    
    @staticmethod
    def format_progress(message: str) -> str:
        """Format a progress message.
        
        Args:
            message: The progress message to format
            
        Returns:
            Formatted progress message
        """
        return f"[*] {message}"
    
    @staticmethod
    def format_error(message: str) -> str:
        """Format an error message.
        
        Args:
            message: The error message to format
            
        Returns:
            Formatted error message
        """
        return f"[ERROR] {message}"
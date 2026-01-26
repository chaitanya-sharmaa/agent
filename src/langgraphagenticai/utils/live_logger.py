"""
Live logging handler for displaying logs in both CLI and Streamlit UI.

Provides real-time log streaming to console and Streamlit UI components.
"""

import logging
import sys
from typing import Optional, Callable
from datetime import datetime


class StreamlitLogHandler(logging.Handler):
    """Custom logging handler that sends logs to Streamlit UI."""
    
    def __init__(self, log_placeholder=None):
        """
        Initialize Streamlit log handler.
        
        Args:
            log_placeholder: Streamlit placeholder to display logs in
        """
        super().__init__()
        self.log_placeholder = log_placeholder
        self.log_messages = []
        
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to Streamlit."""
        try:
            msg = self.format(record)
            self.log_messages.append(msg)
            
            # Update Streamlit UI if placeholder exists
            if self.log_placeholder:
                try:
                    import streamlit as st
                    
                    # Build the complete log text (last 100 messages)
                    log_text = "\n".join(self.log_messages[-100:])
                    
                    # Update placeholder with all accumulated logs
                    with self.log_placeholder.container():
                        st.code(log_text, language="text")
                except Exception as e:
                    # If Streamlit update fails, just store the message
                    pass
        except Exception:
            self.handleError(record)


class CLILogHandler(logging.StreamHandler):
    """Custom logging handler for CLI with colored output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def __init__(self, stream=None, use_colors=True):
        """
        Initialize CLI log handler.
        
        Args:
            stream: Output stream (default: sys.stdout)
            use_colors: Whether to use colored output
        """
        super().__init__(stream or sys.stdout)
        self.use_colors = use_colors and sys.stdout.isatty()
        
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to CLI with colors."""
        try:
            msg = self.format(record)
            
            if self.use_colors:
                color = self.COLORS.get(record.levelname, '')
                msg = f"{color}{msg}{self.RESET}"
            
            self.stream.write(msg + '\n')
            self.stream.flush()
        except Exception:
            self.handleError(record)


class LiveLogger:
    """
    Live logger for both CLI and Streamlit UI.
    
    Provides a unified interface for logging to both console and Streamlit UI.
    """
    
    _instance: Optional['LiveLogger'] = None
    
    def __new__(cls):
        """Singleton pattern to ensure single logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the live logger."""
        if self._initialized:
            return
            
        self.logger = logging.getLogger('langgraphagenticai.live')
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # Avoid duplicate logs via root handlers
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add CLI handler
        cli_handler = CLILogHandler()
        cli_handler.setLevel(logging.DEBUG)
        cli_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        cli_handler.setFormatter(cli_formatter)
        self.logger.addHandler(cli_handler)
        
        self.streamlit_handler = None
        self.streamlit_container = None
        self._initialized = True
        
    def setup_streamlit_logging(self, log_placeholder):
        """
        Set up Streamlit logging placeholder.
        
        Args:
            log_placeholder: Streamlit placeholder to display logs in
        """
        try:
            import streamlit as st
            
            # Remove old Streamlit handler if exists
            if self.streamlit_handler:
                self.logger.removeHandler(self.streamlit_handler)
            
            self.streamlit_container = log_placeholder
            self.streamlit_handler = StreamlitLogHandler(log_placeholder)
            self.streamlit_handler.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            self.streamlit_handler.setFormatter(formatter)
            self.logger.addHandler(self.streamlit_handler)
            
        except ImportError:
            # Streamlit not available, skip
            pass
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)
    
    def status(self, message: str):
        """Log a status update (appears in both CLI and UI)."""
        self.info(f"✅ {message}")
    
    def step(self, step_num: int, total_steps: int, message: str):
        """Log a step update."""
        self.info(f"[Step {step_num}/{total_steps}] {message}")
    
    def section(self, title: str):
        """Log a section header."""
        separator = "=" * 80
        self.info(f"\n{separator}")
        self.info(f">>> {title}")
        self.info(f"{separator}\n")
    
    def subsection(self, title: str):
        """Log a subsection header."""
        separator = "-" * 60
        self.info(f"\n{separator}")
        self.info(f">> {title}")
        self.info(f"{separator}\n")


def get_live_logger() -> LiveLogger:
    """Get the singleton LiveLogger instance."""
    return LiveLogger()

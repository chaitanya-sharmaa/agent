"""
Probe manager for tracking executed Kubernetes resource probes.
Handles persistence of probe execution state across application runs.
"""

import json
import logging
import os
from typing import Set

logger = logging.getLogger(__name__)


class ProbeManager:
    """Manages persistent tracking of executed Kubernetes probes."""

    def __init__(self, probes_file_path: str):
        """
        Initialize the probe manager.
        
        Args:
            probes_file_path: Path to the JSON file storing probe state
        """
        self.probes_file_path = probes_file_path
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Create the directory for the probes file if it doesn't exist."""
        try:
            os.makedirs(os.path.dirname(self.probes_file_path), exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create probe directory: {e}")

    def load_probes(self) -> Set[str]:
        """
        Load persisted probe data from disk.
        
        Returns:
            Set of probe keys that have been executed
        """
        try:
            if os.path.exists(self.probes_file_path):
                with open(self.probes_file_path, "r") as f:
                    data = json.load(f)
                    return set(data or [])
        except Exception as e:
            logger.warning(f"Failed to load probes: {e}")
        return set()

    def save_probes(self, probes: Set[str]) -> None:
        """
        Save probe data to disk.
        
        Args:
            probes: Set of probe keys to persist
        """
        try:
            with open(self.probes_file_path, "w") as f:
                json.dump(sorted(list(probes)), f)
        except Exception as e:
            logger.error(f"Failed to save probes: {e}")

    def add_probes(self, new_probes: Set[str]) -> None:
        """
        Add new probes to the persisted set.
        
        Args:
            new_probes: Set of new probe keys to add
        """
        try:
            existing = self.load_probes()
            updated = existing.union(new_probes)
            self.save_probes(updated)
        except Exception as e:
            logger.error(f"Failed to add probes: {e}")

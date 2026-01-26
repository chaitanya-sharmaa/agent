"""Utility functions for deduplicating tool calls and data structures.

This module provides common deduplication logic used across the application.
"""

from typing import Dict, List, Any, Set, Tuple


def deduplicate_tool_calls(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate tool calls by (name, args) keeping first occurrence.
    
    Args:
        tool_calls: List of tool call dictionaries with 'name' and 'args' keys
        
    Returns:
        Deduplicated list preserving order (first occurrence kept)
        
    Example:
        >>> calls = [
        ...     {"id": "1", "name": "kubectl_get", "args": {"resource": "pods"}},
        ...     {"id": "2", "name": "kubectl_get", "args": {"resource": "pods"}},
        ...     {"id": "3", "name": "kubectl_get", "args": {"resource": "services"}},
        ... ]
        >>> deduplicate_tool_calls(calls)
        [
            {"id": "1", "name": "kubectl_get", "args": {"resource": "pods"}},
            {"id": "3", "name": "kubectl_get", "args": {"resource": "services"}},
        ]
    """
    seen: Set[Tuple[str, Tuple[Tuple[str, Any], ...]]] = set()
    deduped = []
    
    for tc in tool_calls:
        # Create a hashable key from tool name and sorted args
        name = tc.get("name", "")
        args = tc.get("args", {}) or {}
        key = (name, tuple(sorted(args.items())))
        
        # Skip if we've already seen this combination
        if key in seen:
            continue
            
        seen.add(key)
        deduped.append(tc)
    
    return deduped


def deduplicate_by_key(
    items: List[Dict[str, Any]],
    key_func=None
) -> List[Dict[str, Any]]:
    """Generic deduplication by custom key function.
    
    Args:
        items: List of items to deduplicate
        key_func: Function that returns a hashable key for each item.
                 If None, uses the entire item (must be hashable).
        
    Returns:
        Deduplicated list preserving order
    """
    seen = set()
    deduped = []
    
    for item in items:
        key = key_func(item) if key_func else item
        
        # Try to hash the key; if it fails, skip deduplication for this item
        try:
            if key in seen:
                continue
            seen.add(key)
        except TypeError:
            # Key is not hashable; add item without deduplication
            pass
        
        deduped.append(item)
    
    return deduped

"""
Runtime audit module for detecting silent bugs and anti-patterns.
"""
import sys
import json
import functools
import warnings
import inspect
from typing import Callable, Any, Optional

from .messages import _format_message  # Reuse consistent styling

# Global state to track patches
_patches = {}

def _warn_audit(title: str, explanation: str, suggestions: list) -> None:
    """Emit a formatted audit warning to stderr."""
    msg = _format_message(
        f"⚠️ AUDIT WARNING: {title}",
        explanation,
        suggestions
    )
    print(f"\n{msg}\n", file=sys.stderr)

def _audit_json_dumps(original_func: Callable) -> Callable:
    """Wrapper for json.dumps to detect dangerous defaults."""
    @functools.wraps(original_func)
    def wrapper(*args, **kwargs):
        # Check for default=str
        default_handler = kwargs.get('default')
        
        if default_handler is str:
            _warn_audit(
                "Dangerous JSON Serialization Detected",
                "You are using `json.dumps(..., default=str)`. This is known as the 'Silent Destroyer'.\n"
                "It converts complex objects (like datetime, set, or custom classes) into strings, "
                "destroying their structure and type information without raising an error.",
                [
                    "Use a custom encoder subclass: `class MyEncoder(json.JSONEncoder):`",
                    "Explicitly convert objects to dicts before serializing.",
                    "If you really mean to stringify everything, use a lambda: `default=lambda x: str(x)` to suppress this warning."
                ]
            )
        
        return original_func(*args, **kwargs)
    return wrapper

def enable_audit() -> None:
    """
    Enable runtime auditing (monkey-patching).
    
    This wraps specific standard library functions to detect common bug patterns
    that don't normally raise exceptions (silent failures).
    """
    global _patches
    
    # 1. Audit json.dumps
    if 'json' not in _patches:
        _patches['json'] = json.dumps
        json.dumps = _audit_json_dumps(json.dumps)
        print("✅ Auditing enabled: Monitoring json.dumps for data loss patterns.", file=sys.stderr)

def disable_audit() -> None:
    """Disable runtime auditing and restore original functions."""
    global _patches
    
    # Restore json.dumps
    if 'json' in _patches:
        json.dumps = _patches['json']
        del _patches['json']

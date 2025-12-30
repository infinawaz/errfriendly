"""
Handler for Python warnings (e.g. DeprecationWarning).
"""
import sys
import warnings
from .messages import get_friendly_warning

_original_showwarning = None

def _friendly_showwarning(message, category, filename, lineno, file=None, line=None):
    """
    Custom warning hook that shows a friendly explanation box.
    """
    # Respect the file argument (default to stderr)
    outfile = file or sys.stderr
    
    # 1. Provide the standard concise output (useful for IDEs/logs)
    # We call formatwarning which returns "file:line: category: msg\n"
    try:
        original_text = warnings.formatwarning(message, category, filename, lineno, line)
        outfile.write(original_text)
    except Exception:
        # Fallback if formatwarning fails
        pass

    # 2. Add our Friendly Explanation Box
    try:
        friendly = get_friendly_warning(category, message)
        # Add some padding
        outfile.write(f"\n{friendly}\n")
    except Exception:
        # If our friendly logic fails, swallow it to avoid crashing the app during a warning
        pass

def enable_warnings() -> None:
    """
    Enable friendly formatting for Python warnings.
    """
    global _original_showwarning
    if _original_showwarning is None:
        _original_showwarning = warnings.showwarning
        warnings.showwarning = _friendly_showwarning

def disable_warnings() -> None:
    """
    Disable friendly warnings and restore default behavior.
    """
    global _original_showwarning
    if _original_showwarning is not None:
        warnings.showwarning = _original_showwarning
        _original_showwarning = None

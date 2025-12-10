"""
handler.py - Exception hook handler for errfriendly.

This module provides the core functionality to install and uninstall
a custom exception hook that displays friendly error messages alongside
the standard Python traceback.
"""

import sys
import traceback
from typing import Type, Optional

from .messages import get_friendly_message

# Store the original excepthook so we can restore it later
_original_excepthook: Optional[object] = None
_show_original_traceback: bool = True


def _friendly_excepthook(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_traceback
) -> None:
    """
    Custom exception hook that shows both the original traceback
    and a friendly explanation.
    
    Args:
        exc_type: The exception class.
        exc_value: The exception instance.
        exc_traceback: The traceback object.
    """
    global _show_original_traceback
    
    # Show the original traceback if configured to do so
    if _show_original_traceback:
        # Print the standard Python traceback
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    # Get and print the friendly message
    friendly_message = get_friendly_message(exc_type, exc_value)
    print(friendly_message, file=sys.stderr)


def install(show_original_traceback: bool = True) -> None:
    """
    Install the friendly exception hook.
    
    After calling this function, all unhandled exceptions will display
    a human-friendly explanation in addition to (or instead of) the
    standard Python traceback.
    
    Args:
        show_original_traceback: If True (default), show the standard Python
            traceback before the friendly message. If False, only show the
            friendly message.
    
    Example:
        >>> import errfriendly
        >>> errfriendly.install()
        >>> # Now exceptions will show friendly messages
        >>> 1 / 0  # Will show friendly ZeroDivisionError explanation
    """
    global _original_excepthook, _show_original_traceback
    
    # Store the original hook only if we haven't already
    if _original_excepthook is None:
        _original_excepthook = sys.excepthook
    
    # Store the configuration
    _show_original_traceback = show_original_traceback
    
    # Install our custom hook
    sys.excepthook = _friendly_excepthook


def uninstall() -> None:
    """
    Uninstall the friendly exception hook and restore the original behavior.
    
    After calling this function, exceptions will display normally without
    the friendly explanations.
    
    Example:
        >>> import errfriendly
        >>> errfriendly.install()
        >>> # ... use your code ...
        >>> errfriendly.uninstall()  # Back to normal exceptions
    """
    global _original_excepthook
    
    # Restore the original hook if we have one saved
    if _original_excepthook is not None:
        sys.excepthook = _original_excepthook
        _original_excepthook = None
    else:
        # No original hook saved, restore the default
        sys.excepthook = sys.__excepthook__


def is_installed() -> bool:
    """
    Check if the friendly exception hook is currently installed.
    
    Returns:
        True if errfriendly is currently handling exceptions, False otherwise.
    
    Example:
        >>> import errfriendly
        >>> errfriendly.is_installed()
        False
        >>> errfriendly.install()
        >>> errfriendly.is_installed()
        True
    """
    return sys.excepthook is _friendly_excepthook

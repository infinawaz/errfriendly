"""
handler.py - Exception hook handler for errfriendly.

This module provides the core functionality to install and uninstall
a custom exception hook that displays friendly error messages alongside
the standard Python traceback.
"""

import sys
import traceback
import logging
from typing import Type, Optional
from pathlib import Path

from .messages import get_friendly_message

# Store the original excepthook so we can restore it later
_original_excepthook: Optional[object] = None
_show_original_traceback: bool = True
_logger: Optional[logging.Logger] = None


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
    global _show_original_traceback, _logger
    
    # Show the original traceback if configured to do so
    if _show_original_traceback:
        # Print the standard Python traceback
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    # Wrap friendly message generation in try/except for robustness
    try:
        friendly_message = get_friendly_message(exc_type, exc_value)
        print(friendly_message, file=sys.stderr)
        
        # Log to file if logging is configured
        if _logger is not None:
            # Log both the original traceback and friendly message
            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            _logger.error(f"Exception occurred:\n{tb_str}\n{friendly_message}")
    except Exception as e:
        # If errfriendly fails, print a warning and ensure the original traceback is shown
        print(
            f"\n[errfriendly] Failed to generate friendly message: {e}",
            file=sys.stderr
        )
        # If we didn't already show the traceback, show it now
        if not _show_original_traceback:
            traceback.print_exception(exc_type, exc_value, exc_traceback)


def install(
    show_original_traceback: bool = True,
    log_file: Optional[str] = None
) -> None:
    """
    Install the friendly exception hook.
    
    After calling this function, all unhandled exceptions will display
    a human-friendly explanation in addition to (or instead of) the
    standard Python traceback.
    
    Args:
        show_original_traceback: If True (default), show the standard Python
            traceback before the friendly message. If False, only show the
            friendly message.
        log_file: Optional path to a log file. If provided, exceptions will
            also be logged to this file.
    
    Example:
        >>> import errfriendly
        >>> errfriendly.install()
        >>> # Now exceptions will show friendly messages
        >>> 1 / 0  # Will show friendly ZeroDivisionError explanation
    """
    global _original_excepthook, _show_original_traceback, _logger
    
    # Store the original hook only if we haven't already
    if _original_excepthook is None:
        _original_excepthook = sys.excepthook
    
    # Store the configuration
    _show_original_traceback = show_original_traceback
    
    # Set up logging if log_file is provided
    if log_file is not None:
        _logger = logging.getLogger("errfriendly")
        _logger.setLevel(logging.ERROR)
        # Remove existing handlers to avoid duplicates
        _logger.handlers.clear()
        # Create file handler
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s\n%(message)s")
        )
        _logger.addHandler(handler)
    else:
        _logger = None
    
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
    global _original_excepthook, _logger
    
    # Restore the original hook if we have one saved
    if _original_excepthook is not None:
        sys.excepthook = _original_excepthook
        _original_excepthook = None
    else:
        # No original hook saved, restore the default
        sys.excepthook = sys.__excepthook__
    
    # Clean up logger
    if _logger is not None:
        for handler in _logger.handlers:
            handler.close()
        _logger.handlers.clear()
        _logger = None


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


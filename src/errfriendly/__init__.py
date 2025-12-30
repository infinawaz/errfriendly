"""
errfriendly - Friendly explanations for Python errors.

This package provides human-readable explanations for common Python exceptions,
making debugging easier and more accessible for developers of all skill levels.

v3.0 adds AI-powered contextual explanations and exception chain analysis.
"""

from .handler import (
    install,
    uninstall,
    is_installed,
    enable_ai,
    disable_ai,
    configure,
    get_config,
)
from .audit import enable_audit, disable_audit
from .warning_handler import enable_warnings, disable_warnings
from .messages import get_friendly_message
from .models import (
    Config,
    AIBackend,
    ExplainDepth,
    ExplanationStyle,
    PrivacyMode,
    ErrorContext,
    ExceptionChain,
    AIExplanation,
)

__version__ = "3.4.1"
__all__ = [
    # Core functions (backward compatible)
    "install",
    "uninstall",
    "is_installed",
    "get_friendly_message",
    # v3.0: AI functions
    "enable_ai",
    "disable_ai",
    "configure",
    "get_config",
    
    # Audit (v3.1)
    "enable_audit",
    "disable_audit",

    # Warnings (v3.4)
    "enable_warnings",
    "disable_warnings",
    
    # v3.0: Data types
    "Config",
    "AIBackend",
    "ExplainDepth",
    "ExplanationStyle",
    "PrivacyMode",
    "ErrorContext",
    "ExceptionChain",
    "AIExplanation",
]

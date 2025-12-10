"""
errfriendly - Friendly explanations for Python errors.

This package provides human-readable explanations for common Python exceptions,
making debugging easier and more accessible for developers of all skill levels.
"""

from .handler import install, uninstall, is_installed
from .messages import get_friendly_message

__version__ = "0.1.0"
__all__ = ["install", "uninstall", "is_installed", "get_friendly_message"]

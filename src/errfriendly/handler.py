"""
handler.py - Exception hook handler for errfriendly.

This module provides the core functionality to install and uninstall
a custom exception hook that displays friendly error messages alongside
the standard Python traceback.

v3.0 adds AI-powered contextual explanations and exception chain analysis.
"""

import sys
import traceback
import logging
from typing import Type, Optional, Union, Dict, Any

from .messages import get_friendly_message
from .models import (
    Config, 
    AIBackend, 
    ExplainDepth, 
    PrivacyMode,
    ExplanationStyle,
)

# Lazy imports for optional AI features
_context_collector = None
_ai_explainer = None
_chain_analyzer = None

# Store the original excepthook so we can restore it later
_original_excepthook: Optional[object] = None
_show_original_traceback: bool = True
_logger: Optional[logging.Logger] = None

# v3.0 configuration
_config: Config = Config()


def _get_context_collector():
    """Lazy-load the context collector."""
    global _context_collector
    if _context_collector is None:
        from .context_collector import ContextCollector
        _context_collector = ContextCollector(_config)
    return _context_collector


def _get_ai_explainer():
    """Lazy-load the AI explainer."""
    global _ai_explainer
    if _ai_explainer is None:
        from .ai_explainer import AIExplainer
        _ai_explainer = AIExplainer(_config)
    return _ai_explainer


def _get_chain_analyzer():
    """Lazy-load the exception chain analyzer."""
    global _chain_analyzer
    if _chain_analyzer is None:
        from .exception_graph import ExceptionChainAnalyzer
        _chain_analyzer = ExceptionChainAnalyzer()
    return _chain_analyzer


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
    global _show_original_traceback, _logger, _config
    
    # Show the original traceback if configured to do so
    if _show_original_traceback:
        # Print the standard Python traceback
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    # Wrap all message generation in try/except for robustness
    try:
        output_parts = []
        
        # Check for exception chains first (v3.0)
        if _config.show_chain_analysis and _has_exception_chain(exc_value):
            chain_output = _generate_chain_analysis(exc_type, exc_value, exc_traceback)
            if chain_output:
                output_parts.append(chain_output)
        
        # Try AI explanation if enabled (v3.0)
        if _config.ai_enabled:
            ai_output = _generate_ai_explanation(exc_type, exc_value, exc_traceback)
            if ai_output:
                output_parts.append(ai_output)
        
        # Always include static friendly message as fallback/complement
        friendly_message = get_friendly_message(exc_type, exc_value, tb=exc_traceback)
        
        # If we have AI/chain output, combine them appropriately
        if output_parts:
            full_output = "\n".join(output_parts)
            # Add a separator before static message if AI provided output
            full_output += "\n\n" + "=" * 70 + "\n"
            full_output += "📝 Quick Reference (Static):\n"
            full_output += friendly_message
        else:
            full_output = friendly_message
        
        print(full_output, file=sys.stderr)
        
        # Log to file if logging is configured
        if _logger is not None:
            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            _logger.error(f"Exception occurred:\n{tb_str}\n{full_output}")
            
    except Exception as e:
        # If errfriendly fails, print a warning and ensure the original traceback is shown
        print(
            f"\n[errfriendly] Failed to generate friendly message: {e}",
            file=sys.stderr
        )
        # If we didn't already show the traceback, show it now
        if not _show_original_traceback:
            traceback.print_exception(exc_type, exc_value, exc_traceback)


def _has_exception_chain(exc_value: BaseException) -> bool:
    """Check if the exception has a chain (__cause__ or __context__)."""
    return exc_value.__cause__ is not None or (
        exc_value.__context__ is not None and not exc_value.__suppress_context__
    )


def _generate_chain_analysis(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_traceback
) -> Optional[str]:
    """Generate exception chain analysis output.
    
    This function analyzes __cause__ and __context__ chains to provide
    a debugging narrative for chained exceptions.
    
    Design Note:
        Internal exceptions are caught and suppressed by design (graceful
        degradation). If chain analysis fails, the core friendly message
        still displays. Use `errfriendly.configure(debug_mode=True)` to
        see internal errors for library development/debugging.
    
    Returns:
        Formatted chain analysis string, or None if chain analysis fails
        or the exception has no chain.
    """
    try:
        analyzer = _get_chain_analyzer()
        chain = analyzer.analyze(exc_type, exc_value, exc_traceback)
        
        if chain.has_chain:
            output = "\n" + "=" * 70 + "\n"
            output += "🔗 EXCEPTION CHAIN ANALYSIS\n"
            output += "=" * 70 + "\n\n"
            output += analyzer.generate_narrative(chain)
            return output
    except Exception as e:
        # Intentional graceful degradation - see Design Note in docstring
        if _config.debug_mode:
            print(f"[errfriendly] Chain analysis failed: {e}", file=sys.stderr)
    
    return None


def _generate_ai_explanation(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_traceback
) -> Optional[str]:
    """Generate AI-powered explanation output.
    
    This function uses an AI backend (local or cloud) to provide
    contextual, personalized error explanations.
    
    Design Note:
        Internal exceptions are caught and suppressed by design (graceful
        degradation). AI failures (network timeouts, missing Ollama, rate
        limits, etc.) should not prevent the core friendly message from
        displaying. Use `errfriendly.configure(debug_mode=True)` to see
        internal errors for library development/debugging.
    
    Returns:
        Formatted AI explanation string, or None if AI is disabled,
        unavailable, or fails.
    """
    try:
        collector = _get_context_collector()
        context = collector.collect(exc_type, exc_value, exc_traceback)
        
        explainer = _get_ai_explainer()
        explanation = explainer.explain(context)
        
        if explanation:
            output = "\n" + "=" * 70 + "\n"
            output += "🤖 AI-POWERED EXPLANATION"
            if _config.show_confidence:
                output += f" (Confidence: {explanation.confidence:.0%})"
            output += "\n" + "=" * 70 + "\n\n"
            output += explanation.format_markdown()
            return output
    except Exception as e:
        # Intentional graceful degradation - see Design Note in docstring
        if _config.debug_mode:
            print(f"[errfriendly] AI explanation failed: {e}", file=sys.stderr)
    
    return None


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
    global _original_excepthook, _logger, _config
    global _context_collector, _ai_explainer, _chain_analyzer
    
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
    
    # Reset AI components
    _context_collector = None
    _ai_explainer = None
    _chain_analyzer = None
    
    # Reset config to defaults
    _config = Config()


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


# =============================================================================
# v3.0 API: AI and Configuration Functions
# =============================================================================

def enable_ai(
    backend: Union[str, AIBackend] = "local",
    model: Optional[str] = None,
    explain_depth: Union[str, ExplainDepth] = "intermediate",
    api_key: Optional[str] = None,
) -> None:
    """
    Enable AI-powered contextual explanations.
    
    This function enables the AI features of errfriendly, which provide
    context-aware, personalized error explanations based on your actual code.
    
    Args:
        backend: AI backend to use. Options:
            - "local": Ollama (default, privacy-first, requires Ollama running)
            - "openai": OpenAI API (requires API key)
            - "anthropic": Anthropic Claude API (requires API key)
            - "gemini": Google Gemini API (requires API key)
        model: Model name to use. Defaults depend on backend:
            - local: "codellama"
            - openai: "gpt-4o-mini"
            - anthropic: "claude-3-haiku-20240307"
            - gemini: "gemini-1.5-flash"
        explain_depth: Explanation detail level. Options:
            - "beginner": ELI5 style, simple language
            - "intermediate": Standard developer explanations (default)
            - "expert": Deep technical details
        api_key: API key for cloud backends. Can also use environment variables:
            - OPENAI_API_KEY for OpenAI
            - ANTHROPIC_API_KEY for Anthropic
            - GOOGLE_API_KEY for Gemini
    
    Example:
        >>> import errfriendly
        >>> errfriendly.install()
        >>> 
        >>> # Enable local AI (Ollama)
        >>> errfriendly.enable_ai(backend="local", model="codellama")
        >>> 
        >>> # Or enable OpenAI
        >>> errfriendly.enable_ai(backend="openai", api_key="sk-...")
    
    Note:
        AI features require optional dependencies. Install them with:
        - pip install errfriendly[ai-local]  # For Ollama
        - pip install errfriendly[ai-openai]  # For OpenAI
        - pip install errfriendly[ai-all]  # For all backends
    """
    global _config, _ai_explainer, _context_collector
    
    # Parse backend
    if isinstance(backend, str):
        backend_map = {
            "local": AIBackend.LOCAL,
            "ollama": AIBackend.LOCAL,
            "deepseek": AIBackend.DEEPSEEK,
            "openai": AIBackend.OPENAI,
            "anthropic": AIBackend.ANTHROPIC,
            "gemini": AIBackend.GEMINI,
            "google": AIBackend.GEMINI,
        }
        _config.ai_backend = backend_map.get(backend.lower(), AIBackend.DEEPSEEK)
    else:
        _config.ai_backend = backend
    
    # Parse explain depth
    if isinstance(explain_depth, str):
        depth_map = {
            "beginner": ExplainDepth.BEGINNER,
            "intermediate": ExplainDepth.INTERMEDIATE,
            "expert": ExplainDepth.EXPERT,
        }
        _config.explain_depth = depth_map.get(explain_depth.lower(), ExplainDepth.INTERMEDIATE)
    else:
        _config.explain_depth = explain_depth
    
    # Set model (use defaults if not provided)
    if model:
        _config.ai_model = model
    else:
        default_models = {
            AIBackend.LOCAL: "codellama",
            AIBackend.DEEPSEEK: "deepseek-chat",
            AIBackend.OPENAI: "gpt-4o-mini",
            AIBackend.ANTHROPIC: "claude-3-haiku-20240307",
            AIBackend.GEMINI: "gemini-1.5-flash",
        }
        _config.ai_model = default_models.get(_config.ai_backend, "deepseek-chat")
    
    # Set API key if provided (for cloud backends)
    if api_key and _config.ai_backend != AIBackend.LOCAL:
        import os
        env_vars = {
            AIBackend.DEEPSEEK: "DEEPSEEK_API_KEY",
            AIBackend.OPENAI: "OPENAI_API_KEY",
            AIBackend.ANTHROPIC: "ANTHROPIC_API_KEY",
            AIBackend.GEMINI: "GOOGLE_API_KEY",
        }
        env_var = env_vars.get(_config.ai_backend)
        if env_var:
            os.environ[env_var] = api_key
    
    # Update privacy mode based on backend
    if _config.ai_backend == AIBackend.LOCAL:
        _config.privacy_mode = PrivacyMode.LOCAL_ONLY
    else:
        _config.privacy_mode = PrivacyMode.ALLOW_CLOUD
    
    # Enable AI
    _config.ai_enabled = True
    
    # Reset explainer to pick up new config
    _ai_explainer = None
    _context_collector = None
    
    # Print confirmation
    backend_name = _config.ai_backend.value
    print(f"[errfriendly] AI enabled: {backend_name} ({_config.ai_model})", file=sys.stderr)


def disable_ai() -> None:
    """
    Disable AI-powered explanations.
    
    After calling this, errfriendly will use only static explanations.
    """
    global _config, _ai_explainer
    
    _config.ai_enabled = False
    _ai_explainer = None
    
    print("[errfriendly] AI disabled", file=sys.stderr)


def configure(**kwargs: Any) -> None:
    """
    Configure errfriendly options.
    
    This function allows fine-grained control over errfriendly behavior.
    
    Args:
        ai_threshold: Confidence threshold for caching AI responses (0.0-1.0).
            Default: 0.7
        max_context_lines: Maximum lines of code to include in context.
            Default: 15
        include_variable_values: Include variable values in context.
            Default: True
        privacy_mode: Privacy setting ("local_only" or "allow_cloud").
            Default: "local_only"
        explanation_style: Output style ("bullet_points", "narrative", "stepwise").
            Default: "bullet_points"
        show_confidence: Show AI confidence scores.
            Default: True
        show_chain_analysis: Show exception chain analysis.
            Default: True
        collect_git_changes: Include recent git changes in context.
            Default: False
        ai_timeout: Timeout for AI requests in seconds.
            Default: 10.0
        max_requests_per_minute: Rate limit for AI requests.
            Default: 10
    
    Example:
        >>> import errfriendly
        >>> errfriendly.install()
        >>> errfriendly.configure(
        ...     max_context_lines=20,
        ...     include_variable_values=True,
        ...     explanation_style="narrative",
        ... )
    """
    global _config, _ai_explainer, _context_collector
    
    for key, value in kwargs.items():
        if hasattr(_config, key):
            # Handle string-to-enum conversions
            current = getattr(_config, key)
            if isinstance(current, PrivacyMode) and isinstance(value, str):
                value = PrivacyMode(value)
            elif isinstance(current, ExplanationStyle) and isinstance(value, str):
                value = ExplanationStyle(value)
            elif isinstance(current, ExplainDepth) and isinstance(value, str):
                depth_map = {
                    "beginner": ExplainDepth.BEGINNER,
                    "intermediate": ExplainDepth.INTERMEDIATE,
                    "expert": ExplainDepth.EXPERT,
                }
                value = depth_map.get(value.lower(), current)
            
            setattr(_config, key, value)
        else:
            import warnings
            warnings.warn(f"Unknown configuration option: {key}")
    
    # Reset components to pick up new config
    _ai_explainer = None
    _context_collector = None


def get_config() -> Config:
    """
    Get the current errfriendly configuration.
    
    Returns:
        Current Config object.
    """
    return _config

"""
test_v3_features.py - Tests for errfriendly v3.0 features.

Tests AI-powered explanations, exception chain analysis, and new API functions.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock

# Import v3.0 components
from errfriendly.models import (
    Config,
    AIBackend,
    ExplainDepth,
    ExplanationStyle,
    PrivacyMode,
    ErrorContext,
    ExceptionChain,
    ChainLink,
    AIExplanation,
    FrameInfo,
)
from errfriendly.context_collector import ContextCollector
from errfriendly.exception_graph import ExceptionChainAnalyzer
from errfriendly.ai_explainer import AIExplainer
import errfriendly


class TestModels:
    """Test data structure models."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = Config()
        assert config.ai_enabled is False
        assert config.ai_backend == AIBackend.LOCAL
        assert config.explain_depth == ExplainDepth.INTERMEDIATE
        assert config.max_context_lines == 15
        assert config.include_variable_values is True
    
    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "ai_enabled": True,
            "ai_backend": "openai",
            "max_context_lines": 20,
        }
        config = Config.from_dict(data)
        assert config.ai_enabled is True
        assert config.max_context_lines == 20
    
    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = Config()
        config.ai_enabled = True
        data = config.to_dict()
        assert data["ai_enabled"] is True
        assert data["ai_backend"] == "local"
    
    def test_frame_info(self):
        """Test FrameInfo dataclass."""
        frame = FrameInfo(
            filename="test.py",
            lineno=10,
            function="test_func",
            code_context=["x = 1 + 2"],
            local_variables={"x": "3"},
        )
        assert frame.filename == "test.py"
        assert frame.lineno == 10
    
    def test_error_context_to_prompt(self):
        """Test ErrorContext prompt formatting."""
        context = ErrorContext(
            exception_type="ValueError",
            error_message="invalid literal",
            full_traceback=[],
            code_snippet="x = int('abc')",
            local_variables={"x": "'abc'"},
            import_statements=["import sys"],
            python_version="3.11.0",
        )
        prompt = context.to_prompt_context()
        assert "ValueError" in prompt
        assert "invalid literal" in prompt
        assert "x = 'abc'" in prompt
    
    def test_chain_link(self):
        """Test ChainLink dataclass."""
        link = ChainLink(
            exception_type="KeyError",
            message="'missing'",
            traceback_summary="test.py:10 in func",
            cause_type="cause",
        )
        assert str(link) == "KeyError: 'missing'"
    
    def test_exception_chain_properties(self):
        """Test ExceptionChain properties."""
        primary = ChainLink("TypeError", "msg", "file:1", "none")
        chain = ExceptionChain(
            primary_exception=primary,
            chain=[ChainLink("KeyError", "key", "file:2", "cause")],
        )
        assert chain.depth == 2
        assert chain.has_chain is True
    
    def test_ai_explanation_format(self):
        """Test AIExplanation markdown formatting."""
        explanation = AIExplanation(
            what_happened="You tried to add a string to an int.",
            root_cause_analysis="Type mismatch",
            confidence=0.85,
            quick_fix="Convert string to int first",
            robust_solution="Use type checking",
            preventive_pattern="Add type hints",
            related_docs=["https://docs.python.org/"],
        )
        md = explanation.format_markdown()
        assert "## 🤔 What Happened?" in md
        assert "85%" in md
        assert "https://docs.python.org/" in md


class TestContextCollector:
    """Test context collection."""
    
    def test_collect_basic_error(self):
        """Test collecting context from a basic error."""
        collector = ContextCollector()
        
        try:
            x = 1 / 0
        except ZeroDivisionError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            context = collector.collect(exc_type, exc_value, exc_tb)
        
        assert context.exception_type == "ZeroDivisionError"
        assert "division by zero" in context.error_message
        assert len(context.full_traceback) > 0
    
    def test_collect_with_variables(self):
        """Test that local variables are collected."""
        collector = ContextCollector(Config(include_variable_values=True))
        
        my_var = "test_value"
        try:
            raise ValueError("test error")
        except ValueError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            context = collector.collect(exc_type, exc_value, exc_tb)
        
        # my_var should be in local variables
        assert "my_var" in context.local_variables
    
    def test_sensitive_variable_redaction(self):
        """Test that sensitive variables are redacted."""
        config = Config(sanitize_secrets=True, include_variable_values=True)
        collector = ContextCollector(config)
        
        password = "secret123"
        api_key = "sk-1234567890"
        try:
            raise ValueError("test")
        except ValueError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            context = collector.collect(exc_type, exc_value, exc_tb)
        
        # Sensitive variables should be redacted
        if "password" in context.local_variables:
            assert context.local_variables["password"] == "<REDACTED>"
        if "api_key" in context.local_variables:
            assert context.local_variables["api_key"] == "<REDACTED>"
    
    def test_detect_patterns(self):
        """Test anti-pattern detection."""
        collector = ContextCollector()
        
        try:
            data = None
            x = data[0]  # NoneType subscript error
        except TypeError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            context = collector.collect(exc_type, exc_value, exc_tb)
        
        # Should detect NoneType pattern
        assert any("None" in p for p in context.detected_patterns)


class TestExceptionChainAnalyzer:
    """Test exception chain analysis."""
    
    def test_simple_exception(self):
        """Test analysis of a simple (non-chained) exception."""
        analyzer = ExceptionChainAnalyzer()
        
        try:
            raise ValueError("simple error")
        except ValueError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            chain = analyzer.analyze(exc_type, exc_value, exc_tb)
        
        assert chain.chain_type == "simple"
        assert chain.primary_exception.exception_type == "ValueError"
        assert not chain.has_chain
    
    def test_chained_exception_cause(self):
        """Test analysis of exception with __cause__."""
        analyzer = ExceptionChainAnalyzer()
        
        try:
            try:
                raise KeyError("original")
            except KeyError as e:
                raise ValueError("wrapper") from e
        except ValueError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            chain = analyzer.analyze(exc_type, exc_value, exc_tb)
        
        assert chain.has_chain
        assert chain.primary_exception.exception_type == "ValueError"
        assert len(chain.chain) == 1
        assert chain.chain[0].exception_type == "KeyError"
        assert chain.root_cause.exception_type == "KeyError"
    
    def test_chained_exception_context(self):
        """Test analysis of exception with __context__."""
        analyzer = ExceptionChainAnalyzer()
        
        try:
            try:
                raise KeyError("first")
            except KeyError:
                raise TypeError("second")  # Implicit chaining
        except TypeError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            chain = analyzer.analyze(exc_type, exc_value, exc_tb)
        
        assert chain.has_chain
        assert chain.primary_exception.exception_type == "TypeError"
    
    def test_suppressed_context(self):
        """Test handling of suppressed context (raise from None)."""
        analyzer = ExceptionChainAnalyzer()
        
        try:
            try:
                raise KeyError("original")
            except KeyError:
                raise ValueError("wrapper") from None  # Suppress context
        except ValueError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            chain = analyzer.analyze(exc_type, exc_value, exc_tb)
        
        # Chain should only have primary exception
        assert chain.chain_type == "simple"
    
    def test_generate_narrative(self):
        """Test narrative generation."""
        analyzer = ExceptionChainAnalyzer()
        
        try:
            try:
                raise KeyError("'user_id'")
            except KeyError as e:
                raise ValueError("User lookup failed") from e
        except ValueError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            chain = analyzer.analyze(exc_type, exc_value, exc_tb)
        
        narrative = analyzer.generate_narrative(chain)
        assert "Investigation Map" in narrative
        assert "KeyError" in narrative
        assert "ValueError" in narrative
    
    def test_fix_strategy(self):
        """Test fix strategy generation."""
        analyzer = ExceptionChainAnalyzer()
        
        try:
            try:
                raise KeyError("missing")
            except KeyError as e:
                raise RuntimeError("Failed") from e
        except RuntimeError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            chain = analyzer.analyze(exc_type, exc_value, exc_tb)
        
        strategy = analyzer.generate_fix_strategy(chain)
        assert len(strategy) > 0


class TestAIExplainer:
    """Test AI explainer (with mocked backends)."""
    
    def test_explainer_disabled(self):
        """Test that explainer returns None when AI is disabled."""
        config = Config(ai_enabled=False)
        explainer = AIExplainer(config)
        
        context = ErrorContext(
            exception_type="ValueError",
            error_message="test",
            full_traceback=[],
            code_snippet="",
            local_variables={},
            import_statements=[],
        )
        
        result = explainer.explain(context)
        assert result is None
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        config = Config(ai_enabled=True)
        explainer = AIExplainer(config)
        
        context1 = ErrorContext(
            exception_type="ValueError",
            error_message="same message",
            full_traceback=[],
            code_snippet="",
            local_variables={},
            import_statements=[],
        )
        context2 = ErrorContext(
            exception_type="ValueError",
            error_message="same message",
            full_traceback=[],
            code_snippet="different code",
            local_variables={"x": "1"},
            import_statements=[],
        )
        
        # Same error type + message should have same cache key
        key1 = explainer._compute_cache_key(context1)
        key2 = explainer._compute_cache_key(context2)
        assert key1 == key2
    
    def test_rate_limiting(self):
        """Test rate limiting."""
        config = Config(ai_enabled=True, max_requests_per_minute=2)
        explainer = AIExplainer(config)
        
        # First two should pass
        assert explainer._check_rate_limit() is True
        assert explainer._check_rate_limit() is True
        
        # Third should fail
        assert explainer._check_rate_limit() is False
    
    def test_prompt_building(self):
        """Test prompt building."""
        config = Config(ai_enabled=True, explain_depth=ExplainDepth.BEGINNER)
        explainer = AIExplainer(config)
        
        system_prompt = explainer._build_system_prompt()
        assert "simple language" in system_prompt or "beginner" in system_prompt.lower()


class TestAPIFunctions:
    """Test the public API functions."""
    
    def setup_method(self):
        """Reset state before each test."""
        errfriendly.uninstall()
    
    def teardown_method(self):
        """Clean up after each test."""
        errfriendly.uninstall()
    
    def test_install_uninstall(self):
        """Test basic install/uninstall."""
        assert errfriendly.is_installed() is False
        errfriendly.install()
        assert errfriendly.is_installed() is True
        errfriendly.uninstall()
        assert errfriendly.is_installed() is False
    
    def test_enable_ai_local(self):
        """Test enabling local AI."""
        errfriendly.install()
        errfriendly.enable_ai(backend="local", model="codellama")
        
        config = errfriendly.get_config()
        assert config.ai_enabled is True
        assert config.ai_backend == AIBackend.LOCAL
        assert config.ai_model == "codellama"
    
    def test_enable_ai_openai(self):
        """Test enabling OpenAI backend."""
        errfriendly.install()
        errfriendly.enable_ai(backend="openai", model="gpt-4")
        
        config = errfriendly.get_config()
        assert config.ai_enabled is True
        assert config.ai_backend == AIBackend.OPENAI
        assert config.ai_model == "gpt-4"
    
    def test_disable_ai(self):
        """Test disabling AI."""
        errfriendly.install()
        errfriendly.enable_ai(backend="local")
        errfriendly.disable_ai()
        
        config = errfriendly.get_config()
        assert config.ai_enabled is False
    
    def test_configure(self):
        """Test configuration function."""
        errfriendly.install()
        errfriendly.configure(
            max_context_lines=20,
            include_variable_values=False,
            ai_threshold=0.8,
        )
        
        config = errfriendly.get_config()
        assert config.max_context_lines == 20
        assert config.include_variable_values is False
        assert config.ai_threshold == 0.8
    
    def test_explain_depth_configuration(self):
        """Test explain depth settings."""
        errfriendly.install()
        errfriendly.enable_ai(backend="local", explain_depth="beginner")
        
        config = errfriendly.get_config()
        assert config.explain_depth == ExplainDepth.BEGINNER


class TestBackwardCompatibility:
    """Test backward compatibility with v2.x API."""
    
    def setup_method(self):
        """Reset state before each test."""
        errfriendly.uninstall()
    
    def teardown_method(self):
        """Clean up after each test."""
        errfriendly.uninstall()
    
    def test_basic_install_works(self):
        """Test that basic install() works without AI."""
        import errfriendly
        errfriendly.install()
        assert errfriendly.is_installed()
    
    def test_get_friendly_message(self):
        """Test that get_friendly_message still works."""
        from errfriendly import get_friendly_message
        
        msg = get_friendly_message(ValueError, ValueError("test"))
        assert "ValueError" in msg or "value" in msg.lower()
    
    def test_install_with_log_file(self):
        """Test install with log_file parameter."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as f:
            log_path = f.name
        
        try:
            errfriendly.install(log_file=log_path)
            assert errfriendly.is_installed()
        finally:
            errfriendly.uninstall()
            if os.path.exists(log_path):
                os.remove(log_path)
    
    def test_install_hide_traceback(self):
        """Test install with show_original_traceback=False."""
        errfriendly.install(show_original_traceback=False)
        assert errfriendly.is_installed()

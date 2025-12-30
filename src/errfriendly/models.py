"""
models.py - Data structures for errfriendly v3.0.

This module contains all the dataclasses and enums used for AI-powered
error analysis and exception chain representation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ExplainDepth(Enum):
    """User's preferred explanation detail level."""
    BEGINNER = "beginner"        # ELI5 style, avoid jargon
    INTERMEDIATE = "intermediate"  # Standard developer explanation
    EXPERT = "expert"            # Deep technical details


class AIBackend(Enum):
    """Supported AI backend types."""
    LOCAL = "local"              # Ollama, llama.cpp, GPT4All
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class ExplanationStyle(Enum):
    """Output format style for explanations."""
    BULLET_POINTS = "bullet_points"
    NARRATIVE = "narrative"
    STEPWISE = "stepwise"


class PrivacyMode(Enum):
    """Privacy configuration for AI features."""
    LOCAL_ONLY = "local_only"    # No data leaves the machine
    ALLOW_CLOUD = "allow_cloud"  # User consented to cloud APIs


@dataclass
class FrameInfo:
    """Information about a single stack frame."""
    filename: str
    lineno: int
    function: str
    code_context: List[str]      # Lines around the error
    local_variables: Dict[str, str]  # Sanitized string representations
    
    def __post_init__(self):
        # Ensure code_context is always a list
        if self.code_context is None:
            self.code_context = []
        if self.local_variables is None:
            self.local_variables = {}


@dataclass
class ErrorContext:
    """Complete context for AI-powered error analysis.
    
    This dataclass captures all relevant information about an error
    for AI analysis, including the traceback, variable states,
    surrounding code, and project structure.
    """
    exception_type: str
    error_message: str
    full_traceback: List[FrameInfo]
    code_snippet: str            # 5-10 lines around error
    local_variables: Dict[str, Any]  # Top frame variables
    import_statements: List[str]
    project_structure: List[str] = field(default_factory=list)
    recent_changes: Optional[str] = None  # Git diff if available
    detected_patterns: List[str] = field(default_factory=list)  # Anti-patterns
    python_version: str = ""
    
    def to_prompt_context(self) -> str:
        """Convert context to a string suitable for AI prompts."""
        lines = [
            f"Exception Type: {self.exception_type}",
            f"Error Message: {self.error_message}",
            f"Python Version: {self.python_version}",
            "",
            "Code Snippet:",
            self.code_snippet,
            "",
            "Local Variables:",
        ]
        
        for name, value in self.local_variables.items():
            lines.append(f"  {name} = {value}")
        
        if self.detected_patterns:
            lines.append("")
            lines.append("Detected Patterns:")
            for pattern in self.detected_patterns:
                lines.append(f"  - {pattern}")
        
        if self.import_statements:
            lines.append("")
            lines.append("Imports:")
            for imp in self.import_statements[:10]:  # Limit imports
                lines.append(f"  {imp}")
        
        return "\n".join(lines)


@dataclass
class ChainLink:
    """A single exception in the exception chain."""
    exception_type: str
    message: str
    traceback_summary: str
    cause_type: str              # "cause" (__cause__) or "context" (__context__)
    is_suppressed: bool = False  # raise ... from None
    frame_count: int = 0         # Number of frames in this exception's traceback
    
    def __str__(self) -> str:
        return f"{self.exception_type}: {self.message}"


@dataclass
class ExceptionChain:
    """Represents the full chain of exceptions.
    
    This tracks __cause__ and __context__ relationships between
    exceptions to provide a complete debugging narrative.
    """
    primary_exception: Optional[ChainLink] = None
    chain: List[ChainLink] = field(default_factory=list)
    root_cause: Optional[ChainLink] = None
    chain_type: str = "simple"   # "simple", "wrapper", "cascade", "cleanup"
    fix_priority: List[int] = field(default_factory=list)  # Indices by priority
    
    @property
    def depth(self) -> int:
        """Return the depth of the exception chain."""
        return 1 + len(self.chain)
    
    @property
    def has_chain(self) -> bool:
        """Check if this is a chained exception."""
        return len(self.chain) > 0


@dataclass
class AIExplanation:
    """AI-generated explanation response.
    
    Contains the structured explanation with multiple fix options
    and confidence scoring.
    """
    what_happened: str
    root_cause_analysis: str
    confidence: float            # 0.0 to 1.0
    quick_fix: str               # Option 1: Immediate workaround
    robust_solution: str         # Option 2: Proper fix
    preventive_pattern: str      # Option 3: Future prevention
    related_docs: List[str] = field(default_factory=list)
    raw_response: str = ""       # Original AI response for debugging
    
    def format_markdown(self) -> str:
        """Format explanation as markdown."""
        lines = [
            "## 🤔 What Happened?",
            self.what_happened,
            "",
            "## 🔍 Root Cause Analysis",
            self.root_cause_analysis,
            f"- Confidence: {self.confidence:.0%}",
            "",
            "## 🛠️ How to Fix",
            "",
            "### Option 1: Quick Fix (Immediate)",
            self.quick_fix,
            "",
            "### Option 2: Robust Solution (Recommended)",
            self.robust_solution,
            "",
            "### Option 3: Prevent Future Occurrences",
            self.preventive_pattern,
        ]
        
        if self.related_docs:
            lines.extend([
                "",
                "## 📚 Related Documentation",
            ])
            for doc in self.related_docs:
                lines.append(f"- {doc}")
        
        return "\n".join(lines)


@dataclass
class Config:
    """errfriendly configuration.
    
    Centralized configuration for all errfriendly features including
    AI settings, privacy controls, and output formatting.
    """
    # AI Settings
    ai_enabled: bool = False
    ai_backend: AIBackend = AIBackend.LOCAL
    ai_model: str = "codellama"
    explain_depth: ExplainDepth = ExplainDepth.INTERMEDIATE
    ai_threshold: float = 0.7    # Confidence threshold for caching
    ai_timeout: float = 10.0     # Timeout in seconds
    
    # Context Collection
    max_context_lines: int = 15
    include_variable_values: bool = True
    max_variable_repr_length: int = 200
    collect_git_changes: bool = False
    
    # Privacy & Safety
    privacy_mode: PrivacyMode = PrivacyMode.LOCAL_ONLY
    sanitize_paths: bool = True  # Remove absolute paths
    sanitize_secrets: bool = True  # Remove likely secrets
    
    # Output
    explanation_style: ExplanationStyle = ExplanationStyle.BULLET_POINTS
    show_confidence: bool = True
    show_chain_analysis: bool = True
    
    # Debug & Internals
    debug_mode: bool = False  # If True, log internal errors to stderr
    max_cache_size: int = 100  # Maximum cached AI explanations
    
    # Rate Limiting
    max_requests_per_minute: int = 10
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        config = cls()
        
        for key, value in data.items():
            if hasattr(config, key):
                attr = getattr(config, key)
                # Handle enum conversions
                if isinstance(attr, Enum) and isinstance(value, str):
                    enum_class = type(attr)
                    try:
                        value = enum_class(value)
                    except ValueError:
                        continue
                setattr(config, key, value)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result

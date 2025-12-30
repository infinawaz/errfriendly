# errfriendly v3.0 API Reference

> Complete API documentation for errfriendly's public interfaces.

---

## Table of Contents

- [Core Functions](#core-functions)
- [AI Functions](#ai-functions)
- [Configuration](#configuration)
- [Data Types](#data-types)
- [Advanced Usage](#advanced-usage)

---

## Core Functions

### `install()`

Install the friendly exception hook.

```python
errfriendly.install(
    show_original_traceback: bool = True,
    log_file: str | None = None
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `show_original_traceback` | `bool` | `True` | Show Python's standard traceback before friendly message |
| `log_file` | `str \| None` | `None` | Path to log file for exception logging |

**Example:**

```python
import errfriendly

# Basic installation
errfriendly.install()

# Hide traceback, only show friendly message
errfriendly.install(show_original_traceback=False)

# Enable file logging
errfriendly.install(log_file="errors.log")
```

---

### `uninstall()`

Restore the original exception hook.

```python
errfriendly.uninstall() -> None
```

**Example:**

```python
errfriendly.install()
# ... your code ...
errfriendly.uninstall()  # Back to normal Python exceptions
```

---

### `is_installed()`

Check if errfriendly is currently active.

```python
errfriendly.is_installed() -> bool
```

**Returns:** `True` if errfriendly is handling exceptions.

---

### `get_friendly_message()`

Get a friendly explanation for an exception without raising it.

```python
from errfriendly import get_friendly_message

get_friendly_message(
    exc_type: Type[BaseException],
    exc_value: BaseException
) -> str
```

**Example:**

```python
msg = get_friendly_message(ValueError, ValueError("invalid literal"))
print(msg)
```

---

## AI Functions

### `enable_ai()`

Enable AI-powered contextual explanations.

```python
errfriendly.enable_ai(
    backend: str | AIBackend = "local",
    model: str | None = None,
    explain_depth: str | ExplainDepth = "intermediate",
    api_key: str | None = None
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | `str \| AIBackend` | `"local"` | AI backend: `"local"`, `"openai"`, `"anthropic"`, `"gemini"` |
| `model` | `str \| None` | Backend default | Model name (e.g., `"codellama"`, `"gpt-4"`) |
| `explain_depth` | `str \| ExplainDepth` | `"intermediate"` | Detail level: `"beginner"`, `"intermediate"`, `"expert"` |
| `api_key` | `str \| None` | `None` | API key for cloud backends |

**Default Models by Backend:**

| Backend | Default Model |
|---------|---------------|
| `local` | `codellama` |
| `openai` | `gpt-4o-mini` |
| `anthropic` | `claude-3-haiku-20240307` |
| `gemini` | `gemini-1.5-flash` |

**Example:**

```python
# Local AI with Ollama
errfriendly.enable_ai(backend="local", model="codellama")

# OpenAI with API key
errfriendly.enable_ai(
    backend="openai",
    model="gpt-4",
    api_key="sk-..."
)

# Beginner-friendly explanations
errfriendly.enable_ai(
    backend="local",
    explain_depth="beginner"
)
```

**Environment Variables:**

Instead of passing `api_key`, you can set:
- `OPENAI_API_KEY` for OpenAI
- `ANTHROPIC_API_KEY` for Anthropic
- `GOOGLE_API_KEY` for Gemini

---

### `disable_ai()`

Disable AI-powered explanations.

```python
errfriendly.disable_ai() -> None
```

After calling this, errfriendly uses only static explanations.

---

## Configuration

### `configure()`

Fine-tune errfriendly behavior.

```python
errfriendly.configure(**options) -> None
```

**Available Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ai_threshold` | `float` | `0.7` | Confidence threshold for caching (0.0-1.0) |
| `ai_timeout` | `float` | `10.0` | AI request timeout in seconds |
| `max_requests_per_minute` | `int` | `10` | Rate limit for AI requests |
| `max_context_lines` | `int` | `15` | Lines of code to include in context |
| `include_variable_values` | `bool` | `True` | Include variable values in analysis |
| `collect_git_changes` | `bool` | `False` | Include recent git changes |
| `privacy_mode` | `str` | `"local_only"` | `"local_only"` or `"allow_cloud"` |
| `explanation_style` | `str` | `"bullet_points"` | `"bullet_points"`, `"narrative"`, `"stepwise"` |
| `show_confidence` | `bool` | `True` | Show AI confidence scores |
| `show_chain_analysis` | `bool` | `True` | Show exception chain visualization |

**Example:**

```python
errfriendly.configure(
    max_context_lines=20,
    include_variable_values=True,
    show_confidence=True,
    ai_timeout=15.0,
)
```

---

### `get_config()`

Get the current configuration.

```python
errfriendly.get_config() -> Config
```

**Returns:** Current `Config` object.

**Example:**

```python
config = errfriendly.get_config()
print(f"AI enabled: {config.ai_enabled}")
print(f"Backend: {config.ai_backend.value}")
```

---

## Data Types

### `Config`

Configuration dataclass.

```python
from errfriendly import Config

@dataclass
class Config:
    ai_enabled: bool = False
    ai_backend: AIBackend = AIBackend.LOCAL
    ai_model: str = "codellama"
    explain_depth: ExplainDepth = ExplainDepth.INTERMEDIATE
    ai_threshold: float = 0.7
    ai_timeout: float = 10.0
    max_context_lines: int = 15
    include_variable_values: bool = True
    # ... more options
```

**Methods:**

- `Config.from_dict(data: dict) -> Config` - Create from dictionary
- `config.to_dict() -> dict` - Convert to dictionary

---

### `AIBackend`

Enum for AI backend types.

```python
from errfriendly import AIBackend

class AIBackend(Enum):
    LOCAL = "local"          # Ollama
    OPENAI = "openai"        # OpenAI API
    ANTHROPIC = "anthropic"  # Anthropic Claude
    GEMINI = "gemini"        # Google Gemini
```

---

### `ExplainDepth`

Enum for explanation detail levels.

```python
from errfriendly import ExplainDepth

class ExplainDepth(Enum):
    BEGINNER = "beginner"        # Simple, no jargon
    INTERMEDIATE = "intermediate"  # Standard developer
    EXPERT = "expert"            # Deep technical details
```

---

### `ErrorContext`

Context collected for AI analysis.

```python
from errfriendly import ErrorContext

@dataclass
class ErrorContext:
    exception_type: str
    error_message: str
    full_traceback: List[FrameInfo]
    code_snippet: str
    local_variables: Dict[str, Any]
    import_statements: List[str]
    project_structure: List[str]
    recent_changes: Optional[str]
    detected_patterns: List[str]
    python_version: str
```

**Methods:**

- `context.to_prompt_context() -> str` - Format for AI prompts

---

### `ExceptionChain`

Represents an exception chain.

```python
from errfriendly import ExceptionChain

@dataclass
class ExceptionChain:
    primary_exception: ChainLink | None
    chain: List[ChainLink]
    root_cause: ChainLink | None
    chain_type: str  # "simple", "wrapper", "cascade", "cleanup"
    fix_priority: List[int]
```

**Properties:**

- `chain.depth -> int` - Chain depth
- `chain.has_chain -> bool` - Whether chained

---

### `AIExplanation`

AI-generated explanation.

```python
from errfriendly import AIExplanation

@dataclass
class AIExplanation:
    what_happened: str
    root_cause_analysis: str
    confidence: float  # 0.0 to 1.0
    quick_fix: str
    robust_solution: str
    preventive_pattern: str
    related_docs: List[str]
```

**Methods:**

- `explanation.format_markdown() -> str` - Format as markdown

---

## Advanced Usage

### Direct Context Collection

```python
from errfriendly.context_collector import ContextCollector
from errfriendly import Config
import sys

config = Config(include_variable_values=True)
collector = ContextCollector(config)

try:
    x = 1 / 0
except:
    context = collector.collect(*sys.exc_info())
    print(f"Exception: {context.exception_type}")
    print(f"Patterns: {context.detected_patterns}")
    print(f"Variables: {context.local_variables}")
```

---

### Direct Chain Analysis

```python
from errfriendly.exception_graph import ExceptionChainAnalyzer
import sys

analyzer = ExceptionChainAnalyzer()

try:
    try:
        raise KeyError("original")
    except KeyError as e:
        raise ValueError("wrapper") from e
except:
    chain = analyzer.analyze(*sys.exc_info())
    print(f"Chain type: {chain.chain_type}")
    print(f"Root cause: {chain.root_cause}")
    print(analyzer.generate_narrative(chain))
    print(analyzer.generate_fix_strategy(chain))
```

---

### Custom AI Backend

```python
from errfriendly.ai_explainer import AIBackendBase, AIExplainer
from errfriendly import Config

class MyCustomBackend(AIBackendBase):
    @property
    def name(self) -> str:
        return "MyBackend"
    
    def is_available(self) -> bool:
        return True
    
    def generate(self, prompt: str, system_prompt: str) -> str:
        # Your custom AI logic here
        return "My custom explanation..."

# Use custom backend
config = Config(ai_enabled=True)
explainer = AIExplainer(config)
explainer._backend = MyCustomBackend()
```

---

## Exception Types Supported

errfriendly provides friendly explanations for 23+ exception types:

| Category | Exceptions |
|----------|------------|
| **Type Errors** | `TypeError`, `ValueError`, `AttributeError` |
| **Container Errors** | `KeyError`, `IndexError` |
| **Import Errors** | `ImportError`, `ModuleNotFoundError` |
| **Name Errors** | `NameError`, `SyntaxError` |
| **Math Errors** | `ZeroDivisionError`, `OverflowError` |
| **File Errors** | `FileNotFoundError`, `PermissionError` |
| **Memory Errors** | `MemoryError`, `RecursionError` |
| **Encoding Errors** | `UnicodeDecodeError`, `UnicodeEncodeError` |
| **Other** | `AssertionError`, `NotImplementedError`, `StopIteration`, `TimeoutError`, `ConnectionError`, `KeyboardInterrupt` |

Plus a **fallback handler** for any unrecognized exception type.

# 🎯 errfriendly

> **Friendly, human-readable explanations for Python exceptions — now with AI-powered contextual understanding!**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/errfriendly.svg)](https://pypi.org/project/errfriendly/)

**errfriendly** transforms cryptic Python error messages into clear, actionable explanations. Version 3.0 introduces **AI-powered contextual analysis** and **exception chain visualization** for an intelligent debugging assistant experience.

---

## ✨ What's New in v3.0

- 🤖 **AI-Powered Explanations**: Get context-aware, personalized error explanations
- 🔗 **Exception Chain Analysis**: Visualize and understand `__cause__` and `__context__` chains
- 🏠 **Local-First AI**: Privacy-first with Ollama support (no data leaves your machine)
- ☁️ **Cloud AI Fallback**: OpenAI, Anthropic, and Gemini support (opt-in)
- 🎚️ **Explanation Depth**: Beginner, Intermediate, or Expert level explanations
- 🔒 **Zero Breaking Changes**: Existing v2.x code works unchanged

---

## ✨ Features

- 🔍 **Clear Explanations**: Understand what went wrong in plain English
- 💡 **Actionable Suggestions**: Get step-by-step guidance on how to fix common errors
- 🤖 **AI Analysis**: Deep contextual understanding of your code (optional)
- 🔗 **Chain Visualization**: Map exception causes into debugging stories
- 🎨 **Colorful Output**: ANSI colors in terminal for better readability
- 📝 **Logging Support**: Optionally log exceptions to a file
- 🎯 **Zero Dependencies**: Core package requires no external packages
- ⚡ **Easy Integration**: Just two lines of code to get started
- 🔧 **Configurable**: Extensive customization options
- 📦 **23+ Exception Types**: Covers all common Python exceptions

---

## 📦 Installation

```bash
# Core package (zero dependencies)
pip install errfriendly

# With AI features
pip install errfriendly[ai-local]    # Ollama support
pip install errfriendly[ai-openai]   # OpenAI support
pip install errfriendly[ai-all]      # All AI backends
```

For development installation:

```bash
git clone https://github.com/infinawaz/errfriendly.git
cd errfriendly
pip install -e ".[dev]"
```

---

## 🚀 Quickstart

### Basic Usage (v2.x Compatible)

```python
import errfriendly

# Enable friendly error messages
errfriendly.install()

# That's it! Now all exceptions will show friendly explanations.
```

### AI-Powered Explanations (v3.0)

```python
import errfriendly

# Install the exception hook
errfriendly.install()

# Enable AI with local LLM (Ollama)
errfriendly.enable_ai(
    backend="local",
    model="codellama",
    explain_depth="intermediate"
)

# Or use OpenAI
errfriendly.enable_ai(
    backend="openai",
    api_key="sk-...",  # Or set OPENAI_API_KEY env var
    explain_depth="beginner"
)
```

### Fine-Grained Configuration

```python
errfriendly.configure(
    ai_threshold=0.7,           # Confidence threshold for caching
    max_context_lines=15,       # Lines of code to analyze
    include_variable_values=True,
    privacy_mode="local_only",  # or "allow_cloud"
    show_confidence=True,       # Show AI confidence scores
    show_chain_analysis=True,   # Show exception chain maps
)
```

---

## 📸 Before & After

### Before (Standard Python)

```
Traceback (most recent call last):
  File "example.py", line 3, in <module>
    result = data[0]
TypeError: 'NoneType' object is not subscriptable
```

😕 *"What does subscriptable even mean?"*

### After (With errfriendly + AI)

```
Traceback (most recent call last):
  File "example.py", line 3, in <module>
    result = data[0]
TypeError: 'NoneType' object is not subscriptable

======================================================================
🤖 AI-POWERED EXPLANATION (Confidence: 92%)
======================================================================

## 🤔 What Happened?
You tried to access index `[0]` on the variable `data`, but `data` is `None`.
Looking at your code, `data` was assigned `None` on line 2.

## 🔍 Root Cause Analysis
- Primary issue: Accessing an index on a None value
- Contributing factors: Missing null check before indexing
- Confidence: High

## 🛠️ How to Fix

### Option 1: Quick Fix (Immediate)
```python
if data is not None:
    result = data[0]
```

### Option 2: Robust Solution (Recommended)
```python
result = data[0] if data else default_value
```

### Option 3: Prevent Future Occurrences
```python
def get_first_item(data: list | None) -> Any:
    if not data:
        raise ValueError("data cannot be empty or None")
    return data[0]
```

======================================================================
📝 Quick Reference (Static):
======================================================================
📛 TypeError: Trying to index None
...
```

---

## 🔗 Exception Chain Analysis

When exceptions are chained (using `raise ... from ...`), errfriendly visualizes the chain:

```python
try:
    user = db.get_user(user_id)  # KeyError
except KeyError as e:
    raise ValueError("User not found") from e
```

**Output:**

```
======================================================================
🔗 EXCEPTION CHAIN ANALYSIS
======================================================================

🕵️ Exception Investigation Map:

[Primary Error] ValueError: User not found
    ↳ Caused by: [KeyError] 'user_id'

📖 Story:
(1) First, a KeyError occurred: "'user_id'" → 
(2) which caused a ValueError: "User not found"

🔧 Fix Strategy:
Focus on the underlying KeyError: "'user_id'". 
The ValueError is just a wrapper.
```

---

## 🎛️ Configuration Options

### AI Backend Options

| Backend | Description | Requirements |
|---------|-------------|--------------|
| `local` / `ollama` | Local LLM via Ollama | Ollama running locally |
| `openai` | OpenAI API | `OPENAI_API_KEY` env var |
| `anthropic` | Anthropic Claude | `ANTHROPIC_API_KEY` env var |
| `gemini` | Google Gemini | `GOOGLE_API_KEY` env var |

### Explanation Depth

| Level | Description |
|-------|-------------|
| `beginner` | ELI5 style, simple language, explains jargon |
| `intermediate` | Standard developer explanations (default) |
| `expert` | Deep technical details, CPython internals |

### All Configuration Options

```python
errfriendly.configure(
    # AI Settings
    ai_threshold=0.7,           # Cache confidence threshold (0.0-1.0)
    ai_timeout=10.0,            # AI request timeout (seconds)
    max_requests_per_minute=10, # Rate limiting
    
    # Context Collection
    max_context_lines=15,       # Lines of code to include
    include_variable_values=True,
    collect_git_changes=False,  # Include git diff
    
    # Privacy & Safety
    privacy_mode="local_only",  # "local_only" or "allow_cloud"
    
    # Output
    explanation_style="bullet_points",  # or "narrative", "stepwise"
    show_confidence=True,
    show_chain_analysis=True,
)
```

---

## 📋 Supported Exception Types

errfriendly provides friendly explanations for:

| Exception | Common Causes |
|-----------|--------------|
| `TypeError` | Wrong type operations, None subscripting, not callable |
| `ValueError` | Invalid conversions, unpacking issues |
| `IndexError` | List/tuple/string index out of range |
| `KeyError` | Missing dictionary keys |
| `AttributeError` | Accessing non-existent attributes |
| `NameError` | Undefined variables |
| `ImportError` | Failed imports |
| `ModuleNotFoundError` | Missing modules |
| `ZeroDivisionError` | Division by zero |
| `FileNotFoundError` | Missing files |
| `PermissionError` | Access denied |
| `RecursionError` | Infinite recursion |
| `SyntaxError` | Invalid syntax |
| `UnicodeDecodeError` | Encoding issues |
| `UnicodeEncodeError` | Encoding issues |
| `OverflowError` | Number too large |
| `MemoryError` | Out of memory |
| `StopIteration` | Iterator exhausted |
| `AssertionError` | Failed assertions |
| `NotImplementedError` | Unimplemented features |
| `KeyboardInterrupt` | User interruption (Ctrl+C) |
| `TimeoutError` | Operation timeouts |
| `ConnectionError` | Network connection failures |

Plus a **fallback handler** for any other exception types!

---

## 🛠️ Advanced Usage

### Programmatic Access

```python
from errfriendly import get_friendly_message
from errfriendly.context_collector import ContextCollector
from errfriendly.exception_graph import ExceptionChainAnalyzer

# Get a friendly message directly
message = get_friendly_message(TypeError, TypeError("'int' object is not callable"))
print(message)

# Analyze exception context
collector = ContextCollector()
try:
    1 / 0
except:
    import sys
    context = collector.collect(*sys.exc_info())
    print(f"Detected patterns: {context.detected_patterns}")

# Analyze exception chains
analyzer = ExceptionChainAnalyzer()
try:
    try:
        raise KeyError("original")
    except KeyError as e:
        raise ValueError("wrapper") from e
except:
    chain = analyzer.analyze(*sys.exc_info())
    print(analyzer.generate_narrative(chain))
```

### Integration with Logging

```python
import errfriendly
import logging

# Install with file logging
errfriendly.install(log_file="errors.log")
```

### In Jupyter Notebooks

```python
# Works in Jupyter too!
import errfriendly
errfriendly.install()
errfriendly.enable_ai(backend="local")

# Exceptions in cells will show AI-powered explanations
```

---

## 🧪 Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=errfriendly --cov-report=html
```

---

## 🗺️ Roadmap

### v3.0.0 ✅ (Current)
- [x] AI-powered contextual explanations
- [x] Exception chain analysis and visualization
- [x] Multiple AI backends (Ollama, OpenAI, Anthropic, Gemini)
- [x] Explanation depth levels
- [x] Privacy-first design

### v3.1.0 (Planned)
- [ ] IDE integrations (VS Code extension)
- [ ] Custom prompt templates
- [ ] Framework-specific patterns (Django, FastAPI, etc.)
- [ ] Async/await chain analysis

### v4.0.0 (Goal)
- [ ] Interactive debugging assistant
- [ ] Code fix suggestions with auto-apply
- [ ] Learning from user feedback
- [ ] Multi-language support

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report bugs**: Open an issue describing the problem
2. **Suggest features**: Open an issue with your idea
3. **Submit PRs**: Fork, make changes, and submit a pull request

### Development Setup

```bash
git clone https://github.com/infinawaz/errfriendly.git
cd errfriendly
pip install -e ".[dev,ai-all]"
pytest
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 💖 Acknowledgments

- Inspired by the Python community's focus on developer experience
- Thanks to all contributors who help make error messages friendlier

---

<p align="center">
  Made with ❤️ for Python developers everywhere
</p>

# 🎯 errfriendly

> **Friendly, human-readable explanations for Python exceptions.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/errfriendly.svg)](https://badge.fury.io/py/errfriendly)

**errfriendly** transforms cryptic Python error messages into clear, actionable explanations. Perfect for beginners learning Python or experienced developers who want faster debugging.

---

## ✨ Features

- 🔍 **Clear Explanations**: Understand what went wrong in plain English
- 💡 **Actionable Suggestions**: Get step-by-step guidance on how to fix common errors
- 🎯 **Zero Dependencies**: Pure Python, no external packages required
- ⚡ **Easy Integration**: Just two lines of code to get started
- 🔧 **Configurable**: Show or hide the original traceback as needed
- 📦 **18+ Exception Types**: Covers all common Python exceptions

---

## 📦 Installation

```bash
pip install errfriendly
```

For development installation:

```bash
git clone https://github.com/yourusername/errfriendly.git
cd errfriendly
pip install -e ".[dev]"
```

---

## 🚀 Quickstart

```python
import errfriendly

# Enable friendly error messages
errfriendly.install()

# That's it! Now all exceptions will show friendly explanations.
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

### After (With errfriendly)

```
Traceback (most recent call last):
  File "example.py", line 3, in <module>
    result = data[0]
TypeError: 'NoneType' object is not subscriptable

======================================================================
🔍 FRIENDLY ERROR EXPLANATION
======================================================================

📛 TypeError: Trying to index None

💡 What happened:
   You tried to use square brackets [] on a variable that is None.
   This usually happens when a function returned None instead of a list/dict,
   or when a variable wasn't properly initialized.

🔧 How to fix it:
   1. Check if your variable is None before accessing it: `if my_var is not None:`
   2. Make sure the function you called actually returns something.
   3. Print the variable before this line to see what it contains.
   4. Look for functions that might return None on failure (like .get(), .find(), etc.).

======================================================================
```

✅ *Now you know exactly what to do!*

---

## 🎛️ Configuration

### Show Only Friendly Messages (Hide Traceback)

```python
import errfriendly

# Hide the original traceback, show only the friendly explanation
errfriendly.install(show_original_traceback=False)
```

### Disable Friendly Messages

```python
import errfriendly

# Enable friendly messages
errfriendly.install()

# ... your code ...

# Restore original Python behavior
errfriendly.uninstall()
```

### Check Installation Status

```python
from errfriendly.handler import is_installed

if is_installed():
    print("errfriendly is active!")
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

Plus a **fallback handler** for any other exception types!

---

## 🛠️ Advanced Usage

### Integration with Logging

```python
import errfriendly
import logging

# Install errfriendly
errfriendly.install()

# Your logging still works normally
logging.basicConfig(level=logging.DEBUG)
```

### In Jupyter Notebooks

```python
# Works in Jupyter too!
import errfriendly
errfriendly.install()

# Exceptions in cells will show friendly messages
```

### Testing Your Error Handling

```python
import errfriendly
from errfriendly.messages import get_friendly_message

# Get a friendly message without raising an exception
message = get_friendly_message(TypeError, TypeError("'int' object is not callable"))
print(message)
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

### v0.2.0 (Planned)
- [ ] Colored output for terminal
- [ ] Suggestion ranking by likelihood
- [ ] Integration with popular IDEs

### v0.3.0 (Future)
- [ ] Machine learning-based error classification
- [ ] Custom error message templates
- [ ] Internationalization (i18n) support
- [ ] Stack trace analysis for better context

### v1.0.0 (Goal)
- [ ] Stable API
- [ ] Comprehensive documentation
- [ ] Plugin system for custom handlers
- [ ] Integration with error tracking services (Sentry, etc.)

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report bugs**: Open an issue describing the problem
2. **Suggest features**: Open an issue with your idea
3. **Submit PRs**: Fork, make changes, and submit a pull request

### Development Setup

```bash
git clone https://github.com/yourusername/errfriendly.git
cd errfriendly
pip install -e ".[dev]"
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

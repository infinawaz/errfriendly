# 🎯 errfriendly

> **Turn confusing Python errors into simple, helpful explanations!**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/errfriendly.svg)](https://pypi.org/project/errfriendly/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Get Started in 30 Seconds

### Install
```bash
pip install errfriendly
```

### Use
```python
import errfriendly
errfriendly.install()

# That's it! Now your errors look like this:
```

### Before vs After

**❌ Before (confusing):**
```
Traceback (most recent call last):
  File "app.py", line 5, in <module>
    print(data[0])
TypeError: 'NoneType' object is not subscriptable
```

**✅ After (helpful):**
```
======================================================================
🔍 FRIENDLY ERROR EXPLANATION
======================================================================

📛 TypeError: Trying to index None

💡 What happened:
   You tried to use square brackets [] on a variable that is None.
   This usually happens when a function returned None instead of a list/dict.

🔧 How to fix it:
   1. Check if your variable is None before accessing it: `if my_var is not None:`
   2. Make sure the function you called actually returns something.
   3. Print the variable before this line to see what it contains.

======================================================================
```

---

## 🤖 Want AI-Powered Explanations? (Optional)

Get even smarter, context-aware explanations using **DeepSeek** (open-source, cheap!):

### Step 1: Install with AI support
```bash
pip install errfriendly[ai-deepseek]
```

### Step 2: Get your API key
1. Go to https://platform.deepseek.com/
2. Sign up and get your API key (free credits included!)

### Step 3: Set your API key
```bash
# Windows (PowerShell)
$env:DEEPSEEK_API_KEY = "sk-your-key-here"

# Mac/Linux
export DEEPSEEK_API_KEY="sk-your-key-here"
```

### Step 4: Enable AI
```python
import errfriendly

errfriendly.install()
errfriendly.enable_ai()  # Uses DeepSeek by default!
```

> **💡 Tip:** Don't have a DeepSeek key? The basic `errfriendly.install()` works great without AI!

---

## 📚 All Supported Errors

errfriendly explains **23+ common Python errors**, including:

| Error | Example |
|-------|---------|
| `TypeError` | `None[0]`, `"hello" + 5` |
| `KeyError` | `my_dict['missing_key']` |
| `IndexError` | `my_list[100]` |
| `ValueError` | `int("not a number")` |
| `AttributeError` | `None.something()` |
| `NameError` | Using undefined variables |
| `FileNotFoundError` | Opening missing files |
| `ZeroDivisionError` | `1 / 0` |
| `ImportError` | Missing packages |
| And 15+ more... | |

---

## ⚙️ Configuration Options

```python
import errfriendly

# Basic install
errfriendly.install()

# Hide the original Python traceback (only show friendly message)
errfriendly.install(show_original_traceback=False)

# Log errors to a file
errfriendly.install(log_file="errors.log")

# Disable when done
errfriendly.uninstall()

# Check if installed
print(errfriendly.is_installed())  # True or False
```

---

## 🔗 Exception Chain Analysis (v3.0)

When one error causes another, errfriendly shows you the full story:

```python
try:
    data = get_user(user_id)  # Returns None
except TypeError:
    raise ValueError("User lookup failed")  # Chained exception
```

Output:
```
🔗 EXCEPTION CHAIN ANALYSIS
======================================================================

🕵️ Exception Investigation Map:

[Primary Error] ValueError: User lookup failed
    ↳ Caused by: [TypeError] 'NoneType' object is not subscriptable

📖 Story:
(1) First, a TypeError occurred → (2) which caused a ValueError

🔧 Fix Strategy:
Focus on the underlying TypeError first. The ValueError is just a wrapper.
```

---

## 🌐 AI Backend Options

| Backend | Command | Best For |
|---------|---------|----------|
| **DeepSeek** ⭐ | `pip install errfriendly[ai-deepseek]` | Open-source, cheap, great quality (default) |
| **OpenAI** | `pip install errfriendly[ai-openai]` | Best quality |
| **Anthropic** | `pip install errfriendly[ai-anthropic]` | Claude fans |
| **Gemini** | `pip install errfriendly[ai-gemini]` | Free tier available |
| **Ollama** | `pip install errfriendly[ai-local]` | Privacy (runs locally) |

```python
# Choose your backend
errfriendly.enable_ai()                        # DeepSeek (default)
errfriendly.enable_ai(backend="deepseek")      # DeepSeek (explicit)
errfriendly.enable_ai(backend="openai")        # ChatGPT
errfriendly.enable_ai(backend="anthropic")     # Claude
errfriendly.enable_ai(backend="gemini")        # Google Gemini
errfriendly.enable_ai(backend="local")         # Ollama (local)
```

---

## 🛡️ Proactive Runtime Audit (v3.1)

errfriendly can now detect "silent failures"—bugs that corrupt data without crashing (like usage of `default=str` in JSON).

```python
# Enable proactive auditing
errfriendly.enable_audit()

# Now it watches for dangerous patterns:
import json
from datetime import datetime

# ⚠️ This would normally fail silently (destroying the datetime object)
# With audit enabled, errfriendly warns you immediately!
json.dumps({"time": datetime.now()}, default=str)
```

**Output:**
```
⚠️ AUDIT WARNING: Dangerous JSON Serialization Detected

💡 The 'Silent Destroyer':
   You are using json.dumps(..., default=str).
   This converts complex objects (like datetime) into dumb strings,
   destroying type information without raising an error.

🔧 Fix:
   Use a custom encoder subclass or explicit conversion.
```

---

## ❓ FAQ

### Do I need an API key?
**No!** The basic `errfriendly.install()` works without any API key. AI is optional.

### Will this slow down my code?
**No.** errfriendly only runs when an error actually happens.

### Can I use this in production?
It's designed for **development and learning**. For production, use proper logging.

### Does it work in Jupyter notebooks?
**Yes!** Just add `errfriendly.install()` at the top of your notebook.

---

## 📦 Quick Reference

```python
import errfriendly

# Basic (no API key needed)
errfriendly.install()

# With AI (needs OPENAI_API_KEY)
errfriendly.enable_ai(backend="openai")

# Customize AI
errfriendly.enable_ai(
    backend="openai",
    model="gpt-4o-mini",           # Which model to use
    explain_depth="beginner"       # beginner, intermediate, or expert
)

# Fine-tune settings
errfriendly.configure(
    show_chain_analysis=True,      # Show exception chains
    show_confidence=True,          # Show AI confidence score
)

# Disable
errfriendly.disable_ai()           # Turn off AI
errfriendly.uninstall()            # Remove completely
```

---

## 📄 License

MIT License - Use it however you want!

---

<p align="center">
  Made with ❤️ to help Python beginners understand errors
</p>

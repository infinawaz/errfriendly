#!/usr/bin/env python3
"""
Demo script for errfriendly package.

Run this script to see friendly error messages in action:
    python examples/demo.py
"""

import errfriendly

# Install the friendly exception handler
errfriendly.install()

print("=" * 60)
print("🎯 errfriendly Demo")
print("=" * 60)
print()
print("This script will trigger a TypeError to demonstrate")
print("how errfriendly provides helpful error explanations.")
print()
print("Watch for the friendly message after the traceback!")
print()
print("-" * 60)

# Trigger a common error: trying to subscript None
data = None
result = data[0]  # This will show a friendly error!

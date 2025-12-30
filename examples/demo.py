#!/usr/bin/env python3
"""
Demo script for errfriendly v3.0 features.

This script demonstrates:
1. Basic friendly error messages (v2.x compatible)
2. Exception chain analysis (v3.0)
3. AI-powered explanations (v3.0) - if AI backend is available

Run this script to see v3.0 features in action:
    python examples/demo.py
    python examples/demo.py --ai        # With AI (requires Ollama or API key)
    python examples/demo.py --chain     # Exception chain demo
"""

import sys
import argparse

import errfriendly


def demo_basic():
    """Demo 1: Basic friendly error messages (v2.x compatible)."""
    print("=" * 70)
    print("🎯 Demo 1: Basic Friendly Error Messages")
    print("=" * 70)
    print()
    print("This demonstrates the core errfriendly functionality.")
    print("We'll trigger a TypeError by trying to subscript None.")
    print()
    print("-" * 70)
    
    # Install errfriendly
    errfriendly.install()
    
    # Trigger a common error
    data = None
    result = data[0]  # TypeError: 'NoneType' object is not subscriptable


def demo_chain():
    """Demo 2: Exception chain analysis (v3.0)."""
    print("=" * 70)
    print("🔗 Demo 2: Exception Chain Analysis")
    print("=" * 70)
    print()
    print("This demonstrates exception chain visualization.")
    print("We'll create a chain: KeyError → ValueError → RuntimeError")
    print()
    print("-" * 70)
    
    # Install and configure
    errfriendly.install()
    errfriendly.configure(show_chain_analysis=True)
    
    # Create a chained exception
    try:
        # Simulate a database lookup that fails
        user_data = {}
        user_id = user_data["user_id"]  # KeyError
    except KeyError as e1:
        try:
            # Try to handle it but fail
            raise ValueError("User lookup failed") from e1
        except ValueError as e2:
            # Wrap it again
            raise RuntimeError("Could not complete request") from e2


def demo_ai():
    """Demo 3: AI-powered explanations (v3.0)."""
    print("=" * 70)
    print("🤖 Demo 3: AI-Powered Explanations")
    print("=" * 70)
    print()
    print("This demonstrates AI-powered contextual explanations.")
    print("Requires Ollama running locally or an API key.")
    print()
    
    # Install errfriendly
    errfriendly.install()
    
    # Try to enable AI
    try:
        errfriendly.enable_ai(
            backend="local",
            model="codellama",
            explain_depth="intermediate"
        )
        print("✅ AI enabled with local Ollama backend")
    except Exception as e:
        print(f"⚠️  Could not enable AI: {e}")
        print("   Falling back to static explanations.")
        print()
        print("   To enable AI, install and run Ollama:")
        print("   1. Install Ollama: https://ollama.ai")
        print("   2. Pull a model: ollama pull codellama")
        print("   3. Run this demo again")
        print()
    
    print("-" * 70)
    
    # Trigger an error with context
    numbers = [1, 2, 3, 4, 5]
    multiplier = "2"  # Oops, string instead of int
    
    # This will fail with TypeError
    result = [n * multiplier for n in numbers]


def demo_all_errors():
    """Demo: Show various error types."""
    print("=" * 70)
    print("📋 Demo: Various Error Types")
    print("=" * 70)
    print()
    
    errfriendly.install()
    
    error_demos = [
        ("TypeError (None subscript)", lambda: None[0]),
        ("KeyError", lambda: {}["missing"]),
        ("IndexError", lambda: [][0]),
        ("ZeroDivisionError", lambda: 1/0),
        ("ValueError", lambda: int("abc")),
        ("AttributeError", lambda: None.nonexistent),
    ]
    
    print("Select an error type to demonstrate:")
    for i, (name, _) in enumerate(error_demos, 1):
        print(f"  {i}. {name}")
    print()
    
    try:
        choice = int(input("Enter number (1-6): ")) - 1
        if 0 <= choice < len(error_demos):
            name, func = error_demos[choice]
            print()
            print(f"Triggering: {name}")
            print("-" * 70)
            func()
        else:
            print("Invalid choice")
    except ValueError:
        print("Please enter a number")


def demo_configure():
    """Demo: Show configuration options."""
    print("=" * 70)
    print("⚙️  Demo: Configuration Options")
    print("=" * 70)
    print()
    
    errfriendly.install()
    
    # Show current config
    config = errfriendly.get_config()
    print("Current configuration:")
    print(f"  AI Enabled: {config.ai_enabled}")
    print(f"  AI Backend: {config.ai_backend.value}")
    print(f"  Explain Depth: {config.explain_depth.value}")
    print(f"  Max Context Lines: {config.max_context_lines}")
    print(f"  Include Variables: {config.include_variable_values}")
    print(f"  Show Chain Analysis: {config.show_chain_analysis}")
    print(f"  Privacy Mode: {config.privacy_mode.value}")
    print()
    
    # Configure for beginner-friendly explanations
    print("Configuring for beginner-friendly output...")
    errfriendly.configure(
        max_context_lines=10,
        show_chain_analysis=True,
        show_confidence=True,
    )
    
    print("✅ Configuration updated")
    print()
    print("-" * 70)
    print("Triggering a ZeroDivisionError...")
    print()
    
    x = 10
    y = 0
    result = x / y


def main():
    parser = argparse.ArgumentParser(
        description="errfriendly v3.0 Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo.py           # Basic demo
  python demo.py --chain   # Exception chain demo
  python demo.py --ai      # AI-powered demo (requires Ollama)
  python demo.py --all     # Interactive demo of various errors
  python demo.py --config  # Configuration options demo
        """
    )
    parser.add_argument(
        "--chain", 
        action="store_true",
        help="Demo exception chain analysis"
    )
    parser.add_argument(
        "--ai", 
        action="store_true",
        help="Demo AI-powered explanations"
    )
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Interactive demo of various error types"
    )
    parser.add_argument(
        "--config", 
        action="store_true",
        help="Demo configuration options"
    )
    
    args = parser.parse_args()
    
    print()
    print("🎯 errfriendly v3.0 Demo")
    print(f"   Version: {errfriendly.__version__}")
    print()
    
    if args.chain:
        demo_chain()
    elif args.ai:
        demo_ai()
    elif args.all:
        demo_all_errors()
    elif args.config:
        demo_configure()
    else:
        demo_basic()


if __name__ == "__main__":
    main()

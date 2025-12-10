"""
messages.py - Human-friendly error message generators.

This module contains functions that generate helpful, plain-English explanations
for common Python exceptions. Each exception type has its own handler function
that analyzes the error message and provides contextual advice.
"""

import re
import sys
from typing import Type, Optional


# ANSI color codes for terminal output
class _Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"


def _use_colors() -> bool:
    """Check if we should use ANSI colors (only if stderr is a TTY)."""
    try:
        return sys.stderr.isatty()
    except Exception:
        return False


def get_friendly_message(exc_type: Type[BaseException], exc_value: BaseException) -> str:
    """
    Get a friendly, human-readable explanation for an exception.
    
    Args:
        exc_type: The type of the exception (e.g., TypeError, ValueError).
        exc_value: The exception instance containing the error message.
    
    Returns:
        A string containing a friendly explanation of the error and suggestions
        for how to fix it.
    """
    exc_name = exc_type.__name__
    error_message = str(exc_value)
    
    # Map exception types to their handler functions
    handlers = {
        "TypeError": _explain_type_error,
        "IndexError": _explain_index_error,
        "KeyError": _explain_key_error,
        "ValueError": _explain_value_error,
        "AttributeError": _explain_attribute_error,
        "ImportError": _explain_import_error,
        "ModuleNotFoundError": _explain_module_not_found_error,
        "ZeroDivisionError": _explain_zero_division_error,
        "FileNotFoundError": _explain_file_not_found_error,
        "NameError": _explain_name_error,
        "SyntaxError": _explain_syntax_error,
        "RecursionError": _explain_recursion_error,
        "PermissionError": _explain_permission_error,
        "StopIteration": _explain_stop_iteration,
        "OverflowError": _explain_overflow_error,
        "MemoryError": _explain_memory_error,
        "UnicodeDecodeError": _explain_unicode_decode_error,
        "UnicodeEncodeError": _explain_unicode_encode_error,
        "AssertionError": _explain_assertion_error,
        "NotImplementedError": _explain_not_implemented_error,
        "KeyboardInterrupt": _explain_keyboard_interrupt,
        "TimeoutError": _explain_timeout_error,
        "ConnectionError": _explain_connection_error,
    }
    
    handler = handlers.get(exc_name, _explain_generic_error)
    return handler(exc_type, exc_value, error_message)


def _format_message(title: str, explanation: str, suggestions: list[str]) -> str:
    """
    Format a friendly error message with consistent styling.
    
    Args:
        title: A short title for the error.
        explanation: A plain-English explanation of what went wrong.
        suggestions: A list of suggestions for how to fix the error.
    
    Returns:
        A formatted string with the error explanation.
    """
    use_colors = _use_colors()
    c = _Colors
    
    # Helper to apply color if TTY
    def colorize(text: str, color: str) -> str:
        return f"{color}{text}{c.RESET}" if use_colors else text
    
    separator = colorize("=" * 70, c.CYAN)
    header = colorize("🔍 FRIENDLY ERROR EXPLANATION", c.BOLD + c.CYAN)
    title_text = colorize(f"📛 {title}", c.BOLD + c.RED)
    what_happened = colorize("💡 What happened:", c.BOLD + c.YELLOW)
    how_to_fix = colorize("🔧 How to fix it:", c.BOLD + c.GREEN)
    
    lines = [
        "",
        separator,
        header,
        separator,
        "",
        title_text,
        "",
        what_happened,
        f"   {explanation}",
        "",
        how_to_fix,
    ]
    
    for i, suggestion in enumerate(suggestions, 1):
        lines.append(f"   {i}. {suggestion}")
    
    lines.extend(["", separator, ""])
    
    return "\n".join(lines)


# =============================================================================
# Exception-specific handlers
# =============================================================================

def _explain_type_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle TypeError exceptions."""
    
    # NoneType is not subscriptable
    if "NoneType" in error_message and "subscriptable" in error_message:
        return _format_message(
            "TypeError: Trying to index None",
            "You tried to use square brackets [] on a variable that is None. "
            "This usually happens when a function returned None instead of a list/dict, "
            "or when a variable wasn't properly initialized.",
            [
                "Check if your variable is None before accessing it: `if my_var is not None:`",
                "Make sure the function you called actually returns something.",
                "Print the variable before this line to see what it contains.",
                "Look for functions that might return None on failure (like .get(), .find(), etc.)."
            ]
        )
    
    # NoneType is not callable
    if "NoneType" in error_message and "callable" in error_message:
        return _format_message(
            "TypeError: Trying to call None as a function",
            "You tried to call None as if it were a function by adding parentheses (). "
            "This often happens when you accidentally overwrite a function with None, "
            "or when a method/attribute lookup returns None.",
            [
                "Check if you accidentally assigned None to a variable that should be a function.",
                "Verify that the method or function you're calling exists.",
                "Make sure you didn't overwrite a built-in function name.",
                "If using a callback, ensure it's properly assigned before calling."
            ]
        )
    
    # Not callable (general)
    if "not callable" in error_message:
        match = re.search(r"'(\w+)'.*not callable", error_message)
        type_name = match.group(1) if match else "object"
        return _format_message(
            f"TypeError: '{type_name}' is not callable",
            f"You tried to call a {type_name} as if it were a function by adding parentheses (). "
            f"A {type_name} cannot be called like a function.",
            [
                "Check if you accidentally used parentheses () instead of square brackets [].",
                f"Verify that the variable is actually a function, not a {type_name}.",
                "If you meant to access an item, use square brackets: `my_list[0]`",
                "Make sure you didn't overwrite a function with another type."
            ]
        )
    
    # Unsupported operand types
    if "unsupported operand type" in error_message:
        match = re.search(r"unsupported operand type\(s\) for (.+): '(\w+)' and '(\w+)'", error_message)
        if match:
            operator, type1, type2 = match.groups()
            return _format_message(
                f"TypeError: Can't use '{operator}' with {type1} and {type2}",
                f"You tried to use the '{operator}' operator with incompatible types. "
                f"Python doesn't know how to {operator} a {type1} and a {type2} together.",
                [
                    f"Convert both values to the same type before using '{operator}'.",
                    f"If working with strings and numbers, use str() or int()/float().",
                    "Check if any variable is None or an unexpected type.",
                    "Print both values to verify their types: `print(type(var1), type(var2))`"
                ]
            )
    
    # Can only concatenate
    if "can only concatenate" in error_message:
        match = re.search(r"can only concatenate (\w+).*to (\w+)", error_message)
        if match:
            type1, type2 = match.groups()
            return _format_message(
                f"TypeError: Can't concatenate {type1} to {type2}",
                f"You tried to combine (concatenate) a {type1} with a {type2} using +. "
                "Python requires both values to be the same type for concatenation.",
                [
                    "Convert both values to the same type (usually str).",
                    "Use f-strings for combining strings and other types: `f'Value: {number}'`",
                    "Use str() to convert numbers: `'Count: ' + str(count)`",
                    "For lists, make sure both sides are lists before using +."
                ]
            )
    
    # Missing positional argument
    if "missing" in error_message and "required positional argument" in error_message:
        match = re.search(r"missing (\d+) required positional argument", error_message)
        count = match.group(1) if match else "some"
        return _format_message(
            "TypeError: Missing required argument(s)",
            f"You called a function but didn't provide {count} required argument(s). "
            "The function expects more parameters than you passed.",
            [
                "Check the function definition to see what arguments it needs.",
                "Make sure you're passing all required arguments in the right order.",
                "Use keyword arguments for clarity: `func(name='value')`",
                "Check if you need to pass 'self' or if the function is a method."
            ]
        )
    
    # Too many positional arguments
    if "takes" in error_message and "positional argument" in error_message and "given" in error_message:
        return _format_message(
            "TypeError: Too many arguments",
            "You called a function with more arguments than it accepts. "
            "Check the function signature to see how many parameters it takes.",
            [
                "Remove the extra arguments from the function call.",
                "Check if you're calling the right function.",
                "Verify the function signature - maybe it was recently changed.",
                "If passing a list, you might need to unpack it with *args."
            ]
        )
    
    # Generic TypeError
    return _format_message(
        "TypeError: Type mismatch",
        f"A type error occurred: {error_message}. "
        "This means you're trying to do something with a value that doesn't support that operation.",
        [
            "Check the types of all variables involved using type().",
            "Make sure you're using the right data type for the operation.",
            "Look for None values that might be unexpected.",
            "Verify function return types match what you expect."
        ]
    )


def _explain_index_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle IndexError exceptions."""
    
    if "list index out of range" in error_message:
        return _format_message(
            "IndexError: List index out of range",
            "You tried to access an item at an index that doesn't exist in the list. "
            "Remember: Python lists are 0-indexed, so a list with 5 items has indices 0-4.",
            [
                "Check the length of your list: `len(my_list)`",
                "Make sure your index is less than the list length.",
                "Use `my_list[-1]` to safely get the last item.",
                "Check if the list is empty before accessing items.",
                "Consider using `.get()` method if working with lists that might be short."
            ]
        )
    
    if "tuple index out of range" in error_message:
        return _format_message(
            "IndexError: Tuple index out of range",
            "You tried to access an item at an index that doesn't exist in the tuple. "
            "Tuples work like lists - they're 0-indexed and have a fixed length.",
            [
                "Check the length of your tuple: `len(my_tuple)`",
                "Make sure your index is within the valid range.",
                "Use `my_tuple[-1]` to get the last item.",
                "Verify the tuple has the expected number of elements."
            ]
        )
    
    if "string index out of range" in error_message:
        return _format_message(
            "IndexError: String index out of range",
            "You tried to access a character at an index that doesn't exist in the string. "
            "This often happens when iterating beyond the string length or when the string is empty.",
            [
                "Check the length of your string: `len(my_string)`",
                "Make sure the string isn't empty before accessing characters.",
                "Use `my_string[-1]` to safely get the last character.",
                "Verify your loop bounds when iterating over string indices."
            ]
        )
    
    return _format_message(
        "IndexError: Index out of range",
        f"You tried to access an item at an index that doesn't exist: {error_message}. "
        "The sequence (list, tuple, or string) doesn't have that many items.",
        [
            "Check the length of your sequence using len().",
            "Remember that indices start at 0, not 1.",
            "Use negative indices (-1, -2) to access items from the end.",
            "Always check if the sequence is empty before accessing items."
        ]
    )


def _explain_key_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle KeyError exceptions."""
    
    # Extract the key that caused the error
    key_repr = error_message if error_message else "unknown"
    
    return _format_message(
        f"KeyError: Key {key_repr} not found",
        f"You tried to access a dictionary key that doesn't exist. "
        f"The key {key_repr} is not present in the dictionary.",
        [
            "Use `.get(key, default)` to provide a default value: `my_dict.get('key', 'default')`",
            "Check if the key exists first: `if 'key' in my_dict:`",
            "Print all available keys: `print(my_dict.keys())`",
            "Check for typos in the key name.",
            "Use `.setdefault(key, value)` if you want to add the key if missing."
        ]
    )


def _explain_value_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle ValueError exceptions."""
    
    # Invalid literal for int() with base 10
    if "invalid literal for int()" in error_message:
        match = re.search(r"invalid literal for int\(\) with base \d+: ['\"](.+)['\"]", error_message)
        bad_value = match.group(1) if match else "your value"
        return _format_message(
            "ValueError: Can't convert string to integer",
            f"You tried to convert '{bad_value}' to an integer, but it's not a valid number. "
            "The string must contain only digits (and optionally a leading minus sign).",
            [
                "Make sure the string contains only numbers: '123' not '123abc'",
                "Remove whitespace: `my_string.strip()` before converting.",
                "For decimal numbers, use float() instead of int().",
                "Check if the input is empty or contains unexpected characters.",
                "Use try/except to handle invalid input gracefully."
            ]
        )
    
    # could not convert string to float
    if "could not convert string to float" in error_message:
        return _format_message(
            "ValueError: Can't convert string to float",
            "You tried to convert a string to a floating-point number, but the string "
            "doesn't represent a valid number.",
            [
                "Check that the string contains a valid number format: '3.14' or '42'",
                "Remove any non-numeric characters (letters, symbols, etc.).",
                "Watch out for thousand separators: '1,000' won't convert directly.",
                "Strip whitespace from the string: `my_string.strip()`",
                "Handle the error gracefully with try/except."
            ]
        )
    
    # too many values to unpack
    if "too many values to unpack" in error_message:
        return _format_message(
            "ValueError: Too many values to unpack",
            "You're trying to unpack a sequence into fewer variables than the sequence contains. "
            "For example: `a, b = [1, 2, 3]` fails because there are 3 values but only 2 variables.",
            [
                "Make sure the number of variables matches the number of values.",
                "Use *rest to capture extra values: `a, *rest = [1, 2, 3]`",
                "Check the length of your sequence before unpacking.",
                "Consider using indexing instead: `a, b = my_list[0], my_list[1]`"
            ]
        )
    
    # not enough values to unpack
    if "not enough values to unpack" in error_message:
        return _format_message(
            "ValueError: Not enough values to unpack",
            "You're trying to unpack a sequence into more variables than the sequence contains. "
            "For example: `a, b, c = [1, 2]` fails because there are only 2 values but 3 variables.",
            [
                "Make sure the number of variables matches the number of values.",
                "Check if your sequence might be empty or shorter than expected.",
                "Use len() to verify the sequence length before unpacking.",
                "Consider using indexing with bounds checking instead."
            ]
        )
    
    # is not in list
    if "is not in list" in error_message:
        return _format_message(
            "ValueError: Item not in list",
            "You tried to find or remove an item that doesn't exist in the list. "
            "This happens with methods like .remove() or .index().",
            [
                "Check if the item exists first: `if item in my_list:`",
                "Use try/except to handle the case when item is missing.",
                "For finding items, consider using `in` operator or .count() method.",
                "Make sure you're comparing the right type (e.g., '1' is not the same as 1)."
            ]
        )
    
    return _format_message(
        "ValueError: Invalid value",
        f"A value error occurred: {error_message}. "
        "This means a function received an argument of the right type but an inappropriate value.",
        [
            "Check the documentation for what values are accepted.",
            "Validate input before passing it to functions.",
            "Use try/except to handle invalid values gracefully.",
            "Print the value to see what's actually being passed."
        ]
    )


def _explain_attribute_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle AttributeError exceptions."""
    
    # Extract type and attribute from error message
    match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error_message)
    if match:
        obj_type, attr_name = match.groups()
        return _format_message(
            f"AttributeError: '{obj_type}' has no attribute '{attr_name}'",
            f"You tried to access an attribute or method called '{attr_name}' on a {obj_type} object, "
            f"but {obj_type} doesn't have that attribute.",
            [
                f"Check if '{attr_name}' is spelled correctly.",
                f"Verify that the object is the type you expect (use `type(obj)`).",
                f"Look up the available methods for {obj_type}: `dir(obj)`",
                "If the object might be None, check for that first.",
                "Make sure you're not confusing a method with a property (parentheses vs no parentheses)."
            ]
        )
    
    # NoneType specific
    if "'NoneType' object has no attribute" in error_message:
        attr_match = re.search(r"no attribute '(\w+)'", error_message)
        attr = attr_match.group(1) if attr_match else "method/attribute"
        return _format_message(
            f"AttributeError: None has no attribute '{attr}'",
            f"You tried to access '{attr}' on None. This usually means a variable you "
            "expected to have a value is actually None.",
            [
                "Check if a function call returned None unexpectedly.",
                "Add a None check: `if my_var is not None:`",
                "Look for functions that return None on failure.",
                "Print the variable before this line to see its value."
            ]
        )
    
    return _format_message(
        "AttributeError: Attribute not found",
        f"An attribute error occurred: {error_message}. "
        "You tried to access an attribute or method that doesn't exist on the object.",
        [
            "Check the spelling of the attribute name.",
            "Verify the object type with type() or isinstance().",
            "Use dir(obj) to see available attributes.",
            "Make sure the object isn't None."
        ]
    )


def _explain_import_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle ImportError exceptions."""
    
    # Cannot import name
    if "cannot import name" in error_message:
        match = re.search(r"cannot import name '(\w+)'", error_message)
        name = match.group(1) if match else "the item"
        return _format_message(
            f"ImportError: Cannot import '{name}'",
            f"Python found the module but couldn't import '{name}' from it. "
            "This could be a typo, or the item doesn't exist in that module.",
            [
                f"Check if '{name}' is spelled correctly.",
                "Verify the item exists in the module you're importing from.",
                "Check for circular imports (module A imports B, B imports A).",
                "The item might have been renamed or removed in a newer version.",
                "Try importing the whole module: `import module_name`"
            ]
        )
    
    return _format_message(
        "ImportError: Failed to import",
        f"An import error occurred: {error_message}. "
        "Python could not import something from a module.",
        [
            "Check if the module is installed: `pip install module_name`",
            "Verify the import statement syntax.",
            "Look for circular import issues.",
            "Make sure you're using the right Python environment."
        ]
    )


def _explain_module_not_found_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle ModuleNotFoundError exceptions."""
    
    match = re.search(r"No module named '([^']+)'", error_message)
    module_name = match.group(1) if match else "the module"
    
    return _format_message(
        f"ModuleNotFoundError: No module named '{module_name}'",
        f"Python cannot find a module called '{module_name}'. "
        "This usually means the package isn't installed or there's a typo.",
        [
            f"Install the package: `pip install {module_name.split('.')[0]}`",
            "Check if you're in the right virtual environment.",
            f"Verify the spelling of '{module_name}'.",
            "Make sure your Python path includes the module location.",
            "For local modules, check that __init__.py exists in the package folder."
        ]
    )


def _explain_zero_division_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle ZeroDivisionError exceptions."""
    
    if "integer division or modulo" in error_message:
        return _format_message(
            "ZeroDivisionError: Division by zero (integer)",
            "You tried to divide an integer by zero or use the modulo operator with zero. "
            "This is mathematically undefined.",
            [
                "Check if the divisor could ever be zero and handle that case.",
                "Use a conditional: `result = a // b if b != 0 else 0`",
                "Validate input before performing division.",
                "Think about what the result should be when dividing by zero."
            ]
        )
    
    return _format_message(
        "ZeroDivisionError: Division by zero",
        "You tried to divide a number by zero, which is mathematically undefined. "
        "No number times zero can give you the original number back.",
        [
            "Check if the divisor is zero before dividing.",
            "Use a conditional: `result = a / b if b != 0 else 0`",
            "Look for where the divisor value comes from - it might be unexpectedly zero.",
            "Consider using try/except to handle this edge case."
        ]
    )


def _explain_file_not_found_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle FileNotFoundError exceptions."""
    
    # Try to extract filename
    filename = getattr(exc_value, 'filename', None) or "the file"
    
    return _format_message(
        f"FileNotFoundError: Cannot find '{filename}'",
        f"Python tried to open a file at '{filename}' but it doesn't exist. "
        "This could be a wrong path, missing file, or permission issue.",
        [
            "Check if the file path is correct and the file exists.",
            "Use absolute paths to avoid confusion: `os.path.abspath(path)`",
            "Check your current working directory: `os.getcwd()`",
            "On Windows, use raw strings for paths: `r'C:\\folder\\file.txt'`",
            "For creating new files, use mode 'w' to create if not exists.",
            "Use `os.path.exists(path)` to check if file exists first."
        ]
    )


def _explain_name_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle NameError exceptions."""
    
    match = re.search(r"name '(\w+)' is not defined", error_message)
    name = match.group(1) if match else "the variable"
    
    return _format_message(
        f"NameError: '{name}' is not defined",
        f"You tried to use a variable called '{name}' that doesn't exist yet. "
        "Python doesn't know what this name refers to.",
        [
            f"Check if '{name}' is spelled correctly (Python is case-sensitive).",
            f"Make sure '{name}' is defined before this line of code.",
            "If it's a function/class, check if you imported it.",
            "Look for scope issues - variables inside functions aren't global.",
            "If using global variables in a function, declare them with 'global'."
        ]
    )


def _explain_syntax_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle SyntaxError exceptions."""
    
    return _format_message(
        "SyntaxError: Invalid Python syntax",
        f"There's a syntax error in your code: {error_message}. "
        "Python couldn't understand the code because it doesn't follow Python's grammar rules.",
        [
            "Check for missing colons after if/for/while/def/class statements.",
            "Look for unmatched parentheses, brackets, or quotes.",
            "Make sure you're not using reserved words as variable names.",
            "Check indentation - Python is sensitive to spaces/tabs.",
            "Look at the line BEFORE the error - the problem might be there."
        ]
    )


def _explain_recursion_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle RecursionError exceptions."""
    
    return _format_message(
        "RecursionError: Maximum recursion depth exceeded",
        "Your code called itself too many times without stopping. "
        "This usually means infinite recursion - a function that never reaches its base case.",
        [
            "Check that your recursive function has a proper base case.",
            "Make sure the recursive call moves toward the base case.",
            "Print the input at each call to see if it's progressing.",
            "Consider converting to an iterative approach with loops.",
            "If you need deep recursion, use `sys.setrecursionlimit()` (carefully!)."
        ]
    )


def _explain_permission_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle PermissionError exceptions."""
    
    filename = getattr(exc_value, 'filename', None) or "the file"
    
    return _format_message(
        f"PermissionError: Access denied to '{filename}'",
        "You don't have permission to access this file or directory. "
        "This could be a system-protected location or a file owned by another user.",
        [
            "Check if the file is open in another program.",
            "Try running your script with administrator/sudo privileges.",
            "Verify you have read/write permissions for this location.",
            "On Windows, check if the file is marked as read-only.",
            "Try a different directory that you definitely have access to."
        ]
    )


def _explain_stop_iteration(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle StopIteration exceptions."""
    
    return _format_message(
        "StopIteration: Iterator exhausted",
        "You tried to get the next item from an iterator that has no more items. "
        "This often happens when using next() manually without checking if items remain.",
        [
            "Use a for loop instead of calling next() manually.",
            "Provide a default: `next(iterator, None)`",
            "Convert to a list first: `list(iterator)`",
            "Check if the iterator is empty before getting items.",
            "Remember: once exhausted, most iterators can't be reused."
        ]
    )


def _explain_overflow_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle OverflowError exceptions."""
    
    return _format_message(
        "OverflowError: Number too large",
        "The result of a calculation is too large to represent. "
        "This usually happens with floating-point operations or certain math functions.",
        [
            "Use smaller numbers or scale your calculations.",
            "Consider using the `decimal` module for precise calculations.",
            "For very large integers, Python handles them natively.",
            "Check for exponential growth in your calculations.",
            "Use logarithms for very large number operations."
        ]
    )


def _explain_memory_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle MemoryError exceptions."""
    
    return _format_message(
        "MemoryError: System ran out of memory",
        "Your program tried to use more memory than available. "
        "This usually means you're creating very large data structures.",
        [
            "Process data in smaller chunks instead of loading everything at once.",
            "Use generators instead of lists: `(x for x in range(1000000))`",
            "Delete large objects when done: `del large_list`",
            "Consider using memory-efficient data types (numpy arrays, etc.).",
            "Check for memory leaks - are you accumulating data in loops?"
        ]
    )


def _explain_unicode_decode_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle UnicodeDecodeError exceptions."""
    
    return _format_message(
        "UnicodeDecodeError: Can't decode bytes",
        "Python couldn't convert the bytes to text using the specified encoding. "
        "The file or data might be in a different encoding than expected.",
        [
            "Try a different encoding: `open(file, encoding='latin-1')`",
            "Use charset detection: `chardet` library can guess the encoding.",
            "For reading binary files, use mode 'rb' instead of 'r'.",
            "Use `errors='ignore'` or `errors='replace'` to skip bad characters.",
            "Common encodings to try: 'utf-8', 'latin-1', 'cp1252', 'ascii'."
        ]
    )


def _explain_unicode_encode_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle UnicodeEncodeError exceptions."""
    
    return _format_message(
        "UnicodeEncodeError: Can't encode characters",
        "Python couldn't convert some text to bytes using the specified encoding. "
        "Some characters in your text can't be represented in the target encoding.",
        [
            "Use UTF-8 encoding which supports all characters: `encoding='utf-8'`",
            "Use `errors='ignore'` to skip unencodeable characters.",
            "Use `errors='replace'` to replace with '?' placeholders.",
            "Check if your output destination supports Unicode.",
            "For console output on Windows, set console to UTF-8 mode."
        ]
    )


def _explain_assertion_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle AssertionError exceptions."""
    
    return _format_message(
        "AssertionError: Assertion failed",
        f"An assert statement failed: {error_message or 'No message provided'}. "
        "This means a condition you expected to be True was actually False.",
        [
            "Check the values being compared in the assert statement.",
            "Print the variables before the assert to see their actual values.",
            "Consider whether the assertion condition is correct.",
            "For tests, check if your expected values match what the code produces.",
            "Remove or fix the assert if it's no longer valid."
        ]
    )


def _explain_not_implemented_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle NotImplementedError exceptions."""
    
    return _format_message(
        "NotImplementedError: Feature not implemented",
        "You called a method or function that hasn't been implemented yet. "
        "This is often used as a placeholder in abstract base classes or during development.",
        [
            "Implement the method in a subclass if using abstract classes.",
            "Check if there's an alternative method you should be using.",
            "If this is your code, implement the missing functionality.",
            "Check the documentation to see if this feature is planned.",
            "Consider if you're using the right class or library version."
        ]
    )


def _explain_keyboard_interrupt(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle KeyboardInterrupt exceptions."""
    
    return _format_message(
        "KeyboardInterrupt: Program interrupted",
        "The program was interrupted by the user (usually by pressing Ctrl+C). "
        "This is normal when you want to stop a long-running program.",
        [
            "This is typically intentional - your program was stopped on purpose.",
            "To handle interrupts gracefully, use try/except KeyboardInterrupt.",
            "Consider saving progress before allowing interruption.",
            "For servers/daemons, implement proper shutdown handlers.",
            "Use signal handlers for more control over program termination."
        ]
    )


def _explain_timeout_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle TimeoutError exceptions."""
    
    return _format_message(
        "TimeoutError: Operation timed out",
        "An operation took too long to complete and was aborted. "
        "This usually happens with network requests, file operations, or synchronization.",
        [
            "Check your network connection if this involves remote resources.",
            "Increase the timeout value if the operation legitimately needs more time.",
            "Verify the remote server/service is responsive.",
            "Consider using async/await for non-blocking operations.",
            "Implement retry logic with exponential backoff."
        ]
    )


def _explain_connection_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle ConnectionError exceptions."""
    
    return _format_message(
        "ConnectionError: Connection failed",
        f"A connection could not be established: {error_message}. "
        "This usually happens when trying to connect to a remote server or database.",
        [
            "Check your internet connection.",
            "Verify the server address and port are correct.",
            "Ensure the remote service is running and accessible.",
            "Check if a firewall is blocking the connection.",
            "Implement retry logic to handle temporary network issues."
        ]
    )


def _explain_generic_error(exc_type: Type[BaseException], exc_value: BaseException, error_message: str) -> str:
    """Handle any exception type not specifically covered."""
    
    exc_name = exc_type.__name__
    
    return _format_message(
        f"{exc_name}: An error occurred",
        f"An error of type '{exc_name}' occurred: {error_message}. "
        "This is not a commonly handled exception type, but here are some general tips.",
        [
            "Read the error message carefully - it usually tells you what's wrong.",
            "Check Python documentation for this specific exception type.",
            "Search online for the exact error message.",
            "Print variable values before this line to debug.",
            "Use a debugger or add try/except blocks to isolate the issue."
        ]
    )


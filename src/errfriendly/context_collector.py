"""
context_collector.py - Context collection engine for AI-powered error analysis.

This module captures comprehensive error context including traceback frames,
variable states, code snippets, and project structure for AI analysis.
"""

import sys
import os
import re
import linecache
import traceback as tb_module
from typing import Type, Optional, List, Dict, Any, Tuple
from pathlib import Path

from .models import ErrorContext, FrameInfo, Config

# Patterns for detecting sensitive data
SENSITIVE_PATTERNS = [
    re.compile(r'(password|passwd|pwd|secret|token|api_key|apikey|auth)', re.I),
    re.compile(r'(access_token|refresh_token|bearer)', re.I),
    re.compile(r'(private_key|secret_key|encryption_key)', re.I),
]

# Common anti-patterns that lead to errors
ANTI_PATTERNS = {
    'NoneType': [
        "Accessing attributes/methods on None - check function return values",
        "Missing null checks before operations",
    ],
    'subscript': [
        "Using [] on None instead of a list/dict",
        "Function might return None on failure",
    ],
    'not callable': [
        "Variable shadowing a function name",
        "Missing parentheses in previous assignment",
    ],
    'concatenate': [
        "Mixing str and non-str types in operations",
        "Missing str() conversion",
    ],
    'index out of range': [
        "Off-by-one error in loop bounds",
        "Empty list/sequence not handled",
    ],
    'key': [
        "Using dict[key] instead of dict.get(key)",
        "Key not initialized before access",
    ],
    'division by zero': [
        "Missing zero-check before division",
        "Variable unexpectedly becomes zero",
    ],
    'attribute': [
        "Typo in attribute name",
        "Object is None or wrong type",
    ],
}


class ContextCollector:
    """Collects comprehensive error context for AI analysis.
    
    This class extracts all relevant information from an exception
    to provide rich context for AI-powered explanations.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the context collector.
        
        Args:
            config: Configuration options. Uses defaults if not provided.
        """
        self.config = config or Config()
    
    def collect(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback
    ) -> ErrorContext:
        """Collect full error context from an exception.
        
        Args:
            exc_type: The exception class.
            exc_value: The exception instance.
            exc_traceback: The traceback object.
            
        Returns:
            ErrorContext with all collected information.
        """
        frames = self._extract_frames(exc_traceback)
        code_snippet = self._get_code_snippet(exc_traceback)
        local_vars = self._get_local_variables(exc_traceback)
        imports = self._extract_imports(exc_traceback)
        project_files = self._get_project_structure()
        patterns = self._detect_patterns(exc_type, exc_value)
        git_changes = self._get_recent_changes() if self.config.collect_git_changes else None
        
        return ErrorContext(
            exception_type=exc_type.__name__,
            error_message=str(exc_value),
            full_traceback=frames,
            code_snippet=code_snippet,
            local_variables=local_vars,
            import_statements=imports,
            project_structure=project_files,
            recent_changes=git_changes,
            detected_patterns=patterns,
            python_version=sys.version.split()[0],
        )
    
    def _extract_frames(self, tb) -> List[FrameInfo]:
        """Extract frame information from traceback.
        
        Args:
            tb: Traceback object.
            
        Returns:
            List of FrameInfo objects for each frame.
        """
        frames = []
        current = tb
        
        while current is not None:
            frame = current.tb_frame
            lineno = current.tb_lineno
            filename = frame.f_code.co_filename
            function = frame.f_code.co_name
            
            # Get code context (lines around the error)
            code_context = self._get_lines_around(filename, lineno, context=3)
            
            # Get local variables (sanitized)
            local_vars = self._sanitize_variables(frame.f_locals)
            
            frames.append(FrameInfo(
                filename=self._sanitize_path(filename),
                lineno=lineno,
                function=function,
                code_context=code_context,
                local_variables=local_vars,
            ))
            
            current = current.tb_next
        
        return frames
    
    def _get_code_snippet(self, tb) -> str:
        """Get code around the error line.
        
        Args:
            tb: Traceback object.
            
        Returns:
            String containing lines around the error.
        """
        if tb is None:
            return ""
        
        # Get the innermost frame
        while tb.tb_next is not None:
            tb = tb.tb_next
        
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        lineno = tb.tb_lineno
        
        lines = self._get_lines_around(
            filename, 
            lineno, 
            context=self.config.max_context_lines // 2
        )
        
        # Add line numbers and highlight error line
        result = []
        start_line = max(1, lineno - self.config.max_context_lines // 2)
        for i, line in enumerate(lines):
            current_lineno = start_line + i
            marker = ">>>" if current_lineno == lineno else "   "
            result.append(f"{marker} {current_lineno:4d} | {line}")
        
        return "\n".join(result)
    
    def _get_lines_around(
        self, 
        filename: str, 
        lineno: int, 
        context: int = 5
    ) -> List[str]:
        """Get lines around a specific line number.
        
        Args:
            filename: Path to the source file.
            lineno: Target line number.
            context: Number of lines before/after.
            
        Returns:
            List of source code lines.
        """
        lines = []
        start = max(1, lineno - context)
        end = lineno + context + 1
        
        for i in range(start, end):
            line = linecache.getline(filename, i)
            if line:
                lines.append(line.rstrip())
            else:
                break
        
        return lines
    
    def _get_local_variables(self, tb) -> Dict[str, Any]:
        """Safely extract local variable values from the error frame.
        
        Args:
            tb: Traceback object.
            
        Returns:
            Dictionary of variable names to their sanitized string representations.
        """
        if tb is None:
            return {}
        
        # Get the innermost frame
        while tb.tb_next is not None:
            tb = tb.tb_next
        
        frame = tb.tb_frame
        return self._sanitize_variables(frame.f_locals)
    
    def _sanitize_variables(self, variables: Dict[str, Any]) -> Dict[str, str]:
        """Sanitize variable values for safe display.
        
        Removes sensitive data and limits representation length.
        
        Args:
            variables: Dictionary of variable names to values.
            
        Returns:
            Dictionary with sanitized string representations.
        """
        if not self.config.include_variable_values:
            return {k: f"<{type(v).__name__}>" for k, v in variables.items()}
        
        result = {}
        max_len = self.config.max_variable_repr_length
        
        for name, value in variables.items():
            # Skip private/dunder variables
            if name.startswith('__') and name.endswith('__'):
                continue
            
            # Skip modules and functions
            if hasattr(value, '__module__') and hasattr(value, '__call__'):
                result[name] = f"<function {name}>"
                continue
            
            # Check for sensitive variable names
            if self.config.sanitize_secrets and self._is_sensitive(name):
                result[name] = "<REDACTED>"
                continue
            
            # Get string representation
            try:
                repr_value = repr(value)
                if len(repr_value) > max_len:
                    repr_value = repr_value[:max_len] + "..."
                result[name] = repr_value
            except Exception:
                result[name] = f"<{type(value).__name__}>"
        
        return result
    
    def _is_sensitive(self, name: str) -> bool:
        """Check if a variable name suggests sensitive data.
        
        Args:
            name: Variable name to check.
            
        Returns:
            True if the name matches sensitive patterns.
        """
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(name):
                return True
        return False
    
    def _sanitize_path(self, path: str) -> str:
        """Sanitize file paths if configured.
        
        Args:
            path: Absolute file path.
            
        Returns:
            Sanitized or relative path.
        """
        if not self.config.sanitize_paths:
            return path
        
        try:
            # Try to make it relative to current directory
            cwd = os.getcwd()
            if path.startswith(cwd):
                return os.path.relpath(path, cwd)
        except Exception:
            pass
        
        return path
    
    def _extract_imports(self, tb) -> List[str]:
        """Extract import statements from the error file.
        
        Args:
            tb: Traceback object.
            
        Returns:
            List of import statement strings.
        """
        if tb is None:
            return []
        
        # Get the first (outermost) frame's file
        filename = tb.tb_frame.f_code.co_filename
        
        imports = []
        try:
            # Clear the cache to ensure fresh read
            linecache.checkcache(filename)
            
            line_num = 1
            while True:
                line = linecache.getline(filename, line_num)
                if not line:
                    break
                
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    imports.append(stripped)
                
                line_num += 1
                
                # Stop after reasonable number of lines
                if line_num > 100:
                    break
                
        except Exception:
            pass
        
        return imports
    
    def _get_project_structure(self) -> List[str]:
        """Get key project files.
        
        Returns:
            List of important project file paths.
        """
        key_files = [
            'pyproject.toml',
            'setup.py',
            'setup.cfg',
            'requirements.txt',
            'Pipfile',
            'poetry.lock',
            'tox.ini',
            '.python-version',
        ]
        
        found = []
        try:
            cwd = Path.cwd()
            for filename in key_files:
                if (cwd / filename).exists():
                    found.append(filename)
        except Exception:
            pass
        
        return found
    
    def _detect_patterns(
        self, 
        exc_type: Type[BaseException], 
        exc_value: BaseException
    ) -> List[str]:
        """Detect common anti-patterns that might have caused this error.
        
        Args:
            exc_type: The exception class.
            exc_value: The exception instance.
            
        Returns:
            List of detected anti-pattern descriptions.
        """
        patterns = []
        error_msg = str(exc_value).lower()
        exc_name = exc_type.__name__
        
        for keyword, descriptions in ANTI_PATTERNS.items():
            if keyword.lower() in error_msg or keyword.lower() in exc_name.lower():
                patterns.extend(descriptions)
        
        return list(set(patterns))  # Remove duplicates
    
    def _get_recent_changes(self) -> Optional[str]:
        """Get recent git changes if available.
        
        Returns:
            String with recent git diff, or None if not available.
        """
        try:
            import subprocess
            
            # Check if we're in a git repo
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True,
                text=True,
                timeout=2,
            )
            
            if result.returncode != 0:
                return None
            
            # Get recent changes (staged + unstaged)
            result = subprocess.run(
                ['git', 'diff', 'HEAD', '--stat', '--no-color'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()[:500]  # Limit size
                
        except Exception:
            pass
        
        return None

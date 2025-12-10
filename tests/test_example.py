"""
Test suite for errfriendly package.

These tests verify that the friendly error messages are displayed correctly
when exceptions occur in scripts using errfriendly.
"""

import subprocess
import sys
import tempfile
import os
import textwrap

import pytest


class TestErrorMessages:
    """Test that friendly error messages are displayed for various exception types."""
    
    def run_script(self, script_content: str) -> tuple[str, str, int]:
        """
        Run a Python script and capture its output.
        
        Args:
            script_content: The Python code to execute.
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            f.flush()
            temp_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout, result.stderr, result.returncode
        finally:
            os.unlink(temp_path)
    
    def test_type_error_none_subscript(self):
        """Test that TypeError for NoneType subscript shows friendly message."""
        script = textwrap.dedent("""
            import errfriendly
            errfriendly.install()
            
            x = None
            print(x[0])
        """)
        
        stdout, stderr, code = self.run_script(script)
        
        assert code != 0
        assert "FRIENDLY ERROR EXPLANATION" in stderr
        assert "NoneType" in stderr or "None" in stderr
        assert "How to fix it" in stderr
    
    def test_type_error_not_callable(self):
        """Test that TypeError for not callable shows friendly message."""
        script = textwrap.dedent("""
            import errfriendly
            errfriendly.install()
            
            x = 42
            x()
        """)
        
        stdout, stderr, code = self.run_script(script)
        
        assert code != 0
        assert "FRIENDLY ERROR EXPLANATION" in stderr
        assert "callable" in stderr.lower()
        assert "How to fix it" in stderr
    
    def test_index_error(self):
        """Test that IndexError shows friendly message."""
        script = textwrap.dedent("""
            import errfriendly
            errfriendly.install()
            
            my_list = [1, 2, 3]
            print(my_list[10])
        """)
        
        stdout, stderr, code = self.run_script(script)
        
        assert code != 0
        assert "FRIENDLY ERROR EXPLANATION" in stderr
        assert "index" in stderr.lower() or "Index" in stderr
        assert "How to fix it" in stderr
    
    def test_key_error(self):
        """Test that KeyError shows friendly message."""
        script = textwrap.dedent("""
            import errfriendly
            errfriendly.install()
            
            my_dict = {'a': 1}
            print(my_dict['nonexistent'])
        """)
        
        stdout, stderr, code = self.run_script(script)
        
        assert code != 0
        assert "FRIENDLY ERROR EXPLANATION" in stderr
        assert "Key" in stderr or "key" in stderr
        assert "How to fix it" in stderr
    
    def test_value_error_int_conversion(self):
        """Test that ValueError for invalid int conversion shows friendly message."""
        script = textwrap.dedent("""
            import errfriendly
            errfriendly.install()
            
            x = int("not_a_number")
        """)
        
        stdout, stderr, code = self.run_script(script)
        
        assert code != 0
        assert "FRIENDLY ERROR EXPLANATION" in stderr
        assert "How to fix it" in stderr
    
    def test_attribute_error(self):
        """Test that AttributeError shows friendly message."""
        script = textwrap.dedent("""
            import errfriendly
            errfriendly.install()
            
            x = "hello"
            x.nonexistent_method()
        """)
        
        stdout, stderr, code = self.run_script(script)
        
        assert code != 0
        assert "FRIENDLY ERROR EXPLANATION" in stderr
        assert "attribute" in stderr.lower() or "Attribute" in stderr
        assert "How to fix it" in stderr
    
    def test_zero_division_error(self):
        """Test that ZeroDivisionError shows friendly message."""
        script = textwrap.dedent("""
            import errfriendly
            errfriendly.install()
            
            result = 10 / 0
        """)
        
        stdout, stderr, code = self.run_script(script)
        
        assert code != 0
        assert "FRIENDLY ERROR EXPLANATION" in stderr
        assert "zero" in stderr.lower() or "Zero" in stderr
        assert "How to fix it" in stderr
    
    def test_module_not_found_error(self):
        """Test that ModuleNotFoundError shows friendly message."""
        script = textwrap.dedent("""
            import errfriendly
            errfriendly.install()
            
            import this_module_definitely_does_not_exist_12345
        """)
        
        stdout, stderr, code = self.run_script(script)
        
        assert code != 0
        assert "FRIENDLY ERROR EXPLANATION" in stderr
        assert "module" in stderr.lower() or "Module" in stderr
        assert "How to fix it" in stderr
    
    def test_file_not_found_error(self):
        """Test that FileNotFoundError shows friendly message."""
        script = textwrap.dedent("""
            import errfriendly
            errfriendly.install()
            
            with open('/nonexistent/path/to/file.txt') as f:
                pass
        """)
        
        stdout, stderr, code = self.run_script(script)
        
        assert code != 0
        assert "FRIENDLY ERROR EXPLANATION" in stderr
        assert "How to fix it" in stderr
    
    def test_name_error(self):
        """Test that NameError shows friendly message."""
        script = textwrap.dedent("""
            import errfriendly
            errfriendly.install()
            
            print(undefined_variable)
        """)
        
        stdout, stderr, code = self.run_script(script)
        
        assert code != 0
        assert "FRIENDLY ERROR EXPLANATION" in stderr
        assert "How to fix it" in stderr


class TestInstallUninstall:
    """Test the install and uninstall functionality."""
    
    def test_install_and_uninstall(self):
        """Test that install and uninstall work correctly."""
        script = textwrap.dedent("""
            import sys
            import errfriendly
            
            # Store original hook
            original = sys.excepthook
            
            # Install errfriendly
            errfriendly.install()
            assert sys.excepthook is not original, "Hook should be changed after install"
            
            # Check is_installed
            from errfriendly.handler import is_installed
            assert is_installed(), "is_installed should return True"
            
            # Uninstall
            errfriendly.uninstall()
            
            # Check is_installed after uninstall
            assert not is_installed(), "is_installed should return False after uninstall"
            
            print("SUCCESS")
        """)
        
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "SUCCESS" in result.stdout
    
    def test_hide_original_traceback(self):
        """Test that show_original_traceback=False hides the traceback."""
        script = textwrap.dedent("""
            import errfriendly
            errfriendly.install(show_original_traceback=False)
            
            1 / 0
        """)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script)
            f.flush()
            temp_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Should NOT contain "Traceback" since we hid it
            assert "Traceback (most recent call last)" not in result.stderr
            # But SHOULD contain friendly message
            assert "FRIENDLY ERROR EXPLANATION" in result.stderr
        finally:
            os.unlink(temp_path)
    
    def test_show_original_traceback(self):
        """Test that show_original_traceback=True shows both traceback and friendly message."""
        script = textwrap.dedent("""
            import errfriendly
            errfriendly.install(show_original_traceback=True)
            
            1 / 0
        """)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script)
            f.flush()
            temp_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Should contain both
            assert "Traceback (most recent call last)" in result.stderr
            assert "FRIENDLY ERROR EXPLANATION" in result.stderr
        finally:
            os.unlink(temp_path)


class TestMessageModule:
    """Test the messages module directly."""
    
    def test_get_friendly_message_returns_string(self):
        """Test that get_friendly_message returns a non-empty string."""
        from errfriendly.messages import get_friendly_message
        
        # Test with various exception types
        exceptions = [
            (TypeError, TypeError("test")),
            (ValueError, ValueError("test")),
            (KeyError, KeyError("test")),
            (IndexError, IndexError("test")),
            (ZeroDivisionError, ZeroDivisionError("test")),
        ]
        
        for exc_type, exc_value in exceptions:
            message = get_friendly_message(exc_type, exc_value)
            assert isinstance(message, str)
            assert len(message) > 0
            assert "FRIENDLY ERROR EXPLANATION" in message
    
    def test_messages_contain_fix_suggestions(self):
        """Test that all messages contain fix suggestions."""
        from errfriendly.messages import get_friendly_message
        
        exceptions = [
            (TypeError, TypeError("'NoneType' object is not subscriptable")),
            (ValueError, ValueError("invalid literal for int() with base 10: 'abc'")),
            (KeyError, KeyError("missing_key")),
            (IndexError, IndexError("list index out of range")),
            (AttributeError, AttributeError("'str' object has no attribute 'foo'")),
        ]
        
        for exc_type, exc_value in exceptions:
            message = get_friendly_message(exc_type, exc_value)
            assert "How to fix it" in message
    
    def test_new_exception_handlers(self):
        """Test the new exception handlers added in v0.2.0."""
        from errfriendly.messages import get_friendly_message
        
        exceptions = [
            (AssertionError, AssertionError("expected 1 but got 2")),
            (NotImplementedError, NotImplementedError("this feature is not available")),
            (TimeoutError, TimeoutError("connection timed out")),
            (ConnectionError, ConnectionError("refused")),
        ]
        
        for exc_type, exc_value in exceptions:
            message = get_friendly_message(exc_type, exc_value)
            assert isinstance(message, str)
            assert len(message) > 0
            assert "FRIENDLY ERROR EXPLANATION" in message
            assert "How to fix it" in message


class TestLogging:
    """Test the logging functionality."""
    
    def test_logging_to_file(self):
        """Test that exceptions are logged to a file when configured."""
        script = textwrap.dedent("""
            import errfriendly
            import tempfile
            import os
            
            # Create a temporary log file
            log_path = os.path.join(tempfile.gettempdir(), 'errfriendly_test.log')
            
            errfriendly.install(log_file=log_path)
            
            # Trigger an exception
            1 / 0
        """)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script)
            f.flush()
            temp_path = f.name
        
        log_path = os.path.join(tempfile.gettempdir(), 'errfriendly_test.log')
        
        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check log file was created and contains exception info
            assert os.path.exists(log_path), "Log file should be created"
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            assert "ZeroDivisionError" in log_content
            assert "FRIENDLY ERROR EXPLANATION" in log_content
        finally:
            os.unlink(temp_path)
            if os.path.exists(log_path):
                os.unlink(log_path)


class TestRobustness:
    """Test the robustness of the exception handler."""
    
    def test_graceful_failure(self):
        """Test that errfriendly fails gracefully if message generation fails."""
        # This tests that if get_friendly_message raises an exception,
        # the original traceback is still shown
        script = textwrap.dedent("""
            import errfriendly
            from errfriendly import handler
            
            # Monkey-patch at the handler module level where it's actually used
            def broken_get(*args, **kwargs):
                raise RuntimeError("Simulated internal failure")
            handler.get_friendly_message = broken_get
            
            errfriendly.install()
            
            # Trigger an exception
            1 / 0
        """)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script)
            f.flush()
            temp_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Should contain the warning about errfriendly failing
            assert "[errfriendly] Failed to generate friendly message" in result.stderr
            # Should still contain the original traceback
            assert "ZeroDivisionError" in result.stderr
        finally:
            os.unlink(temp_path)



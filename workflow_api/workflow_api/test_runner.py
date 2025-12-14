"""
Custom Test Runner for Python 3.13 Compatibility

This custom test runner fixes the 'ValueError: I/O operation on closed file' error
that occurs when running Django tests with Python 3.13+.

The issue is caused by Django's test runner attempting to write to stdout/stderr
after they have been closed during test discovery and database setup.
"""
import sys
import io
from django.test.runner import DiscoverRunner
from django.core.management import color, base


# Monkey-patch Django's supports_color to handle closed stdout
_original_supports_color = color.supports_color

def patched_supports_color():
    """Patched version of supports_color that handles closed stdout."""
    try:
        return _original_supports_color()
    except (ValueError, AttributeError):
        # If stdout is closed or missing, assume no color support
        return False

color.supports_color = patched_supports_color


# Monkey-patch OutputWrapper to handle closed file descriptors
_OriginalOutputWrapper = base.OutputWrapper

class SafeOutputWrapper(_OriginalOutputWrapper):
    """Output wrapper that handles closed file descriptors gracefully."""
    
    def write(self, msg, style_func=None, ending=None):
        """Write output, handling closed file errors."""
        # Ensure the output stream is open
        if hasattr(self._out, 'closed') and self._out.closed:
            # Replace with appropriate fallback stream
            if self._out is sys.stdout or (hasattr(sys, '__stdout__') and self._out is sys.__stdout__):
                self._out = sys.__stdout__ if not sys.__stdout__.closed else io.TextIOWrapper(io.BufferedWriter(io.BytesIO()))
            elif self._out is sys.stderr or (hasattr(sys, '__stderr__') and self._out is sys.__stderr__):
                self._out = sys.__stderr__ if not sys.__stderr__.closed else io.TextIOWrapper(io.BufferedWriter(io.BytesIO()))
        
        try:
            super().write(msg, style_func, ending)
        except (ValueError, AttributeError) as e:
            if "closed file" in str(e).lower() or "i/o operation" in str(e).lower():
                # Silently skip writing if file is still closed
                pass
            else:
                raise

base.OutputWrapper = SafeOutputWrapper


class Python313CompatibleTestRunner(DiscoverRunner):
    """
    Custom test runner that prevents stdout/stderr closure issues in Python 3.13+.
    
    This runner ensures stdout/stderr remain open throughout the entire test lifecycle,
    preventing ValueError exceptions when Django tries to write to these streams.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the test runner and ensure stdout/stderr are available."""
        # Ensure stdout/stderr are not closed before initialization
        self._ensure_open_streams()
        super().__init__(*args, **kwargs)
    
    def _ensure_open_streams(self):
        """Ensure stdout and stderr are open and available."""
        # If stdout is closed, replace with __stdout__ or create new stream
        if sys.stdout is None or (hasattr(sys.stdout, 'closed') and sys.stdout.closed):
            if hasattr(sys, '__stdout__') and sys.__stdout__ is not None:
                sys.stdout = sys.__stdout__
            else:
                sys.stdout = io.TextIOWrapper(io.BufferedWriter(io.BytesIO()))
        
        # If stderr is closed, replace with __stderr__ or create new stream
        if sys.stderr is None or (hasattr(sys.stderr, 'closed') and sys.stderr.closed):
            if hasattr(sys, '__stderr__') and sys.__stderr__ is not None:
                sys.stderr = sys.__stderr__
            else:
                sys.stderr = io.TextIOWrapper(io.BufferedWriter(io.BytesIO()))
    
    def log(self, msg, level=None):
        """
        Safely log messages, handling closed file descriptor errors.
        
        Args:
            msg: The message to log
            level: The logging level (unused in base implementation)
        """
        self._ensure_open_streams()
        try:
            super().log(msg, level)
        except (IOError, ValueError) as e:
            # Suppress errors from writing to closed stdout/stderr
            if "closed file" not in str(e).lower() and "i/o operation" not in str(e).lower():
                # Re-raise if it's a different error
                raise
    
    def build_suite(self, test_labels=None, **kwargs):
        """
        Build the test suite, safely handling logging during discovery.
        
        Args:
            test_labels: Optional list of test labels to run
            **kwargs: Additional arguments passed to parent
            
        Returns:
            Test suite to execute
        """
        self._ensure_open_streams()
        return super().build_suite(test_labels, **kwargs)
    
    def setup_databases(self, **kwargs):
        """
        Set up test databases, ensuring streams are open during migration.
        
        Args:
            **kwargs: Additional arguments passed to parent
            
        Returns:
            Database configuration for teardown
        """
        self._ensure_open_streams()
        return super().setup_databases(**kwargs)
    
    def run_suite(self, suite, **kwargs):
        """
        Run the test suite, ensuring streams remain open.
        
        Args:
            suite: The test suite to run
            **kwargs: Additional arguments passed to parent
            
        Returns:
            Test result
        """
        self._ensure_open_streams()
        return super().run_suite(suite, **kwargs)

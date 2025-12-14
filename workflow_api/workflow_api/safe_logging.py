"""
Safe print/logging utility for Python 3.13 compatibility.

This module provides safe alternatives to print() that handle closed stdout/stderr
gracefully during Django test execution.
"""
import sys
import logging

# Configure a logger for the workflow_api
logger = logging.getLogger(__name__)


def safe_print(*args, **kwargs):
    """
    Safe version of print() that handles closed stdout/stderr.
    
    Falls back to logging if stdout is unavailable.
    """
    try:
        # Check if stdout is available
        if hasattr(sys.stdout, 'closed') and sys.stdout.closed:
            # Use logging as fallback
            message = ' '.join(str(arg) for arg in args)
            logger.info(message)
        else:
            print(*args, **kwargs)
    except (ValueError, AttributeError, IOError):
        # Fallback to logging if print fails
        message = ' '.join(str(arg) for arg in args)
        logger.info(message)

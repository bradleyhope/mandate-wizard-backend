"""
Timeout utilities for preventing hanging operations
"""

import signal
import functools
from typing import Any, Callable

class TimeoutError(Exception):
    """Raised when an operation times out"""
    pass

def timeout(seconds: int = 30, error_message: str = "Operation timed out"):
    """
    Decorator to add timeout to a function
    
    Args:
        seconds: Maximum time to allow function to run
        error_message: Error message to raise on timeout
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            def _handle_timeout(signum, frame):
                raise TimeoutError(error_message)
            
            # Set the signal handler and alarm
            old_handler = signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                # Disable the alarm and restore old handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
        
        return wrapper
    return decorator

def with_timeout(func: Callable, timeout_seconds: int, *args, **kwargs) -> Any:
    """
    Execute a function with a timeout
    
    Args:
        func: Function to execute
        timeout_seconds: Maximum time to allow
        *args, **kwargs: Arguments to pass to function
        
    Returns:
        Function result or None if timeout
    """
    def _handle_timeout(signum, frame):
        raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds}s")
    
    old_handler = signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(timeout_seconds)
    
    try:
        result = func(*args, **kwargs)
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        return result
    except TimeoutError:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        print(f"[TIMEOUT] {func.__name__} exceeded {timeout_seconds}s limit")
        return None
    except Exception as e:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        raise e


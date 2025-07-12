import time as pytime
from typing import Optional
import datetime

# Global start time
_start: Optional[float] = None


def ocl_time() -> str:
    """Get elapsed time since program start with error handling"""
    try:
        if _start is None:
            return "0.000s"

        elapsed = pytime.time() - _start

        # Handle negative time (system clock changes)
        if elapsed < 0:
            return "0.000s"

        return f"{elapsed:.3f}s"

    except Exception as e:
        return f"[Time Error: {e}]"


def ocl_timestamp() -> str:
    """Get current timestamp with error handling"""
    try:
        return str(int(pytime.time()))
    except Exception as e:
        return f"[Timestamp Error: {e}]"


def ocl_datetime() -> str:
    """Get current date and time with error handling"""
    try:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return f"[DateTime Error: {e}]"


def ocl_date() -> str:
    """Get current date with error handling"""
    try:
        return datetime.datetime.now().strftime("%Y-%m-%d")
    except Exception as e:
        return f"[Date Error: {e}]"


def ocl_sleep(seconds: float) -> None:
    """Sleep for specified seconds with validation"""
    try:
        if not isinstance(seconds, (int, float)):
            raise TypeError(f"Sleep duration must be numeric, got {type(seconds).__name__}")

        if seconds < 0:
            raise ValueError("Sleep duration cannot be negative")

        if seconds > 3600:  # Limit to 1 hour
            raise ValueError("Sleep duration cannot exceed 1 hour")

        pytime.sleep(seconds)

    except Exception as e:
        raise RuntimeError(f"Sleep error: {e}")


def reset_timer() -> None:
    """Reset the program timer with error handling"""
    global _start
    try:
        _start = pytime.time()
    except Exception as e:
        raise RuntimeError(f"Timer reset error: {e}")


def get_uptime() -> float:
    """Get program uptime in seconds with error handling"""
    try:
        if _start is None:
            return 0.0

        uptime = pytime.time() - _start
        return max(0.0, uptime)  # Ensure non-negative

    except Exception as e:
        raise RuntimeError(f"Uptime error: {e}")


def register(env: dict):
    """Register time functions in environment with error handling"""
    global _start

    try:
        # Initialize start time
        _start = pytime.time()

        # Register functions
        env["time"] = ocl_time
        env["timestamp"] = ocl_timestamp
        env["datetime"] = ocl_datetime
        env["date"] = ocl_date
        env["sleep"] = ocl_sleep
        env["reset_timer"] = reset_timer
        env["uptime"] = get_uptime

    except Exception as e:
        raise RuntimeError(f"Failed to register time module: {e}")


# Legacy compatibility
def ocl_time_ms() -> str:
    """Get elapsed time in milliseconds"""
    try:
        if _start is None:
            return "0ms"

        elapsed = (pytime.time() - _start) * 1000

        if elapsed < 0:
            return "0ms"

        return f"{elapsed:.0f}ms"

    except Exception as e:
        return f"[Time Error: {e}]"
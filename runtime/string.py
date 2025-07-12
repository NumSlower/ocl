import sys
from typing import Any


def safe_print(*args):
    """Safe print function that handles various data types"""
    try:
        # Convert all arguments to strings safely
        str_args = []
        for arg in args:
            if arg is None:
                str_args.append("null")
            elif isinstance(arg, bool):
                str_args.append("true" if arg else "false")
            elif isinstance(arg, (int, float)):
                str_args.append(str(arg))
            elif isinstance(arg, str):
                str_args.append(arg)
            else:
                str_args.append(str(arg))

        print(*str_args, end='')
        sys.stdout.flush()  # Ensure output is flushed

    except BrokenPipeError:
        # Handle broken pipe gracefully (e.g., when piping to head)
        pass
    except UnicodeEncodeError as e:
        # Handle encoding errors
        print(f"[Encoding Error: {e}]", end='')
    except Exception as e:
        # Handle any other print errors
        print(f"[Print Error: {e}]", end='')


def safe_println(*args):
    """Safe println function that handles various data types"""
    try:
        # Convert all arguments to strings safely
        str_args = []
        for arg in args:
            if arg is None:
                str_args.append("null")
            elif isinstance(arg, bool):
                str_args.append("true" if arg else "false")
            elif isinstance(arg, (int, float)):
                str_args.append(str(arg))
            elif isinstance(arg, str):
                str_args.append(arg)
            else:
                str_args.append(str(arg))

        print(*str_args)
        sys.stdout.flush()  # Ensure output is flushed

    except BrokenPipeError:
        # Handle broken pipe gracefully (e.g., when piping to head)
        pass
    except UnicodeEncodeError as e:
        # Handle encoding errors
        print(f"[Encoding Error: {e}]")
    except Exception as e:
        # Handle any other print errors
        print(f"[Print Error: {e}]")


def ocl_len(value: Any) -> int:
    """Get length of string or collection with error handling"""
    try:
        if hasattr(value, '__len__'):
            return len(value)
        elif value is None:
            return 0
        else:
            return len(str(value))
    except Exception as e:
        raise RuntimeError(f"Cannot get length of {type(value).__name__}: {e}")


def ocl_substr(string: Any, start: int, end: int = None) -> str:
    """Safe substring function with bounds checking"""
    try:
        s = str(string) if string is not None else ""

        if not isinstance(start, int):
            raise TypeError(f"Start index must be integer, got {type(start).__name__}")

        if end is not None and not isinstance(end, int):
            raise TypeError(f"End index must be integer, got {type(end).__name__}")

        length = len(s)

        # Handle negative indices
        if start < 0:
            start = max(0, length + start)
        if end is not None and end < 0:
            end = max(0, length + end)

        # Clamp to valid range
        start = max(0, min(start, length))
        if end is not None:
            end = max(start, min(end, length))
            return s[start:end]
        else:
            return s[start:]

    except Exception as e:
        raise RuntimeError(f"Substring error: {e}")


def ocl_upper(value: Any) -> str:
    """Convert to uppercase with error handling"""
    try:
        return str(value).upper() if value is not None else ""
    except Exception as e:
        raise RuntimeError(f"Cannot convert to uppercase: {e}")


def ocl_lower(value: Any) -> str:
    """Convert to lowercase with error handling"""
    try:
        return str(value).lower() if value is not None else ""
    except Exception as e:
        raise RuntimeError(f"Cannot convert to lowercase: {e}")


def register(env: dict):
    """Register string functions in environment"""
    try:
        env["print"] = safe_print
        env["println"] = safe_println
        env["len"] = ocl_len
        env["substr"] = ocl_substr
        env["upper"] = ocl_upper
        env["lower"] = ocl_lower
    except Exception as e:
        raise RuntimeError(f"Failed to register string module: {e}")


# Legacy compatibility
ocl_print = safe_print
ocl_println = safe_println
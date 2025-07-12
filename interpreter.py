import importlib
import sys
import traceback
from typing import Any, Dict, Optional, List
from ocl_ast import *


class RuntimeError(Exception):
    """Custom runtime error for OCL interpreter"""
    pass


class UndefinedVariableError(RuntimeError):
    """Raised when accessing undefined variables"""
    pass


class UndefinedFunctionError(RuntimeError):
    """Raised when calling undefined functions"""
    pass


class TypeError(RuntimeError):
    """Raised for type-related errors"""
    pass


class ModuleLoadError(RuntimeError):
    """Raised when module loading fails"""
    pass


class ExecutionFrame:
    """Represents a function execution frame with local variables"""
    def __init__(self, function_name: str, parameters: Dict[str, Any] = None):
        self.function_name = function_name
        self.local_vars = parameters or {}
        
    def get_variable(self, name: str) -> Any:
        """Get variable from local scope"""
        if name in self.local_vars:
            return self.local_vars[name]
        raise UndefinedVariableError(f"Undefined variable: {name}")
    
    def set_variable(self, name: str, value: Any):
        """Set variable in local scope"""
        self.local_vars[name] = value


class Interpreter:
    def __init__(self, program: Program):
        if not isinstance(program, Program):
            raise TypeError("Expected Program object")

        self.program = program
        self.env = {}  # Built-in functions and constants
        self.global_vars = {}  # Global variables
        self.call_stack = []  # Stack of ExecutionFrame objects
        self.max_call_depth = 1000

    def run(self) -> int:
        """Run the program with comprehensive error handling"""
        try:
            # Validate program structure
            if not self.program.functions:
                raise RuntimeError("No functions defined in program")

            # Load all imported modules
            for imp in self.program.imports:
                try:
                    self.load_module(imp.module)
                except Exception as e:
                    print(f"Warning: Failed to load module '{imp.module}': {e}")
                    # Continue execution - some modules might be optional

            # Execute global statements
            for stmt in self.program.statements:
                try:
                    self.execute_statement(stmt)
                except Exception as e:
                    print(f"Error executing global statement: {e}")
                    raise

            # Find and execute main function
            main_fn = self._find_function("main")
            if not main_fn:
                raise RuntimeError("No `main` function found")

            result = self.execute_function(main_fn, [])
            return result if result is not None else 0

        except KeyboardInterrupt:
            print("\nProgram interrupted by user")
            return 130
        except RuntimeError as e:
            print(f"Runtime error: {e}")
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}")
            if hasattr(e, '__traceback__'):
                traceback.print_exc()
            return 1

    def load_module(self, name: str):
        """Load a module with proper error handling"""
        if not name:
            raise ModuleLoadError("Module name cannot be empty")

        if not name.replace('_', '').isalnum():
            raise ModuleLoadError(f"Invalid module name: {name}")

        module_loaded = False
        last_error = None

        # Try to import from runtime package first
        try:
            mod = importlib.import_module(f"runtime.{name}")
            module_loaded = True
        except ModuleNotFoundError as e:
            last_error = e
            try:
                # If that fails, try importing from current directory
                mod = importlib.import_module(name)
                module_loaded = True
            except ModuleNotFoundError as e2:
                last_error = e2

        if not module_loaded:
            raise ModuleLoadError(f"Module '{name}' not found: {last_error}")

        # Check for register function
        if not hasattr(mod, "register"):
            raise ModuleLoadError(f"Module '{name}' does not have a register() function")

        # Register the module
        try:
            mod.register(self.env)
        except Exception as e:
            raise ModuleLoadError(f"Error registering module '{name}': {e}")

    def _find_function(self, name: str) -> Optional[FunctionDef]:
        """Find a function by name"""
        if not name:
            return None

        for fn in self.program.functions:
            if fn.name == name:
                return fn
        return None

    def execute_function(self, fn: FunctionDef, args: List[Any]) -> Any:
        """Execute a function with call stack management and parameter binding"""
        if len(self.call_stack) >= self.max_call_depth:
            raise RuntimeError(f"Maximum call depth exceeded ({self.max_call_depth})")

        # Check parameter count
        if len(args) != len(fn.parameters):
            raise RuntimeError(f"Function '{fn.name}' expects {len(fn.parameters)} arguments, got {len(args)}")

        # Create parameter bindings
        param_bindings = {}
        for i, param in enumerate(fn.parameters):
            param_bindings[param.name] = args[i]

        # Create new execution frame
        frame = ExecutionFrame(fn.name, param_bindings)
        self.call_stack.append(frame)

        try:
            for stmt in fn.body:
                result = self.execute_statement(stmt)
                if isinstance(stmt, Return):
                    return result

            # If no return statement, return None for void functions or 0 for int functions
            return 0 if fn.return_type == "int" else None

        except Exception as e:
            # Add function context to error
            raise RuntimeError(f"Error in function '{fn.name}': {e}")
        finally:
            self.call_stack.pop()

    def execute_statement(self, stmt) -> Any:
        """Execute a statement with type checking"""
        try:
            if isinstance(stmt, Call):
                return self.evaluate(stmt)
            elif isinstance(stmt, Return):
                return self.evaluate(stmt.value)
            elif isinstance(stmt, LetStatement):
                value = self.evaluate(stmt.value)
                self.set_variable(stmt.name, value)
                return value
            else:
                raise RuntimeError(f"Unknown statement type: {type(stmt)}")
        except Exception as e:
            raise RuntimeError(f"Error executing statement: {e}")

    def set_variable(self, name: str, value: Any):
        """Set variable in current scope"""
        if self.call_stack:
            # Set in local scope
            self.call_stack[-1].set_variable(name, value)
        else:
            # Set in global scope
            self.global_vars[name] = value

    def get_variable(self, name: str) -> Any:
        """Get variable from current scope"""
        # Try local scope first
        if self.call_stack:
            try:
                return self.call_stack[-1].get_variable(name)
            except UndefinedVariableError:
                pass
        
        # Try global scope
        if name in self.global_vars:
            return self.global_vars[name]
        
        # Try built-in environment (for constants like pi, e)
        if name in self.env:
            return self.env[name]
        
        raise UndefinedVariableError(f"Undefined variable: {name}")

    def evaluate(self, node) -> Any:
        """Evaluate an expression with comprehensive type checking"""
        if node is None:
            return None

        try:
            if isinstance(node, StringLiteral):
                return node.value
            elif isinstance(node, NumberLiteral):
                return node.value
            elif isinstance(node, Variable):
                return self.get_variable(node.name)
            elif isinstance(node, Call):
                return self.evaluate_call(node)
            elif isinstance(node, BinaryOp):
                return self.evaluate_binary_op(node)
            elif isinstance(node, UnaryOp):
                return self.evaluate_unary_op(node)
            else:
                raise RuntimeError(f"Cannot evaluate node type: {type(node)}")
        except Exception as e:
            raise RuntimeError(f"Error evaluating expression: {e}")

    def evaluate_call(self, call: Call) -> Any:
        """Evaluate function call with argument validation"""
        if not call.name:
            raise RuntimeError("Function name cannot be empty")

        # Check if it's a built-in function (must be callable)
        if call.name in self.env and callable(self.env[call.name]):
            func = self.env[call.name]

            try:
                # Evaluate arguments
                args = []
                for i, arg in enumerate(call.args):
                    try:
                        args.append(self.evaluate(arg))
                    except Exception as e:
                        raise RuntimeError(f"Error evaluating argument {i + 1} of function '{call.name}': {e}")

                # Call the built-in function
                return func(*args)

            except TypeError as e:
                if "arguments" in str(e):
                    raise RuntimeError(f"Wrong number of arguments for function '{call.name}': {e}")
                else:
                    raise RuntimeError(f"Type error in function '{call.name}': {e}")
            except Exception as e:
                raise RuntimeError(f"Error calling function '{call.name}': {e}")

        # Check if it's a user-defined function
        user_fn = self._find_function(call.name)
        if user_fn:
            try:
                # Evaluate arguments
                args = []
                for i, arg in enumerate(call.args):
                    try:
                        args.append(self.evaluate(arg))
                    except Exception as e:
                        raise RuntimeError(f"Error evaluating argument {i + 1} of function '{call.name}': {e}")

                # Call the user-defined function
                return self.execute_function(user_fn, args)

            except Exception as e:
                raise RuntimeError(f"Error calling user function '{call.name}': {e}")

        raise UndefinedFunctionError(f"Unknown function: {call.name}")

    def evaluate_binary_op(self, binop: BinaryOp) -> Any:
        """Evaluate binary operations with type checking"""
        try:
            left = self.evaluate(binop.left)
            right = self.evaluate(binop.right)

            if binop.operator == "+":
                # Handle string concatenation and numeric addition
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)
                elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return left + right
                else:
                    raise TypeError(f"Cannot add {type(left).__name__} and {type(right).__name__}")
            elif binop.operator == "-":
                # Handle numeric subtraction
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return left - right
                else:
                    raise TypeError(f"Cannot subtract {type(right).__name__} from {type(left).__name__}")
            elif binop.operator == "*":
                # Handle numeric multiplication
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return left * right
                else:
                    raise TypeError(f"Cannot multiply {type(left).__name__} and {type(right).__name__}")
            elif binop.operator == "/":
                # Handle numeric division
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    if right == 0:
                        raise RuntimeError("Division by zero")
                    return left / right
                else:
                    raise TypeError(f"Cannot divide {type(left).__name__} by {type(right).__name__}")
            elif binop.operator == "%":
                # Handle modulo operation
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    if right == 0:
                        raise RuntimeError("Modulo by zero")
                    return left % right
                else:
                    raise TypeError(f"Cannot get modulo of {type(left).__name__} and {type(right).__name__}")
            else:
                raise RuntimeError(f"Unknown binary operator: {binop.operator}")

        except Exception as e:
            raise RuntimeError(f"Error evaluating binary operation: {e}")

    def evaluate_unary_op(self, unary_op: UnaryOp) -> Any:
        """Evaluate unary operations with type checking"""
        try:
            operand = self.evaluate(unary_op.operand)

            if unary_op.operator == "-":
                # Handle numeric negation
                if isinstance(operand, (int, float)):
                    return -operand
                else:
                    raise TypeError(f"Cannot negate {type(operand).__name__}")
            elif unary_op.operator == "+":
                # Handle unary plus (identity operation)
                if isinstance(operand, (int, float)):
                    return +operand
                else:
                    raise TypeError(f"Cannot apply unary plus to {type(operand).__name__}")
            else:
                raise RuntimeError(f"Unknown unary operator: {unary_op.operator}")

        except Exception as e:
            raise RuntimeError(f"Error evaluating unary operation: {e}")

    def get_call_stack(self) -> List[str]:
        """Get current call stack for debugging"""
        return [frame.function_name for frame in self.call_stack]

    def get_variables(self) -> Dict[str, Any]:
        """Get all variables for debugging"""
        result = self.global_vars.copy()
        if self.call_stack:
            result.update(self.call_stack[-1].local_vars)
        return result

    def get_functions(self) -> List[str]:
        """Get all available functions"""
        builtin_funcs = [name for name, value in self.env.items() if callable(value)]
        user_funcs = [fn.name for fn in self.program.functions]
        return builtin_funcs + user_funcs
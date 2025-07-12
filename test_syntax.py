#!/usr/bin/env python3
"""
Example usage of the enhanced OCL interpreter with error handling
"""

from main import OCLCompiler


def test_valid_program():
    """Test a valid OCL program"""
    print("=== Testing Valid Program ===")

    code = '''
@version "v0.00.11"

import string;
import time;

let message = "Hello from OCL!"
let x = 5 + 3

int main() {
    println("Welcome to OCL - v0.00.11");
    println(message);
    println("x =", x);
    println("Elapsed time:", time());
    return 0;
}
'''

    compiler = OCLCompiler(debug=True)
    exit_code = compiler.compile_and_run(code, "test_valid.ocl")
    print(f"Exit code: {exit_code}")
    return exit_code == 0


def test_syntax_error():
    """Test handling of syntax errors"""
    print("\n=== Testing Syntax Error Handling ===")

    code = '''
@version "v0.00.11"

import string;
import time;

int main() {
    println("This has a syntax error"
    // Missing closing parenthesis and semicolon
    return 0;
}
'''

    compiler = OCLCompiler(debug=True)
    exit_code = compiler.compile_and_run(code, "test_syntax_error.ocl")
    print(f"Exit code: {exit_code}")
    return exit_code != 0  # Should fail


def test_runtime_error():
    """Test handling of runtime errors"""
    print("\n=== Testing Runtime Error Handling ===")

    code = '''
@version "v0.00.11"

import string;

int main() {
    println("About to call undefined function");
    undefined_function();
    return 0;
}
'''

    compiler = OCLCompiler(debug=True)
    exit_code = compiler.compile_and_run(code, "test_runtime_error.ocl")
    print(f"Exit code: {exit_code}")
    return exit_code != 0  # Should fail


def test_lexer_error():
    """Test handling of lexer errors"""
    print("\n=== Testing Lexer Error Handling ===")

    code = '''
@version "v0.00.11"

import string;

int main() {
    println("Unterminated string literal);
    return 0;
}
'''

    compiler = OCLCompiler(debug=True)
    exit_code = compiler.compile_and_run(code, "test_lexer_error.ocl")
    print(f"Exit code: {exit_code}")
    return exit_code != 0  # Should fail


def test_missing_main():
    """Test handling of missing main function"""
    print("\n=== Testing Missing Main Function ===")

    code = '''
@version "v0.00.11"

import string;

int helper() {
    println("This is a helper function");
    return 0;
}
'''

    compiler = OCLCompiler(debug=True)
    exit_code = compiler.compile_and_run(code, "test_missing_main.ocl")
    print(f"Exit code: {exit_code}")
    return exit_code != 0  # Should fail


def test_variable_operations():
    """Test variable operations with error handling"""
    print("\n=== Testing Variable Operations ===")

    code = '''
@version "v0.00.11"

import string;

let a = 10
let b = 20
let c = a + b
let greeting = "Hello"
let name = "World"
let message = greeting + " " + name

int main() {
    println("a =", a);
    println("b =", b);
    println("c = a + b =", c);
    println("message =", message);
    return 0;
}
'''

    compiler = OCLCompiler(debug=True)
    exit_code = compiler.compile_and_run(code, "test_variables.ocl")
    print(f"Exit code: {exit_code}")
    return exit_code == 0


def test_undefined_variable():
    """Test handling of undefined variables"""
    print("\n=== Testing Undefined Variable Handling ===")

    code = '''
@version "v0.00.11"

import string;

int main() {
    println("Using undefined variable:", undefined_var);
    return 0;
}
'''

    compiler = OCLCompiler(debug=True)
    exit_code = compiler.compile_and_run(code, "test_undefined_var.ocl")
    print(f"Exit code: {exit_code}")
    return exit_code != 0  # Should fail


def test_module_loading():
    """Test module loading with error handling"""
    print("\n=== Testing Module Loading ===")

    code = '''
@version "v0.00.11"

import string;
import time;
import nonexistent_module;

int main() {
    println("Testing module loading");
    println("Time:", time());
    return 0;
}
'''

    compiler = OCLCompiler(debug=True)
    exit_code = compiler.compile_and_run(code, "test_modules.ocl")
    print(f"Exit code: {exit_code}")
    # Should continue execution despite missing module
    return True


def run_all_tests():
    """Run all test cases"""
    print("Running OCL Interpreter Error Handling Tests")
    print("=" * 50)

    tests = [
        ("Valid Program", test_valid_program),
        ("Syntax Error", test_syntax_error),
        ("Runtime Error", test_runtime_error),
        ("Lexer Error", test_lexer_error),
        ("Missing Main", test_missing_main),
        ("Variable Operations", test_variable_operations),
        ("Undefined Variable", test_undefined_variable),
        ("Module Loading", test_module_loading),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nRunning test: {test_name}")
        try:
            if test_func():
                print(f"✓ {test_name} passed")
                passed += 1
            else:
                print(f"✗ {test_name} failed")
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")

    print(f"\n{'=' * 50}")
    print(f"Test Results: {passed}/{total} passed")

    if passed == total:
        print("All tests passed! 🎉")
    else:
        print(f"{total - passed} tests failed. 😞")

    return passed == total


if __name__ == "__main__":
    run_all_tests()
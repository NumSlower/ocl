import sys
import traceback
from pathlib import Path
from typing import Optional, List, Tuple

# Import enhanced modules
from lexer import tokenize, tokenize_with_recovery, LexerError
from parser import Parser, ParseError
from interpreter import Interpreter, RuntimeError as OCLRuntimeError


class OCLCompiler:
    """Main OCL compiler class with comprehensive error handling"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.errors = []
        self.warnings = []

    def compile_and_run(self, code: str, filename: str = "<string>") -> int:
        """Compile and run OCL code with full error handling"""
        try:
            # Tokenization phase
            tokens = self.tokenize_phase(code, filename)
            if not tokens:
                return 1

            # Parsing phase
            program = self.parse_phase(tokens, filename)
            if not program:
                return 1

            # Interpretation phase
            return self.interpret_phase(program, filename)

        except KeyboardInterrupt:
            print("\nCompilation interrupted by user")
            return 130
        except Exception as e:
            print(f"Fatal error: {e}")
            if self.debug:
                traceback.print_exc()
            return 1

    def tokenize_phase(self, code: str, filename: str) -> Optional[List[Tuple[str, str, int, int]]]:
        """Tokenization phase with error recovery"""
        if self.debug:
            print("=== Tokenization Phase ===")

        try:
            tokens = tokenize(code)
            if self.debug:
                print(f"Successfully tokenized {len(tokens)} tokens")
                for i, token in enumerate(tokens[:10]):  # Show first 10 tokens
                    print(f"  {i}: {token}")
                if len(tokens) > 10:
                    print(f"  ... and {len(tokens) - 10} more tokens")
            return tokens

        except LexerError as e:
            print(f"Lexer error in {filename}: {e}")

            # Try recovery
            print("Attempting error recovery...")
            tokens, recovery_errors = tokenize_with_recovery(code)
            if tokens:
                print(f"Recovery successful: {len(tokens)} tokens extracted")
                for error in recovery_errors:
                    print(f"  Recovery error: {error}")
                return tokens
            else:
                print("Recovery failed")
                return None

        except Exception as e:
            print(f"Unexpected tokenization error in {filename}: {e}")
            if self.debug:
                traceback.print_exc()
            return None

    def parse_phase(self, tokens: List[Tuple[str, str, int, int]], filename: str) -> Optional['Program']:
        """Parsing phase with error recovery"""
        if self.debug:
            print("=== Parsing Phase ===")

        try:
            parser = Parser(tokens)
            program = parser.parse()

            # Check for parse errors
            if parser.has_errors():
                print(f"Parse errors in {filename}:")
                for error in parser.get_errors():
                    print(f"  {error}")

                if not program:
                    print("Parsing failed completely")
                    return None
                else:
                    print("Parsing completed with errors, attempting to continue...")

            if self.debug and program:
                print(f"Successfully parsed program:")
                print(f"  Version: {program.version.version if program.version else 'None'}")
                print(f"  Imports: {len(program.imports)}")
                print(f"  Functions: {len(program.functions)}")
                print(f"  Statements: {len(program.statements)}")

            return program

        except Exception as e:
            print(f"Unexpected parsing error in {filename}: {e}")
            if self.debug:
                traceback.print_exc()
            return None

    def interpret_phase(self, program: 'Program', filename: str) -> int:
        """Interpretation phase with runtime error handling"""
        if self.debug:
            print("=== Interpretation Phase ===")

        try:
            interpreter = Interpreter(program)

            if self.debug:
                print("Available functions:", interpreter.get_functions())

            exit_code = interpreter.run()

            if self.debug:
                print(f"Program completed with exit code: {exit_code}")
                variables = interpreter.get_variables()
                if variables:
                    print("Final variables:", variables)

            return exit_code

        except OCLRuntimeError as e:
            print(f"Runtime error in {filename}: {e}")
            if self.debug:
                call_stack = interpreter.get_call_stack() if 'interpreter' in locals() else []
                if call_stack:
                    print("Call stack:", " -> ".join(call_stack))
            return 1
        except Exception as e:
            print(f"Unexpected runtime error in {filename}: {e}")
            if self.debug:
                traceback.print_exc()
            return 1

    def compile_file(self, filepath: str) -> int:
        """Compile and run OCL file"""
        try:
            path = Path(filepath)
            if not path.exists():
                print(f"Error: File '{filepath}' not found")
                return 1

            if not path.is_file():
                print(f"Error: '{filepath}' is not a file")
                return 1

            code = path.read_text(encoding='utf-8')
            return self.compile_and_run(code, filepath)

        except UnicodeDecodeError as e:
            print(f"Error: Cannot read file '{filepath}' - {e}")
            return 1
        except Exception as e:
            print(f"Error reading file '{filepath}': {e}")
            return 1


def main():
    """Main entry point with command line argument handling"""
    import argparse

    parser = argparse.ArgumentParser(description='OCL Interpreter with Enhanced Error Handling')
    parser.add_argument('file', nargs='?', help='OCL file to execute')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    parser.add_argument('-v', '--version', action='version', version='OCL Interpreter v0.00.11')

    args = parser.parse_args()

    compiler = OCLCompiler(debug=args.debug)

    if args.file:
        # Compile and run file
        exit_code = compiler.compile_file(args.file)
    else:
        # Default embedded code for testing
        code = '''
@version "v0.00.18"

import string;
import time;
import math;

void test_math() {
    println("Add:", add(2, 3));
    println("Sub:", sub(10, 4));
    println("Abs:", abs(-7));
    println("Sqrt:", sqrt(25));
    println("Sin(pi/2):", sin(div(pi, 2)));
}

int main() {
    test_math();

    println("Welcome to OCL - v0.00.18");
    println("Hello, World!");
    println("Elapsed:", time());
    println("x =", add(5, 5));  // Simulating let x = 5 + 5
    return 0;
}
'''
        exit_code = compiler.compile_and_run(code)

    print(f"\n[exit code: {exit_code}]")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
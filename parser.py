from ocl_ast import *
from typing import List, Tuple, Optional, Union


class ParseError(Exception):
    """Custom exception for parser errors"""

    def __init__(self, message: str, token: Optional[Tuple[str, str, int, int]] = None):
        self.message = message
        self.token = token
        if token:
            super().__init__(f"Parse error at line {token[2]}, column {token[3]}: {message}")
        else:
            super().__init__(f"Parse error: {message}")


class Parser:
    def __init__(self, tokens: List[Tuple[str, str, int, int]]):
        self.tokens = tokens
        self.pos = 0
        self.errors = []
        self.panic_mode = False

    def peek(self) -> Optional[Tuple[str, str, int, int]]:
        """Get current token without advancing"""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self) -> Optional[Tuple[str, str, int, int]]:
        """Get current token and advance position"""
        tok = self.peek()
        if tok:
            self.pos += 1
        return tok

    def is_at_end(self) -> bool:
        """Check if we're at the end of tokens"""
        return self.pos >= len(self.tokens)

    def expect(self, kind: str) -> Tuple[str, str, int, int]:
        """Expect a specific token type"""
        token = self.peek()
        if not token:
            raise ParseError(f"Expected {kind}, but reached end of file")

        if token[0] != kind:
            raise ParseError(f"Expected {kind}, got {token[0]} ('{token[1]}')", token)

        return self.advance()

    def match(self, *kinds: str) -> bool:
        """Check if current token matches any of the given kinds"""
        token = self.peek()
        return token and token[0] in kinds

    def synchronize(self):
        """Synchronize after a parse error"""
        self.panic_mode = False

        while not self.is_at_end():
            # Look for statement boundaries
            if self.match("SEMI", "RBRACE", "INT", "VOID", "IMPORT", "VERSION"):
                return
            self.advance()

    def report_error(self, message: str, token: Optional[Tuple[str, str, int, int]] = None):
        """Report a parse error"""
        error = ParseError(message, token)
        self.errors.append(str(error))
        self.panic_mode = True

    def parse(self) -> Optional[Program]:
        """Parse the entire program with error recovery"""
        try:
            return self._parse_program()
        except Exception as e:
            self.report_error(f"Fatal parse error: {e}")
            return None

    def _parse_program(self) -> Program:
        """Parse the program structure"""
        version = None
        imports = []
        functions = []
        statements = []

        # Parse version directive
        if self.match("VERSION"):
            try:
                version = self.parse_version()
            except ParseError as e:
                self.report_error(str(e))
                self.synchronize()

        # Parse imports
        while self.match("IMPORT"):
            try:
                imports.append(self.parse_import())
            except ParseError as e:
                self.report_error(str(e))
                self.synchronize()

        # Parse global statements (like let x = 5 + 5)
        while self.match("LET"):
            try:
                statements.append(self.parse_let_statement())
            except ParseError as e:
                self.report_error(str(e))
                self.synchronize()

        # Parse functions
        while self.match("INT", "VOID"):
            try:
                functions.append(self.parse_function())
            except ParseError as e:
                self.report_error(str(e))
                self.synchronize()

        # Check for unexpected tokens
        if not self.is_at_end():
            remaining = self.peek()
            self.report_error(f"Unexpected token '{remaining[1]}'", remaining)

        return Program(version, imports, functions, statements)

    def parse_version(self) -> VersionDirective:
        """Parse version directive with validation"""
        try:
            self.expect("VERSION")
            version_token = self.expect("STRING")
            version_str = version_token[1].strip('"')

            # Validate version format
            if not version_str:
                raise ParseError("Version string cannot be empty", version_token)

            return VersionDirective(version=version_str)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Error parsing version directive: {e}")

    def parse_import(self) -> Import:
        """Parse import statement with validation"""
        try:
            self.expect("IMPORT")
            module_token = self.expect("IDENT")
            module_name = module_token[1]

            # Validate module name
            if not module_name:
                raise ParseError("Module name cannot be empty", module_token)

            self.expect("SEMI")
            return Import(module=module_name)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Error parsing import statement: {e}")

    def parse_let_statement(self) -> 'LetStatement':
        """Parse let statement (let x = 5 + 5)"""
        try:
            self.expect("LET")
            name_token = self.expect("IDENT")
            name = name_token[1]
            self.expect("ASSIGN")
            value = self.parse_expression()

            return LetStatement(name=name, value=value)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Error parsing let statement: {e}")

    def parse_function(self) -> FunctionDef:
        """Parse function definition with parameters"""
        try:
            return_type = self.advance()[0]  # INT or VOID
            name_token = self.expect("IDENT")
            name = name_token[1]

            # Validate function name
            if not name:
                raise ParseError("Function name cannot be empty", name_token)

            self.expect("LPAREN")
            
            # Parse parameters
            parameters = []
            if not self.match("RPAREN"):
                parameters.append(self.parse_parameter())
                while self.match("COMMA"):
                    self.advance()  # consume comma
                    parameters.append(self.parse_parameter())

            self.expect("RPAREN")
            self.expect("LBRACE")

            body = []
            while not self.match("RBRACE") and not self.is_at_end():
                try:
                    stmt = self.parse_statement()
                    if stmt:
                        body.append(stmt)
                except ParseError as e:
                    self.report_error(str(e))
                    self.synchronize()

            if self.is_at_end():
                raise ParseError("Unexpected end of file, expected '}'")

            self.expect("RBRACE")
            return FunctionDef(name=name, parameters=parameters, return_type=return_type, body=body)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Error parsing function '{name if 'name' in locals() else 'unknown'}': {e}")

    def parse_parameter(self) -> Parameter:
        """Parse function parameter (type name)"""
        try:
            # Parse parameter type
            type_token = self.expect("IDENT")
            param_type = type_token[1]
            
            # Parse parameter name  
            name_token = self.expect("IDENT")
            param_name = name_token[1]
            
            if not param_name:
                raise ParseError("Parameter name cannot be empty", name_token)
                
            return Parameter(type=param_type, name=param_name)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Error parsing parameter: {e}")

    def parse_statement(self) -> Optional[Union['Call', 'Return', 'LetStatement']]:
        """Parse a statement"""
        if self.match("RETURN"):
            return self.parse_return()
        elif self.match("LET"):
            return self.parse_let_statement()
        elif self.match("IDENT"):
            return self.parse_call_statement()
        else:
            token = self.peek()
            raise ParseError(f"Unexpected statement token: {token[0] if token else 'EOF'}", token)

    def parse_call_statement(self) -> Call:
        """Parse function call statement"""
        try:
            call = self.parse_call_expression()
            self.expect("SEMI")
            return call
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Error parsing call statement: {e}")

    def parse_call_expression(self) -> Call:
        """Parse function call expression"""
        try:
            name_token = self.advance()
            name = name_token[1]

            if not name:
                raise ParseError("Function name cannot be empty", name_token)

            self.expect("LPAREN")
            args = []

            if not self.match("RPAREN"):
                args.append(self.parse_expression())
                while self.match("COMMA"):
                    self.advance()  # consume comma
                    args.append(self.parse_expression())

            self.expect("RPAREN")
            return Call(name=name, args=args)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Error parsing call expression: {e}")

    def parse_return(self) -> Return:
        """Parse return statement"""
        try:
            self.expect("RETURN")
            value = None

            if not self.match("SEMI"):
                value = self.parse_expression()

            self.expect("SEMI")
            return Return(value=value)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Error parsing return statement: {e}")

    def parse_expression(self) -> Union['StringLiteral', 'NumberLiteral', 'Call', 'Variable', 'BinaryOp', 'UnaryOp']:
        """Parse expression with operator precedence"""
        return self.parse_addition()

    def parse_addition(self) -> Union['StringLiteral', 'NumberLiteral', 'Call', 'Variable', 'BinaryOp', 'UnaryOp']:
        """Parse addition/subtraction expressions"""
        expr = self.parse_multiplication()

        while self.match("PLUS", "MINUS"):
            op = self.advance()[1]
            right = self.parse_multiplication()
            expr = BinaryOp(left=expr, operator=op, right=right)

        return expr

    def parse_multiplication(self) -> Union['StringLiteral', 'NumberLiteral', 'Call', 'Variable', 'BinaryOp', 'UnaryOp']:
        """Parse multiplication/division expressions"""
        return self.parse_unary()

    def parse_unary(self) -> Union['StringLiteral', 'NumberLiteral', 'Call', 'Variable', 'BinaryOp', 'UnaryOp']:
        """Parse unary expressions"""
        if self.match("MINUS"):
            op = self.advance()[1]
            expr = self.parse_unary()
            return UnaryOp(operator=op, operand=expr)
        
        return self.parse_primary()

    def parse_primary(self) -> Union['StringLiteral', 'NumberLiteral', 'Call', 'Variable']:
        """Parse primary expressions"""
        token = self.peek()

        if not token:
            raise ParseError("Unexpected end of file in expression")

        tok_type, value = token[0], token[1]

        if tok_type == "STRING":
            self.advance()
            return StringLiteral(value.strip('"'))
        elif tok_type == "NUMBER":
            self.advance()
            try:
                return NumberLiteral(int(value))
            except ValueError:
                raise ParseError(f"Invalid number format: {value}", token)
        elif tok_type == "IDENT":
            # Check if it's a function call or variable
            next_token = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_token and next_token[0] == "LPAREN":
                return self.parse_call_expression()
            else:
                self.advance()
                return Variable(name=value)
        elif tok_type == "LPAREN":
            self.advance()
            expr = self.parse_expression()
            self.expect("RPAREN")
            return expr
        else:
            raise ParseError(f"Unexpected token in expression: {tok_type} ('{value}')", token)

    def get_errors(self) -> List[str]:
        """Get all parsing errors"""
        return self.errors.copy()

    def has_errors(self) -> bool:
        """Check if there were any parsing errors"""
        return len(self.errors) > 0
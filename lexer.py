import re
from typing import List, Tuple, Optional


class LexerError(Exception):
    """Custom exception for lexer errors"""

    def __init__(self, message: str, position: int, line: int, column: int):
        self.message = message
        self.position = position
        self.line = line
        self.column = column
        super().__init__(f"Lexer error at line {line}, column {column}: {message}")


class Position:
    """Track position in source code"""

    def __init__(self):
        self.line = 1
        self.column = 1
        self.position = 0

    def advance(self, char: str):
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.position += 1

    def copy(self):
        pos = Position()
        pos.line = self.line
        pos.column = self.column
        pos.position = self.position
        return pos


# Enhanced token regex with type system support
TOKEN_REGEX = [
    ("VERSION", r"@version"),
    ("IMPORT", r"import"),
    ("RETURN", r"return"),
    ("FN", r"fn"),          # New function keyword
    ("LET", r"let"),
    ("CONST", r"const"),    # New constant keyword
    ("CAST", r"cast"),      # New cast function
    ("TO_STRING", r"to_string"),
    ("TO_INT", r"to_int"),
    ("TO_FLOAT", r"to_float"),
    ("TO_BOOL", r"to_bool"),
    
    # Type keywords
    ("INT_TYPE", r"int"),
    ("FLOAT_TYPE", r"float"),
    ("BOOL_TYPE", r"bool"),
    ("STRING_TYPE", r"string"),
    ("VOID_TYPE", r"void"),
    
    # Boolean literals
    ("BOOL_LITERAL", r"true|false"),
    
    # Operators
    ("ASSIGN", r"="),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("MULTIPLY", r"\*"),
    ("DIVIDE", r"/"),
    ("MODULO", r"%"),
    ("POWER", r"\*\*"),
    
    # Comparison operators
    ("EQ", r"=="),
    ("NE", r"!="),
    ("LT", r"<"),
    ("LE", r"<="),
    ("GT", r">"),
    ("GE", r">="),
    
    # Logical operators
    ("AND", r"&&"),
    ("OR", r"\|\|"),
    ("NOT", r"!"),
    
    # Literals
    ("STRING", r'"[^"]*"'),
    ("FLOAT", r'-?\d+\.\d+'),     # Float numbers (with decimal point)
    ("INT", r'-?\d+'),            # Integer numbers
    
    # Identifiers and punctuation
    ("IDENT", r'[A-Za-z_][A-Za-z0-9_]*'),
    ("LPAREN", r'\('),
    ("RPAREN", r'\)'),
    ("LBRACE", r'\{'),
    ("RBRACE", r'\}'),
    ("LBRACKET", r'\['),
    ("RBRACKET", r'\]'),
    ("COLON", r':'),
    ("SEMI", r';'),
    ("COMMA", r','),
    ("DOT", r'\.'),
    ("ARROW", r'->'),
    
    # Generic types
    ("LANGLE", r'<'),
    ("RANGLE", r'>'),
    
    # Whitespace and comments
    ("WHITESPACE", r'\s+'),
    ("COMMENT", r'//.*'),
]


def tokenize(code: str) -> List[Tuple[str, str, int, int]]:
    """
    Tokenize code with enhanced type system support
    Returns list of (token_type, value, line, column) tuples
    """
    if not isinstance(code, str):
        raise TypeError("Code must be a string")

    if not code.strip():
        return []

    pos = Position()
    tokens = []
    code_length = len(code)

    while pos.position < code_length:
        match = None
        start_pos = pos.copy()

        # Try to match each token pattern
        for tok_type, pattern in TOKEN_REGEX:
            try:
                regex = re.compile(pattern)
                match = regex.match(code, pos.position)
                if match:
                    text = match.group(0)

                    # Skip whitespace and comments
                    if tok_type not in ("WHITESPACE", "COMMENT"):
                        tokens.append((tok_type, text, start_pos.line, start_pos.column))

                    # Advance position for each character
                    for char in text:
                        pos.advance(char)
                    break
            except re.error as e:
                raise LexerError(f"Invalid regex pattern for {tok_type}: {e}",
                                 pos.position, pos.line, pos.column)

        if not match:
            # Handle unterminated strings
            if code[pos.position] == '"':
                end_pos = pos.position + 1
                while end_pos < code_length and code[end_pos] != '"':
                    end_pos += 1
                if end_pos >= code_length:
                    raise LexerError("Unterminated string literal",
                                     pos.position, pos.line, pos.column)

            # Handle other unknown characters
            char = code[pos.position]
            if char.isprintable():
                error_msg = f"Unexpected character '{char}'"
            else:
                error_msg = f"Unexpected character (ASCII {ord(char)})"

            raise LexerError(error_msg, pos.position, pos.line, pos.column)

    return tokens


def tokenize_with_recovery(code: str) -> Tuple[List[Tuple[str, str, int, int]], List[str]]:
    """
    Tokenize with error recovery - returns tokens and list of errors
    """
    errors = []
    tokens = []

    try:
        tokens = tokenize(code)
    except LexerError as e:
        errors.append(str(e))
        # Try to recover by skipping problematic character
        try:
            # Simple recovery: skip one character and try again
            recovered_code = code[:e.position] + ' ' + code[e.position + 1:]
            tokens, more_errors = tokenize_with_recovery(recovered_code)
            errors.extend(more_errors)
        except:
            pass

    return tokens, errors


def is_numeric_literal(token_type: str) -> bool:
    """Check if token represents a numeric literal"""
    return token_type in ("INT", "FLOAT")


def is_type_keyword(token_type: str) -> bool:
    """Check if token represents a type keyword"""
    return token_type in ("INT_TYPE", "FLOAT_TYPE", "BOOL_TYPE", "STRING_TYPE", "VOID_TYPE")


def is_literal(token_type: str) -> bool:
    """Check if token represents a literal value"""
    return token_type in ("INT", "FLOAT", "STRING", "BOOL_LITERAL")


def is_operator(token_type: str) -> bool:
    """Check if token represents an operator"""
    return token_type in ("PLUS", "MINUS", "MULTIPLY", "DIVIDE", "MODULO", "POWER",
                          "EQ", "NE", "LT", "LE", "GT", "GE", "AND", "OR", "NOT")


def get_operator_precedence(token_type: str) -> int:
    """Get operator precedence for parsing"""
    precedence = {
        "OR": 1,
        "AND": 2,
        "EQ": 3, "NE": 3,
        "LT": 4, "LE": 4, "GT": 4, "GE": 4,
        "PLUS": 5, "MINUS": 5,
        "MULTIPLY": 6, "DIVIDE": 6, "MODULO": 6,
        "POWER": 7,
        "NOT": 8,  # Unary operators have highest precedence
    }
    return precedence.get(token_type, 0)


def is_binary_operator(token_type: str) -> bool:
    """Check if token represents a binary operator"""
    return token_type in ("PLUS", "MINUS", "MULTIPLY", "DIVIDE", "MODULO", "POWER",
                          "EQ", "NE", "LT", "LE", "GT", "GE", "AND", "OR")


def is_unary_operator(token_type: str) -> bool:
    """Check if token represents a unary operator"""
    return token_type in ("MINUS", "NOT")


def token_to_string(token: Tuple[str, str, int, int]) -> str:
    """Convert token to readable string for error messages"""
    tok_type, value, line, col = token
    return f"{tok_type}('{value}') at line {line}, column {col}"
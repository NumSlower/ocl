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


TOKEN_REGEX = [
    ("VERSION", r"@version"),
    ("IMPORT", r"import"),
    ("RETURN", r"return"),
    ("INT", r"int"),
    ("VOID", r"void"),
    ("LET", r"let"),
    ("ASSIGN", r"="),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),  # Added minus operator
    ("STRING", r'"[^"]*"'),
    ("NUMBER", r'-?\d+'),  # Support negative numbers
    ("IDENT", r'[A-Za-z_][A-Za-z0-9_]*'),
    ("LPAREN", r'\('),
    ("RPAREN", r'\)'),
    ("LBRACE", r'\{'),
    ("RBRACE", r'\}'),
    ("SEMI", r';'),
    ("COMMA", r','),
    ("WHITESPACE", r'\s+'),
    ("COMMENT", r'//.*'),
]


def tokenize(code: str) -> List[Tuple[str, str, int, int]]:
    """
    Tokenize code with enhanced error handling
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
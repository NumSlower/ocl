from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class VersionDirective:
    version: str


@dataclass
class Import:
    module: str


@dataclass
class Parameter:
    """Function parameter with type and name"""
    type: str
    name: str


@dataclass
class LetStatement:
    name: str
    value: Union['StringLiteral', 'NumberLiteral', 'Call', 'Variable', 'BinaryOp', 'UnaryOp']


@dataclass
class Program:
    version: Optional[VersionDirective]
    imports: List[Import]
    functions: List['FunctionDef']
    statements: List[LetStatement] = None

    def __post_init__(self):
        if self.statements is None:
            self.statements = []


@dataclass
class FunctionDef:
    name: str
    parameters: List[Parameter]
    body: List[Union['Call', 'Return', 'LetStatement']]
    return_type: str = "int"


@dataclass
class Call:
    name: str
    args: List[Union['StringLiteral', 'NumberLiteral', 'Call', 'Variable', 'BinaryOp', 'UnaryOp']]


@dataclass
class Return:
    value: Optional[Union['StringLiteral', 'NumberLiteral', 'Call', 'Variable', 'BinaryOp', 'UnaryOp']]


@dataclass
class StringLiteral:
    value: str


@dataclass
class NumberLiteral:
    value: int


@dataclass
class Variable:
    name: str


@dataclass
class BinaryOp:
    left: Union['StringLiteral', 'NumberLiteral', 'Call', 'Variable', 'BinaryOp', 'UnaryOp']
    operator: str
    right: Union['StringLiteral', 'NumberLiteral', 'Call', 'Variable', 'BinaryOp', 'UnaryOp']


@dataclass
class UnaryOp:
    operator: str
    operand: Union['StringLiteral', 'NumberLiteral', 'Call', 'Variable', 'BinaryOp', 'UnaryOp']
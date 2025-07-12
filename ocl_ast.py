from dataclasses import dataclass
from typing import List, Optional, Union, Dict, Any
from enum import Enum


class OCLType(Enum):
    """OCL type system enumeration"""
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    VOID = "void"
    UNKNOWN = "unknown"
    
    def __str__(self):
        return self.value
    
    def is_numeric(self) -> bool:
        """Check if type is numeric (int or float)"""
        return self in (OCLType.INT, OCLType.FLOAT)
    
    def is_compatible_with(self, other: 'OCLType') -> bool:
        """Check if this type is compatible with another for operations"""
        if self == other:
            return True
        # Allow int/float compatibility for arithmetic
        if self.is_numeric() and other.is_numeric():
            return True
        return False


@dataclass
class TypeAnnotation:
    """Type annotation for variables and expressions"""
    type: OCLType
    is_const: bool = False
    generic_params: Optional[List['TypeAnnotation']] = None
    
    def __str__(self):
        return str(self.type)


@dataclass
class VersionDirective:
    version: str


@dataclass
class Import:
    module: str


@dataclass
class Parameter:
    """Function parameter with type and name"""
    name: str
    type_annotation: TypeAnnotation
    
    def __str__(self):
        return f"{self.name}: {self.type_annotation}"


@dataclass
class VariableDeclaration:
    """Variable declaration with explicit type"""
    name: str
    type_annotation: TypeAnnotation
    initial_value: Optional[Union['Expression']] = None
    is_const: bool = False
    
    def __str__(self):
        const_str = "const " if self.is_const else "let "
        return f"{const_str}{self.name}: {self.type_annotation}"


@dataclass
class Program:
    version: Optional[VersionDirective]
    imports: List[Import]
    functions: List['FunctionDef']
    global_declarations: List[VariableDeclaration]
    
    def __post_init__(self):
        if self.global_declarations is None:
            self.global_declarations = []


@dataclass
class FunctionDef:
    name: str
    parameters: List[Parameter]
    return_type: TypeAnnotation
    body: List[Union['Statement']]
    
    def __str__(self):
        params_str = ", ".join(str(p) for p in self.parameters)
        return f"fn {self.name}({params_str}): {self.return_type}"


# Base classes for AST nodes
@dataclass
class ASTNode:
    """Base class for all AST nodes"""
    line: int = 0
    column: int = 0
    
    def set_position(self, line: int, column: int):
        self.line = line
        self.column = column


@dataclass
class Expression(ASTNode):
    """Base class for all expressions"""
    inferred_type: Optional[TypeAnnotation] = None
    
    def get_type(self) -> TypeAnnotation:
        """Get the type of this expression"""
        if self.inferred_type is None:
            return TypeAnnotation(OCLType.UNKNOWN)
        return self.inferred_type
    
    def set_type(self, type_annotation: TypeAnnotation):
        """Set the inferred type of this expression"""
        self.inferred_type = type_annotation


@dataclass
class Statement(ASTNode):
    """Base class for all statements"""
    pass


# Expressions
@dataclass
class StringLiteral(Expression):
    value: str
    
    def __post_init__(self):
        self.set_type(TypeAnnotation(OCLType.STRING))


@dataclass
class IntLiteral(Expression):
    value: int
    
    def __post_init__(self):
        self.set_type(TypeAnnotation(OCLType.INT))


@dataclass
class FloatLiteral(Expression):
    value: float
    
    def __post_init__(self):
        self.set_type(TypeAnnotation(OCLType.FLOAT))


@dataclass
class BoolLiteral(Expression):
    value: bool
    
    def __post_init__(self):
        self.set_type(TypeAnnotation(OCLType.BOOL))


@dataclass
class Variable(Expression):
    name: str
    # Type will be set during type checking phase


@dataclass
class BinaryOp(Expression):
    left: Expression
    operator: str
    right: Expression
    
    def get_result_type(self) -> TypeAnnotation:
        """Get the result type of binary operation"""
        left_type = self.left.get_type().type
        right_type = self.right.get_type().type
        
        # Arithmetic operations
        if self.operator in ["+", "-", "*", "/", "%", "**"]:
            if left_type == OCLType.FLOAT or right_type == OCLType.FLOAT:
                return TypeAnnotation(OCLType.FLOAT)
            elif left_type == OCLType.INT and right_type == OCLType.INT:
                return TypeAnnotation(OCLType.INT)
            elif left_type == OCLType.STRING and right_type == OCLType.STRING and self.operator == "+":
                return TypeAnnotation(OCLType.STRING)
        
        # Comparison operations
        elif self.operator in ["==", "!=", "<", "<=", ">", ">=", "&&", "||"]:
            return TypeAnnotation(OCLType.BOOL)
        
        return TypeAnnotation(OCLType.UNKNOWN)


@dataclass
class UnaryOp(Expression):
    operator: str
    operand: Expression
    
    def get_result_type(self) -> TypeAnnotation:
        """Get the result type of unary operation"""
        operand_type = self.operand.get_type().type
        
        if self.operator == "-":
            if operand_type in [OCLType.INT, OCLType.FLOAT]:
                return TypeAnnotation(operand_type)
        elif self.operator == "!":
            return TypeAnnotation(OCLType.BOOL)
        
        return TypeAnnotation(OCLType.UNKNOWN)


@dataclass
class FunctionCall(Expression):
    name: str
    args: List[Expression]
    # Type will be determined during type checking


@dataclass
class CastExpression(Expression):
    target_type: TypeAnnotation
    expression: Expression
    
    def __post_init__(self):
        self.set_type(self.target_type)


@dataclass
class TypeConversion(Expression):
    """Type conversion functions like to_string, to_int, etc."""
    function_name: str  # to_string, to_int, to_float, to_bool
    expression: Expression
    
    def get_result_type(self) -> TypeAnnotation:
        """Get the result type of type conversion"""
        type_map = {
            "to_string": OCLType.STRING,
            "to_int": OCLType.INT,
            "to_float": OCLType.FLOAT,
            "to_bool": OCLType.BOOL,
        }
        result_type = type_map.get(self.function_name, OCLType.UNKNOWN)
        return TypeAnnotation(result_type)


# Statements
@dataclass
class ExpressionStatement(Statement):
    expression: Expression


@dataclass
class VariableAssignment(Statement):
    name: str
    value: Expression
    declared_type: Optional[TypeAnnotation] = None  # For type checking


@dataclass
class ReturnStatement(Statement):
    value: Optional[Expression] = None
    expected_type: Optional[TypeAnnotation] = None  # For type checking


@dataclass
class IfStatement(Statement):
    condition: Expression
    then_branch: List[Statement]
    else_branch: Optional[List[Statement]] = None


@dataclass
class WhileStatement(Statement):
    condition: Expression
    body: List[Statement]


@dataclass
class ForStatement(Statement):
    init: Optional[Statement]
    condition: Optional[Expression]
    update: Optional[Statement]
    body: List[Statement]


@dataclass
class BlockStatement(Statement):
    statements: List[Statement]


# Type checking utilities
class TypeChecker:
    """Utility class for type checking operations"""
    
    @staticmethod
    def can_cast(from_type: OCLType, to_type: OCLType) -> bool:
        """Check if one type can be cast to another"""
        if from_type == to_type:
            return True
        
        # Numeric conversions
        if from_type.is_numeric() and to_type.is_numeric():
            return True
        
        # String conversions
        if to_type == OCLType.STRING:
            return True  # Everything can be converted to string
        
        # Boolean conversions
        if to_type == OCLType.BOOL:
            return True  # Everything can be converted to bool
        
        # Int/Float to numeric
        if from_type == OCLType.STRING and to_type.is_numeric():
            return True  # String can be parsed to numeric (runtime check)
        
        return False
    
    @staticmethod
    def get_binary_op_result_type(left: OCLType, op: str, right: OCLType) -> OCLType:
        """Get the result type of a binary operation"""
        # Arithmetic operations
        if op in ["+", "-", "*", "/", "%", "**"]:
            if left == OCLType.FLOAT or right == OCLType.FLOAT:
                return OCLType.FLOAT
            elif left == OCLType.INT and right == OCLType.INT:
                return OCLType.INT
            elif left == OCLType.STRING and right == OCLType.STRING and op == "+":
                return OCLType.STRING
        
        # Comparison operations
        elif op in ["==", "!=", "<", "<=", ">", ">=", "&&", "||"]:
            return OCLType.BOOL
        
        return OCLType.UNKNOWN
    
    @staticmethod
    def get_unary_op_result_type(op: str, operand: OCLType) -> OCLType:
        """Get the result type of a unary operation"""
        if op == "-":
            if operand in [OCLType.INT, OCLType.FLOAT]:
                return operand
        elif op == "!":
            return OCLType.BOOL
        
        return OCLType.UNKNOWN
    
    @staticmethod
    def are_types_compatible(type1: OCLType, type2: OCLType) -> bool:
        """Check if two types are compatible for operations"""
        if type1 == type2:
            return True
        
        # Numeric compatibility
        if type1.is_numeric() and type2.is_numeric():
            return True
        
        return False


# Built-in function signatures
BUILTIN_FUNCTIONS = {
    # Math functions
    "add": {"params": [OCLType.INT, OCLType.INT], "return": OCLType.INT},
    "sub": {"params": [OCLType.INT, OCLType.INT], "return": OCLType.INT},
    "mul": {"params": [OCLType.INT, OCLType.INT], "return": OCLType.INT},
    "div": {"params": [OCLType.INT, OCLType.INT], "return": OCLType.INT},
    "mod": {"params": [OCLType.INT, OCLType.INT], "return": OCLType.INT},
    "pow": {"params": [OCLType.INT, OCLType.INT], "return": OCLType.INT},
    "abs": {"params": [OCLType.INT], "return": OCLType.INT},
    "sqrt": {"params": [OCLType.FLOAT], "return": OCLType.FLOAT},
    "sin": {"params": [OCLType.FLOAT], "return": OCLType.FLOAT},
    "cos": {"params": [OCLType.FLOAT], "return": OCLType.FLOAT},
    "tan": {"params": [OCLType.FLOAT], "return": OCLType.FLOAT},
    "log": {"params": [OCLType.FLOAT], "return": OCLType.FLOAT},
    "ln": {"params": [OCLType.FLOAT], "return": OCLType.FLOAT},
    "exp": {"params": [OCLType.FLOAT], "return": OCLType.FLOAT},
    "floor": {"params": [OCLType.FLOAT], "return": OCLType.INT},
    "ceil": {"params": [OCLType.FLOAT], "return": OCLType.INT},
    "round": {"params": [OCLType.FLOAT], "return": OCLType.INT},
    "min": {"params": [OCLType.FLOAT, OCLType.FLOAT], "return": OCLType.FLOAT},
    "max": {"params": [OCLType.FLOAT, OCLType.FLOAT], "return": OCLType.FLOAT},
    
    # String functions
    "print": {"params": [], "return": OCLType.VOID, "variadic": True},
    "println": {"params": [], "return": OCLType.VOID, "variadic": True},
    "len": {"params": [OCLType.STRING], "return": OCLType.INT},
    "substr": {"params": [OCLType.STRING, OCLType.INT, OCLType.INT], "return": OCLType.STRING},
    "upper": {"params": [OCLType.STRING], "return": OCLType.STRING},
    "lower": {"params": [OCLType.STRING], "return": OCLType.STRING},
    
    # Time functions
    "time": {"params": [], "return": OCLType.STRING},
    "timestamp": {"params": [], "return": OCLType.STRING},
    "datetime": {"params": [], "return": OCLType.STRING},
    "date": {"params": [], "return": OCLType.STRING},
    "sleep": {"params": [OCLType.FLOAT], "return": OCLType.VOID},
    
    # Type conversion functions
    "to_string": {"params": [], "return": OCLType.STRING, "variadic": True},
    "to_int": {"params": [OCLType.STRING], "return": OCLType.INT},
    "to_float": {"params": [OCLType.STRING], "return": OCLType.FLOAT},
    "to_bool": {"params": [], "return": OCLType.BOOL, "variadic": True},
    
    # Cast function
    "cast": {"params": [], "return": OCLType.UNKNOWN, "special": True},
}


# Built-in constants
BUILTIN_CONSTANTS = {
    "pi": TypeAnnotation(OCLType.FLOAT, is_const=True),
    "e": TypeAnnotation(OCLType.FLOAT, is_const=True),
    "true": TypeAnnotation(OCLType.BOOL, is_const=True),
    "false": TypeAnnotation(OCLType.BOOL, is_const=True),
}
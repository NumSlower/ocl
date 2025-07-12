import math as pymath

def register(env):
    # Arithmetic
    env["add"] = lambda a, b: a + b
    env["sub"] = lambda a, b: a - b
    env["mul"] = lambda a, b: a * b
    env["div"] = lambda a, b: a / b if b != 0 else 0
    env["mod"] = lambda a, b: a % b
    env["pow"] = lambda a, b: a ** b

    # Unary
    env["neg"] = lambda x: -x
    env["abs"] = abs

    # Comparison
    env["min"] = min
    env["max"] = max

    # Math functions
    env["sqrt"] = pymath.sqrt
    env["log"] = pymath.log10
    env["ln"] = pymath.log
    env["exp"] = pymath.exp
    env["floor"] = pymath.floor
    env["ceil"] = pymath.ceil
    env["round"] = round

    # Trigonometry
    env["sin"] = pymath.sin
    env["cos"] = pymath.cos
    env["tan"] = pymath.tan
    env["asin"] = pymath.asin
    env["acos"] = pymath.acos
    env["atan"] = pymath.atan

    # Constants
    env["pi"] = pymath.pi
    env["e"] = pymath.e

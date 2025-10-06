from mcp.server.fastmcp import FastMCP
import math
import re
from typing import Union

mcp = FastMCP("math")

@mcp.tool()
def calculate(expression: str) -> Union[float, int, str]:
    """
    Evaluates any mathematical expression provided as a string.
    
    Supports:
    - Basic operations: +, -, *, /, //, %, **
    - Parentheses for grouping
    - Mathematical functions: sin, cos, tan, sqrt, log, log10, exp, abs, ceil, floor, etc.
    - Constants: pi, e
    - Trigonometric functions (use radians)
    
    Examples:
    - "2 + 2"
    - "sqrt(16) + 5"
    - "sin(pi/2)"
    - "log(100, 10)"
    - "(5 + 3) * 2 ** 3"
    
    Args:
        expression: A mathematical expression as a string
        
    Returns:
        The calculated result or an error message
    """
    try:
        # Create a safe namespace with math functions
        safe_dict = {
            # Math functions
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'atan2': math.atan2,
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
            'sqrt': math.sqrt,
            'log': math.log,
            'log10': math.log10,
            'log2': math.log2,
            'exp': math.exp,
            'abs': abs,
            'pow': pow,
            'ceil': math.ceil,
            'floor': math.floor,
            'round': round,
            'max': max,
            'min': min,
            'sum': sum,
            'factorial': math.factorial,
            'gcd': math.gcd,
            'lcm': math.lcm,
            'degrees': math.degrees,
            'radians': math.radians,
            # Constants
            'pi': math.pi,
            'e': math.e,
            'tau': math.tau,
            'inf': math.inf,
            'nan': math.nan,
        }
        
        # Evaluate the expression safely
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        
        # Return as int if it's a whole number, otherwise float
        if isinstance(result, float) and result.is_integer():
            return int(result)
        return result
        
    except ZeroDivisionError:
        return "Error: Division by zero"
    except SyntaxError:
        return "Error: Invalid syntax in expression"
    except NameError as e:
        return f"Error: Unknown function or variable - {str(e)}"
    except TypeError as e:
        return f"Error: Type error - {str(e)}"
    except ValueError as e:
        return f"Error: Value error - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """
    Multiplies two integers.
    
    Args:
        a: First integer
        b: Second integer
        
    Returns:
        The product of a and b
    """
    return a * b


@mcp.tool()
def add(a: float, b: float) -> float:
    """
    Adds two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The sum of a and b
    """
    return a + b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """
    Subtracts b from a.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The difference (a - b)
    """
    return a - b


@mcp.tool()
def divide(a: float, b: float) -> Union[float, str]:
    """
    Divides a by b.
    
    Args:
        a: Numerator
        b: Denominator
        
    Returns:
        The quotient (a / b) or error message if division by zero
    """
    if b == 0:
        return "Error: Division by zero"
    return a / b


@mcp.tool()
def power(base: float, exponent: float) -> float:
    """
    Calculates base raised to the power of exponent.
    
    Args:
        base: The base number
        exponent: The exponent
        
    Returns:
        base ** exponent
    """
    return base ** exponent


@mcp.tool()
def square_root(n: float) -> Union[float, str]:
    """
    Calculates the square root of a number.
    
    Args:
        n: The number to find square root of
        
    Returns:
        The square root of n or error message if n is negative
    """
    if n < 0:
        return "Error: Cannot calculate square root of negative number"
    return math.sqrt(n)


@mcp.tool()
def factorial(n: int) -> Union[int, str]:
    """
    Calculates the factorial of a non-negative integer.
    
    Args:
        n: A non-negative integer
        
    Returns:
        n! (factorial of n) or error message
    """
    if n < 0:
        return "Error: Factorial not defined for negative numbers"
    if n > 1000:
        return "Error: Number too large for factorial calculation"
    return math.factorial(n)


@mcp.tool()
def solve_quadratic(a: float, b: float, c: float) -> Union[dict, str]:
    """
    Solves quadratic equation ax² + bx + c = 0.
    
    Args:
        a: Coefficient of x²
        b: Coefficient of x
        c: Constant term
        
    Returns:
        Dictionary with solutions or error message
    """
    if a == 0:
        return "Error: 'a' cannot be zero in a quadratic equation"
    
    discriminant = b**2 - 4*a*c
    
    if discriminant > 0:
        x1 = (-b + math.sqrt(discriminant)) / (2*a)
        x2 = (-b - math.sqrt(discriminant)) / (2*a)
        return {
            "solution_type": "Two real solutions",
            "x1": x1,
            "x2": x2
        }
    elif discriminant == 0:
        x = -b / (2*a)
        return {
            "solution_type": "One real solution",
            "x": x
        }
    else:
        real_part = -b / (2*a)
        imaginary_part = math.sqrt(abs(discriminant)) / (2*a)
        return {
            "solution_type": "Two complex solutions",
            "x1": f"{real_part} + {imaginary_part}i",
            "x2": f"{real_part} - {imaginary_part}i"
        }


@mcp.tool()
def percentage(value: float, total: float) -> Union[float, str]:
    """
    Calculates what percentage 'value' is of 'total'.
    
    Args:
        value: The value to calculate percentage for
        total: The total amount
        
    Returns:
        Percentage value or error message
    """
    if total == 0:
        return "Error: Total cannot be zero"
    return (value / total) * 100


@mcp.tool()
def trigonometry(function: str, angle: float, unit: str = "radians") -> Union[float, str]:
    """
    Calculates trigonometric functions.
    
    Args:
        function: One of 'sin', 'cos', 'tan', 'asin', 'acos', 'atan'
        angle: The angle value
        unit: 'radians' or 'degrees' (default is radians)
        
    Returns:
        The calculated trigonometric value or error message
    """
    try:
        if unit.lower() == "degrees":
            angle = math.radians(angle)
        
        functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan
        }
        
        if function.lower() not in functions:
            return f"Error: Unknown function '{function}'. Use: sin, cos, tan, asin, acos, atan"
        
        result = functions[function.lower()](angle)
        
        # For inverse trig functions, convert back to degrees if requested
        if unit.lower() == "degrees" and function.lower() in ['asin', 'acos', 'atan']:
            result = math.degrees(result)
            
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
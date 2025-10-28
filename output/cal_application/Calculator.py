class Calculator:
    def add(self, a: float, b: float) -> float:
        """
        Adds two numbers.

        Parameters:
        - a: float - The first number to add.
        - b: float - The second number to add.

        Returns:
        float - The sum of the two numbers.
        """
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        """
        Subtracts the second number from the first.

        Parameters:
        - a: float - The number from which to subtract.
        - b: float - The number to subtract.

        Returns:
        float - The result of the subtraction.
        """
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        """
        Multiplies two numbers.

        Parameters:
        - a: float - The first number to multiply.
        - b: float - The second number to multiply.

        Returns:
        float - The product of the two numbers.
        """
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        """
        Divides the first number by the second.

        Parameters:
        - a: float - The numerator.
        - b: float - The denominator.

        Returns:
        float - The result of the division.

        Raises:
        ValueError: If b is zero, because division by zero is not allowed.
        """
        if b == 0:
            raise ValueError("Division by zero is not allowed.")
        return a / b
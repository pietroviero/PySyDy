"""
Defines the Auxiliary class for PySyDy library.
"""

class Auxiliary:
    """
    Represents an auxiliary variable in a system dynamics model.

    Auxiliary variables are calculated based on stocks, flows,
    parameters, or other auxiliary variables. They help simplify
    complex relationships and improve model readability.
    """

    def __init__(self, name, calculation_function, inputs=None):
        """
        Initializes an Auxiliary object.

        :param name: The name of the auxiliary variable.
        :type name: str
        :param calculation_function: A function that calculates the auxiliary variable's value.
                                     It should take the current system state
                                     (e.g., a dictionary of stocks, auxiliaries, parameters) as input
                                     and return the calculated value.
        :type calculation_function: callable
        :param inputs: (Optional) A list of input variables (names of stocks, flows, or other auxiliaries)
                       that this auxiliary variable depends on. This is for documentation and potential
                       dependency tracking, but not strictly enforced in the calculation itself.
        :type inputs: list of str, optional
        """
        self.name = name
        self.calculation_function = calculation_function
        self.inputs = inputs if inputs is not None else [] # Store input names for documentation
        self.value = None # Will be calculated in each simulation step

    def calculate_value(self, system_state):
        """
        Calculates the value of the auxiliary variable using its calculation function.

        :param system_state: A dictionary or object representing the current state of the system.
        :type system_state: dict or object
        """
        self.value = self.calculation_function(system_state)

    def get_value(self):
        """
        Returns the current value of the auxiliary variable.

        :returns: The current value.
        :rtype: float or any
        """
        return self.value

    def __str__(self):
        return f"Auxiliary(name='{self.name}', value={self.value})"
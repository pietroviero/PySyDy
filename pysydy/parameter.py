"""
Defines the Parameter class for PySyDy library.
"""

from units import units


class Parameter:
    """
    Represents a parameter (constant value) in a system dynamics model.

    Parameters are used in calculations within flows and auxiliary variables.
    """

    def __init__(self, name, value, description=None, unit=None):
        """
        Initializes a Parameter object.

        :param name: The name of the parameter.
        :type name: str
        :param value: The numerical value of the parameter.
        :type value: float or int
        :param units: (Optional) Units of measurement for the parameter (e.g., "square kilometers", "per year").
        :type units: str, optional
        :param description: (Optional) A description of what the parameter represents.
        :type description: str, optional
        """
        self.name = name
        self.value = units.get_quantity(value, unit)
        self.description = description
        self.unit = units.ureg(unit) if unit else None

    def get_value(self):
        """
        Returns the value of the parameter.

        :returns: The parameter's value.
        :rtype: float or int
        """
        return units.format_quantity(self.value)

    def __str__(self):
        unit_str = f" (units='{self.units}')" if self.units else ""
        desc_str = f", description='{self.description}'" if self.description else ""
        return f"Parameter(name='{self.name}', value={float(self.value)}{unit_str}{desc_str})" # Cast value to float for string representation

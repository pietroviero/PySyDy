"""
Defines the Parameter class for PySyDy library.
"""

from units import units
ureg = units.ureg
Q_ = ureg.Quantity

class Parameter:
    """
    Represents a parameter (constant value) in a system dynamics model.

    Parameters are used in calculations within flows and auxiliary variables.
    """

    def __init__(self, name, value=1.0, description=None, unit=None):
        """
        Initializes a Parameter object.

        :param name: Name of the parameter.
        :param value: The numerical value of the parameter.
        :param description: Description of what the parameter represents.
        :param unit: Units of measurement (e.g., "people", "1/day").
        """
        self.name = name
        self.description = description

        # Normalize unit
        if unit is None:
            self.unit = ureg.dimensionless
        elif isinstance(unit, str):
            if unit.strip().lower() in {"1", "dimensionless"}:
                self.unit = ureg.dimensionless
            else:
                self.unit = ureg.parse_expression(unit).units
        else:
            self.unit = getattr(unit, "units", unit)

        # Wrap the value
        self.value = value if isinstance(value, Q_) else Q_(value, self.unit)


    def get_value(self):
        """
        Returns the value of the parameter.

        :returns: The parameter's value.
        :rtype: float or int
        """
        return units.format_quantity(self.value)

    def __str__(self):
        unit_str = f" (units='{self.unit}')" if self.unit else ""
        desc_str = f", description='{self.description}'" if self.description else ""
        return f"Parameter(name='{self.name}', value={float(self.value)}, {unit_str}{desc_str})" # Cast value to float for string representation
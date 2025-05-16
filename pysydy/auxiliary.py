"""
Defines the Auxiliary class for PySyDy library.
"""
from units import units

ureg = units.ureg
Q_ = ureg.Quantity


class Auxiliary:
    """
    Represents an auxiliary variable in a system dynamics model.

    An auxiliary is a calculated value that depends on other variables in the system.
    """

    def __init__(self, name, calculation_function=None, unit=None, inputs=None):
        """
        Initializes an Auxiliary object.

        :param name: The name of the auxiliary variable.
        :param calculation_function: Function that calculates the value of the auxiliary.
        :param unit: Unit of the calculated value (string or Quantity unit).
        """
        if not callable(calculation_function) or calculation_function is None:
            raise TypeError("calculation_function must be callable")

        self.name = name
        self.calculation_function = calculation_function
        self.value = 0.0
        self.inputs = inputs if inputs is not None else []  # Store input names for documentation

        # Normalize unit
        if unit is None:
            self.unit = ureg.dimensionless
        elif isinstance(unit, str):
            if unit.strip().lower() in {"1", "0", "dimensionless"}:
                self.unit = ureg.dimensionless
            else:
                self.unit = ureg.parse_expression(unit).units
        else:
            self.unit = getattr(unit, "units", unit)

    def calculate_value(self, system_state):
        """
        Calculates the value of the auxiliary using the calculation function.
        Wraps result in Quantity and checks dimensionality.
        """
        raw = self.calculation_function(system_state)

        if isinstance(raw, Q_):
            self.value = raw
        else:
            self.value = Q_(raw, self.unit)

        if self.unit and self.value.dimensionality != self.unit.dimensionality:
            raise ValueError(
                f"[UNIT ERROR] Auxiliary '{self.name}': returned {self.value} "
                f"but declared unit is '{self.unit}'"
            )

        return self.value

    def get_value(self):
        """
        Returns the current value of the auxiliary.
        """
        return self.value

    def __str__(self):
        return f"Auxiliary(name='{self.name}', value={self.value})"

"""
Defines the Flow class for PySyDy library.
"""
from units import units
from pint import Quantity

ureg = units.ureg
Q_ = ureg.Quantity

class Flow:
    """
    Represents a flow in a system dynamics model.
    A flow is a rate variable that changes the level of stocks over time.
    """

    def __init__(self, name, source_stock, target_stock, rate_function, unit=None):
        """
        Initializes a Flow object.

        :param name: The name of the flow.
        :param source_stock: The stock that the flow originates from (can be None).
        :param target_stock: The stock that the flow goes to (can be None).
        :param rate_function: A function that calculates the flow rate.
                              It should take the current state of the system
                              (e.g., stocks' values) as input and return the flow rate.
        :param unit: The expected unit of the flow (e.g., "people/day").
        """
        self.name = name
        self.source_stock = source_stock
        self.target_stock = target_stock
        self.rate_function = rate_function
        self.rate = 0.0  # Current flow rate, updated in each simulation step

        if unit is None:
            self.unit = ureg.dimensionless
        elif isinstance(unit, str):
            if unit.strip().lower() in {"1", "0", "dimensionless"}:
                self.unit = ureg.dimensionless
            else:
                self.unit = ureg.parse_expression(unit).units
        else:
            self.unit = getattr(unit, "units", unit)

        if source_stock:
            source_stock.add_outflow(self)
        if target_stock:
            target_stock.add_inflow(self)

    def calculate_rate(self, system_state):
        """
        Calculates the flow rate using the rate function.
        Wraps result in Quantity and checks dimensionality.
        """
        raw = self.rate_function(system_state)

        if isinstance(raw, Quantity):
            self.rate = raw
        else:
            self.rate = Q_(raw, self.unit)

        if self.unit and self.rate.dimensionality != self.unit.dimensionality:
            raise ValueError(
                f"[UNIT ERROR] Flow '{self.name}': returned {self.rate} "
                f"but declared unit is '{self.unit}'"
            )

        return self.rate

    def get_rate(self):
        """
        Returns the current flow rate (formatted).
        """
        return f"Flow formula: {self.rate} [{self.unit}]"

    def __str__(self):
        return f"Flow(name='{self.name}', rate={self.rate})"

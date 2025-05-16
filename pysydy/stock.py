"""
Defines the Stock class for PySyDy library.
"""
from units import units
ureg = units.ureg
Q_ = ureg.Quantity


class Stock:
    """
    Represents a stock in a system dynamics model.

    A stock is a level variable that accumulates or depletes over time
    due to flows.
    """

    def __init__(self, name, initial_value=0.0, unit = None):
        """
               Initializes a Stock object.

               :param name: The name of the stock.
               :param initial_value: The initial value (scalar or Quantity).
               :param unit: The unit of the stock (string or Quantity-compatible).
               """
        self.name = name

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

        # Wrap initial value
        if isinstance(initial_value, Q_):
            self.initial_value = initial_value
        else:
            self.initial_value = Q_(initial_value, self.unit)

        self.value = self.initial_value
        self.inflows = []
        self.outflows = []

    def add_inflow(self, flow):
        """
        Adds an inflow to the stock.

        :param flow: The flow object to add as an inflow.
        :type flow: Flow
        """
        self.inflows.append(flow)

    def add_outflow(self, flow):
        """
        Adds an outflow to the stock.

        :param flow: The flow object to add as an outflow.
        :type flow: Flow
        """
        self.outflows.append(flow)

    def update(self, timestep):
        """
        Updates the stock's value based on its inflows and outflows.

        :param timestep: The time interval for the update.
        :type timestep: float
        """
        net_flow = 0.0
        for inflow in self.inflows:
            net_flow += inflow.rate
        for outflow in self.outflows:
            net_flow -= outflow.rate
        self.value += net_flow * timestep

    def get_value(self):
        """
        Returns the current value of the stock.

        :returns: The current value of the stock.
        :rtype: float
        """
        return units.format_quantity(self.initial_value)

    def __str__(self):
        return f"Stock(name='{self.name}', value={self.value:.1f})"
"""
Defines the Stock class for PySyDy library.
"""
from units import units

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
        :type name: str
        :param initial_value: The initial value of the stock.
        :type initial_value: float, optional
        """
        self.name = name
        self.initial_value = units.get_quantity(initial_value, unit)
        self.value = self.initial_value
        self.inflows = []
        self.outflows = []
        self.unit = units.ureg(unit) if unit else None

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

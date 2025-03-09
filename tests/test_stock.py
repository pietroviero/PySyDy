# tests/test_stock.py
import unittest
from pysydy.stock import Stock
from pysydy.flow import Flow  # We might need Flow for stock tests indirectly

class TestStock(unittest.TestCase):

    def test_stock_creation(self):
        """Test basic stock creation and initial values."""
        stock = Stock(name="TestStock", initial_value=100.0)
        self.assertEqual(stock.name, "TestStock")
        self.assertEqual(stock.value, 100.0)
        self.assertEqual(stock.inflows, [])
        self.assertEqual(stock.outflows, [])

    def test_add_inflow_outflow(self):
        """Test adding inflows and outflows to a stock."""
        stock = Stock(name="TestStock")
        inflow1 = Flow(name="Inflow1", source_stock=None, target_stock=stock, rate_function=lambda state: 10)
        outflow1 = Flow(name="Outflow1", source_stock=stock, target_stock=None, rate_function=lambda state: 5)

        stock.add_inflow(inflow1)
        stock.add_outflow(outflow1)

        self.assertIn(inflow1, stock.inflows)
        self.assertIn(outflow1, stock.outflows)

    def test_update_stock_value(self):
        """Test updating stock value based on inflows and outflows."""
        stock = Stock(name="TestStock", initial_value=50.0)
        inflow1 = Flow(name="Inflow1", source_stock=None, target_stock=stock, rate_function=lambda state: 10)
        outflow1 = Flow(name="Outflow1", source_stock=stock, target_stock=None, rate_function=lambda state: 5)
        # Remove the following two lines - they are redundant and cause double addition
        # stock.add_inflow(inflow1)
        # stock.add_outflow(outflow1)

        # Calculate flow rates BEFORE updating stock
        system_state = {} # System state is not used in these simple rate functions
        inflow1.calculate_rate(system_state)
        outflow1.calculate_rate(system_state)

        stock.update(timestep=1.0)
        self.assertEqual(stock.get_value(), 55.0)  # 50 + (10 - 5) * 1

        # Calculate flow rates AGAIN before the next update
        inflow1.calculate_rate(system_state)
        outflow1.calculate_rate(system_state)
        stock.update(timestep=0.5)
        self.assertEqual(stock.get_value(), 57.5) # 55 + (10 - 5) * 0.5

    def test_get_value(self):
        """Test getting the stock's value."""
        stock = Stock(name="TestStock", initial_value=25.0)
        self.assertEqual(stock.get_value(), 25.0)
        stock.value = 75.0 # Directly change value for test
        self.assertEqual(stock.get_value(), 75.0)

    def test_stock_str_representation(self):
        """Test the string representation of a stock."""
        stock = Stock(name="ResourceStock", initial_value=100)
        self.assertEqual(str(stock), "Stock(name='ResourceStock', value=100.0)")


if __name__ == '__main__':
    unittest.main()
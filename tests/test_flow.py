# tests/test_flow.py
import unittest
from pysydy.stock import Stock
from pysydy.flow import Flow

class TestFlow(unittest.TestCase):

    def test_flow_creation(self):
        """Test basic flow creation and attributes."""
        source_stock = Stock(name="SourceStock")
        target_stock = Stock(name="TargetStock")
        rate_func = lambda state: 20  # Simple constant rate function
        flow = Flow(name="TestFlow", source_stock=source_stock, target_stock=target_stock, rate_function=rate_func)

        self.assertEqual(flow.name, "TestFlow")
        self.assertEqual(flow.source_stock, source_stock)
        self.assertEqual(flow.target_stock, target_stock)
        self.assertEqual(flow.rate_function, rate_func)
        self.assertEqual(flow.rate, 0.0) # Initial rate should be 0

        self.assertIn(flow, source_stock.outflows) # Flow should be added to source outflow
        self.assertIn(flow, target_stock.inflows)   # Flow should be added to target inflow

    def test_flow_creation_no_source_target(self):
        """Test flow creation without source or target stocks (source/sink flows)."""
        rate_func = lambda state: 5
        source_flow = Flow(name="SourceFlow", source_stock=None, target_stock=Stock(name="Target"), rate_function=rate_func)
        sink_flow = Flow(name="SinkFlow", source_stock=Stock(name="Source"), target_stock=None, rate_function=rate_func)

        self.assertIsNone(source_flow.source_stock)
        self.assertIsNone(sink_flow.target_stock)

    def test_calculate_rate(self):
        """Test calculating flow rate using the rate function."""
        source_stock = Stock(name="SourceStock", initial_value=100)
        target_stock = Stock(name="TargetStock", initial_value=0)
        def rate_func(state):
            return state['SourceStock'].get_value() * 0.1 # Rate depends on source stock

        flow = Flow(name="TestFlow", source_stock=source_stock, target_stock=target_stock, rate_function=rate_func)
        system_state = {'SourceStock': source_stock, 'TargetStock': target_stock}

        flow.calculate_rate(system_state)
        self.assertEqual(flow.get_rate(), 10.0) # Rate should be 100 * 0.1 = 10

        source_stock.value = 50 # Change source stock value
        flow.calculate_rate(system_state)
        self.assertEqual(flow.get_rate(), 5.0)  # Rate should now be 50 * 0.1 = 5

    def test_get_rate(self):
        """Test getting the flow rate."""
        rate_func = lambda state: 15
        flow = Flow(name="TestFlow", source_stock=None, target_stock=None, rate_function=rate_func)
        system_state = {} # Rate function doesn't depend on state in this test
        flow.calculate_rate(system_state) # Calculate rate to set flow.rate
        self.assertEqual(flow.get_rate(), 15.0)

    def test_flow_str_representation(self):
        """Test the string representation of a flow."""
        flow = Flow(name="BirthFlow", source_stock=None, target_stock=Stock(name="Population"), rate_function=lambda state: 20)
        system_state = {}
        flow.calculate_rate(system_state) # Calculate rate to set flow.rate for string representation
        self.assertEqual(str(flow), "Flow(name='BirthFlow', rate=20.0)")


if __name__ == '__main__':
    unittest.main()
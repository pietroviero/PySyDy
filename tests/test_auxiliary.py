import unittest
from pysydy.auxiliary import Auxiliary

class TestAuxiliary(unittest.TestCase):

    def test_auxiliary_creation(self):
        """Test basic auxiliary variable creation."""
        def calc_func(state): return state['input_val'] * 2

        aux = Auxiliary(name="TestAux", calculation_function=calc_func, inputs=['input_val'])
        self.assertEqual(aux.name, "TestAux")
        self.assertEqual(aux.calculation_function, calc_func)
        self.assertEqual(aux.inputs, ['input_val'])
        self.assertIsNone(aux.value) # Value is initially None

    def test_calculate_value_and_get_value(self):
        """Test calculating and getting auxiliary variable value."""
        def calc_func(state): return state['stock_val'].get_value() * 0.5

        aux = Auxiliary(name="TestAux", calculation_function=calc_func, inputs=['stock_val'])
        stock = MockStock(name="MockStock", value=100) # Use MockStock for testing

        system_state = {'stock_val': stock}
        aux.calculate_value(system_state)
        self.assertEqual(aux.get_value(), 50.0) # 100 * 0.5

        stock.value = 200 # Change stock value
        aux.calculate_value(system_state) # Recalculate
        self.assertEqual(aux.get_value(), 100.0) # 200 * 0.5

    def test_auxiliary_str_representation(self):
        """Test string representation of auxiliary variable."""
        def calc_func(state): return 42
        aux = Auxiliary(name="OutputAux", calculation_function=calc_func)
        system_state = {}
        aux.calculate_value(system_state) # Calculate to set aux.value
        self.assertEqual(str(aux), "Auxiliary(name='OutputAux', value=42)")


# Mock Stock class for testing Auxiliaries in isolation (so we don't need full Stock class)
class MockStock:
    def __init__(self, name, value):
        self.name = name
        self.value = value
    def get_value(self):
        return self.value


if __name__ == '__main__':
    unittest.main()
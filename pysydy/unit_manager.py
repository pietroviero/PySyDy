import pint

class UnitManager:
    """
    Manages units of measurement for the PySyDy library.
    Loads a predefined set of units and allows runtime unit validation.
    """
    _instance = None

    def __new__(cls, unit_definition_file=None):
        if cls._instance is None:
            cls._instance = super(UnitManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, unit_definition_file=None):
        if self._initialized:
            return
        if unit_definition_file:
            self.ureg = pint.UnitRegistry(unit_definition_file)
        else:
            self.ureg = pint.UnitRegistry()
        self.Q_ = self.ureg.Quantity
        self._initialized = True


    def define_unit(self, definition: str):
        """
        Defines a new custom unit at runtime.

        Example: 'cases = [people]'
        """
        self.ureg.define(definition)

    def get_quantity(self, value, unit: str = None):
        """
        Wraps a value with a unit if provided.

        Example: get_quantity(1000, 'people')
        """
        if unit:
            return value * self.ureg(unit)
        else:
            return value

    def check_compatibility(self, quantity1, quantity2):
        """
        Checks if two quantities have compatible units.

        Raises a pint.DimensionalityError if they are not compatible.
        """
        return quantity1.check(quantity2)

    def to(self, quantity, target_unit: str):
        """
        Converts a quantity to another unit.

        Example: to(energy, 'kWh')
        """
        return quantity.to(target_unit)

    def format_quantity(self, quantity):
        """
        Formats a quantity to a string including the magnitude and unit.

        Example: format_quantity(1000 * people) -> '1000 people'
        """
        return f"{quantity.magnitude} {quantity.units}" if hasattr(quantity, 'units') else str(quantity)



    def safe_define(self, definition: str):
        """
        Safely defines a new unit at runtime.

        If the unit is already defined, silently ignore.
        If the definition is invalid, raise a clear error.

        Example: safe_define('vaccines = [dose]')
        """
        try:
            self.ureg.define(definition)
            print(f"[UnitManager] Defined new unit: {definition}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"[UnitManager] Unit already exists, skipping: {definition}")
            else:
                raise ValueError(f"[UnitManager] Error defining unit '{definition}': {str(e)}")

    def batch_define(self, definitions: list):
        """
        Safely defines a list of units at runtime.

        Each unit is processed individually. Already existing units are skipped.

        Example:
            batch_define([
                'vaccine = [dose]',
                'appointment = [event]',
                'session = [event]'
            ])
        """
        for definition in definitions:
            self.safe_define(definition)

    def force_quantity(self, value, unit):
        """
        Ensures that a value is a Pint Quantity.
        If it is already a Quantity, returns as-is.
        If it is a number (int or float), wraps it into a Quantity with the given unit.
        """
        if hasattr(value, 'magnitude'):
            return value
        else:
            return self.get_quantity(value, unit)

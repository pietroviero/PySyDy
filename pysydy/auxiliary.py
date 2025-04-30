from __future__ import annotations
from typing import Callable, List, Any
from units import units                # your singleton wrapper
ureg = units.ureg
Q_   = ureg.Quantity


class Auxiliary:
    """
    Auxiliary variable in a system-dynamics model.
    """

    def __init__(
        self,
        name: str,
        calculation_function: Callable[[dict[str, Any]], Any],
        inputs: List[str] | None = None,
        unit: str | None = None,
    ):
        if not callable(calculation_function):
            raise TypeError("calculation_function must be callable")

        self.name   = name
        self.inputs = inputs or []
        self.func   = calculation_function

        # Normalise the unit: None → None, str → pint.Unit, Quantity → its .units
        if unit is None:
            self.unit = None
        elif isinstance(unit, str):
            self.unit = ureg.parse_expression(unit).units          # pint.Unit
        else:                               # Quantity or Unit already
            self.unit = getattr(unit, "units", unit)

        self.value = None                   # updated each step

    # ------------------------------------------------------------------ #
    # main logic
    # ------------------------------------------------------------------ #
    def calculate_value(self, system_state: dict[str, Any]):
        """
        Evaluate the user-supplied function, wrap in pint.Quantity,
        and verify dimensionality.
        """
        raw = self.func(system_state)

        # 1) make sure we end up with a Quantity
        if isinstance(raw, Q_):
            self.value = raw
        else:
            unit_to_use = self.unit or ureg.dimensionless
            self.value  = Q_(raw, unit_to_use)

        # 2) dimensionality check
        if self.unit and self.value.dimensionality != self.unit.dimensionality:
            raise ValueError(
                f"[UNIT ERROR] {self.name}: returned {self.value} "
                f"but declared unit is '{self.unit}'"
            )
        return self.value

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    def get_value(self):
        return self.value

    def get_value_updated(self, system_state: dict[str, Any]):
        return self.calculate_value(system_state)

    # nice representation
    def _str_(self):
        return f"Auxiliary({self.name}, value={self.value})"

import os
from unit_manager import UnitManager

# Calculate the path relative to where this file is located
base_dir = os.path.dirname(__file__)
unit_file_path = os.path.join(base_dir, "my_units.txt")

units = UnitManager(unit_file_path)

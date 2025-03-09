"""
PySyDy - A simple Python library for System Dynamics modeling.
"""

from .stock import Stock
from .flow import Flow
from .auxiliary import Auxiliary # Import the new Auxiliary class

__all__ = [
    'Stock',
    'Flow',
    'Auxiliary', # Add Auxiliary to __all__
]
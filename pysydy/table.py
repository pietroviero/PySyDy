# pysydy/table.py

import numpy as np # Added import

class Table:
    """
    A class for representing tabular data with linear interpolation between points.

    This class allows for lookup of values based on a piecewise linear interpolation
    between defined data points. It's useful for representing empirical relationships
    or complex nonlinear functions as a series of connected line segments.
    """

    def __init__(self, x_values, y_values, name="Table"):
        """
        Initialize a Table with x and y values.

        Parameters:
        -----------
        x_values : list or array-like
            The x-coordinates of the data points. Must be monotonically increasing.
        y_values : list or array-like
            The y-coordinates of the data points.
        name : str, optional
            A name for the table (default: "Table")
        """
        if len(x_values) != len(y_values):
            raise ValueError("Table x_values and y_values must have the same length.")

        if len(x_values) < 2:
            # Allow tables with 1 point? Vensim might, but interp needs 2.
            # Let's enforce at least 2 for np.interp to work as expected.
            raise ValueError("Table must have at least two data points for interpolation.")

        # Ensure x_values are monotonically increasing (required by np.interp)
        x_arr = np.array(x_values)
        y_arr = np.array(y_values)
        if not np.all(np.diff(x_arr) >= 0):
             # Sort if not monotonic? Or raise error? Let's raise an error for clarity.
             raise ValueError("Table x_values must be monotonically increasing.")
             # Alternative: Sort them
             # sorted_indices = np.argsort(x_arr)
             # self.x_values = x_arr[sorted_indices]
             # self.y_values = y_arr[sorted_indices]
        else:
            self.x_values = x_arr
            self.y_values = y_arr

        self.name = name
        # print(f"  Table '{self.name}' initialized.") # Optional debug

    def lookup(self, x):
        """
        Look up a y-value for a given x-value using linear interpolation.

        Handles extrapolation by returning the boundary values if x is outside
        the defined range of x_values.

        Parameters:
        -----------
        x : float or array-like
            The x-value(s) to look up.

        Returns:
        --------
        float or ndarray
            The interpolated y-value(s).
        """
        # np.interp handles boundary conditions (returns boundary y values)
        # and performs linear interpolation efficiently.
        return np.interp(x, self.x_values, self.y_values)

    def __call__(self, x):
        """
        Allow the table to be called as a function.

        Parameters:
        -----------
        x : float or array-like
            The x-value(s) to look up.

        Returns:
        --------
        float or ndarray
            The interpolated y-value(s).
        """
        return self.lookup(x)

    def __str__(self):
        return f"Table(name='{self.name}')"
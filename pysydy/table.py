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
            The x-coordinates of the data points
        y_values : list or array-like
            The y-coordinates of the data points
        name : str, optional
            A name for the table (default: "Table")
        """
        if len(x_values) != len(y_values):
            raise ValueError("x_values and y_values must have the same length")
        
        if len(x_values) < 2:
            raise ValueError("Table must have at least two data points")
        
        # Sort the points by x-value to ensure correct interpolation
        points = sorted(zip(x_values, y_values), key=lambda p: p[0])
        self.x_values = [p[0] for p in points]
        self.y_values = [p[1] for p in points]
        self.name = name
    
    def lookup(self, x):
        """
        Look up a y-value for a given x-value using linear interpolation.
        
        If x is less than the smallest x-value, returns the first y-value.
        If x is greater than the largest x-value, returns the last y-value.
        Otherwise, performs linear interpolation between the two nearest points.
        
        Parameters:
        -----------
        x : float
            The x-value to look up
            
        Returns:
        --------
        float
            The interpolated y-value
        """
        # Handle out-of-range values
        if x <= self.x_values[0]:
            return self.y_values[0]
        
        if x >= self.x_values[-1]:
            return self.y_values[-1]
        
        # Find the two points to interpolate between
        for i in range(len(self.x_values) - 1):
            if self.x_values[i] <= x <= self.x_values[i + 1]:
                # Linear interpolation formula
                x0, y0 = self.x_values[i], self.y_values[i]
                x1, y1 = self.x_values[i + 1], self.y_values[i + 1]
                
                # Avoid division by zero
                if x1 == x0:
                    return y0
                
                # Linear interpolation: y = y0 + (x - x0) * (y1 - y0) / (x1 - x0)
                return y0 + (x - x0) * (y1 - y0) / (x1 - x0)
        
        # This should never happen if the code is correct
        raise ValueError(f"Could not interpolate for x={x}")
    
    def __call__(self, x):
        """
        Allow the table to be called as a function.
        
        Parameters:
        -----------
        x : float
            The x-value to look up
            
        Returns:
        --------
        float
            The interpolated y-value
        """
        return self.lookup(x)
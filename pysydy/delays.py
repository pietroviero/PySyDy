"""Defines delay classes for PySyDy library.

This module provides implementations of common delay structures in system dynamics modeling.
"""

import numpy as np
from collections import deque

class MaterialDelay:
    """
    Represents a material delay in a system dynamics model.
    
    Material delays occur when physical entities (people, materials, etc.) take time to move
    through a process. They conserve the quantity being delayed (what goes in eventually comes out).
    """
    
    def __init__(self, name, delay_time, initial_value=0.0, order=3):
        """
        Initializes a MaterialDelay object.
        
        :param name: The name of the delay.
        :type name: str
        :param delay_time: The average time it takes for material to flow through the delay.
        :type delay_time: float
        :param initial_value: The initial outflow rate.
        :type initial_value: float, optional
        :param order: The order of the delay (number of stages), higher orders make the delay approach a fixed time delay.
        :type order: int, optional
        """
        self.name = name
        self.delay_time = delay_time
        self.order = max(1, int(order))  # Ensure order is at least 1
        self.outflow = initial_value
        
        # Initialize the delay stages (for nth-order delay)
        self.stages = [initial_value / self.order] * self.order
        self.history = [initial_value]
    
    def update(self, inflow, timestep):
        """
        Updates the delay based on the current inflow.
        
        :param inflow: The current inflow rate.
        :type inflow: float
        :param timestep: The time interval for the update.
        :type timestep: float
        :returns: The current outflow rate.
        :rtype: float
        """
        # Calculate the transit rate between stages
        transit_rate = self.order / self.delay_time
        
        # Update each stage in the delay chain
        for i in range(self.order):
            if i == 0:
                # First stage receives the inflow
                self.stages[i] += (inflow - transit_rate * self.stages[i]) * timestep
            else:
                # Subsequent stages receive outflow from previous stage
                self.stages[i] += (transit_rate * self.stages[i-1] - transit_rate * self.stages[i]) * timestep
        
        # Outflow is the outflow from the last stage
        self.outflow = transit_rate * self.stages[-1]
        self.history.append(self.outflow)
        
        return self.outflow
    
    def get_outflow(self):
        """
        Returns the current outflow rate.
        
        :returns: The current outflow rate.
        :rtype: float
        """
        return self.outflow
    
    def __str__(self):
        return f"MaterialDelay(name='{self.name}', delay_time={self.delay_time}, order={self.order})"


class InformationDelay:
    """
    Represents an information delay in a system dynamics model.
    
    Information delays occur when information takes time to be perceived, processed, or transmitted.
    They smooth out fluctuations in the input signal.
    """
    
    def __init__(self, name, delay_time, initial_value=0.0, order=1):
        """
        Initializes an InformationDelay object.
        
        :param name: The name of the delay.
        :type name: str
        :param delay_time: The average time it takes for information to be processed.
        :type delay_time: float
        :param initial_value: The initial output value.
        :type initial_value: float, optional
        :param order: The order of the delay (number of stages), higher orders make the delay approach a fixed time delay.
        :type order: int, optional
        """
        self.name = name
        self.delay_time = delay_time
        self.order = max(1, int(order))  # Ensure order is at least 1
        self.output = initial_value
        
        # Initialize the delay stages (for nth-order delay)
        self.stages = [initial_value] * self.order
        self.history = [initial_value]
    
    def update(self, input_value, timestep):
        """
        Updates the delay based on the current input value.
        
        :param input_value: The current input value.
        :type input_value: float
        :param timestep: The time interval for the update.
        :type timestep: float
        :returns: The current output value.
        :rtype: float
        """
        # Calculate the adjustment rate for each stage
        adjustment_rate = self.order / self.delay_time
        
        # Update each stage in the delay chain
        for i in range(self.order):
            if i == 0:
                # First stage adjusts toward the input value
                self.stages[i] += (input_value - self.stages[i]) * adjustment_rate * timestep
            else:
                # Subsequent stages adjust toward the previous stage
                self.stages[i] += (self.stages[i-1] - self.stages[i]) * adjustment_rate * timestep
        
        # Output is the value of the last stage
        self.output = self.stages[-1]
        self.history.append(self.output)
        
        return self.output
    
    def get_output(self):
        """
        Returns the current output value.
        
        :returns: The current output value.
        :rtype: float
        """
        return self.output
    
    def __str__(self):
        return f"InformationDelay(name='{self.name}', delay_time={self.delay_time}, order={self.order})"


class FixedDelay:
    """
    Represents a fixed delay (pipeline delay) in a system dynamics model.
    
    Fixed delays output exactly what went in, after a fixed time delay.
    They are useful for representing processes where the delay time is constant.
    """
    
    def __init__(self, name, delay_time, initial_value=0.0, timestep=1.0):
        """
        Initializes a FixedDelay object.
        
        :param name: The name of the delay.
        :type name: str
        :param delay_time: The fixed time it takes for input to become output.
        :type delay_time: float
        :param initial_value: The initial output value.
        :type initial_value: float, optional
        :param timestep: The expected simulation timestep (used to size the internal buffer).
        :type timestep: float, optional
        """
        self.name = name
        self.delay_time = delay_time
        self.output = initial_value
        
        # Calculate buffer size based on delay time and timestep
        buffer_size = int(delay_time / timestep) + 1
        
        # Initialize the buffer with initial values
        self.buffer = deque([initial_value] * buffer_size, maxlen=buffer_size)
        self.history = [initial_value]
    
    def update(self, inflow, timestep):
        """
        Updates the delay based on the current inflow.
        
        :param inflow: The current inflow rate.
        :type inflow: float
        :param timestep: The time interval for the update.
        :type timestep: float
        :returns: The current outflow rate.
        :rtype: float
        """
        # Add the new inflow to the buffer
        self.buffer.appendleft(inflow)
        
        # Output is what comes out of the buffer
        self.output = self.buffer[-1]
        self.history.append(self.output)
        
        return self.output
    
    def get_output(self):
        """
        Returns the current output value.
        
        :returns: The current output value.
        :rtype: float
        """
        return self.output
    
    def __str__(self):
        return f"FixedDelay(name='{self.name}', delay_time={self.delay_time})"
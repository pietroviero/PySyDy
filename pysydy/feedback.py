"""Defines feedback loop classes for PySyDy library.

This module provides implementations of feedback loop structures in system dynamics modeling.
"""

class ReinforcingLoop:
    """
    Represents a reinforcing feedback loop in a system dynamics model.
    
    Reinforcing loops amplify changes in a system, creating exponential growth or collapse.
    This class helps document and analyze reinforcing loops in a model.
    """
    
    def __init__(self, name, components, description=None):
        """
        Initializes a ReinforcingLoop object.
        
        :param name: The name of the feedback loop.
        :type name: str
        :param components: A list of components (stocks, flows, auxiliaries) that form the loop.
        :type components: list
        :param description: A description of the feedback mechanism.
        :type description: str, optional
        """
        self.name = name
        self.components = components
        self.description = description
        self.polarity = 'positive'  # Reinforcing loops have positive polarity
    
    def get_components(self):
        """
        Returns the components that form the feedback loop.
        
        :returns: The list of components.
        :rtype: list
        """
        return self.components
    
    def __str__(self):
        desc = f", description='{self.description}'" if self.description else ""
        return f"ReinforcingLoop(name='{self.name}'{desc})"


class BalancingLoop:
    """
    Represents a balancing feedback loop in a system dynamics model.
    
    Balancing loops counteract changes in a system, creating goal-seeking or oscillatory behavior.
    This class helps document and analyze balancing loops in a model.
    """
    
    def __init__(self, name, components, goal=None, description=None):
        """
        Initializes a BalancingLoop object.
        
        :param name: The name of the feedback loop.
        :type name: str
        :param components: A list of components (stocks, flows, auxiliaries) that form the loop.
        :type components: list
        :param goal: The goal or target value that the loop seeks to achieve.
        :type goal: float, optional
        :param description: A description of the feedback mechanism.
        :type description: str, optional
        """
        self.name = name
        self.components = components
        self.goal = goal
        self.description = description
        self.polarity = 'negative'  # Balancing loops have negative polarity
    
    def get_components(self):
        """
        Returns the components that form the feedback loop.
        
        :returns: The list of components.
        :rtype: list
        """
        return self.components
    
    def __str__(self):
        goal_str = f", goal={self.goal}" if self.goal is not None else ""
        desc = f", description='{self.description}'" if self.description else ""
        return f"BalancingLoop(name='{self.name}'{goal_str}{desc})"


class FeedbackStructure:
    """
    Represents a collection of feedback loops in a system dynamics model.
    
    This class helps analyze the overall feedback structure of a model,
    identifying dominant loops and leverage points.
    """
    
    def __init__(self, name):
        """
        Initializes a FeedbackStructure object.
        
        :param name: The name of the feedback structure.
        :type name: str
        """
        self.name = name
        self.reinforcing_loops = []
        self.balancing_loops = []
    
    def add_reinforcing_loop(self, loop):
        """
        Adds a reinforcing loop to the feedback structure.
        
        :param loop: The reinforcing loop to add.
        :type loop: ReinforcingLoop
        """
        self.reinforcing_loops.append(loop)
    
    def add_balancing_loop(self, loop):
        """
        Adds a balancing loop to the feedback structure.
        
        :param loop: The balancing loop to add.
        :type loop: BalancingLoop
        """
        self.balancing_loops.append(loop)
    
    def get_all_loops(self):
        """
        Returns all feedback loops in the structure.
        
        :returns: A list of all feedback loops.
        :rtype: list
        """
        return self.reinforcing_loops + self.balancing_loops
    
    def __str__(self):
        return f"FeedbackStructure(name='{self.name}', reinforcing_loops={len(self.reinforcing_loops)}, balancing_loops={len(self.balancing_loops)})"
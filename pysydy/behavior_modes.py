"""Defines behavior mode descriptor classes for PySyDy library.

This module provides classes to describe or label common behavior modes 
observed in parts of a system dynamics model constructed from stocks, flows, etc.
These classes are primarily for documentation and analysis, similar to feedback loop descriptors.
"""

class BehaviorMode:
    """
    Abstract base class for behavior mode descriptors.
    """
    def __init__(self, name, components, description=None):
        """
        Initializes a BehaviorMode descriptor.
        
        :param name: The name of the behavior pattern observed.
        :type name: str
        :param components: A list of model components (stocks, flows, auxiliaries) 
                           that collectively exhibit this behavior.
        :type components: list
        :param description: An optional description of the behavior pattern.
        :type description: str, optional
        """
        if not isinstance(components, list):
            raise TypeError("Components must be provided as a list.")
            
        self.name = name
        self.components = components
        self.description = description
        self.behavior_type = "Generic" # Overridden by subclasses

    def get_components(self):
        """
        Returns the components associated with this behavior pattern.
        
        :returns: The list of components.
        :rtype: list
        """
        return self.components

    def __str__(self):
        desc = f", description='{self.description}'" if self.description else ""
        comp_names = [str(c.name) if hasattr(c, 'name') else str(c) for c in self.components] # Handle potential non-element components
        return f"{self.behavior_type}(name='{self.name}', components={comp_names}{desc})"

# --- Specific Behavior Mode Descriptors ---

class ExponentialGrowth(BehaviorMode):
    """Describes a part of the model exhibiting exponential growth."""
    def __init__(self, name, components, description=None):
        super().__init__(name, components, description)
        self.behavior_type = "ExponentialGrowth"

class ExponentialDecay(BehaviorMode):
    """Describes a part of the model exhibiting exponential decay."""
    def __init__(self, name, components, description=None):
        super().__init__(name, components, description)
        self.behavior_type = "ExponentialDecay"

class GoalSeeking(BehaviorMode):
    """Describes a part of the model exhibiting goal-seeking behavior."""
    def __init__(self, name, components, description=None, goal_variable=None):
        super().__init__(name, components, description)
        self.behavior_type = "GoalSeeking"
        self.goal_variable = goal_variable # Optional: reference to the element representing the goal

    def __str__(self):
        base_str = super().__str__()
        goal_str = f", goal_variable='{self.goal_variable.name}'" if hasattr(self.goal_variable, 'name') else ""
        # Need to insert goal_str before the closing parenthesis
        parts = base_str.split(')')
        return f"{parts[0]}{goal_str})"


class Oscillation(BehaviorMode):
    """Describes a part of the model exhibiting oscillation."""
    def __init__(self, name, components, description=None):
        super().__init__(name, components, description)
        self.behavior_type = "Oscillation"

class SShapedGrowth(BehaviorMode):
    """Describes a part of the model exhibiting S-shaped (logistic) growth."""
    def __init__(self, name, components, description=None, capacity_variable=None):
        super().__init__(name, components, description)
        self.behavior_type = "SShapedGrowth"
        self.capacity_variable = capacity_variable # Optional: reference to the element representing capacity

    def __str__(self):
        base_str = super().__str__()
        cap_str = f", capacity_variable='{self.capacity_variable.name}'" if hasattr(self.capacity_variable, 'name') else ""
        # Need to insert cap_str before the closing parenthesis
        parts = base_str.split(')')
        return f"{parts[0]}{cap_str})"

class OvershootAndCollapse(BehaviorMode):
     """Describes a part of the model exhibiting overshoot and collapse."""
     def __init__(self, name, components, description=None):
         super().__init__(name, components, description)
         self.behavior_type = "OvershootAndCollapse"

# Note: You might add other common behaviors like "Growth with Overshoot" etc.
# following the same pattern.

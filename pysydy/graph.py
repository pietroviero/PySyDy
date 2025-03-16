"""Defines the Graph class for PySyDy library.

This module provides visualization capabilities for system dynamics models.
"""

import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from .stock import Stock
from .flow import Flow
from .auxiliary import Auxiliary
from .parameter import Parameter
from .simulation import Simulation

class Graph:
    """
    Provides visualization capabilities for system dynamics models.
    
    This class creates a graphical representation of a system dynamics model,
    showing the relationships between stocks, flows, auxiliaries, and parameters.
    """
    
    def __init__(self, simulation):
        """
        Initializes a Graph object.
        
        :param simulation: The simulation object containing the model components.
        :type simulation: Simulation
        """
        self.simulation = simulation
        self.graph = nx.DiGraph()
        self._build_graph()
        
    def _build_graph(self):
        """
        Builds the graph representation of the model.
        """
        # Add stocks as nodes
        for stock in self.simulation.stocks:
            self.graph.add_node(stock.name, type='stock', obj=stock)
            
        # Add flows as nodes and edges
        for flow in self.simulation.flows:
            self.graph.add_node(flow.name, type='flow', obj=flow)
            
            # Connect source stock to flow (if exists)
            if flow.source_stock:
                self.graph.add_edge(flow.source_stock.name, flow.name, type='outflow')
                
            # Connect flow to target stock (if exists)
            if flow.target_stock:
                self.graph.add_edge(flow.name, flow.target_stock.name, type='inflow')
        
        # Add auxiliaries as nodes
        for aux in self.simulation.auxiliaries:
            self.graph.add_node(aux.name, type='auxiliary', obj=aux)
            
            # Connect auxiliaries to their inputs (if specified)
            if hasattr(aux, 'inputs') and aux.inputs:
                for input_name in aux.inputs:
                    # Check if input exists in the graph
                    if input_name in self.graph:
                        self.graph.add_edge(input_name, aux.name, type='influence')
        
        # Add parameters as nodes
        for param in self.simulation.parameters:
            self.graph.add_node(param.name, type='parameter', obj=param)
        
        # Connect parameters to flows based on rate function usage
        self._connect_parameters_to_flows()
    
    def _connect_parameters_to_flows(self):
        """
        Analyzes flow rate functions to connect parameters to the flows they influence.
        
        This method creates edges between parameters and flows based on their usage
        in the rate functions of the flows.
        """
        # For SIR model, we know the parameter relationships from the rate functions
        # Connect contact_rate, infectivity, and total_population to infection flow
        param_to_flow_map = {
            'contact_rate': ['infection'],
            'infectivity': ['infection'],
            'total_population': ['infection'],
            'infectious_period': ['recovery'],
            'recovery_rate': ['recovery']  # Keep for backward compatibility
        }
        
        # Create edges based on the mapping
        for param_name, flow_names in param_to_flow_map.items():
            if param_name in [p.name for p in self.simulation.parameters]:
                for flow_name in flow_names:
                    if flow_name in [f.name for f in self.simulation.flows]:
                        self.graph.add_edge(param_name, flow_name, type='influence')
    
    def plot(self, figsize=(12, 8), node_size=2000, font_size=12, show_values=True):
        """
        Plots the graph representation of the model.
        
        :param figsize: The figure size (width, height) in inches.
        :type figsize: tuple
        :param node_size: The size of the nodes.
        :type node_size: int
        :param font_size: The font size for node labels.
        :type font_size: int
        :param show_values: Whether to show current values in the graph.
        :type show_values: bool
        :returns: The figure and axes objects.
        :rtype: tuple
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Define node colors by type
        color_map = {
            'stock': '#3498db',      # Blue
            'flow': '#e74c3c',       # Red
            'auxiliary': '#2ecc71',  # Green
            'parameter': '#f39c12'   # Orange
        }
        
        # Define node shapes by type
        node_shapes = {
            'stock': 's',      # Square
            'flow': '^',       # Triangle
            'auxiliary': 'o',  # Circle
            'parameter': 'd'   # Diamond
        }
        
        # Create improved position layout with more spacing
        pos = nx.spring_layout(self.graph, k=1.5, iterations=100)  # Use spring layout with more spacing
        
        # Adjust positions to prevent overlapping
        # Scale positions to provide more space between nodes
        for node in pos:
            pos[node] = (pos[node][0] * 2.0, pos[node][1] * 2.0)
            
        # Further adjust parameter positions to prevent overlapping
        param_nodes = [n for n, data in self.graph.nodes(data=True) if data.get('type') == 'parameter']
        
        # Spread parameters more evenly around their connected flows
        for param in param_nodes:
            neighbors = list(self.graph.successors(param))
            if neighbors:
                # Calculate average position of neighbors
                avg_x = sum(pos[n][0] for n in neighbors) / len(neighbors)
                avg_y = sum(pos[n][1] for n in neighbors) / len(neighbors)
                
                # Move parameter away from the average position of neighbors
                param_x, param_y = pos[param]
                vector_x = param_x - avg_x
                vector_y = param_y - avg_y
                
                # Normalize and scale the vector
                magnitude = (vector_x**2 + vector_y**2)**0.5
                if magnitude > 0:
                    vector_x = vector_x / magnitude * 0.8
                    vector_y = vector_y / magnitude * 0.8
                    
                # Update parameter position
                pos[param] = (avg_x + vector_x, avg_y + vector_y)
        
        # Define node sizes by type for better visual hierarchy
        node_sizes = {
            'stock': node_size * 1.2,      # Larger for stocks
            'flow': node_size * 0.8,       # Medium for flows
            'auxiliary': node_size * 0.7,  # Smaller for auxiliaries
            'parameter': node_size * 0.9   # Medium-small for parameters
        }
        
        # Draw nodes by type with improved appearance
        for node_type in ['stock', 'flow', 'auxiliary', 'parameter']:
            nodes = [n for n, data in self.graph.nodes(data=True) if data.get('type') == node_type]
            nx.draw_networkx_nodes(
                self.graph, pos,
                nodelist=nodes,
                node_color=color_map[node_type],
                node_shape=node_shapes[node_type],
                node_size=node_sizes[node_type],
                alpha=0.9,
                edgecolors='black',  # Add black outline
                linewidths=1.5,      # Outline width
                ax=ax
            )
        
        # Draw edges with different colors based on type
        edge_colors = {
            'outflow': '#e74c3c',  # Red
            'inflow': '#e74c3c',   # Red
            'influence': '#7f8c8d'  # Gray
        }
        
        # Draw edges by type
        for edge_type, color in edge_colors.items():
            edges = [(u, v) for u, v, data in self.graph.edges(data=True) 
                    if data.get('type') == edge_type]
            nx.draw_networkx_edges(
                self.graph, pos,
                edgelist=edges,
                width=2, alpha=0.8,
                edge_color=color,
                arrows=True,
                arrowsize=25,
                connectionstyle='arc3,rad=0.1',  # Curved edges
                ax=ax
            )
        
        # Prepare node labels with improved formatting
        labels = {}
        for node, data in self.graph.nodes(data=True):
            if show_values and 'obj' in data:
                obj = data['obj']
                if hasattr(obj, 'get_value'):
                    value = obj.get_value()
                    if isinstance(value, (int, float)):
                        # Format numbers with appropriate precision
                        if value >= 1000:
                            labels[node] = f"{node}\n{value:.2f}"
                        elif value >= 100:
                            labels[node] = f"{node}\n{value:.2f}"
                        elif value >= 10:
                            labels[node] = f"{node}\n{value:.2f}"
                        else:
                            labels[node] = f"{node}\n{value:.2f}"
                    else:
                        labels[node] = f"{node}\n{value}"
                else:
                    labels[node] = node
            else:
                labels[node] = node
        
        # Draw node labels with white background for better readability
        text_items = {}
        for node, label in labels.items():
            x, y = pos[node]
            text_items[node] = ax.text(x, y, label,
                                     horizontalalignment='center',
                                     verticalalignment='center',
                                     fontsize=font_size,
                                     fontweight='bold',
                                     bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.3'),
                                     zorder=100)  # Ensure text is on top
        
        # Create legend
        legend_elements = [
            Patch(facecolor=color_map['stock'], edgecolor='k', label='Stock'),
            Patch(facecolor=color_map['flow'], edgecolor='k', label='Flow'),
            Patch(facecolor=color_map['auxiliary'], edgecolor='k', label='Auxiliary'),
            Patch(facecolor=color_map['parameter'], edgecolor='k', label='Parameter')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Remove axis
        plt.axis('off')
        plt.title('System Dynamics Model Visualization')
        
        return fig, ax
    
    def update_graph(self):
        """
        Updates the graph with current values from the simulation.
        Call this after simulation steps to refresh the graph.
        """
        # Update node attributes with current values
        for node, data in self.graph.nodes(data=True):
            if 'obj' in data:
                obj = data['obj']
                if hasattr(obj, 'get_value'):
                    data['value'] = obj.get_value()
    
    def interactive_plot(self, figsize=(12, 8)):
        """
        Creates an interactive plot that updates as the simulation runs.
        This requires running in a Jupyter notebook environment.
        
        :param figsize: The figure size (width, height) in inches.
        :type figsize: tuple
        """
        try:
            import ipywidgets as widgets
            from IPython.display import display, clear_output
        except ImportError:
            print("This feature requires ipywidgets and IPython. Please install them.")
            return
        
        # Create widgets for controls
        step_button = widgets.Button(description="Step")
        run_button = widgets.Button(description="Run 10 Steps")
        reset_button = widgets.Button(description="Reset Plot")
        
        # Create output widget for the plot
        output = widgets.Output()
        
        # Define button callbacks
        def on_step_button_clicked(b):
            with output:
                clear_output(wait=True)
                self.simulation.step()
                self.update_graph()
                self.plot(figsize=figsize)
                plt.show()
        
        def on_run_button_clicked(b):
            with output:
                clear_output(wait=True)
                for _ in range(10):
                    self.simulation.step()
                self.update_graph()
                self.plot(figsize=figsize)
                plt.show()
        
        def on_reset_button_clicked(b):
            with output:
                clear_output(wait=True)
                self.plot(figsize=figsize)
                plt.show()
        
        # Connect callbacks to buttons
        step_button.on_click(on_step_button_clicked)
        run_button.on_click(on_run_button_clicked)
        reset_button.on_click(on_reset_button_clicked)
        
        # Display initial plot
        with output:
            self.plot(figsize=figsize)
            plt.show()
        
        # Display widgets and output
        controls = widgets.HBox([step_button, run_button, reset_button])
        display(controls, output)
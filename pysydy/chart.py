import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class Chart:
    """
    Provides plotting capabilities for system dynamics models.
    
    This class focuses on time series visualization of stocks, flows, and auxiliary variables,
    showing how they change over the simulation period.
    """
    
    def __init__(self, simulation):
        """
        Initializes a Chart object.
        
        :param simulation: The simulation object containing the model components and results.
        :type simulation: Simulation
        """
        self.simulation = simulation
    
    def plot_stocks_time_series(self, figsize=(12, 8), title="Stock Values Over Time", grid=True):
        """
        Plots the time series of stock values from the simulation history.
        
        :param figsize: The figure size (width, height) in inches.
        :type figsize: tuple
        :param title: The title of the plot.
        :type title: str
        :param grid: Whether to show grid lines.
        :type grid: bool
        :returns: The figure and axes objects.
        :rtype: tuple
        """
        # Get simulation results
        results = self.simulation.get_results()
        
        # Check if there are any results to plot
        if results.empty:
            print("No simulation results to plot. Run the simulation first.")
            return None, None
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot each stock as a line
        for stock in self.simulation.stocks:
            if stock.name in results.columns:
                ax.plot(results.index, results[stock.name], 
                        label=stock.name, linewidth=2)
        
        # Add labels and title
        ax.set_xlabel('Time')
        ax.set_ylabel('Stock Value')
        ax.set_title(title)
        ax.legend()
        
        # Add grid if requested
        if grid:
            ax.grid(True, linestyle='--', alpha=0.7)
        
        return fig, ax
    
    def plot_individual_stock(self, stock_name, figsize=(10, 6), title=None, grid=True, color='#3498db'):
        """
        Plots the time series of a single stock from the simulation history.
        
        :param stock_name: The name of the stock to plot.
        :type stock_name: str
        :param figsize: The figure size (width, height) in inches.
        :type figsize: tuple
        :param title: The title of the plot. If None, uses the stock name.
        :type title: str
        :param grid: Whether to show grid lines.
        :type grid: bool
        :param color: The color of the line.
        :type color: str
        :returns: The figure and axes objects.
        :rtype: tuple
        """
        # Get simulation results
        results = self.simulation.get_results()
        
        # Check if there are any results to plot
        if results.empty:
            print("No simulation results to plot. Run the simulation first.")
            return None, None
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)
        
        # Check if the stock exists in the results
        if stock_name in results.columns:
            # Plot the stock
            ax.plot(results.index, results[stock_name], label=stock_name, linewidth=2, color=color)
            
            # Add labels and title
            ax.set_xlabel('Time')
            ax.set_ylabel('Stock Value')
            ax.set_title(title if title else f"{stock_name} Over Time")
            ax.legend()
            
            # Add grid if requested
            if grid:
                ax.grid(True, linestyle='--', alpha=0.7)
            
            return fig, ax
        else:
            print(f"Stock '{stock_name}' not found in simulation results.")
            return None, None
    
    def plot_individual_auxiliary(self, auxiliary_name, figsize=(10, 6), title=None, grid=True, color='#2ecc71'):
        """
        Plots the time series of a single auxiliary variable from the simulation history.
        
        :param auxiliary_name: The name of the auxiliary variable to plot.
        :type auxiliary_name: str
        :param figsize: The figure size (width, height) in inches.
        :type figsize: tuple
        :param title: The title of the plot. If None, uses the auxiliary name.
        :type title: str
        :param grid: Whether to show grid lines.
        :type grid: bool
        :param color: The color of the line.
        :type color: str
        :returns: The figure and axes objects.
        :rtype: tuple
        """
        # Get simulation results
        results = self.simulation.get_results()
        
        # Check if there are any results to plot
        if results.empty:
            print("No simulation results to plot. Run the simulation first.")
            return None, None
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)
        
        # Check if the auxiliary variable exists in the results
        if auxiliary_name in results.columns:
            # Plot the auxiliary variable
            ax.plot(results.index, results[auxiliary_name], label=auxiliary_name, 
                   linewidth=2, color=color, linestyle='--')
            
            # Add labels and title
            ax.set_xlabel('Time')
            ax.set_ylabel('Value')
            ax.set_title(title if title else f"{auxiliary_name} Over Time")
            ax.legend()
            
            # Add grid if requested
            if grid:
                ax.grid(True, linestyle='--', alpha=0.7)
            
            return fig, ax
        else:
            print(f"Auxiliary variable '{auxiliary_name}' not found in simulation results.")
            return None, None
    
    def plot_auxiliaries_time_series(self, figsize=(12, 8), title="Auxiliary Variables Over Time", grid=True):
        """
        Plots the time series of auxiliary variable values from the simulation history.
        
        :param figsize: The figure size (width, height) in inches.
        :type figsize: tuple
        :param title: The title of the plot.
        :type title: str
        :param grid: Whether to show grid lines.
        :type grid: bool
        :returns: The figure and axes objects.
        :rtype: tuple
        """
        # Get simulation results
        results = self.simulation.get_results()
        
        # Check if there are any results to plot
        if results.empty:
            print("No simulation results to plot. Run the simulation first.")
            return None, None
        
        # Get auxiliary names from the simulation
        auxiliary_names = [aux.name for aux in self.simulation.auxiliaries]
        
        # Check if any auxiliary variables exist in the results
        aux_in_results = [name for name in auxiliary_names if name in results.columns]
        
        if aux_in_results:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot each auxiliary as a line
            for aux_name in aux_in_results:
                ax.plot(results.index, results[aux_name], label=aux_name, linewidth=2, linestyle='--')
            
            # Add labels and title
            ax.set_xlabel('Time')
            ax.set_ylabel('Value')
            ax.set_title(title)
            ax.legend()
            
            # Add grid if requested
            if grid:
                ax.grid(True, linestyle='--', alpha=0.7)
            
            return fig, ax
        else:
            print("No auxiliary variable data found in simulation results.")
            return None, None
            
    def plot_flows_time_series(self, figsize=(12, 8), title="Flow Rates Over Time", grid=True):
        """
        Plots the time series of flow rates from the simulation history.
        
        :param figsize: The figure size (width, height) in inches.
        :type figsize: tuple
        :param title: The title of the plot.
        :type title: str
        :param grid: Whether to show grid lines.
        :type grid: bool
        :returns: The figure and axes objects.
        :rtype: tuple
        """
        # Get simulation results
        results = self.simulation.get_results()
        
        # Check if there are any results to plot
        if results.empty:
            print("No simulation results to plot. Run the simulation first.")
            return None, None
        
        # Get flow names from the simulation
        flow_names = [flow.name for flow in self.simulation.flows]
        
        # Check if any flows exist in the results
        flows_in_results = [name for name in flow_names if name in results.columns]
        
        if flows_in_results:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot each flow as a line
            for flow_name in flows_in_results:
                ax.plot(results.index, results[flow_name], label=flow_name, linewidth=2, linestyle='-.')
            
            # Add labels and title
            ax.set_xlabel('Time')
            ax.set_ylabel('Flow Rate')
            ax.set_title(title)
            ax.legend()
            
            # Add grid if requested
            if grid:
                ax.grid(True, linestyle='--', alpha=0.7)
            
            return fig, ax
        else:
            print("No flow data found in simulation results.")
            return None, None
            
    def plot_individual_flow(self, flow_name, figsize=(10, 6), title=None, grid=True, color='#e74c3c'):
        """
        Plots the time series of a single flow from the simulation history.
        
        :param flow_name: The name of the flow to plot.
        :type flow_name: str
        :param figsize: The figure size (width, height) in inches.
        :type figsize: tuple
        :param title: The title of the plot. If None, uses the flow name.
        :type title: str
        :param grid: Whether to show grid lines.
        :type grid: bool
        :param color: The color of the line.
        :type color: str
        :returns: The figure and axes objects.
        :rtype: tuple
        """
        # Get simulation results
        results = self.simulation.get_results()
        
        # Check if there are any results to plot
        if results.empty:
            print("No simulation results to plot. Run the simulation first.")
            return None, None
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)
        
        # Check if the flow exists in the results
        if flow_name in results.columns:
            # Plot the flow
            ax.plot(results.index, results[flow_name], label=flow_name, linewidth=2, color=color, linestyle='-.')
            
            # Add labels and title
            ax.set_xlabel('Time')
            ax.set_ylabel('Flow Rate')
            ax.set_title(title if title else f"{flow_name} Over Time")
            ax.legend()
            
            # Add grid if requested
            if grid:
                ax.grid(True, linestyle='--', alpha=0.7)
            
            return fig, ax
        else:
            print(f"Flow '{flow_name}' not found in simulation results.")
            return None, None
    
    def plot_all_variables(self, figsize=(14, 10), title="Model Variables Over Time", grid=True):
        """
        Plots stocks, flows, and auxiliary variables on the same graph.
        
        :param figsize: The figure size (width, height) in inches.
        :type figsize: tuple
        :param title: The title of the plot.
        :type title: str
        :param grid: Whether to show grid lines.
        :type grid: bool
        :returns: The figure and axes objects.
        :rtype: tuple
        """
        # Get simulation results
        results = self.simulation.get_results()
        
        # Check if there are any results to plot
        if results.empty:
            print("No simulation results to plot. Run the simulation first.")
            return None, None
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot stocks
        for stock in self.simulation.stocks:
            if stock.name in results.columns:
                ax.plot(results.index, results[stock.name], 
                        label=f"Stock: {stock.name}", linewidth=2)
        
        # Plot flows
        for flow in self.simulation.flows:
            if flow.name in results.columns:
                ax.plot(results.index, results[flow.name], 
                        label=f"Flow: {flow.name}", linewidth=2, linestyle='-.')
        
        # Plot auxiliaries
        for aux in self.simulation.auxiliaries:
            if aux.name in results.columns:
                ax.plot(results.index, results[aux.name], 
                        label=f"Aux: {aux.name}", linewidth=2, linestyle='--')
        
        # Add labels and title
        ax.set_xlabel('Time')
        ax.set_ylabel('Value')
        ax.set_title(title)
        ax.legend(loc='best')
        
        # Add grid if requested
        if grid:
            ax.grid(True, linestyle='--', alpha=0.7)
        
        return fig, ax
    
    def plot_variables_separately(self, figsize=(16, 12), grid=True):
        """
        Creates a figure with three subplots: one for stocks, one for flows, and one for auxiliary variables.
        
        :param figsize: The figure size (width, height) in inches.
        :type figsize: tuple
        :param grid: Whether to show grid lines.
        :type grid: bool
        :returns: The figure object.
        :rtype: matplotlib.figure.Figure
        """
        # Get simulation results
        results = self.simulation.get_results()
        
        # Check if there are any results to plot
        if results.empty:
            print("No simulation results to plot. Run the simulation first.")
            return None
        
        # Create figure with three subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=figsize)
        fig.suptitle("Model Variables Over Time", fontsize=16)
        
        # Plot stocks in the first subplot
        for stock in self.simulation.stocks:
            if stock.name in results.columns:
                ax1.plot(results.index, results[stock.name], 
                        label=stock.name, linewidth=2)
        
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Stock Value')
        ax1.set_title('Stocks')
        ax1.legend(loc='best')
        
        if grid:
            ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Plot flows in the second subplot
        flow_names = [flow.name for flow in self.simulation.flows]
        flows_in_results = [name for name in flow_names if name in results.columns]
        
        if flows_in_results:
            for flow_name in flows_in_results:
                ax2.plot(results.index, results[flow_name], 
                        label=flow_name, linewidth=2, linestyle='-.')
            
            ax2.set_xlabel('Time')
            ax2.set_ylabel('Flow Rate')
            ax2.set_title('Flows')
            ax2.legend(loc='best')
            
            if grid:
                ax2.grid(True, linestyle='--', alpha=0.7)
        else:
            ax2.text(0.5, 0.5, "No flow data available", 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax2.transAxes)
            ax2.set_title('Flows')
        
        # Plot auxiliaries in the third subplot
        for aux in self.simulation.auxiliaries:
            if aux.name in results.columns:
                ax3.plot(results.index, results[aux.name], 
                        label=aux.name, linewidth=2, linestyle='--')
        
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Value')
        ax3.set_title('Auxiliary Variables')
        ax3.legend(loc='best')
        
        if grid:
            ax3.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust for suptitle
        return fig
    
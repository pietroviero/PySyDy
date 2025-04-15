import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add the parent directory (PySyDy) to the Python path
# This allows importing pysydy modules when running the script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from pysydy import Simulation, Stock, Flow, Parameter, Auxiliary, Graph
from pysydy.chart import Chart
from pysydy import ReinforcingLoop, BalancingLoop
from pysydy.table import Table
from pysydy.delays import MaterialDelay, InformationDelay, FixedDelay

# --- Define Model Components ---

# Parameters
initial_customer_demand = Parameter("Initial Customer Demand", 10)  # units per time unit
safety_stock_time = Parameter("Safety Stock Time", 2)  # time units of coverage
time_to_adjust_inventory = Parameter("Time to Adjust Inventory", 8)  # time units
time_to_smooth_demand = Parameter("Time to Smooth Demand", 8)  # time units
order_processing_time = Parameter("Order Processing Time", 10)  # time units

# Parameters for customer order pattern
sine_amplitude = Parameter("Sine Amplitude", 4)  # amplitude of sine wave (adjust value as needed)
sine_period = Parameter("Sine Period", 2)  # period of sine wave in time units (adjust value as needed)
noise_deviation = Parameter("Noise Deviation", 1)  # standard deviation of noise (restored)
step_height = Parameter("Step Height", 10)  # height of step function (increase from base)
step_time = Parameter("Step Time", 1)  # when step occurs

# Stocks
inventory = Stock("Inventory", 100)  # initial inventory level
expected_order_rate = Stock("Expected Order Rate", 10)  # initial expected order rate

# Auxiliaries
def calculate_customer_order_rate(state): # state is passed by framework, but ignored for time calculation
    """Calculate customer order rate using the original formula:
       Initial customer demand*(1+step+sine*noise)
    """
    # Get current time directly from the simulation object
    t = sim.time

    base = initial_customer_demand.get_value()

    # Step function component (Vensim's STEP function applies height directly at time)
    sh = step_height.get_value()
    st = step_time.get_value()
    step_component = sh if t >= st else 0

    # Sine wave component
    amplitude = sine_amplitude.get_value()
    period = sine_period.get_value()
    sine_component = amplitude * np.sin(2 * np.pi * t / period)

    # Noise component (Vensim step applies noise only after time=1)
    nd = noise_deviation.get_value()
    noise_factor = nd if t >= 1 else 0
    # Vensim RANDOM NORMAL(-4, 4, 0, 1, 1000) -> numpy.random.normal(mean=0, std=1)
    # Clipping to -4, 4 is less standard in numpy, but let's add it if needed.
    # For now, assuming standard normal N(0,1) is intended.
    noise_value = np.random.normal(0, 1)

    # Combine according to the original formula
    order_rate = base * (1 + step_component + sine_component * noise_factor * noise_value)

    final_rate = max(0, order_rate) # ensure non-negative
    return final_rate

customer_order_rate = Auxiliary("Customer Order Rate", calculate_customer_order_rate)

# Desired inventory level based on expected order rate and safety stock
def calculate_desired_inventory(state):
    return expected_order_rate.get_value() * (order_processing_time.get_value() + safety_stock_time.get_value())

desired_inventory_level = Auxiliary("Desired Inventory Level", calculate_desired_inventory)

# Adjustment from inventory
def calculate_adjustment(state):
    inventory_gap = desired_inventory_level.get_value() - inventory.get_value()
    return inventory_gap / time_to_adjust_inventory.get_value()

adjustment_from_inventory = Auxiliary("Adjustment from Inventory", calculate_adjustment)

# Desired production rate
def calculate_desired_production(state):
    return max(0, expected_order_rate.get_value() + adjustment_from_inventory.get_value())

desired_production = Auxiliary("Desired Production", calculate_desired_production)

# Maximum shipment rate based on inventory
def calculate_max_shipment_rate(state):
    return inventory.get_value() / order_processing_time.get_value()  # assume can ship entire inventory in 1 time unit if needed

max_shipment_rate = Auxiliary("Max Shipment Rate", calculate_max_shipment_rate)

# Create a lookup table for order fulfillment ratio
# Data points from the graph: (ratio of max shipment rate to customer order rate, order fulfillment ratio)
fulfillment_table = Table(
    x_values=[0, 0.152905, 0.324159, 0.525994, 0.850153, 1.25382, 2],
    y_values=[0, 0.280702, 0.535088, 0.723684, 0.811404, 0.903509, 1],
    name="Order Fulfillment Table"
)

# Order fulfillment ratio using table lookup
def calculate_order_fulfillment_ratio(state):
    if customer_order_rate.get_value() > 0:
        # Calculate the ratio of max shipment rate to customer order rate
        ratio = max_shipment_rate.get_value() / customer_order_rate.get_value()
        # Use the table to look up the order fulfillment ratio
        return fulfillment_table(ratio)
    else:
        return 1.0  # if no orders, fulfillment ratio is 1

order_fulfillment_ratio = Auxiliary("Order Fulfillment Ratio", calculate_order_fulfillment_ratio)

# Flows
# Production rate (inflow to inventory) - Now directly uses Desired Production
production_rate = Flow(name="Production Rate",
                      source_stock=None,  # external source
                      target_stock=inventory,
                      rate_function=lambda state: desired_production.get_value()) # Directly use desired rate

# Shipment rate (outflow from inventory)
def shipment_rate_eq(state):
    # Calculate desired shipment rate based on customer orders and fulfillment ratio
    desired_shipment = customer_order_rate.get_value() * order_fulfillment_ratio.get_value()
    # Ensure shipment rate doesn't exceed maximum shipment rate (physical constraint)
    return min(desired_shipment, max_shipment_rate.get_value())

shipment_rate = Flow(name="Shipment Rate", 
                    source_stock=inventory, 
                    target_stock=None,  # external sink
                    rate_function=shipment_rate_eq)

# Change in expected order rate
def change_in_expected_order_rate_eq(state):
    gap = customer_order_rate.get_value() - expected_order_rate.get_value()
    return gap / time_to_smooth_demand.get_value()

change_in_expected_order_rate = Flow(name="Change in Expected Order Rate", 
                                    source_stock=None,  # not a physical flow
                                    target_stock=expected_order_rate, 
                                    rate_function=change_in_expected_order_rate_eq)

# --- Prepare Simulation ---

# Collect components into lists
stocks = [inventory, expected_order_rate]
flows = [production_rate, shipment_rate, change_in_expected_order_rate]
auxiliaries = [customer_order_rate, desired_inventory_level, adjustment_from_inventory, 
              desired_production, max_shipment_rate, order_fulfillment_ratio]
parameters = [initial_customer_demand, safety_stock_time, time_to_adjust_inventory, 
             time_to_smooth_demand, order_processing_time,
             sine_amplitude, sine_period, noise_deviation,
             step_height, step_time]

# Initialize Simulation
sim = Simulation(stocks=stocks, flows=flows, auxiliaries=auxiliaries, parameters=parameters, timestep=1)

# Document Feedback Loops
# Production adjustment loop (B)
production_adjustment_components = [inventory, adjustment_from_inventory, desired_production, production_rate]
loop_B1 = BalancingLoop("Production Adjustment Loop (B1)", production_adjustment_components, 
                       "Low inventory -> positive adjustment -> higher desired production -> higher production rate -> higher inventory")
sim.add_loop(loop_B1)

# Demand estimation loop (B)
demand_estimation_components = [expected_order_rate, desired_inventory_level, adjustment_from_inventory, 
                              desired_production, production_rate, inventory, max_shipment_rate, 
                              order_fulfillment_ratio, shipment_rate]
loop_B2 = BalancingLoop("Demand Estimation Loop (B2)", demand_estimation_components, 
                       "Higher expected orders -> higher desired inventory -> positive adjustment -> higher production -> higher inventory -> higher max shipment rate -> higher order fulfillment -> higher shipments")
sim.add_loop(loop_B2)

# --- Run Simulation ---
simulation_duration = 100
sim.run(duration=simulation_duration)

# --- Display Results ---
results = sim.get_results()  # Get the simulation results as a DataFrame

# Create a chart object
chart = Chart(sim)

# Plot all stocks together
fig_stocks, ax_stocks = chart.plot_stocks_time_series(
    figsize=(12, 8),
    title="Inventory Model - Stock Values Over Time"
)
plt.savefig('inventory_model_stocks.png', dpi=300, bbox_inches='tight')

# Plot all flows together
fig_flows, ax_flows = chart.plot_flows_time_series(
    figsize=(12, 8),
    title="Inventory Model - Flow Rates Over Time"
)
plt.savefig('inventory_model_flows.png', dpi=300, bbox_inches='tight')

# Plot all auxiliary variables together
fig_aux, ax_aux = chart.plot_auxiliaries_time_series(
    figsize=(12, 8),
    title="Inventory Model - Auxiliary Variables Over Time"
)
plt.savefig('inventory_model_auxiliaries.png', dpi=300, bbox_inches='tight')


# Plot stocks, flows, and auxiliaries in separate subplots
fig_separate = chart.plot_variables_separately(figsize=(16, 12))
plt.savefig('inventory_model_separate_plots.png', dpi=300, bbox_inches='tight')

# Plot key variables of interest
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# Get the results in the correct format
stocks_df = results

# Plot inventory vs desired inventory
ax1.plot(results.index, stocks_df['Inventory'], label='Actual Inventory')
ax1.plot(results.index, stocks_df['Desired Inventory Level'], label='Desired Inventory')
ax1.set_ylabel('Units')
ax1.set_title('Inventory vs Desired Inventory')
ax1.legend()
ax1.grid(True)

# Plot production rate vs shipment rate
ax2.plot(results.index, stocks_df['Production Rate'], label='Production Rate')
ax2.plot(results.index, stocks_df['Shipment Rate'], label='Shipment Rate')
ax2.set_ylabel('Units/Time')
ax2.set_title('Production Rate vs Shipment Rate')
ax2.legend()
ax2.grid(True)

# Plot customer order rate vs expected order rate
ax3.plot(results.index, stocks_df['Customer Order Rate'], label='Customer Order Rate')
ax3.plot(results.index, stocks_df['Expected Order Rate'], label='Expected Order Rate')
ax3.set_xlabel('Time')
ax3.set_ylabel('Units/Time')
ax3.set_title('Customer Order Rate vs Expected Order Rate')
ax3.legend()
ax3.grid(True)

plt.tight_layout()
plt.savefig('inventory_model_key_variables.png', dpi=300, bbox_inches='tight')


# Plot only Order Fulfillment Ratio - Just one auxiliary variable
fig_ofr, ax_ofr = chart.plot_individual_auxiliary(
    auxiliary_name='Order Fulfillment Ratio',
    figsize=(10, 6), # You can adjust the figure size
    title='Order Fulfillment Ratio Over Time'
)
if fig_ofr: # Check if the plot was created successfully
    plt.savefig('order_fulfillment_ratio_plot.png', dpi=300, bbox_inches='tight')
    # plt.close(fig_ofr) # Optional: close the figure window if you only want to save it

# Create a graph visualization of the model
#model_graph = Graph(sim)

# Plot the graph
#fig, ax = model_graph.plot(figsize=(12, 10), show_values=True)
#plt.savefig('inventory_model_graph.png', dpi=300, bbox_inches='tight')

print("Simulation Complete. Results saved as PNG files in the current directory.")
print("Files saved: inventory_model_stocks.png, inventory_model_flows.png, inventory_model_auxiliaries.png,")
print("inventory_model_separate_plots.png, inventory_model_key_variables.png, inventory_model_graph.png")

# Uncomment to show plots interactively
# plt.show()
# examples/inventory_model_auto_loops.py

import sys
import os
import matplotlib.pyplot as plt
import numpy as np # Needed for Table interp and noise
import pandas as pd

# --- Path Setup ---
# (Assuming this is correct and pysydy is accessible)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
pysydy_package_dir = os.path.join(project_root, 'pysydy')
if os.path.isdir(pysydy_package_dir): # Check if the directory exists before adding
    if pysydy_package_dir not in sys.path:
        sys.path.insert(0, pysydy_package_dir)
else:
    print(f"Warning: Could not find the 'pysydy' package directory at: {pysydy_package_dir}")
    # For standalone execution, you might need to point to where pysydy classes are
    # Example: if pysydy is one level up:
    # parent_dir = os.path.dirname(project_root)
    # sys.path.insert(0, parent_dir)


# --- Library Imports ---
try:
    from pysydy.simulation import Simulation, DEFAULT_EPSILON, ureg, Q_ # Make ureg, Q_ accessible
    from pysydy.stock import Stock
    from pysydy.flow import Flow
    from pysydy.parameter import Parameter
    from pysydy.auxiliary import Auxiliary
    # from pysydy.units import units # Assuming your UnitManager is initialized and ureg comes from there
                                 # For this example, I'll use ureg directly from Simulation for simplicity if it's exposed
except ImportError as e:
    print(f"\n--- ImportError ---: {e}")
    print("Ensure pysydy package directory and required files (simulation.py, etc.) exist,")
    print("and that pysydy is in your PYTHONPATH or accessible via relative paths.")
    sys.exit(1)

ureg.define('widget = []') 
# --- Simple Table Class Implementation (Placeholder) ---
class Table:
    """Simple Table lookup with linear interpolation."""
    def __init__(self, x_values, y_values, name="Lookup Table"):
        if len(x_values) != len(y_values):
            raise ValueError("Table x_values and y_values must have the same length.")
        if not all(x_values[i] <= x_values[i+1] for i in range(len(x_values)-1)):
             raise ValueError("Table x_values must be monotonically increasing.")
        self.x_values = np.array(x_values)
        self.y_values = np.array(y_values)
        self.name = name
        # print(f"  Table '{name}' initialized.")

    def __call__(self, input_value):
        """Performs lookup using linear interpolation."""
        return np.interp(input_value, self.x_values, self.y_values)

# --- Define Model Components (WITH UNITS and revised Customer Order Rate) ---

# 1. Parameters
initial_customer_demand = Parameter("Initial Customer Demand", 10.0, unit="widget/day")
safety_stock_time = Parameter("Safety Stock Time", 2.0, unit="day")
time_to_adjust_inventory = Parameter("Time to Adjust Inventory", 8.0, unit="day")
time_to_smooth_demand = Parameter("Time to Smooth Demand", 8.0, unit="day")
order_processing_time = Parameter("Order Processing Time", 10.0, unit="day")

# Parameters for customer order pattern
sine_amplitude = Parameter("Sine Amplitude", 4.0, unit="widget/day") # Amplitude of demand rate
sine_period = Parameter("Sine Period", 20.0, unit="day") # Adjusted for visibility
noise_deviation_std = Parameter("Noise Deviation Std", 1.0, unit="widget/day") # Std dev of additive noise
step_height = Parameter("Step Height", 10.0, unit="widget/day") # Height of step in demand rate
step_time = Parameter("Step Time", 50.0, unit="day") # Step happens later

# 2. Stocks
inventory = Stock("Inventory", initial_value=100.0, unit="widget")
expected_order_rate = Stock("Expected Order Rate", initial_value=10.0, unit="widget/day")

# --- 3. Auxiliaries ---

def calculate_customer_order_rate_simplified(state):
    """Simplified, dimensionally consistent customer order rate."""
    t_qty = state['time'] # Quantity, e.g., 10 day
    params = state['parameters']

    base_demand = params['Initial Customer Demand'].value
    step_h_val = params['Step Height'].value
    step_t_val = params['Step Time'].value
    sine_amp_val = params['Sine Amplitude'].value
    sine_p_val = params['Sine Period'].value
    # noise_std_val = params['Noise Deviation Std'].value

    current_rate = base_demand

    if t_qty >= step_t_val:
        current_rate += step_h_val
    
    if sine_p_val.magnitude > 1e-9: # Avoid division by zero
        # t_qty and sine_p_val must have compatible time units for division to be dimensionless
        time_ratio_for_sine = (t_qty / sine_p_val).to_base_units().magnitude
        current_rate += sine_amp_val * np.sin(2 * np.pi * time_ratio_for_sine)

    # Additive noise (optional, can be complex to make perfectly match Vensim)
    # For simplicity, let's use a placeholder for noise if needed, or omit for core dynamics.
    # if noise_std_val.magnitude > 0:
    #     noise_effect = np.random.normal(0, noise_std_val.magnitude) * ureg(noise_std_val.units)
    #     current_rate += noise_effect
    
    # Ensure non-negative
    return max(Q_(0, base_demand.units), current_rate)

customer_order_rate = Auxiliary(
    name="Customer Order Rate",
    calculation_function=calculate_customer_order_rate_simplified,
    inputs=["Initial Customer Demand", "Step Height", "Step Time",
            "Sine Amplitude", "Sine Period", "Noise Deviation Std"], # Time is implicit
    unit="widget/day"
)

def calculate_desired_inventory(state):
    eor = state['stocks']['Expected Order Rate'].value
    opt = state['parameters']['Order Processing Time'].value
    sst = state['parameters']['Safety Stock Time'].value
    return max(Q_(0, "widget"), eor * (opt + sst))
desired_inventory_level = Auxiliary(
    name="Desired Inventory Level",
    calculation_function=calculate_desired_inventory,
    inputs=["Expected Order Rate", "Order Processing Time", "Safety Stock Time"],
    unit="widget"
)

def calculate_adjustment(state):
    desired = state['auxiliaries']['Desired Inventory Level'].value
    current = state['stocks']['Inventory'].value
    tta = state['parameters']['Time to Adjust Inventory'].value
    if tta.magnitude == 0: return Q_(0, "widget/day")
    inventory_gap = desired - current
    return inventory_gap / tta
adjustment_from_inventory = Auxiliary(
    name="Adjustment from Inventory",
    calculation_function=calculate_adjustment,
    inputs=["Desired Inventory Level", "Inventory", "Time to Adjust Inventory"],
    unit="widget/day"
)

def calculate_desired_production(state):
    eor = state['stocks']['Expected Order Rate'].value
    adj = state['auxiliaries']['Adjustment from Inventory'].value
    return max(Q_(0, "widget/day"), eor + adj)
desired_production = Auxiliary(
    name="Desired Production",
    calculation_function=calculate_desired_production,
    inputs=["Expected Order Rate", "Adjustment from Inventory"],
    unit="widget/day"
)

def calculate_max_shipment_rate(state):
    inv = state['stocks']['Inventory'].value
    opt = state['parameters']['Order Processing Time'].value
    if opt.magnitude == 0: return Q_(0, "widget/day")
    return max(Q_(0, "widget/day"), inv / opt)
max_shipment_rate = Auxiliary(
    name="Max Shipment Rate",
    calculation_function=calculate_max_shipment_rate,
    inputs=["Inventory", "Order Processing Time"],
    unit="widget/day"
)

fulfillment_table = Table(
    x_values=[0, 0.15, 0.32, 0.53, 0.85, 1.25, 2],
    y_values=[0, 0.28, 0.54, 0.72, 0.81, 0.90, 1],
    name="Order Fulfillment Table"
)

def calculate_order_fulfillment_ratio(state):
    cor = state['auxiliaries']['Customer Order Rate'].value
    msr = state['auxiliaries']['Max Shipment Rate'].value
    if cor.magnitude == 0: return Q_(1.0, "dimensionless") # Fulfillment is 100% if no orders
    # Ratio should be dimensionless for the table
    ratio_val = (msr / cor).to_base_units().magnitude
    clamped_ratio = np.clip(ratio_val, fulfillment_table.x_values[0], fulfillment_table.x_values[-1])
    return Q_(fulfillment_table(clamped_ratio), "dimensionless")
order_fulfillment_ratio = Auxiliary(
    name="Order Fulfillment Ratio",
    calculation_function=calculate_order_fulfillment_ratio,
    inputs=["Customer Order Rate", "Max Shipment Rate"],
    unit="dimensionless"
)

# --- 4. Flows ---
def production_rate_func(state):
    desired_prod = state['auxiliaries']['Desired Production'].value
    return max(Q_(0,"widget/day"), desired_prod)
production_rate = Flow(
    name="Production Rate", source_stock=None, target_stock=inventory,
    rate_function=production_rate_func, inputs=["Desired Production"], unit="widget/day"
)

def shipment_rate_func(state):
    cor = state['auxiliaries']['Customer Order Rate'].value
    ofr = state['auxiliaries']['Order Fulfillment Ratio'].value # Dimensionless quantity
    return max(Q_(0,"widget/day"), cor * ofr) # (widget/day) * dimensionless -> widget/day
shipment_rate = Flow(
    name="Shipment Rate", source_stock=inventory, target_stock=None,
    rate_function=shipment_rate_func, inputs=["Customer Order Rate", "Order Fulfillment Ratio"], unit="widget/day"
)

def change_eor_func(state):
    cor = state['auxiliaries']['Customer Order Rate'].value
    eor = state['stocks']['Expected Order Rate'].value
    ttsd = state['parameters']['Time to Smooth Demand'].value
    if ttsd.magnitude == 0: return Q_(0, "widget/day**2")
    gap = cor - eor # widget/day
    return gap / ttsd # (widget/day) / day = widget/day/day**2
change_in_expected_order_rate = Flow(
    name="Change in Expected Order Rate", source_stock=None, target_stock=expected_order_rate,
    rate_function=change_eor_func,
    inputs=["Customer Order Rate", "Expected Order Rate", "Time to Smooth Demand"],
    unit="widget/day**2" # Rate of change of a rate
)

# --- Simulation Setup ---
print("Setting up simulation...")
stocks_list = [inventory, expected_order_rate]
flows_list = [production_rate, shipment_rate, change_in_expected_order_rate]
auxiliaries_list = [
    customer_order_rate, max_shipment_rate, order_fulfillment_ratio,
    desired_inventory_level, adjustment_from_inventory, desired_production
]
parameters_list = [
    initial_customer_demand, safety_stock_time, time_to_adjust_inventory,
    time_to_smooth_demand, order_processing_time, sine_amplitude,
    sine_period, noise_deviation_std, step_height, step_time
]

# Ensure DEFAULT_EPSILON is small enough if values are small, or adjust if needed
# The perturbation in _estimate_link_sign uses DEFAULT_EPSILON.
# print(f"Using DEFAULT_EPSILON: {DEFAULT_EPSILON}")


sim = Simulation(
    stocks=stocks_list,
    flows=flows_list,
    auxiliaries=auxiliaries_list,
    parameters=parameters_list,
    timestep=1.0,
    timestep_unit='day' # Ensure this matches units used in parameters like 'Sine Period'
)
print("Simulation object created.")

# --- Analysis using Simulation methods ---
print("\nRunning simulation for analysis...")
sim.run(duration=100) # Run for 100 days

print("\n--- Analysis Results ---")

# 1. Print Detected Loops and their Polarities
sim.print_loops()

# 2. Print All Model Relationships and Link Polarities
sim.print_relationships()

# 3. Plot and Save the Model Structure Graph
sim.plot_structure_graph(filename="inventory_model_structure.png", k=0.8, figsize=(20,15)) # Adjusted k and figsize

# 4. Plot Simulation Results
# Plot all stocks, flows, and auxiliaries together
sim.plot_results(filename="inventory_model_results_all.png")

# Plot individual stocks (optional)
# sim.plot_each_stock()

# Plot specific variables of interest separately
sim.plot_results(
    columns=["Inventory", "Expected Order Rate", "Customer Order Rate", "Shipment Rate", "Production Rate"],
    together=False, # Plot each in a separate file
    filename="inventory_model_key_vars.png" # Base filename for separate plots
)

# 5. Get Results as a Pandas DataFrame
results_df = sim.get_results_for_plot()

print("\n--- End of Analysis ---")
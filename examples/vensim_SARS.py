import sys
import os
import matplotlib.pyplot as plt

# --- Path Setup ---
# (Same as before)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
pysydy_package_dir = os.path.join(project_root, 'pysydy')
if os.path.isdir(pysydy_package_dir):
    if pysydy_package_dir not in sys.path:
         sys.path.insert(0, pysydy_package_dir)
else:
    print(f"Warning: Could not find the 'pysydy' package directory at: {pysydy_package_dir}")

# --- Library Imports ---
try:
    from pysydy.simulation import Simulation, ureg, Q_
    from pysydy.stock import Stock
    from pysydy.flow import Flow
    from pysydy.parameter import Parameter
    from pysydy.auxiliary import Auxiliary
except ImportError as e:
    print(f"\n--- ImportError ---: {e}")
    print("Ensure pysydy package and required files exist, and ureg, Q_ are exposed from pysydy.simulation.")
    sys.exit(1)

try:
    ureg.Unit('person')
except:
    ureg.define('person = []')


# --- Define Model Components ---

# Parameters
_initial_total_pop = 350.0 # Define this once for consistency

contact_frequency = Parameter(
    name="Contact Frequency",
    value=10.0,
    unit="1/day"
)
infectivity = Parameter(
    name="Infectivity",
    value=0.05,
    unit="dimensionless"
)
total_population_param = Parameter( # <<<< CHANGED TO PARAMETER
    name="Total Population",
    value=_initial_total_pop,
    unit="person"
)

# Stocks
initial_susceptible = _initial_total_pop - 1.0
initial_infected = 1.0

pop_susceptible = Stock(
    name="Population Susceptible to SARS", initial_value=initial_susceptible, unit="person"
)
pop_infected = Stock(
    name="Population infected with SARS", initial_value=initial_infected, unit="person"
)
cumulative_cases = Stock(
    name="Cumulative Reported Cases", initial_value=initial_infected, unit="person"
)

# Auxiliaries
# "Total Population" is now a Parameter, so we remove the Auxiliary for it.

def calculate_susceptible_contacts(state):
    sus = state['stocks']["Population Susceptible to SARS"].value
    cf = state['parameters']["Contact Frequency"].value
    return sus * cf

susceptible_contacts = Auxiliary(
    name="Susceptible Contacts",
    calculation_function=calculate_susceptible_contacts,
    inputs=["Population Susceptible to SARS", "Contact Frequency"],
    unit="person / day"
)

def calculate_prob_contact_infected(state):
    infected = state['stocks']["Population infected with SARS"].value
    total_pop_val = state['parameters']["Total Population"].value # <<<< CHANGED: Access from parameters
    if total_pop_val.magnitude > 1e-9:
        return (infected / total_pop_val).to_base_units()
    return Q_(0.0, "dimensionless")

prob_contact_infected = Auxiliary(
    name="Probability of contacts with Infected people",
    calculation_function=calculate_prob_contact_infected,
    inputs=["Population infected with SARS", "Total Population"], # "Total Population" is now a Parameter
    unit="dimensionless"
)

def calculate_contacts_inf_uninf(state):
    sus_contacts_val = state['auxiliaries']["Susceptible Contacts"].value
    prob_inf_val = state['auxiliaries']["Probability of contacts with Infected people"].value
    return sus_contacts_val * prob_inf_val

contacts_inf_uninf = Auxiliary(
    name="Contacts between Infected and Uninfected People",
    calculation_function=calculate_contacts_inf_uninf,
    inputs=["Susceptible Contacts", "Probability of contacts with Infected people"],
    unit="person / day"
)

# Flows (definitions remain the same)
def infection_rate_eq(state):
    contacts_iu_val = state['auxiliaries']["Contacts between Infected and Uninfected People"].value
    infectivity_val = state['parameters']["Infectivity"].value
    return contacts_iu_val * infectivity_val

infection_rate = Flow(
    name="Infection Rate",
    source_stock=pop_susceptible,
    target_stock=pop_infected,
    rate_function=infection_rate_eq,
    inputs=["Contacts between Infected and Uninfected People", "Infectivity"],
    unit="person/day"
)

def new_reported_cases_eq(state):
    return state['flows']["Infection Rate"].rate

new_reported_cases = Flow(
    name="New Reported Cases",
    source_stock=None,
    target_stock=cumulative_cases,
    rate_function=new_reported_cases_eq,
    inputs=["Infection Rate"],
    unit="person/day"
)

# --- Prepare Simulation ---
stocks_list = [pop_susceptible, pop_infected, cumulative_cases]
flows_list = [infection_rate, new_reported_cases]
# Remove total_population_aux from this list
auxiliaries_list = [susceptible_contacts, prob_contact_infected, contacts_inf_uninf]
# Add total_population_param to this list
parameters_list = [contact_frequency, infectivity, total_population_param]

# Initialize Simulation
sim = Simulation(
    stocks=stocks_list,
    flows=flows_list,
    auxiliaries=auxiliaries_list,
    parameters=parameters_list, # Make sure total_population_param is included
    timestep=0.1,
    timestep_unit="day"
)
print("SARS Model Simulation object created (Total Population as Parameter).")

# --- Run Simulation ---
# ... (rest of your simulation run and plotting code remains the same)
simulation_duration = 120 # days
print(f"Running simulation for {simulation_duration} {sim.timestep.units}...")
sim.run(duration=simulation_duration)
print("Simulation run complete.")

# --- Analysis and Display Results ---
print("\n--- Model Analysis Results ---")
output_dir = "sars_model_v4_param_N_outputs" # Changed output dir name
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
print(f"Saving graph and plots to ./{output_dir}/")

# 1. Print Detected Loops and their Polarities
sim.print_loops()

# 2. Print All Model Relationships and Link Polarities
sim.print_relationships()

# 3. Plot and Save the Model Structure Graph
sim.plot_structure_graph(filename=os.path.join(output_dir, "sars_model_structure.png"), k=0.7, figsize=(18,14))

# 4. Plot Simulation Results
results_df_for_plot = sim.get_results_for_plot()

if results_df_for_plot.empty:
    print("No results to plot.")
else:
    stock_names = [s.name for s in stocks_list if s.name in results_df_for_plot.columns]
    flow_names = [f.name for f in flows_list if f.name in results_df_for_plot.columns]
    # "Total Population" will not be in aux_names if it's a parameter and not explicitly recorded
    # unless your sim._record_state or sim.get_results also includes parameters.
    # For plotting, we can add it to plot_cols if needed and if present in results.
    aux_names_to_plot = [a.name for a in auxiliaries_list if a.name in results_df_for_plot.columns]

    key_vars = ["Population Susceptible to SARS", "Population infected with SARS", "Infection Rate", "Cumulative Reported Cases"]
    key_vars_present = [v for v in key_vars if v in results_df_for_plot.columns]


    sim.plot_results(
        columns=stock_names,
        together=True,
        figsize=(12, 7),
        title="SARS Model - Stocks Over Time",
        filename=os.path.join(output_dir, 'sars_model_stocks.png')
    )
    sim.plot_results(
        columns=flow_names,
        together=True,
        figsize=(12, 7),
        title="SARS Model - Flows Over Time",
        filename=os.path.join(output_dir, 'sars_model_flows.png')
    )
    if aux_names_to_plot: # Check if there are any auxiliaries to plot
        sim.plot_results(
            columns=aux_names_to_plot,
            together=True,
            figsize=(12, 7),
            title="SARS Model - Auxiliaries Over Time",
            filename=os.path.join(output_dir,'sars_model_auxiliaries.png')
        )
    if key_vars_present:
        sim.plot_results(
            columns=key_vars_present,
            together=True,
            figsize=(12, 7),
            title="SARS Model - Key Dynamics",
            filename=os.path.join(output_dir,'sars_model_key_dynamics.png')
        )
    else:
        print("Warning: None of the predefined key variables found in results for plotting.")


# 5. Get Results as a Pandas DataFrame
results_df_with_units = sim.get_results()
print("\n--- Simulation Results (first 5 rows with units) ---")
print(results_df_with_units.head())

sim.plot_structure_graph(filename="sars_graph.png", k=0.8, figsize=(20,15)) # Adjusted k and figsize

print(f"\nAnalysis complete. Outputs are in './{output_dir}/' directory.")
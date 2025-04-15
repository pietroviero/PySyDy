import sys
import os
import matplotlib.pyplot as plt

# Add the parent directory (PySyDy) to the Python path
# This allows importing pysydy modules when running the script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pysydy import Simulation, Stock, Flow, Parameter, Auxiliary, Graph
from pysydy.chart import Chart  # Import the Chart class
from pysydy import ReinforcingLoop, BalancingLoop # For documentation
from pysydy.behavior_modes import ExponentialGrowth, ExponentialDecay, GoalSeeking, Oscillation, SShapedGrowth  # For behavior pattern documentation

# --- Define Model Components ---

# Parameters
contact_frequency = Parameter("Contact Frequency", 1) # contacts per person per time unit (e.g., day)
infectivity = Parameter("Infectivity", 0.1) # probability of transmission per contact

# Stocks
# Need initial values - let's assume a starting population for calculation
# We'll define total_pop as a simple variable first for initial calculation
_initial_total_pop = 500 
initial_susceptible = _initial_total_pop - 1
initial_infected = 1

pop_susceptible = Stock("Population Susceptible to SARS", initial_susceptible)
pop_infected = Stock("Population infected with SARS", initial_infected)
cumulative_cases = Stock("Cumulative Reported Cases", initial_infected) # Start counting from initial infected

# Auxiliaries
# Note: Order matters if auxiliaries depend on each other
# Lambda functions now accept one argument (state), even if unused
total_population = Auxiliary("Total Population", lambda state: pop_susceptible.get_value() + pop_infected.get_value())
susceptible_contacts = Auxiliary("Susceptible Contacts", lambda state: pop_susceptible.get_value() * contact_frequency.get_value())

# Handle division by zero if total_population is 0 initially (though unlikely here)
# This function doesn't need the state explicitly, but the Auxiliary framework might pass it
def calculate_prob_contact_infected(state): # Add state argument
    tot_pop = total_population.get_value() # Assumes total_population is calculated first in the step
    if isinstance(tot_pop, (int, float)) and tot_pop > 0:
        # Assumes pop_infected value is current for this step
        return pop_infected.get_value() / tot_pop
    else:
        return 0
# Pass the function reference, it now accepts state
prob_contact_infected = Auxiliary("Probability of contacts with Infected people", calculate_prob_contact_infected) 

def calculate_contacts_inf_uninf(state):
    susceptible_value = susceptible_contacts.get_value()
    prob_infected_value = prob_contact_infected.get_value()
    
    if susceptible_value is not None and prob_infected_value is not None:
        # Convert values to float to ensure numeric multiplication
        # Ensure values are numeric before multiplication
        try:
            # Ensure values are numeric and can be converted to float
            if isinstance(susceptible_value, (int, float)) and isinstance(prob_infected_value, (int, float)):
                return float(susceptible_value) * float(prob_infected_value)
            return 0.0
        except (TypeError, ValueError):
            return 0.0
    return 0

contacts_inf_uninf = Auxiliary("Contacts between Infected and Uninfected People", calculate_contacts_inf_uninf)

# Flows
# Define the equation for the flow first
def infection_rate_eq(state): # Add state argument
    # Ensure dependencies are calculated based on their current values
    # Note: The Simulation class needs to handle calculation order correctly
    # Note: The Simulation class needs to handle calculation order correctly
    # The rate_function passed to Flow might receive system_state, but we assume
    # dependencies (auxiliaries) are calculated beforehand in the sim loop.
    contacts_value = contacts_inf_uninf.get_value()
    infectivity_value = infectivity.get_value()
    
    if contacts_value is not None and infectivity_value is not None:
        try:
            # Ensure values are numeric and handle potential type conversion errors
            try:
                contacts_float = float(contacts_value if contacts_value is not None else 0)
                infectivity_float = float(infectivity_value if infectivity_value is not None else 0)
                return contacts_float * infectivity_float
            except (TypeError, ValueError):
                return 0.0
        except (TypeError, ValueError):
            return 0.0
    return 0.0

# Create the Flow objects with correct arguments
infection_rate = Flow(name="Infection Rate", 
                        source_stock=pop_susceptible, 
                        target_stock=pop_infected, 
                        rate_function=infection_rate_eq)

# Define the New Reported Cases flow 
# Source is None as it represents the rate itself flowing into the cumulative stock
new_reported_cases = Flow(name="New Reported Cases", 
                          source_stock=None, 
                          target_stock=cumulative_cases, 
                          rate_function=lambda system_state: infection_rate.get_rate()) # Use the calculated rate

# Connecting flows to stocks is now handled within the Flow constructor
# Remove redundant calls:
# pop_susceptible.add_outflow(infection_rate)
# pop_infected.add_inflow(infection_rate)
# cumulative_cases.add_inflow(new_reported_cases)

# --- Prepare Simulation ---

# Collect components into lists
stocks = [pop_susceptible, pop_infected, cumulative_cases]
flows = [infection_rate, new_reported_cases]
auxiliaries = [total_population, susceptible_contacts, prob_contact_infected, contacts_inf_uninf]
parameters = [contact_frequency, infectivity]

# Initialize Simulation
sim = Simulation(stocks=stocks, flows=flows, auxiliaries=auxiliaries, parameters=parameters, timestep=0.1)

# (Optional) Document Feedback Loops
# Components involved in the Reinforcing 'Contagion' loop (R)
contagion_components = [pop_infected, prob_contact_infected, contacts_inf_uninf, infection_rate]
loop_R = ReinforcingLoop("Contagion Loop (R)", contagion_components, "More infected -> higher probability of contact -> more contacts -> higher infection rate -> more infected")
sim.add_loop(loop_R)

# Components involved in the Balancing 'Depletion' loop (B)
depletion_components = [pop_susceptible, susceptible_contacts, contacts_inf_uninf, infection_rate]
loop_B = BalancingLoop("Depletion Loop (B)", depletion_components, "More infected -> higher infection rate -> fewer susceptible -> fewer susceptible contacts -> fewer contacts -> lower infection rate")
sim.add_loop(loop_B)

# --- Run Simulation ---
simulation_duration = 120
sim.run(duration=simulation_duration)

# --- Display Results ---
results = sim.get_results() # Get the simulation results as a DataFrame

chart = Chart(sim)

# Plot all stocks together
fig_stocks, ax_stocks = chart.plot_stocks_time_series(
    figsize=(12, 8),
    title="SARS Model - Stock Values Over Time"
)
plt.savefig('sars_model_stocks.png', dpi=300, bbox_inches='tight')

# Plot all flows together
fig_flows, ax_flows = chart.plot_flows_time_series(
    figsize=(12, 8),
    title="SARS Model - Flow Rates Over Time"
)
plt.savefig('sars_model_flows.png', dpi=300, bbox_inches='tight')

# Plot all auxiliary variables together
fig_aux, ax_aux = chart.plot_auxiliaries_time_series(
    figsize=(12, 8),
    title="SARS Model - Auxiliary Variables Over Time"
)
plt.savefig('sars_model_auxiliaries.png', dpi=300, bbox_inches='tight')

# Plot stocks, flows, and auxiliaries on the same graph
fig_all, ax_all = chart.plot_all_variables(
    figsize=(14, 10),
    title="SARS Model - All Variables Over Time"
)
plt.savefig('sars_model_all_variables.png', dpi=300, bbox_inches='tight')

# Plot stocks, flows, and auxiliaries in separate subplots
fig_separate = chart.plot_variables_separately(figsize=(16, 12))
plt.savefig('sars_model_separate_plots.png', dpi=300, bbox_inches='tight')

# Plot individual stock of interest
fig_susceptible, ax_susceptible = chart.plot_individual_stock(
    "Population Susceptible to SARS",
    figsize=(10, 6),
    title="Susceptible Population Over Time"
)
plt.savefig('sars_model_susceptible.png', dpi=300, bbox_inches='tight')

# Plot individual flow of interest
fig_infection, ax_infection = chart.plot_individual_flow(
    "Infection Rate",
    figsize=(10, 6),
    title="Infection Rate Over Time"
)
plt.savefig('sars_model_infection_rate.png', dpi=300, bbox_inches='tight')

# Plot individual auxiliary variable of interest
fig_prob, ax_prob = chart.plot_individual_auxiliary(
    "Probability of contacts with Infected people",
    figsize=(10, 6),
    title="Infection Probability Over Time"
)
plt.savefig('sars_model_infection_probability.png', dpi=300, bbox_inches='tight')

print("Simulation Complete. Results saved as PNG files in the current directory.")
print("Files saved: sars_model_stocks.png, sars_model_flows.png, sars_model_auxiliaries.png,")
print("sars_model_all_variables.png, sars_model_separate_plots.png, sars_model_susceptible.png,")
print("sars_model_infection_rate.png, sars_model_infection_probability.png")
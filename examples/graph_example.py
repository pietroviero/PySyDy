import sys
import os

# Add the parent directory to the path so we can import pysydy
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pysydy
import matplotlib.pyplot as plt

# Create stocks (compartments)
susceptible = pysydy.Stock('Susceptible', 9999)
infected = pysydy.Stock('Infected', 1)
recovered = pysydy.Stock('Recovered', 0)

# Create parameters
contact_rate = pysydy.Parameter('contact_rate', 6.0, units='contacts/person/day')
infectivity = pysydy.Parameter('infectivity', 0.25, units='probability')
infectious_period = pysydy.Parameter('infectious_period', 2.0, units='days')  # Average duration of infectivity
total_population = pysydy.Parameter('total_population', 10000.0, units='people')

# Create flows
infection_flow = pysydy.Flow(
    name='infection',
    source_stock=susceptible,
    target_stock=infected,
    rate_function=lambda state: (
        state['parameters']['contact_rate'].value *
        state['parameters']['infectivity'].value *
        state['stocks']['Susceptible'].value *
        state['stocks']['Infected'].value /
        state['parameters']['total_population'].value
    )
)

recovery_flow = pysydy.Flow(
    name='recovery',
    source_stock=infected,
    target_stock=recovered,
    rate_function=lambda state: (
        (1.0 / state['parameters']['infectious_period'].value) *
        state['stocks']['Infected'].value
    )
)

# Create and run simulation
sim = pysydy.Simulation(
    stocks=[susceptible, infected, recovered],
    flows=[infection_flow, recovery_flow],
    auxiliaries=[],
    parameters=[contact_rate, infectivity, infectious_period, total_population],
    timestep=0.1  # Smaller timestep for better accuracy
)

# Create a graph visualization of the model
model_graph = pysydy.Graph(sim)

# Plot the graph
fig, ax = model_graph.plot(figsize=(10, 8), show_values=True)
plt.savefig('sir_model_graph.png')  # Save the graph as an image
plt.show()

# Run a few simulation steps
print("Running simulation for 5 days...")
sim.run(duration=5)

# Update the graph with new values
model_graph.update_graph()

# Plot the updated graph
fig, ax = model_graph.plot(figsize=(10, 8), show_values=True)
plt.title('SIR Model After 5 Days')
plt.savefig('sir_model_graph_after_5_days.png')
plt.show()

print("\nTo use the interactive plot feature in a Jupyter notebook, use:")
print("model_graph.interactive_plot()")
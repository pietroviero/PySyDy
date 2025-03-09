import pysydy

# 1. Stocks
population = pysydy.Stock(name="Population", initial_value=1000)
resources = pysydy.Stock(name="Resources", initial_value=5000)

# 2. Parameters (Constants)
area = 100.0  # Square kilometers (example area)

# 3. Auxiliary Variable (now as an Auxiliary object)
def population_density_calculation(system_state):
    """Calculation function for population density."""
    pop = system_state['Population'].get_value()
    return pop / system_state['Area'] # Access 'Area' from system_state

population_density = pysydy.Auxiliary(
    name="PopulationDensity",
    calculation_function=population_density_calculation,
    inputs=['Population', 'Area'] # Documenting inputs (optional)
)

# 4. Flows (Births and Consumption - rate functions can now use the Auxiliary)
def birth_rate_function(system_state):
    return system_state['Population'].get_value() * 0.02

def consumption_rate_function(system_state):
    pop = system_state['Population'].get_value()
    res = system_state['Resources'].get_value()
    density = system_state['PopulationDensity'].get_value() # Get value from Auxiliary
    # Example: Consumption could be affected by density (not used in this simple example)
    # consumption_factor = 1.0 + (density / 100)
    # consumption_rate = pop * 0.1 * consumption_factor
    if res > 0:
        return pop * 0.1
    else:
        return 0.0

births = pysydy.Flow(
    name="Births",
    source_stock=None,
    target_stock=population,
    rate_function=birth_rate_function
)

consumption = pysydy.Flow(
    name="Consumption",
    source_stock=resources,
    target_stock=None,
    rate_function=consumption_rate_function
)

# 5. Simulation
system_state = {
    'Population': population,
    'Resources': resources,
    'Area': area, # Include parameter in system state
    'PopulationDensity': population_density # Include auxiliary in system state
}
timestep = 1.0
simulation_time = 50

time_points = range(simulation_time + 1)
population_values = []
resource_values = []
density_values = []

for _ in time_points:
    population_values.append(population.get_value())
    resource_values.append(resources.get_value())

    population_density.calculate_value(system_state) # Calculate auxiliary value
    density_values.append(population_density.get_value())

    births.calculate_rate(system_state)
    consumption.calculate_rate(system_state)

    population.update(timestep)
    resources.update(timestep)

# 6. Print Results (including Density)
print("Time\tPopulation\tResources\tDensity")
for t in time_points:
    print(f"{t}\t{population_values[t]:.2f}\t\t{resource_values[t]:.2f}\t\t{density_values[t]:.2f}")
import pysydy
import matplotlib.pyplot as plt
import pandas as pd

# Create stocks (compartments)
susceptible = pysydy.Stock('Susceptible', 9999)
infected = pysydy.Stock('Infected', 1)
recovered = pysydy.Stock('Recovered', 0)

# Create parameters
contact_rate = pysydy.Parameter('contact_rate', 6.0, units='contacts/person/day')
infectivity = pysydy.Parameter('infectivity', 0.25, units='probability')
recovery_rate = pysydy.Parameter('recovery_rate', 0.5, units='1/day')  # 1/2 days
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
        state['parameters']['recovery_rate'].value *
        state['stocks']['Infected'].value
    )
)

# Create and run simulation
sim = pysydy.Simulation(
    stocks=[susceptible, infected, recovered],
    flows=[infection_flow, recovery_flow],
    auxiliaries=[],
    parameters=[contact_rate, infectivity, recovery_rate, total_population],
    timestep=0.1  # Smaller timestep for better accuracy
)

sim.run(duration=30)  # Simulate 30 days

# Plot results
results = sim.get_results()
df = results['stocks'].apply(pd.Series)
df.columns = ['Susceptible', 'Infected', 'Recovered']

plt.figure(figsize=(10, 6))
plt.plot(df)
plt.title('SIR Model Dynamics')
plt.xlabel('Days')
plt.ylabel('Population')
plt.legend(df.columns)
plt.grid(True)
plt.show()
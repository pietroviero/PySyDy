import pysydy
import matplotlib.pyplot as plt
import pandas as pd
from ipywidgets import interact, FloatSlider
import numpy as np

# Initialize stocks with fixed initial values
susceptible = pysydy.Stock('Susceptible', 9999)
infected = pysydy.Stock('Infected', 1)
recovered = pysydy.Stock('Recovered', 0)

# Create mutable parameter objects
params = {
    'contact_rate': pysydy.Parameter('contact_rate', 6.0),
    'infectivity': pysydy.Parameter('infectivity', 0.25),
    'recovery_rate': pysydy.Parameter('recovery_rate', 0.5),
    'total_population': pysydy.Parameter('total_population', 10000.0)
}

# Create flows with lambda functions that reference the parameter objects
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

# Create a reusable simulation object
sim = pysydy.Simulation(
    stocks=[susceptible, infected, recovered],
    flows=[infection_flow, recovery_flow],
    auxiliaries=[],
    parameters=list(params.values()),
    timestep=0.1
)

# Set up plot
plt.ioff()
fig, ax = plt.subplots(figsize=(10, 6))
lines = {}

def update_plot(results):
    df = results['stocks'].apply(pd.Series)
    df.columns = ['Susceptible', 'Infected', 'Recovered']
    
    for col in df.columns:
        if col not in lines:
            lines[col], = ax.plot(df.index, df[col], label=col)
        else:
            lines[col].set_ydata(df[col])
    
    ax.relim()
    ax.autoscale_view()
    ax.legend(loc='upper right')
    fig.canvas.draw()

def run_simulation(contact_rate, infectivity, recovery_days):
    # Update parameter values
    params['contact_rate'].value = contact_rate
    params['infectivity'].value = infectivity
    params['recovery_rate'].value = 1/recovery_days  # Convert days to rate
    
    # Reset stocks to initial values
    susceptible.value = 9999
    infected.value = 1
    recovered.value = 0
    sim.history = []
    sim.time = 0.0
    
    # Run simulation
    sim.run(duration=30)
    update_plot(sim.get_results())

# Create interactive widgets
interact(
    run_simulation,
    contact_rate=FloatSlider(min=1, max=10, step=0.5, value=6, description="Contacts/day"),
    infectivity=FloatSlider(min=0.1, max=0.5, step=0.05, value=0.25, description="Infectivity"),
    recovery_days=FloatSlider(min=1, max=5, step=0.5, value=2, description="Infectious Period (days)")
)

ax.set_title('Interactive SIR Model')
ax.set_xlabel('Days')
ax.set_ylabel('Population')
ax.grid(True)
plt.tight_layout()
plt.show()
import matplotlib.pyplot as plt
import ipywidgets as widgets
from ipywidgets import interact

# Import your library classes (adjust the import path as needed)
from pysydy import Stock, Flow

def simulate_sir(contact_rate=6.0, infectivity=0.25, duration=2.0, initial_infected=1, days=30):
    """
    Runs an SIR simulation with the given parameters and plots the results.
    
    Parameters:
        contact_rate (float): The contact rate per person per day.
        infectivity (float): The probability of infection per contact.
        duration (float): Average duration (in days) that an individual remains infectious.
        initial_infected (int): The initial number of infectious individuals.
        days (int): The number of days to simulate.
    """
    # Total population remains constant
    N = 10_000
    I0 = initial_infected
    S0 = N - I0
    R0 = 0

    # Create Stocks from your library
    S = Stock("Susceptible", initial_value=S0)
    I = Stock("Infectious", initial_value=I0)
    R = Stock("Recovered",   initial_value=R0)

    # Define flow rate functions
    def infection_rate(system_state):
        # Infection flow from Susceptible to Infectious:
        S_val = system_state["Susceptible"].get_value()
        I_val = system_state["Infectious"].get_value()
        return contact_rate * infectivity * (S_val * I_val / N)

    def recovery_rate(system_state):
        # Recovery flow from Infectious to Recovered:
        I_val = system_state["Infectious"].get_value()
        return I_val / duration

    # Create Flows using your library classes
    infection_flow = Flow(
        name="InfectionFlow",
        source_stock=S,
        target_stock=I,
        rate_function=infection_rate
    )

    recovery_flow = Flow(
        name="RecoveryFlow",
        source_stock=I,
        target_stock=R,
        rate_function=recovery_rate
    )

    # Lists to store simulation history
    susceptible_history = []
    infectious_history = []
    recovered_history = []
    time_points = list(range(days + 1))

    # Run the simulation over the specified number of days
    for t in time_points:
        susceptible_history.append(S.get_value())
        infectious_history.append(I.get_value())
        recovered_history.append(R.get_value())

        # Calculate flow rates based on the current state
        system_state = {"Susceptible": S, "Infectious": I, "Recovered": R}
        infection_flow.calculate_rate(system_state)
        recovery_flow.calculate_rate(system_state)

        # Update stocks with a timestep of 1 day
        S.update(1.0)
        I.update(1.0)
        R.update(1.0)

    # Plot the results
    plt.figure(figsize=(8, 6))
    plt.plot(time_points, susceptible_history, label="Susceptible")
    plt.plot(time_points, infectious_history, label="Infectious")
    plt.plot(time_points, recovered_history, label="Recovered")
    plt.xlabel("Days")
    plt.ylabel("Population")
    plt.title("Interactive SIR Model Simulation")
    plt.legend()
    plt.show()

# Create interactive widgets for the parameters.
interact(
    simulate_sir,
    contact_rate=widgets.FloatSlider(min=1, max=10, step=0.5, value=6.0, description="Contact Rate"),
    infectivity=widgets.FloatSlider(min=0.1, max=1.0, step=0.05, value=0.25, description="Infectivity"),
    duration=widgets.FloatSlider(min=1.0, max=10.0, step=0.5, value=2.0, description="Duration"),
    initial_infected=widgets.IntSlider(min=1, max=100, step=1, value=1, description="Initial Infected"),
    days=widgets.IntSlider(min=10, max=100, step=5, value=30, description="Days")
)

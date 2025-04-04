import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# Add the parent directory to the path so we can import pysydy
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pysydy

def delay_example():
    """
    Demonstrates the use of different delay types in PySyDy.
    """
    print("\n=== Delay Example ===")
    
    # Create delay objects
    material_delay = pysydy.MaterialDelay(name="Material Delay", delay_time=5.0, initial_value=0.0)
    info_delay = pysydy.InformationDelay(name="Information Delay", delay_time=5.0, initial_value=0.0)
    fixed_delay = pysydy.FixedDelay(name="Fixed Delay", delay_time=5.0, initial_value=0.0, timestep=1.0)
    
    # Simulate a step input
    time_points = np.arange(0, 20, 1.0)
    material_outputs = []
    info_outputs = []
    fixed_outputs = []
    
    for t in time_points:
        # Step input at t=5
        input_value = 0.0 if t < 5 else 10.0
        
        # Update delays
        material_out = material_delay.update(input_value, 1.0)
        info_out = info_delay.update(input_value, 1.0)
        fixed_out = fixed_delay.update(input_value, 1.0)
        
        # Record outputs
        material_outputs.append(material_out)
        info_outputs.append(info_out)
        fixed_outputs.append(fixed_out)
    
    # Plot results
    plt.figure(figsize=(10, 6))
    plt.plot(time_points, [0.0 if t < 5 else 10.0 for t in time_points], 'k--', label='Input')
    plt.plot(time_points, material_outputs, label='Material Delay')
    plt.plot(time_points, info_outputs, label='Information Delay')
    plt.plot(time_points, fixed_outputs, label='Fixed Delay')
    plt.title('Comparison of Delay Types')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    plt.savefig('delay_comparison.png')
    plt.show()

def behavior_modes_example():
    """
    Demonstrates the use of behavior modes in PySyDy.
    """
    print("\n=== Behavior Modes Example ===")
    
    # Create behavior mode objects
    exp_growth = pysydy.ExponentialGrowth(name="Population Growth", initial_value=100.0, growth_rate=0.05)
    exp_decay = pysydy.ExponentialDecay(name="Resource Depletion", initial_value=1000.0, decay_rate=0.03)
    goal_seeking = pysydy.GoalSeeking(name="Temperature Control", initial_value=15.0, goal_value=22.0, adjustment_rate=0.1)
    oscillation = pysydy.Oscillation(name="Business Cycle", initial_value=100.0, goal_value=100.0, adjustment_rate=0.2, delay_time=4.0)
    s_growth = pysydy.SShapedGrowth(name="Market Adoption", initial_value=10.0, carrying_capacity=1000.0, growth_rate=0.1)
    
    # Simulate behavior over time
    time_points = np.arange(0, 50, 1.0)
    growth_values = []
    decay_values = []
    goal_values = []
    oscillation_values = []
    s_growth_values = []
    
    for _ in time_points:
        growth_values.append(exp_growth.update(1.0))
        decay_values.append(exp_decay.update(1.0))
        goal_values.append(goal_seeking.update(1.0))
        oscillation_values.append(oscillation.update(1.0))
        s_growth_values.append(s_growth.update(1.0))
    
    # Plot results
    fig, axs = plt.subplots(3, 2, figsize=(12, 10))
    
    axs[0, 0].plot(time_points, growth_values)
    axs[0, 0].set_title('Exponential Growth')
    axs[0, 0].grid(True)
    
    axs[0, 1].plot(time_points, decay_values)
    axs[0, 1].set_title('Exponential Decay')
    axs[0, 1].grid(True)
    
    axs[1, 0].plot(time_points, goal_values)
    axs[1, 0].set_title('Goal Seeking')
    axs[1, 0].axhline(y=22.0, color='r', linestyle='--')
    axs[1, 0].grid(True)
    
    axs[1, 1].plot(time_points, oscillation_values)
    axs[1, 1].set_title('Oscillation')
    axs[1, 1].axhline(y=100.0, color='r', linestyle='--')
    axs[1, 1].grid(True)
    
    axs[2, 0].plot(time_points, s_growth_values)
    axs[2, 0].set_title('S-Shaped Growth')
    axs[2, 0].axhline(y=1000.0, color='r', linestyle='--')
    axs[2, 0].grid(True)
    
    axs[2, 1].set_visible(False)
    
    plt.tight_layout()
    plt.savefig('behavior_modes.png')
    plt.show()

def coflow_example():
    """
    Demonstrates the use of coflows in PySyDy.
    """
    print("\n=== Coflow Example ===")
    
    # Create a simple population model with age as a coflow attribute
    population = pysydy.Stock('Population', 1000.0)
    births = pysydy.Flow(
        name='Births',
        source_stock=None,
        target_stock=population,
        rate_function=lambda state: state['stocks']['Population'].value * 0.05  # 5% birth rate
    )
    deaths = pysydy.Flow(
        name='Deaths',
        source_stock=population,
        target_stock=None,
        rate_function=lambda state: state['stocks']['Population'].value * 0.02  # 2% death rate
    )
    
    # Create a coflow to track the average age of the population
    age_coflow = pysydy.Coflow(
        name='Age Structure',
        main_stock=population,
        attribute_name='Average Age',
        initial_attribute_value=30.0  # Initial average age is 30 years
    )
    
    # Add inflows and outflows to the coflow
    # Newborns have age 0
    age_coflow.add_inflow(births, lambda state: 0.0)
    
    # Deaths affect the average age (assuming older people die more frequently)
    age_coflow.add_outflow(deaths)
    
    # Simulate the system
    time_points = np.arange(0, 50, 1.0)
    population_values = [population.value]
    average_age_values = [age_coflow.get_attribute_concentration()]
    
    # Simple simulation loop
    for t in time_points[1:]:
        # Update flow rates
        system_state = {'stocks': {'Population': population}}
        births.calculate_rate(system_state)
        deaths.calculate_rate(system_state)
        
        # Update population stock
        population.update(1.0)
        
        # Update age coflow
        age_coflow.update(system_state, 1.0)
        
        # Everyone gets one year older each year - add this as an additional inflow to the attribute stock
        # This represents aging of the existing population
        age_coflow.attribute_stock += population.value * 1.0
        
        # Record values
        population_values.append(population.value)
        average_age_values.append(age_coflow.get_attribute_concentration())
    
    # Plot results
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    ax1.plot(time_points, population_values)
    ax1.set_title('Population Over Time')
    ax1.set_ylabel('Population')
    ax1.grid(True)
    
    ax2.plot(time_points, average_age_values)
    ax2.set_title('Average Age Over Time')
    ax2.set_xlabel('Time (years)')
    ax2.set_ylabel('Average Age (years)')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('coflow_example.png')
    plt.show()

def feedback_example():
    """
    Demonstrates the use of feedback loops in PySyDy.
    """
    print("\n=== Feedback Loop Example ===")
    
    # Create a simple predator-prey model
    prey = pysydy.Stock('Prey', 1000.0)
    predators = pysydy.Stock('Predators', 100.0)
    
    # Parameters
    prey_birth_rate = pysydy.Parameter('prey_birth_rate', 0.1)
    predation_rate = pysydy.Parameter('predation_rate', 0.01)
    predator_death_rate = pysydy.Parameter('predator_death_rate', 0.1)
    predator_efficiency = pysydy.Parameter('predator_efficiency', 0.1)
    
    # Flows
    prey_births = pysydy.Flow(
        name='Prey Births',
        source_stock=None,
        target_stock=prey,
        rate_function=lambda state: state['stocks']['Prey'].value * state['parameters']['prey_birth_rate'].value
    )
    
    predation = pysydy.Flow(
        name='Predation',
        source_stock=prey,
        target_stock=None,
        rate_function=lambda state: (
            state['stocks']['Prey'].value * 
            state['stocks']['Predators'].value * 
            state['parameters']['predation_rate'].value
        )
    )
    
    predator_births = pysydy.Flow(
        name='Predator Births',
        source_stock=None,
        target_stock=predators,
        rate_function=lambda state: (
            state['stocks']['Prey'].value * 
            state['stocks']['Predators'].value * 
            state['parameters']['predation_rate'].value * 
            state['parameters']['predator_efficiency'].value
        )
    )
    
    predator_deaths = pysydy.Flow(
        name='Predator Deaths',
        source_stock=predators,
        target_stock=None,
        rate_function=lambda state: (
            state['stocks']['Predators'].value * 
            state['parameters']['predator_death_rate'].value
        )
    )
    
    # Create feedback loops
    prey_growth_loop = pysydy.ReinforcingLoop(
        name='Prey Growth Loop',
        components=[prey, prey_births],
        description='More prey leads to more births, leading to even more prey.'
    )
    
    predation_loop = pysydy.BalancingLoop(
        name='Predation Loop',
        components=[prey, predation, predators],
        description='More prey leads to more predation, reducing prey population.'
    )
    
    predator_growth_loop = pysydy.ReinforcingLoop(
        name='Predator Growth Loop',
        components=[predators, predation, predator_births],
        description='More predators leads to more predation, leading to more predator births.'
    )
    
    predator_death_loop = pysydy.BalancingLoop(
        name='Predator Death Loop',
        components=[predators, predator_deaths],
        description='More predators leads to more deaths, reducing predator population.'
    )
    
    # Create a feedback structure to analyze the model
    feedback_structure = pysydy.FeedbackStructure('Predator-Prey Dynamics')
    feedback_structure.add_reinforcing_loop(prey_growth_loop)
    feedback_structure.add_reinforcing_loop(predator_growth_loop)
    feedback_structure.add_balancing_loop(predation_loop)
    feedback_structure.add_balancing_loop(predator_death_loop)
    
    # Print feedback structure information
    print(feedback_structure)
    print("Reinforcing loops:")
    for loop in feedback_structure.reinforcing_loops:
        print(f"  - {loop}")
    print("Balancing loops:")
    for loop in feedback_structure.balancing_loops:
        print(f"  - {loop}")
    
    # Simulate the system
    time_points = np.arange(0, 100, 0.25)
    prey_values = [prey.value]
    predator_values = [predators.value]
    
    # Simple simulation loop
    for _ in time_points[1:]:
        # Update flow rates
        system_state = {
            'stocks': {'Prey': prey, 'Predators': predators},
            'parameters': {
                'prey_birth_rate': prey_birth_rate,
                'predation_rate': predation_rate,
                'predator_death_rate': predator_death_rate,
                'predator_efficiency': predator_efficiency
            }
        }
        
        prey_births.calculate_rate(system_state)
        predation.calculate_rate(system_state)
        predator_births.calculate_rate(system_state)
        predator_deaths.calculate_rate(system_state)
        
        # Update stocks
        prey.update(0.25)
        predators.update(0.25)
        
        # Record values
        prey_values.append(prey.value)
        predator_values.append(predators.value)
    
    # Plot results
    plt.figure(figsize=(10, 6))
    plt.plot(time_points, prey_values, label='Prey')
    plt.plot(time_points, predator_values, label='Predators')
    plt.title('Predator-Prey Dynamics with Feedback Loops')
    plt.xlabel('Time')
    plt.ylabel('Population')
    plt.legend()
    plt.grid(True)
    plt.savefig('feedback_example.png')
    plt.show()

# Run the examples
if __name__ == "__main__":
    delay_example()
    behavior_modes_example()
    coflow_example()
    feedback_example()
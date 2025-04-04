# PySyDy: A Simple System Dynamics Library in Python

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)  

**PySyDy** (Python System Dynamics) is a lightweight and intuitive Python library for building and simulating system dynamics models. It provides core components for representing stocks, flows, and auxiliary variables, making it easy to create and explore dynamic systems.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Core Components](#core-components)
  - [Stock](#stock)
  - [Flow](#flow)
  - [Auxiliary](#auxiliary)
  - [Parameter](#parameter)
  - [Simulation](#simulation)
- [Advanced Features](#advanced-features)
  - [Delays](#delays)
  - [Behavior Modes](#behavior-modes)
  - [Coflows](#coflows)
  - [Feedback Loops](#feedback-loops)
- [Visualization](#visualization)
- [Examples](#examples)
- [License](#license)

## Overview

System dynamics is a methodology for understanding the behavior of complex systems over time. PySyDy provides a Python implementation of system dynamics concepts, allowing you to build models that capture the structure and behavior of systems with feedback loops, delays, and nonlinear relationships.

## Installation

You can install PySyDy using pip:

```bash
pip install pysydy
```

Or clone the repository and install from source:

```bash
git clone https://github.com/pietroviero/PySyDy.git
cd PySyDy
pip install -e .
```

## Core Components

### Stock

A Stock represents an accumulation or level in your system. Stocks change over time through inflows and outflows.

**Key Attributes:**
- `name`: The name of the stock
- `value`: The current value of the stock
- `inflows`: List of flows that increase the stock
- `outflows`: List of flows that decrease the stock

**Key Methods:**
- `add_inflow(flow)`: Adds a flow that increases the stock
- `add_outflow(flow)`: Adds a flow that decreases the stock
- `update(timestep)`: Updates the stock's value based on its inflows and outflows
- `get_value()`: Returns the current value of the stock

**Example:**
```python
# Create a stock representing a population of 1000 people
population = pysydy.Stock('Population', 1000)
```

### Flow

A Flow represents a rate of change that affects stocks. Flows can be inflows (increasing a stock) or outflows (decreasing a stock).

**Key Attributes:**
- `name`: The name of the flow
- `source_stock`: The stock that the flow originates from (can be None for sources)
- `target_stock`: The stock that the flow goes to (can be None for sinks)
- `rate_function`: A function that calculates the flow rate
- `rate`: The current flow rate

**Key Methods:**
- `calculate_rate(system_state)`: Calculates the flow rate using the provided rate function
- `get_rate()`: Returns the current flow rate

**Example:**
```python
# Create a birth flow that increases the population
births = pysydy.Flow(
    name='Births',
    source_stock=None,  # External source
    target_stock=population,
    rate_function=lambda state: state['stocks']['Population'].value * 0.05  # 5% birth rate
)
```

### Auxiliary

An Auxiliary variable represents intermediate calculations that help define relationships between stocks and flows. These variables vary over time and are recalculated at each simulation step.

**Key Attributes:**
- `name`: The name of the auxiliary variable
- `calculation_function`: A function that calculates the auxiliary variable's value
- `inputs`: A list of input variables that this auxiliary variable depends on
- `value`: The current value of the auxiliary variable

**Key Methods:**
- `calculate_value(system_state)`: Calculates the value using the provided calculation function
- `get_value()`: Returns the current value
- `get_value_updated(system_state)`: Recalculates and returns the updated value

**Example:**
```python
# Create an auxiliary variable for population density
population_density = pysydy.Auxiliary(
    name='Population Density',
    calculation_function=lambda state: state['stocks']['Population'].value / 100,  # people per square km
    inputs=['Population']
)
```

### Parameter

A Parameter represents a constant value that does not change during a simulation. Parameters are used in calculations within flows and auxiliary variables.

**Key Attributes:**
- `name`: The name of the parameter
- `value`: The numerical value of the parameter
- `units`: Units of measurement for the parameter
- `description`: A description of what the parameter represents

**Key Methods:**
- `get_value()`: Returns the value of the parameter

**Example:**
```python
# Create a parameter for the land area
land_area = pysydy.Parameter('Land Area', 100, units='square kilometers', 
                           description='Total land area available')
```

### Simulation

The Simulation class manages the simulation of a system dynamics model, handling time stepping, calculation order, and data collection.

**Key Attributes:**
- `stocks`: List of stocks in the model
- `flows`: List of flows in the model
- `auxiliaries`: List of auxiliary variables in the model
- `parameters`: List of parameters in the model
- `timestep`: The time interval for each simulation step
- `time`: The current simulation time
- `history`: A list of system states recorded during the simulation

**Key Methods:**
- `step()`: Advances the simulation by one timestep
- `run(duration)`: Runs the simulation for a given duration
- `get_results()`: Returns a DataFrame with the simulation results

**Example:**
```python
# Create and run a simulation
sim = pysydy.Simulation(
    stocks=[population],
    flows=[births, deaths],
    auxiliaries=[population_density],
    parameters=[land_area],
    timestep=0.1
)

# Run for 50 time units
sim.run(50)

# Get and plot results
results = sim.get_results()
```

## Advanced Features

### Delays

Delays represent time lags in a system. PySyDy provides three types of delays:

#### MaterialDelay

Material delays occur when physical entities take time to move through a process. They conserve the quantity being delayed.

**Key Attributes:**
- `name`: The name of the delay
- `delay_time`: The average time it takes for material to flow through the delay
- `order`: The order of the delay (number of stages)
- `outflow`: The current outflow rate

**Key Methods:**
- `update(inflow, timestep)`: Updates the delay based on the current inflow
- `get_outflow()`: Returns the current outflow rate

#### InformationDelay

Information delays occur when information takes time to be perceived, processed, or transmitted. They smooth out fluctuations in the input signal.

**Key Attributes:**
- `name`: The name of the delay
- `delay_time`: The average time it takes for information to be processed
- `order`: The order of the delay (number of stages)
- `output`: The current output value

**Key Methods:**
- `update(input_value, timestep)`: Updates the delay based on the current input
- `get_output()`: Returns the current output value

#### FixedDelay

Fixed delays represent a precise time lag where the output exactly matches the input after a fixed time period.

**Key Attributes:**
- `name`: The name of the delay
- `delay_time`: The exact time it takes for the input to appear at the output
- `history`: A queue of past input values

**Key Methods:**
- `update(input_value, timestep)`: Updates the delay based on the current input
- `get_output()`: Returns the current output value

**Example:**
```python
# Create a material delay for a manufacturing process
production_delay = pysydy.MaterialDelay(
    name="Production Delay", 
    delay_time=5.0,  # 5 time units to complete production
    initial_value=0.0, 
    order=3  # Third-order delay for more realistic behavior
)

# Update the delay with the current production rate
output_rate = production_delay.update(input_rate, timestep)
```

### Behavior Modes

Behavior modes represent common patterns of system behavior over time. PySyDy provides implementations of these patterns:

#### ExponentialGrowth

Represents exponential growth behavior where a quantity increases at a rate proportional to its current value.

#### ExponentialDecay

Represents exponential decay behavior where a quantity decreases at a rate proportional to its current value.

#### GoalSeeking

Represents goal-seeking behavior where a quantity adjusts toward a target value over time.

#### Oscillation

Represents oscillatory behavior where a quantity fluctuates around a goal value due to delays in the system.

#### SShapedGrowth

Represents S-shaped or logistic growth where growth is initially exponential but slows as it approaches a carrying capacity.

**Example:**
```python
# Create an exponential growth model for a population
population_growth = pysydy.ExponentialGrowth(
    name="Population Growth", 
    initial_value=100.0, 
    growth_rate=0.05  # 5% growth rate per time unit
)

# Update the population for one time unit
new_population = population_growth.update(1.0)
```

### Coflows

Coflows track attributes of stocks as they flow through a system. They are useful for modeling situations where you need to track not just the quantity of a stock, but also some attribute or quality associated with it.

**Key Attributes:**
- `name`: The name of the coflow
- `main_stock`: The main stock whose attribute is being tracked
- `attribute_name`: The name of the attribute being tracked
- `attribute_stock`: The total amount of the attribute in the stock
- `attribute_concentration`: The concentration of the attribute in the stock

**Key Methods:**
- `add_inflow(main_flow, attribute_concentration_function)`: Adds an inflow to the coflow
- `add_outflow(main_flow)`: Adds an outflow to the coflow
- `update(system_state, timestep)`: Updates the coflow based on its inflows and outflows
- `get_attribute_stock()`: Returns the total amount of the attribute
- `get_attribute_concentration()`: Returns the concentration of the attribute

**Example:**
```python
# Create a coflow to track the average age of a population
age_coflow = pysydy.Coflow(
    name='Age Structure',
    main_stock=population,
    attribute_name='Average Age',
    initial_attribute_value=30.0  # Initial average age is 30 years
)

# Add inflows and outflows to the coflow
age_coflow.add_inflow(births, lambda state: 0.0)  # Newborns have age 0
age_coflow.add_outflow(deaths)  # Deaths affect the average age

# Update the coflow
age_coflow.update(system_state, timestep)
```

### Feedback Loops

Feedback loops are circular causal relationships in a system. PySyDy provides classes to document and analyze these loops:

#### ReinforcingLoop

Reinforcing loops amplify changes in a system, creating exponential growth or collapse.

#### BalancingLoop

Balancing loops counteract changes in a system, creating goal-seeking or oscillatory behavior.

#### FeedbackStructure

Represents a collection of feedback loops in a system dynamics model, helping to analyze the overall feedback structure.

**Example:**
```python
# Document a reinforcing feedback loop in a population model
population_loop = pysydy.ReinforcingLoop(
    name="Population Growth Loop",
    components=[population, births],
    description="More people lead to more births, which further increases the population."
)
```

## Visualization

The Graph class provides visualization capabilities for system dynamics models, showing the relationships between stocks, flows, auxiliaries, and parameters.

**Key Methods:**
- `plot(figsize, node_size, font_size, show_values)`: Plots the graph representation of the model
- `update_graph()`: Updates the graph with current values from the simulation
- `interactive_plot()`: Creates an interactive plot for Jupyter notebooks

**Example:**
```python
# Create a graph visualization of the model
model_graph = pysydy.Graph(sim)

# Plot the graph
fig, ax = model_graph.plot(figsize=(10, 8), show_values=True)
```

## Examples

### Basic SIR Model

```python
import pysydy
import matplotlib.pyplot as plt

# Create stocks (compartments)
susceptible = pysydy.Stock('Susceptible', 9999)
infected = pysydy.Stock('Infected', 1)
recovered = pysydy.Stock('Recovered', 0)

# Create parameters
contact_rate = pysydy.Parameter('contact_rate', 6.0, units='contacts/person/day')
infectivity = pysydy.Parameter('infectivity', 0.25, units='probability')
recovery_rate = pysydy.Parameter('recovery_rate', 0.5, units='1/day')
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
    stocks=[

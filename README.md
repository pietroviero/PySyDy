# PySyDy: A Simple System Dynamics Library in Python

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)  

**PySyDy** (Python System Dynamics) is a lightweight and intuitive Python library for building and simulating system dynamics models. It provides core components for representing stocks, flows, and auxiliary variables, making it easy to create and explore dynamic systems.

**Key Features:**

*   **Stocks:** Represent accumulations or levels in your system (e.g., Population, Resources).
*   **Flows:** Represent rates of change that affect stocks (e.g., Births, Consumption).
*   **Auxiliary Variables:** Represent intermediate calculations that help define relationships between stocks and flows (e.g., Fractional Birth Rate, Food per Capita). These variables vary over time.
*   **Parameter:** Represent the variables that does not change during a simulation.
*   **Simulation:**  Provides a straightforward simulation loop to step through time and observe system behavior.


This library is designed for:

*   **Learning System Dynamics:**  PySyDy offers a clear and simple API, ideal for students and beginners to grasp the fundamental concepts of system dynamics modeling.
*   **Simple Simulations:**  It's well-suited for creating and experimenting with small to medium-sized system dynamics models for educational purposes or quick explorations.
*   **Extensibility:**  The library is structured in a modular way, allowing for future expansion and customization.

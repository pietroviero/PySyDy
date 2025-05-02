import pandas as pd
from units import units
from tqdm import trange # for a progress live bar

ureg = units.ureg
Q_ = ureg.Quantity

class Simulation:
    """
    Manages the simulation of a system dynamics model, handling time stepping,
    calculation order, and data collection.
    """
    def __init__(self, stocks, flows, auxiliaries, parameters, timestep=1.0, timestep_unit='day'):
        self.stocks = stocks
        self.flows = flows
        self.auxiliaries = auxiliaries
        self.parameters = parameters
        self.timestep = units.get_quantity(timestep, timestep_unit)  # ⬅️ now flexible
        self.time = 0.0 * units.ureg(timestep_unit)
        self.history = []
        self.loops = [] # Add list to store feedback loops

        self.check_units()

    def step(self):
        """
        Advance the simulation by one timestep.
        """

        # 1. Calculate auxiliaries
        for aux in self.auxiliaries:
            aux.calculate_value(self._get_system_state())

        # 2. Calculate flow rates
        for flow in self.flows:
            flow.calculate_rate(self._get_system_state())

        # 3. Update stocks
        for stock in self.stocks:
            stock.update(self.timestep)

        # 4. Record state
        self._record_state()
        self.time += self.timestep

    def _get_system_state(self):
        """
        Returns a dictionary representing the current system state.
        """
        return {
            'stocks': {s.name: s for s in self.stocks},
            'flows': {f.name: f for f in self.flows},
            'auxiliaries': {a.name: a for a in self.auxiliaries},
            'parameters': {p.name: p for p in self.parameters},
        }

    def _record_state(self):
        state = {
            'time': self.time,
            'stocks': {s.name: s.value for s in self.stocks},
            'flows': {f.name: f.rate for f in self.flows},
            'auxiliaries': {a.name: a.value for a in self.auxiliaries},
        }
        self.history.append(state)



    def get_results(self):
        """
        Returns a DataFrame with the simulation results.
        """
        # Create a DataFrame from the history list
        df = pd.DataFrame(self.history)
        
        # Extract nested dictionaries into columns
        # First, create a copy of the DataFrame to avoid modifying during iteration
        result_df = df[['time']].copy()
        
        # Process stocks
        if 'stocks' in df.columns:
            for idx, record in enumerate(df['stocks']):
                for stock_name, stock_value in record.items():
                    if stock_name not in result_df.columns:
                        result_df[stock_name] = None
                    result_df.loc[idx, stock_name] = stock_value
        
        # Process flows
        if 'flows' in df.columns:
            for idx, record in enumerate(df['flows']):
                for flow_name, flow_value in record.items():
                    if flow_name not in result_df.columns:
                        result_df[flow_name] = None
                    result_df.loc[idx, flow_name] = flow_value
        
        # Process auxiliaries
        if 'auxiliaries' in df.columns:
            for idx, record in enumerate(df['auxiliaries']):
                for aux_name, aux_value in record.items():
                    if aux_name not in result_df.columns:
                        result_df[aux_name] = None
                    result_df.loc[idx, aux_name] = aux_value
        
        return result_df.set_index('time')

    def check_units(self):
        """
        Check units consistency across stocks, flows, parameters, auxiliaries.
        """
        errors = []

        # Check Stocks
        for stock in self.stocks:
            if stock.unit is None:
                errors.append(f"Stock '{stock.name}' missing unit definition.")

        # Check Parameters
        for parameter in self.parameters:
            if parameter.unit is None:
                errors.append(f"Parameter '{parameter.name}' missing unit definition.")

        # Check Flows
        for flow in self.flows:
            if flow.unit is None:
                errors.append(f"Flow '{flow.name}' missing unit definition.")
            else:
                # Assume flows should match stock unit/time
                # You could check source_stock or target_stock more strictly later
                if flow.source_stock and flow.source_stock.unit:
                    expected_flow_unit = flow.source_stock.unit / units.ureg.day  # assuming timestep in day
                    if not flow.unit.dimensionality == expected_flow_unit.dimensionality:
                        errors.append(
                            f"Flow '{flow.name}' unit {flow.unit} incompatible with source stock '{flow.source_stock.name}' unit/time ({expected_flow_unit})."
                        )

        # Check Auxiliaries
        for aux in self.auxiliaries:
            if aux.unit is None:
                errors.append(f"Auxiliary '{aux.name}' missing unit definition.")

        # Final result
        if errors:
            print(f"[UNIT CHECK] Found {len(errors)} problem(s):")
            for error in errors:
                print(f" - {error}")
            raise ValueError("[UNIT CHECK FAILED] Please fix unit inconsistencies before running simulation.")



    def validate_influences(self):
        """
        Run all flow and auxiliary functions once to ensure they return values with correct dimensionality.
        """

        system_state = self._get_system_state()

        for aux in self.auxiliaries:
            try:
                aux.calculate_value(system_state)
            except Exception as e:
                print(str(e))
                raise

        for flow in self.flows:
            try:
                flow.calculate_rate(system_state)
            except Exception as e:
                print(str(e))
                raise

    def validate_model(self):
        """
        Runs all unit checks: structure and expression correctness.
        Combines check_units() and validate_influences().
        """
        print("[UNIT CHECK] Running structural and functional unit checks...")

        # 1. Structural: check if units are defined and flow/stock compatibility
        self.check_units()

        # 2. Functional: check calculated values from flows and auxiliaries
        self.validate_influences()

        print("[UNIT CHECK] All units are dimensionally consistent.")

    def run(self, duration):
        """
        Run the simulation for a given duration.

        Duration is automatically interpreted using the timestep unit.
        Raises a warning if dimensionality mismatch is detected.
        """

        self.validate_model()

        if not hasattr(duration, 'units'):
            duration_quantity = units.get_quantity(duration, str(self.timestep.units))
        else:
            duration_quantity = duration

        # Smart dimensionality check
        if not duration_quantity.dimensionality == self.timestep.dimensionality:
            raise ValueError(
                f"[UNIT ERROR] Duration unit {duration_quantity.units} is incompatible with timestep unit {self.timestep.units}."
            )

        # Safe division
        steps = int((duration_quantity / self.timestep).to_base_units().magnitude)
        for _ in range(steps):
            self.step()

        for _ in trange(steps, desc="Running simulation"):
            self.step()

    def add_loop(self, loop):
        """
        Adds a feedback loop object (for documentation/analysis).

        :param loop: The feedback loop object (e.g., ReinforcingLoop, BalancingLoop).
        :type loop: object
        """
        self.loops.append(loop)

    def get_loops(self):
        """
        Returns the list of defined feedback loops.

        :returns: List of feedback loop objects.
        :rtype: list
        """
        return self.loops

    def get_results_for_plot(self):
        """
        Returns a DataFrame ready for plotting:
        - Converts time index from Quantity to float
        - Converts all stock/flow/auxiliary values from Quantity to float
        """
        results = self.get_results().copy()

        # Fix the time index
        if hasattr(results.index[0], 'magnitude'):
            results.index = results.index.to_series().apply(lambda t: t.magnitude)

        # Fix values inside columns
        for col in results.columns:
            if hasattr(results[col].iloc[0], 'magnitude'):
                results[col] = results[col].apply(lambda x: x.magnitude)

        return results

    def plot_each_stock(self):
        """
        Plots each stock separately over time, with its original unit in the Y-axis label.
        """
        import matplotlib.pyplot as plt

        results = self.get_results().copy()
        time_unit = str(self.timestep.units)

        # Convert time index to pure floats
        if hasattr(results.index[0], 'magnitude'):
            results.index = results.index.to_series().apply(lambda t: t.magnitude)

        # Plot each stock individually
        for stock in self.stocks:
            if stock.name in results.columns:
                # Get pure numerical values
                stock_values = results[stock.name].apply(lambda x: x.magnitude if hasattr(x, 'magnitude') else x)

                plt.figure(figsize=(8, 5))
                plt.plot(results.index, stock_values)
                plt.title(f"{stock.name} Over Time")
                plt.xlabel(f"Time [{time_unit}]")
                ylabel = f"{stock.name} [{str(stock.unit)}]" if stock.unit else f"{stock.name} [no unit]"
                plt.ylabel(ylabel)
                plt.grid(True)
                plt.show()


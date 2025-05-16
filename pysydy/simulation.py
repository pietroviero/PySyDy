# Merged Simulation Class with Unit Handling and Polarity Detection

import pandas as pd
import networkx as nx
import copy
import os
import matplotlib.pyplot as plt
from tqdm import trange
from .units import units

ureg = units.ureg
Q_ = ureg.Quantity

DEFAULT_EPSILON = 1e-6

class Simulation:
    def __init__(self, stocks, flows, auxiliaries, parameters, timestep=1.0, timestep_unit='day'):
        self.stocks = {s.name: s for s in stocks}
        self.flows = {f.name: f for f in flows}
        self.auxiliaries = {a.name: a for a in auxiliaries}
        self.parameters = {p.name: p for p in parameters}

        self.timestep = units.get_quantity(timestep, timestep_unit)
        self.time = 0.0 * ureg(timestep_unit)
        self.history = []
        self.loops = []

        self._dependency_graph = None
        self._link_polarities = {}
        self.ureg = ureg # Make ureg available as an instance attribute if needed by helpers
        self.epsilon_for_perturbation = DEFAULT_EPSILON
        self.numeric_threshold = 1e-17 

        self._sorted_auxiliary_names = self._get_auxiliary_calculation_order()
        self.validate_model()

        # Initial values for polarity detection
        print("--- Calculating Initial State (t=0) ---")
        self.initial_state_values = {}
        initial_system_state_for_polarity = None # Initialize
        try:
            # temp_state contains the component objects whose .value/.rate will be updated
            temp_state = self._get_system_state(get_objects=True)
            # Calculate auxiliaries in sorted order
            for aux_name in self._sorted_auxiliary_names:
                aux = self.auxiliaries[aux_name]
                aux.calculate_value(temp_state) # Updates aux.value
                self.initial_state_values[aux.name] = aux.value
            # Calculate flows
            for flow in self.flows.values():
                flow.calculate_rate(temp_state) # Updates flow.rate
                self.initial_state_values[flow.name] = flow.rate
            for stock in self.stocks.values():
                # Stock initial values are set during their instantiation
                self.initial_state_values[stock.name] = stock.value
            print(f"  Initial state values: {self.initial_state_values}")

            # After all initial values are calculated and component objects are updated,
            # capture this complete initial state.
            initial_system_state_for_polarity = self._get_system_state(get_objects=True)

        except Exception as e:
            print(f"[WARN] Initial state calc failed for polarity: {e}")
            self.initial_state_values = None # Keep this to indicate failure

        try:
            # Pass the initial_system_state_for_polarity to _find_loops_and_polarity
            if self.initial_state_values is not None and initial_system_state_for_polarity is not None and nx is not None:
                self._dependency_graph = self._find_loops_and_polarity(initial_system_state_for_polarity)
            elif nx is None:
                print("  Skipping loop detection: networkx library not found.")
                self.loops.append(("?", "Loop detection skipped: networkx not installed."))
            else:
                print("  Skipping loop polarity detection: failed to calculate initial state or capture system state.")
                self.loops.append(("?", "Polarity detection skipped: initial state/system state calculation failed."))

        except Exception as e:
            print(f"\nWarning: Failed during automatic loop/polarity detection. Error: {e}")
            self.loops.append(("Error", f"Error during loop detection: {e}"))

    def _get_system_state(self, get_objects=False):
        current_time = self.time # Get current simulation time
        if get_objects:
            # This state is passed to the calculation functions
            state_dict = {
                'stocks': self.stocks,
                'flows': self.flows,
                'auxiliaries': self.auxiliaries,
                'parameters': self.parameters,
                'time': current_time # <<< ADDED TIME HERE
            }
            return state_dict

        # This state is for recording history
        state_dict_values = {
            'stocks': {s.name: s.value for s in self.stocks.values()},
            'flows': {f.name: f.rate for f in self.flows.values()},
            'auxiliaries': {a.name: a.value for a in self.auxiliaries.values()},
            'parameters': {p.name: p.value for p in self.parameters.values()},
            'time': current_time # <<< ADDED TIME HERE (optional, but good for consistency)
        }
        return state_dict_values

    def step(self):
        state = self._get_system_state(get_objects=True)
        # Calculate auxiliaries in topologically sorted order
        for aux_name in self._sorted_auxiliary_names:
            aux = self.auxiliaries[aux_name]
            aux.calculate_value(state)
        # Then calculate flows
        for flow in self.flows.values():
            flow.calculate_rate(state)
        for stock in self.stocks.values():
            stock.update(self.timestep)
        self._record_state()
        self.time += self.timestep

    def _record_state(self):
        self.history.append({
            'time': self.time,
            'stocks': {s.name: s.value for s in self.stocks.values()},
            'flows': {f.name: f.rate for f in self.flows.values()},
            'auxiliaries': {a.name: a.value for a in self.auxiliaries.values()},
        })

    def _update_auxiliaries_and_flows(self, state_to_update, perturbed_input_aux_or_flow_name):
        """
        Recalculates auxiliaries and flows based on the component objects
        contained within the provided 'state_to_update' dictionary.
        This method updates the .value attribute of auxiliaries and .rate attribute of flows
        within the objects in the provided 'state_to_update'.
        Auxiliaries are calculated in their topological order.
        """
        # Calculate auxiliaries in topologically sorted order.
        # self._sorted_auxiliary_names is derived from the keys of self.auxiliaries.
        # It's assumed state_to_update['auxiliaries'] has corresponding objects for these names.
        for aux_name in self._sorted_auxiliary_names:
            if aux_name == perturbed_input_aux_or_flow_name: # If this is the aux we manually perturbed
            # print(f"[Polarity Debug] Skipping recalculation of perturbed input aux: {aux_name}")
                continue
            if aux_name in state_to_update['auxiliaries']:
                aux_object_in_state = state_to_update['auxiliaries'][aux_name]
                # The calculate_value method of the Auxiliary object will use
                # other components from state_to_update as needed for its inputs.
                aux_object_in_state.calculate_value(state_to_update)
            else:
                # This warning indicates a potential mismatch if a full state copy wasn't provided
                # or if _sorted_auxiliary_names is out of sync with state_to_update's contents.
                print(f"[Warning] Auxiliary '{aux_name}' from sorted list not found in 'state_to_update' during _update_auxiliaries_and_flows.")

        # Then calculate flows.
        # Iterate through flow names from self.flows.keys() as the canonical list.
        # Assumes state_to_update['flows'] has corresponding objects.
        for flow_name in self.flows.keys():
            if flow_name == perturbed_input_aux_or_flow_name: # If this is the flow we manually perturbed
            # print(f"[Polarity Debug] Skipping recalculation of perturbed input flow: {flow_name}")
                continue
            if flow_name in state_to_update['flows']:
                flow_object_in_state = state_to_update['flows'][flow_name]
                # The calculate_rate method of the Flow object will use
                # other components from state_to_update as needed for its inputs.
                flow_object_in_state.calculate_rate(state_to_update)
            else:
                print(f"[Warning] Flow '{flow_name}' from main simulation not found in 'state_to_update' during _update_auxiliaries_and_flows.")

    def run(self, duration):
        if not hasattr(duration, 'units'):
            duration = units.get_quantity(duration, str(self.timestep.units))
        if duration.dimensionality != self.timestep.dimensionality:
            raise ValueError("[UNIT ERROR] Duration and timestep units mismatch.")

        steps = int((duration / self.timestep).to_base_units().magnitude)
        for _ in trange(steps, desc="Running simulation"):
            self.step()

    def get_results(self):
        df = pd.DataFrame(self.history)
        result_df = df[['time']].copy()
        for cat in ['stocks', 'flows', 'auxiliaries']:
            if cat in df.columns:
                for idx, rec in enumerate(df[cat]):
                    for name, val in rec.items():
                        if name not in result_df:
                            result_df[name] = None
                        result_df.loc[idx, name] = val
        return result_df.set_index('time')

    def get_results_for_plot(self):
        df = self.get_results().copy()
        if hasattr(df.index[0], 'magnitude'):
            df.index = df.index.to_series().apply(lambda t: t.magnitude)
        for col in df.columns:
            if hasattr(df[col].iloc[0], 'magnitude'):
                df[col] = df[col].apply(lambda x: x.magnitude)
        return df

    def plot_each_stock(self):
        df = self.get_results_for_plot()
        for stock in self.stocks.values():
            if stock.name in df.columns:
                plt.figure()
                plt.plot(df.index, df[stock.name])
                plt.title(f"{stock.name} Over Time")
                plt.xlabel(f"Time [{self.timestep.units}]")
                plt.ylabel(f"{stock.name} [{stock.unit}]" if stock.unit else stock.name)
                plt.grid(True)
                plt.show()

    def check_units(self):
        errors = []
        for stock in self.stocks.values():
            if stock.unit is None:
                errors.append(f"Stock '{stock.name}' missing unit.")
        for p in self.parameters.values():
            if p.unit is None:
                errors.append(f"Parameter '{p.name}' missing unit.")
        for flow in self.flows.values():
            if flow.unit is None:
                errors.append(f"Flow '{flow.name}' missing unit.")
            elif flow.source_stock and flow.source_stock.unit:
                expected = flow.source_stock.unit / ureg.day
                if flow.unit.dimensionality != expected.dimensionality:
                    errors.append(f"Flow '{flow.name}' unit {flow.unit} incompatible with {flow.source_stock.name}/time")
        for aux in self.auxiliaries.values():
            if aux.unit is None:
                errors.append(f"Auxiliary '{aux.name}' missing unit.")
        if errors:
            for e in errors: print(f" - {e}")
            raise ValueError("[UNIT CHECK FAILED]")

    def validate_influences(self):
        state = self._get_system_state(get_objects=True)
        # Calculate auxiliaries in topologically sorted order
        for aux_name in self._sorted_auxiliary_names:
            aux = self.auxiliaries[aux_name]
            aux.calculate_value(state)
        # Then calculate flows
        for flow in self.flows.values():
            flow.calculate_rate(state)

    def validate_model(self):
        print("[UNIT CHECK] Running checks...")
        self.check_units()
        self.validate_influences()
        print("[UNIT CHECK] Passed.")

    def _find_loops_and_polarity(self, base_state_for_estimation):
        G = nx.DiGraph()
        for comp in {**self.flows, **self.auxiliaries}.values():
            for inp in getattr(comp, 'inputs', []):
                G.add_edge(inp, comp.name)
        for flow in self.flows.values():
            if flow.target_stock:
                G.add_edge(flow.name, flow.target_stock.name)
            if flow.source_stock:
                G.add_edge(flow.name, flow.source_stock.name)

        self._link_polarities = {}
        for (u, v) in G.edges():
            sign = self._estimate_link_sign(u, v, base_state_for_estimation)
            self._link_polarities[(u, v)] = sign
            G.edges[u, v]['sign'] = sign

        cycles = list(nx.simple_cycles(G))
        self.loops = []
        for cycle in cycles:
            polarity = 1
            valid = True
            for i in range(len(cycle)):
                u, v = cycle[i], cycle[(i+1)%len(cycle)]
                sign = G.edges[u, v].get('sign', 0)
                if sign in [None, '?']: valid = False; break
                polarity *= sign
            label = 'R (+)' if polarity > 0 else 'B (-)' if polarity < 0 else 'N (0)'
            self.loops.append((label if valid else '?', ' -> '.join(cycle + [cycle[0]])))
        return G

    def _build_dependency_graph(self):
        G = nx.DiGraph()
        dynamic_components = {**self.stocks, **self.flows, **self.auxiliaries}
        for name, comp in {**dynamic_components, **self.parameters}.items():
            G.add_node(name, object=comp)
        for comp in {**self.flows, **self.auxiliaries}.values():
            for inp in getattr(comp, 'inputs', []):
                if inp in dynamic_components:
                    G.add_edge(inp, comp.name, sign='calculate')
        for flow in self.flows.values():
            if flow.target_stock:
                G.add_edge(flow.name, flow.target_stock.name, sign=1)
            if flow.source_stock:
                G.add_edge(flow.name, flow.source_stock.name, sign=-1)
        return G

    def _calculate_link_polarities(self, G, initial_state_val_dict, epsilon=DEFAULT_EPSILON):
        if initial_state_val_dict is None:
            return {}, G
        all_link_polarities = {}

        def get_perturbed_sign(input_name, target_name):
            state = self._get_system_state(get_objects=True)
            for name, val in initial_state_val_dict.items():
                if name in state['stocks']:
                    state['stocks'][name].value = val
                elif name in state['auxiliaries']:
                    state['auxiliaries'][name].value = val
                elif name in state['flows']:
                    state['flows'][name].rate = val

            base = self._eval_component(target_name, state)
            perturbed = copy.deepcopy(state)

            try:
                if input_name in perturbed['stocks']:
                    val = perturbed['stocks'][input_name].value
                    perturbed['stocks'][input_name].value = perturbed['stocks'][input_name].value = val + Q_(epsilon, val.units)
                elif input_name in perturbed['auxiliaries']:
                    val = perturbed['auxiliaries'][input_name].value
                    perturbed['auxiliaries'][input_name].value = perturbed['stocks'][input_name].value = val + Q_(epsilon, val.units)
                elif input_name in perturbed['parameters']:
                    val = perturbed['parameters'][input_name].value
                    perturbed['parameters'][input_name].value = perturbed['stocks'][input_name].value = val + Q_(epsilon, val.units)

                new = self._eval_component(target_name, perturbed)
                delta = (new.magnitude if hasattr(new, 'magnitude') else new) - (
                    base.magnitude if hasattr(base, 'magnitude') else base)
                if abs(delta) > epsilon * epsilon:
                    return 1 if delta > 0 else -1
            except Exception as e:
                print(f"Error in perturbation: {e}")
            return 0

        for comp_name, comp in {**self.flows, **self.auxiliaries}.items():
            for inp in getattr(comp, 'inputs', []):
                sign = get_perturbed_sign(inp, comp_name)
                all_link_polarities[(inp, comp_name)] = sign
                if G.has_edge(inp, comp_name):
                    G.edges[inp, comp_name]['sign'] = sign

        for u, v, d in G.edges(data=True):
            if (u, v) not in all_link_polarities and 'sign' in d:
                all_link_polarities[(u, v)] = d['sign']
        return all_link_polarities, G

    def _eval_component(self, name, state):
            if name in self.flows:
                self.flows[name].calculate_rate(state)
                result = self.flows[name].rate
            elif name in self.auxiliaries:
                self.auxiliaries[name].calculate_value(state)
                result = self.auxiliaries[name].value
            elif name in self.stocks:
                result = self.stocks[name].value
            elif name in self.parameters:
                result = self.parameters[name].value
            else:
                return 0.0  # default for unknowns

            # Convert to scalar if it's a Quantity
            if isinstance(result, ureg.Quantity):
                try:
                    result = result.to_base_units().magnitude
                except Exception as e:
                    print(f"[WARN] Could not extract magnitude for '{name}': {e}")
                    result = 0.0  # Fallback
            return float(result)

    def get_loops(self):
        return self.loops

    def get_link_polarities(self):
        return self._link_polarities

    def _get_var_value_from_state(self, state, var_name):
        """
        Retrieves the current value of a variable (stock, auxiliary, parameter, or flow rate)
        from a given state dictionary (which contains component objects).
        """
        if var_name in state['stocks']:
            return state['stocks'][var_name].value
        elif var_name in state['auxiliaries']:
            # For auxiliaries, we typically want their calculated value based on the given state.
            # If state['auxiliaries'][var_name] is an object, its .value might be stale
            # or might be from a different state context.
            # It's often better to re-calculate it using _eval_component if this state is a perturbation.
            # However, if this function is just to "get" a value that's assumed to be current in 'state',
            # then direct access is fine. Given the name, direct access is implied.
            return state['auxiliaries'][var_name].value
        elif var_name in state['parameters']:
            return state['parameters'][var_name].value
        elif var_name in state['flows']:
            # Similar to auxiliaries, flow rates are calculated.
            # Direct access to .rate is fine if it's assumed current in 'state'.
            return state['flows'][var_name].rate
        else:
            print(f"[Warning] Variable '{var_name}' not found in state for _get_var_value_from_state.")
            # Depending on how this is used, you might want to raise an error or return a specific
            # value like None or float('nan') to indicate the variable was not found.
            # For polarity calculations, returning None might propagate to an 'unknown' polarity.
            return None

    def _get_auxiliary_calculation_order(self):
        """
        Determines the correct calculation order for auxiliaries based on their dependencies.
        Uses topological sort.
        """
        if not self.auxiliaries:
            return []

        aux_graph = nx.DiGraph()
        aux_names = list(self.auxiliaries.keys())
        aux_graph.add_nodes_from(aux_names)

        for aux_name, aux_obj in self.auxiliaries.items():
            if hasattr(aux_obj, 'inputs') and aux_obj.inputs:
                for input_name in aux_obj.inputs:
                    if input_name in self.auxiliaries:  # If the input is another auxiliary
                        aux_graph.add_edge(input_name, aux_name)
        
        try:
            sorted_auxiliaries = list(nx.topological_sort(aux_graph))
            return sorted_auxiliaries
        except nx.NetworkXUnfeasible:
            # This occurs if there's a cycle in auxiliary dependencies
            cycles = list(nx.simple_cycles(aux_graph))
            cycle_str = "; ".join([" -> ".join(cycle + [cycle[0]]) for cycle in cycles])
            raise ValueError(
                f"Cyclic dependency detected among auxiliaries. Cannot determine calculation order. "
                f"Cycles: {cycle_str}. Please check your model definition."
            )
        except nx.NetworkXError as e:
            # Other graph-related errors
            raise ValueError(f"Error building auxiliary dependency graph: {e}")

    def _set_var_value_in_state(self, state, var_name, new_value):
        """
        Sets the value of a variable (stock, auxiliary, parameter, or flow rate)
        within a given state dictionary (which contains component objects).

        This is typically used for preparing a perturbed state or for specific
        interventions where direct value setting is required. Be cautious, as
        subsequent calls to `step()` or methods that recalculate components
        (like `aux.calculate_value()`) might overwrite these settings for
        auxiliaries and flows.

        :param state: The system state dictionary (e.g., from `_get_system_state(get_objects=True)`).
        :param var_name: The name of the variable to set.
        :param new_value: The new value for the variable. Should be compatible
                          with the variable's expected type (e.g., a pint.Quantity
                          if units are used).
        """
        if var_name in state['stocks']:
            # Assuming new_value is already a Quantity with correct units if applicable
            state['stocks'][var_name].value = new_value
        elif var_name in state['auxiliaries']:
            state['auxiliaries'][var_name].value = new_value
        elif var_name in state['parameters']:
            state['parameters'][var_name].value = new_value
        elif var_name in state['flows']:
            # Flows have a 'rate' attribute that gets calculated
            state['flows'][var_name].rate = new_value
        else:
            print(f"[Warning] Variable '{var_name}' not found in state for _set_var_value_in_state, or its type is not handled for direct setting.")
            # Optionally, raise an error:
            # raise ValueError(f"Variable '{var_name}' not found in state or not settable directly via _set_var_value_in_state.")

    def _estimate_link_sign(self, input_var_name, output_var_name, base_state):
        """
        Estimates the polarity of the link between input_var and output_var
        by perturbing input_var and observing the change in output_var.
        Uses the provided base_state for all calculations.
        """

        # 1. Definitional polarity for Flow -> Stock links
        # Check if the input is a flow AND the output is a stock
        if input_var_name in self.flows and output_var_name in self.stocks:
            # Now it's safe to assume input_var_name is a key in self.flows
            flow_obj = self.flows[input_var_name] # Get the actual flow object
            
            # Check if the output_var_name (the stock) is the target of this flow
            if flow_obj.target_stock and flow_obj.target_stock.name == output_var_name:
                # print(f"Definitional Link (+1): {input_var_name} (Flow) -> {output_var_name} (Target Stock)")
                return 1  # Inflow increases stock
            
            # Check if the output_var_name (the stock) is the source of this flow
            if flow_obj.source_stock and flow_obj.source_stock.name == output_var_name:
                # print(f"Definitional Link (-1): {input_var_name} (Flow) -> {output_var_name} (Source Stock)")
                return -1  # Outflow decreases stock
            
            # If input_var_name is a flow and output_var_name is a stock,
            # but it's not its direct source/target, this specific link might be an error in graph construction
            # or an indirect influence. For direct F->S, it must be source or target.
            # If it falls through here, it means it's a F->S link in the graph but not matching the Flow's properties.
            # This could happen if G.add_edge was called with an incorrect stock for a flow.
            # For safety, let such cases be handled by perturbation or return a neutral/unknown.
            # print(f"[Polarity Warn] Link {input_var_name}->{output_var_name} is F->S in graph but not direct source/target. Perturbing.")

        # --- Perturbation logic starts here if not a definitional F->S link OR if F->S check didn't return ---
        
        # --- Optional Debugging Print Block (Enable for specific failing links) ---
        # Trigger this debug block for a link you are specifically investigating.
        # Example:
        # if input_var_name == "Adjustment from Inventory" and output_var_name == "Desired Production":
        #     print(f"\n--- Debugging Perturbation for Link: {input_var_name} -> {output_var_name} ---")
        #     # Initial values will be printed after they are fetched/calculated below.
        name_to_skip_recalculation = None
        if input_var_name in self.auxiliaries or input_var_name in self.flows:
            name_to_skip_recalculation = input_var_name
        # Get the original value of the input variable from the UNMODIFIED base_state
        original_input_value = self._get_var_value_from_state(base_state, input_var_name)

        if original_input_value is None:
            print(f"[WARN] Polarity: Original input value for '{input_var_name}' is None. Cannot estimate link to '{output_var_name}'. Sign: 0")
            return 0 

        if not isinstance(original_input_value, Q_):
            print(f"[WARN] Polarity: Input '{input_var_name}' value ({original_input_value}) is not a Quantity. Assuming dimensionless.")
            try:
                original_input_value = Q_(original_input_value, self.ureg.dimensionless)
            except Exception as e: # Catch potential errors during Quantity creation
                print(f"[ERROR] Polarity: Failed to convert '{input_var_name}' value ({original_input_value}) to Quantity: {e}. Sign: 0")
                return 0
        
        # Determine units for perturbation: use original_input_value's units, or dimensionless if not a Quantity
        val_units = original_input_value.units if hasattr(original_input_value, 'units') else self.ureg.dimensionless
        perturbation_delta = Q_(self.epsilon_for_perturbation, val_units)

        # --- Positive Perturbation ---
        perturbed_value_plus = original_input_value + perturbation_delta
        current_state_plus = copy.deepcopy(base_state) # Create a fresh deep copy of the base state
        self._set_var_value_in_state(current_state_plus, input_var_name, perturbed_value_plus)
        self._update_auxiliaries_and_flows(current_state_plus, 
                                           perturbed_input_aux_or_flow_name=name_to_skip_recalculation) # Recalculate based on the perturbed state
        output_value_plus = self._get_var_value_from_state(current_state_plus, output_var_name)

        # --- Negative Perturbation ---
        perturbed_value_minus = original_input_value - perturbation_delta
        current_state_minus = copy.deepcopy(base_state) # Create another fresh deep copy
        self._set_var_value_in_state(current_state_minus, input_var_name, perturbed_value_minus)
        self._update_auxiliaries_and_flows(current_state_minus,
                                           perturbed_input_aux_or_flow_name=name_to_skip_recalculation) # Recalculate
        output_value_minus = self._get_var_value_from_state(current_state_minus, output_var_name)

        # --- Post-Perturbation Checks and Delta Calculation ---
        if output_value_plus is None or output_value_minus is None:
            print(f"[WARN] Polarity: Output value for '{output_var_name}' is None for one/both perturbations. Link {input_var_name}->{output_var_name}. Sign: 0")
            return 0

        if not isinstance(output_value_plus, Q_):
            output_value_plus = Q_(output_value_plus, self.ureg.dimensionless)
        if not isinstance(output_value_minus, Q_):
            output_value_minus = Q_(output_value_minus, self.ureg.dimensionless)
        
        if output_value_plus.units != output_value_minus.units:
            print(f"[WARN] Polarity: Unit mismatch for '{output_var_name}' ({output_value_plus.units} vs {output_value_minus.units}). Link {input_var_name}->{output_var_name}. Sign: 0")
            return 0

        delta_output = output_value_plus - output_value_minus
        
        if input_var_name == "Desired Production" and output_var_name == "Production Rate":
            print(f"  Base State Time: {base_state.get('time')}")
            print(f"  Original Input ({input_var_name}): {original_input_value}")
            print(f"  Perturbation Delta: {perturbation_delta}")
            print(f"  Perturbed Input Plus: {perturbed_value_plus}")
            print(f"  Perturbed Input Minus: {perturbed_value_minus}")
            print(f"  --- Values in current_state_plus before calling _get_var_value_from_state for output ---")
            print(f"    current_state_plus['auxiliaries']['Desired Production'].value = {current_state_plus['auxiliaries']['Desired Production'].value}") # Check the perturbed input
            # If 'Production Rate' depends on other auxes, check them too if needed.
            print(f"  Output Plus ({output_var_name}): {output_value_plus}")
            print(f"  --- Values in current_state_minus before calling _get_var_value_from_state for output ---")
            print(f"    current_state_minus['auxiliaries']['Desired Production'].value = {current_state_minus['auxiliaries']['Desired Production'].value}") # Check the perturbed input
            print(f"  Output Minus ({output_var_name}): {output_value_minus}")
            print(f"  Delta Output: {delta_output} (Magnitude: {delta_output.magnitude})")
            print(f"  Numeric Threshold for Output Change ({self.numeric_threshold}) vs. Abs(Delta Output Magnitude): {abs(delta_output.magnitude)}")
            # Determine what the sign *would* be with current logic
            calculated_sign = 0
            if abs(delta_output.magnitude) >= self.numeric_threshold:
                calculated_sign = 1 if delta_output.magnitude > 0 else -1
            print(f"  Calculated Sign (based on current logic): {calculated_sign}")
            print(f"  --- End Debugging Link: {input_var_name} -> {output_var_name} ---\n")


        # --- Determine Sign based on Delta Output ---
        # self.numeric_threshold is defined in __init__ (e.g., 1e-12 or 1e-9)
        if abs(delta_output.magnitude) < self.numeric_threshold:
            # If the change is below the threshold, consider it zero.
            # One final check: if input didn't change but output did, respect that.
            # This covers cases where perturbation_delta is too small relative to original_input_value's magnitude
            # such that original_input_value +/- perturbation_delta numerically equals original_input_value.
            if (perturbed_value_plus.magnitude == original_input_value.magnitude and 
                perturbed_value_minus.magnitude == original_input_value.magnitude):
                # Input didn't effectively change with perturbation.
                # Compare perturbed outputs to the *original* output from base_state.
                original_output_value = self._get_var_value_from_state(base_state, output_var_name)
                if not isinstance(original_output_value, Q_):
                    original_output_value = Q_(original_output_value, self.ureg.dimensionless)
                
                if output_value_plus.units == original_output_value.units: # Ensure units match for comparison
                    if (output_value_plus - original_output_value).magnitude > self.numeric_threshold: return 1
                    if (output_value_plus - original_output_value).magnitude < -self.numeric_threshold: return -1
                # (No need to check output_value_minus if plus didn't show a change from original here)
                # print(f"[Debug] Input {input_var_name} didn't change with perturbation. Output {output_var_name} also stable. Sign: 0")
                return 0 #Truly no change detected if input itself was stable to perturbation
            else:
                # Input did change, but output change was below threshold.
                # print(f"[Debug] Input {input_var_name} changed. Output {output_var_name} change below threshold. Sign: 0")
                return 0 
        elif delta_output.magnitude > 0: # delta_output.magnitude is positive and significant
            return 1
        else: # delta_output.magnitude is negative and significant
            return -1

    def print_loops(self):
        """Formats and prints the detected feedback loops grouped by polarity."""
        print("\n--- Detected Feedback Loops (Polarity @ t=0) ---")
        detected_loops = self.get_loops() # Use the getter
        if not detected_loops: print("  No feedback loops were detected."); return
        elif any(loop[0] == "Error" for loop in detected_loops): print("  Error during loop detection."); return # Simplified error check
        elif any("skipped" in loop[1] for loop in detected_loops): print("  Loop detection incomplete."); return # Simplified skip check

        reinforcing = [loop for loop in detected_loops if loop[0] == 'R (+)']
        balancing = [loop for loop in detected_loops if loop[0] == 'B (-)']
        neutral = [loop for loop in detected_loops if loop[0] == 'N (0)']
        ambiguous = [loop for loop in detected_loops if loop[0] == '?']

        def print_loop_group(title, loops_list):
            print(f"\n  {title}:")
            if not loops_list: print("    None found.")
            else:
                loops_list.sort(key=lambda x: x[1])
                for i, (polarity, loop_str) in enumerate(loops_list): print(f"    {i+1}. {polarity} : {loop_str}")

        print_loop_group("Reinforcing Loops (+)", reinforcing)
        print_loop_group("Balancing Loops (-)", balancing)
        print_loop_group("Neutral Loops (0 @ t=0)", neutral)
        print_loop_group("Ambiguous Loops (?)", ambiguous)
        if neutral or ambiguous: print("\n  Note: Neutral/Ambiguous polarity details...")
        print("----------------------------------------------------")

    def print_relationships(self):
        """Formats and prints all model relationships and their calculated polarities."""
        print("\n--- Model Relationships and Link Polarities (@ t=0) ---")
        all_polarities = self.get_link_polarities()
        if not all_polarities: print("  Could not retrieve link polarities."); return

        link_outputs = []
        for (u, v), sign in all_polarities.items():
            symbol = '?'; source_type = ""
            # Inside the relevant method where line 467 exists (likely related to loop polarity calculation)
            if sign == 1:
                symbol = '+'
            elif sign == -1:
                symbol = '-'
            elif sign == 0:
                symbol = '0'
            else: # Handle unexpected sign values if necessary
                symbol = '?' # Or raise an error
            if u in self.parameters: source_type = "(P)"
            link_outputs.append(f"  {u} {source_type} -> {v} : ({symbol})")

        if not link_outputs: print("  No relationships found.")
        else:
            link_outputs.sort(); print("\n  --- All Links ---")
            for line in link_outputs: print(line)
        print("\n  Note: Polarity (+,-,0,?) calculated via numerical perturbation at t=0.")
        print("----------------------------------------------------")

    def plot_structure_graph(self, filename="structure_graph.png", figsize=(16,12), layout_prog='spring', k=0.9, seed=42, **kwargs):
        """Generates and saves a visual plot of the model structure graph, including parameters."""
        print(f"\nGenerating full model structure graph ('{filename}')...")

        # 1. Get ALL calculated link polarities
        all_polarities = self.get_link_polarities()
        if not all_polarities:
            print("  Cannot generate graph: Link polarities not available.")
            return

        # 2. Create a NEW graph specifically for plotting
        G_plot = nx.DiGraph()

        # 3. Add ALL nodes (Stocks, Flows, Aux, Params involved in links)
        all_nodes_in_links = set(u for u, v in all_polarities.keys()) | set(v for u, v in all_polarities.keys())
        node_labels = {}
        node_types = {}
        all_components = {**self.stocks, **self.flows, **self.auxiliaries, **self.parameters}
        print("    Adding linked nodes (incl. parameters)...")
        for name in all_nodes_in_links:
            if name in all_components:
                 comp = all_components[name]; comp_type = type(comp).__name__
                 node_type_str = 'Unknown'
                 if comp_type == 'Parameter':
                    node_type_str = 'Parameter'
                 elif comp_type == 'Stock':
                    node_type_str = 'Stock'
                 elif comp_type == 'Flow':
                    node_type_str = 'Flow'
                 elif comp_type == 'Auxiliary':
                    node_type_str = 'Auxiliary'
                 G_plot.add_node(name, type=node_type_str)
                 node_labels[name] = name
                 node_types[name] = node_type_str
            # else: print(f"      Warning: Node '{name}' found in links but not in component lists.")

        # 4. Add Edges based on the calculated polarities dictionary
        edge_labels = {}
        print("    Adding edges from calculated polarities...")
        for (u, v), sign in all_polarities.items():
            if G_plot.has_node(u) and G_plot.has_node(v): # Add edge only if both nodes were added
                symbol = '?';
                if sign == 1:
                    symbol = '+';
                elif sign == -1:
                    symbol = '-';
                elif sign == 0:
                    symbol = '0'
                G_plot.add_edge(u, v)
                edge_labels[(u, v)] = symbol

        # 5. Plotting Logic (using G_plot)
        if G_plot.number_of_nodes() == 0: print("  Cannot generate graph: No nodes added."); return
        plt.figure(figsize=figsize); ax_graph = plt.gca()
        print(f"    Calculating '{layout_prog}' layout...")
        try:
            if layout_prog == 'spring': pos = nx.spring_layout(G_plot, k=k, iterations=50, seed=seed)
            elif layout_prog == 'kamada_kawai': pos = nx.kamada_kawai_layout(G_plot)
            else: pos = nx.spring_layout(G_plot, k=k, iterations=50, seed=seed)
        except Exception as e: print(f"    Layout failed ({e}), using spring."); pos = nx.spring_layout(G_plot, k=k, iterations=50, seed=seed)

        node_colors: list[str] = []
        for node in G_plot.nodes(): # Iterate G_plot nodes
            node_type = node_types.get(node, 'Unknown');
            color = 'grey'
            if node_type == 'Stock':
                color = 'skyblue';
            elif node_type == 'Flow':
                color = 'lightcoral'
            elif node_type == 'Auxiliary':
                color = 'lightgreen';
            elif node_type == 'Parameter':
                color = 'lightgrey'
            node_colors.append(color)

        node_size = kwargs.get('node_size', 2000); font_size = kwargs.get('font_size', 8); edge_font_size = kwargs.get('edge_font_size', 9)
        alpha = kwargs.get('alpha', 0.9); arrowstyle = kwargs.get('arrowstyle', '-|>'); arrowsize = kwargs.get('arrowsize', 15);
        edge_color = kwargs.get('edge_color', 'gray'); edge_alpha = kwargs.get('edge_alpha', 0.6); edge_font_color = kwargs.get('edge_font_color', 'red');
        plot_title = kwargs.get('title', "Full Model Structure with Link Polarities (@ t=0)"); dpi = kwargs.get('dpi', 300)

        print("    Drawing graph components...")
        nx.draw_networkx_nodes(G_plot, pos, node_color=node_colors, node_size=node_size, alpha=alpha, ax=ax_graph)
        nx.draw_networkx_edges(G_plot, pos, arrowstyle=arrowstyle, arrowsize=arrowsize, node_size=node_size, edge_color=edge_color, alpha=edge_alpha, ax=ax_graph)
        nx.draw_networkx_labels(G_plot, pos, labels=node_labels, font_size=font_size, ax=ax_graph) # Use node_labels dict
        nx.draw_networkx_edge_labels(G_plot, pos, edge_labels=edge_labels, font_color=edge_font_color, font_size=edge_font_size, ax=ax_graph)

        plt.title(plot_title); plt.axis('off')
        try: plt.savefig(filename, dpi=dpi, bbox_inches='tight'); print(f"  Saved structure graph: {filename}")
        except Exception as e: print(f"  Error saving graph plot: {e}")
        plt.close()

    def plot_results(self, columns=None, together=True, filename="results_plot.png", **kwargs):
        """Generates and saves plots of simulation results."""
        print(f"\nPlotting simulation results ('{filename}')...")
        results_df = self.get_results_for_plot()
        if results_df.empty: print("  Cannot plot results: DataFrame is empty."); return

        plot_cols = []
        if columns is None:
            plot_cols = list(self.stocks.keys()) + list(self.flows.keys()) + list(self.auxiliaries.keys())
            plot_cols = [col for col in plot_cols if col in results_df.columns]
        elif isinstance(columns, list):
            plot_cols = [col for col in columns if col in results_df.columns]
            if not plot_cols: print(f"  Warning: None of the specified columns {columns} found in results."); return
        else: print("  Warning: 'columns' must be None or list. Plotting skipped."); return
        if not plot_cols: print("  No valid columns found to plot."); return

        # Extract relevant kwargs or use defaults
        figsize = kwargs.get('figsize', (12, 7))
        grid = kwargs.get('grid', True)
        xlabel = kwargs.get('xlabel', 'Time')
        title = kwargs.get('title', 'Simulation Results')
        ylabel = kwargs.get('ylabel', 'Value')
        dpi = kwargs.get('dpi', 300)

        if together:
            plt.figure(figsize=figsize)
            try:
                results_df[plot_cols].plot(ax=plt.gca()) # Plot selected columns on the current axes
                plt.title(title); plt.xlabel(xlabel); plt.ylabel(ylabel); plt.grid(grid); plt.legend(); plt.tight_layout()
                plt.savefig(filename, dpi=dpi, bbox_inches='tight'); print(f"  Saved combined results plot: {filename}")
            except Exception as e: print(f"  Error generating combined plot: {e}")
            plt.close()
        else: # Plot separately
            print(f"  Plotting {len(plot_cols)} variables separately...")
            base_filename, ext = os.path.splitext(filename)
            for col in plot_cols:
                plt.figure(figsize=kwargs.get('figsize_sep', (10, 5))) # Allow separate figsize
                try:
                    results_df[[col]].plot(ax=plt.gca(), legend=False); plt.title(f"{col}"); plt.xlabel(xlabel); plt.ylabel(col); plt.grid(grid); plt.tight_layout()
                    sep_filename = f"{base_filename}_{col.replace(' ','_').replace('/','_')}{ext}" # Make filename safe
                    plt.savefig(sep_filename, dpi=dpi, bbox_inches='tight'); print(f"    Saved: {sep_filename}")
                except Exception as e: print(f"    Error generating plot for '{col}': {e}")
                plt.close()
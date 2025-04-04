import pandas as pd
class Simulation:
    """
    Manages the simulation of a system dynamics model, handling time stepping,
    calculation order, and data collection.
    """
    def __init__(self, stocks, flows, auxiliaries, parameters, timestep=1.0):
        self.stocks = stocks
        self.flows = flows
        self.auxiliaries = auxiliaries
        self.parameters = parameters
        self.timestep = timestep
        self.time = 0.0
        self.history = []
        self.loops = [] # Add list to store feedback loops

    def step(self):
        """
        Advance the simulation by one timestep.
        """
        # Calculate auxiliaries (assuming they depend on current state)
        for aux in self.auxiliaries:
            aux.calculate_value(self._get_system_state())
        
        # Calculate flow rates
        for flow in self.flows:
            flow.calculate_rate(self._get_system_state())
        
        # Update stocks
        for stock in self.stocks:
            stock.update(self.timestep)
        
        # Record state
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

        import pandas as pd

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


    def run(self, duration):
        """
        Run the simulation for a given duration.
        """
        steps = int(duration / self.timestep)
        for _ in range(steps):
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

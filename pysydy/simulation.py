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
        return pd.DataFrame(self.history).set_index('time')


    def run(self, duration):
        """
        Run the simulation for a given duration.
        """
        steps = int(duration / self.timestep)
        for _ in range(steps):
            self.step()
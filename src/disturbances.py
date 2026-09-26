# src/disturbances.py

class Disturbance:
    """
    Simple disturbance object used during simulation.
    Mirrors entries from disturbances_scenario_1.yaml.
    """

    def __init__(self, time, kind, magnitude):
        self.time = time          # integer time step
        self.kind = kind          # e.g. "sensor_noise", "world_shift"
        self.magnitude = magnitude

    def to_dict(self):
        return {
            "time": self.time,
            "kind": self.kind,
            "magnitude": self.magnitude,
        }

    def __repr__(self):
        return f"Disturbance(time={self.time}, kind={self.kind}, magnitude={self.magnitude:.2f})"


def build_disturbance_schedule(config_dict):
    """
    Takes the loaded YAML dict from disturbances_scenario_1.yaml
    and returns a dict: time_step -> Disturbance.
    """
    disturbances = config_dict.get("disturbances", [])
    schedule = {}
    for d in disturbances:
        t = d["time"]
        schedule[t] = Disturbance(
            time=t,
            kind=d["kind"],
            magnitude=d["magnitude"],
        )
    return schedule
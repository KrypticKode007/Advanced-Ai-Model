# src/environment.py

import random


class GridWorld:
    """
    Very simple gridworld environment.
    The agent moves on a 2D grid with obstacles, a start, and a goal.
    Observations are simplified to a single float (e.g., distance to goal),
    so it plugs nicely into your WorldModel.
    """

    def __init__(self, world_cfg, task_cfg):
        self.width = world_cfg["width"]
        self.height = world_cfg["height"]

        self.obstacles = {(o["x"], o["y"]) for o in world_cfg.get("obstacles", [])}
        self.hazard_zones = world_cfg.get("hazard_zones", [])

        self.start = (task_cfg["start"]["x"], task_cfg["start"]["y"])
        self.goal = (task_cfg["goal"]["x"], task_cfg["goal"]["y"])
        self.max_steps = task_cfg["max_steps"]

        self.reset()

        # Disturbance-related state
        self.sensor_noise_level = 0.0
        self.sensor_blackout = False
        self.actuator_scale = 1.0

    def reset(self):
        self.pos = list(self.start)
        self.steps = 0
        self.done = False
        self.success = False
        self.collisions = 0

    # ---------- Disturbances ----------

    def apply_disturbance(self, disturbance):
        kind = disturbance.get("kind", "none")
        mag = disturbance.get("magnitude", 0.0)

        if kind == "none":
            return
        elif kind == "sensor_noise":
            self.sensor_noise_level = mag
        elif kind == "sensor_blackout":
            self.sensor_blackout = True
        elif kind == "world_shift":
            # Shift goal for simplicity
            self.goal = (self.goal[0], self.goal[1] + int(mag))
        elif kind == "actuator_weakening":
            self.actuator_scale = max(0.1, 1.0 - mag)
        # You can add more kinds later.

    # ---------- Core env dynamics ----------

    def _distance_to_goal(self):
        return ((self.pos[0] - self.goal[0]) ** 2 + (self.pos[1] - self.goal[1]) ** 2) ** 0.5

    def observe(self):
        """
        Returns a scalar observation: (noisy) distance to goal.
        """
        if self.sensor_blackout:
            return 0.0  # useless reading

        base = self._distance_to_goal()
        noise = random.uniform(-self.sensor_noise_level, self.sensor_noise_level)
        return base + noise

    def step(self, action):
        """
        Action is a simple direction: 'up', 'down', 'left', 'right'.
        Actuator weakening scales movement.
        """
        if self.done:
            return

        dx, dy = 0, 0
        if action == "up":
            dy = 1
        elif action == "down":
            dy = -1
        elif action == "left":
            dx = -1
        elif action == "right":
            dx = 1

        # Apply actuator weakening
        dx = int(round(dx * self.actuator_scale))
        dy = int(round(dy * self.actuator_scale))

        new_x = max(0, min(self.width - 1, self.pos[0] + dx))
        new_y = max(0, min(self.height - 1, self.pos[1] + dy))

        if (new_x, new_y) in self.obstacles:
            self.collisions += 1
            # stay in place
        else:
            self.pos = [new_x, new_y]

        self.steps += 1

        if (self.pos[0], self.pos[1]) == self.goal:
            self.done = True
            self.success = True
        elif self.steps >= self.max_steps:
            self.done = True

    def in_hazard_zone(self):
        x, y = self.pos
        for hz in self.hazard_zones:
            cx, cy, r = hz["x"], hz["y"], hz["radius"]
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 <= r ** 2:
                return True
        return False
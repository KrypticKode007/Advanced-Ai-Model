"""ROS 2 bridge for a simulated two-drone cooperative swarm."""

import json
import time

import numpy as np
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import String


class MultiDroneSwarmAgent:
    """Track one simulated drone's energy, internal state, and position."""

    POWER_TRANSFER_AMOUNT = 0.5

    def __init__(self, agent_id, num_nodes=8):
        self.agent_id = agent_id
        self.num_nodes = num_nodes
        self.battery_level = float(np.random.uniform(40.0, 90.0))
        self.is_sleeping = False
        self.evolutionary_multiplier = 1.0
        self.cortical_state = np.zeros(num_nodes)
        self.sim_x = 0.0
        self.sim_y = 0.0
        self.sim_z = 0.0

    def calculate_internal_state(self, sensory_input, neighbor_battery_status):
        """Update energy and return a mode plus four simulated flight commands."""
        if self.is_sleeping:
            self.battery_level = min(self.battery_level + 3.0, 100.0)
            return "SLEEP_CONSOLIDATION", np.zeros(4)

        sensory_input = np.asarray(sensory_input, dtype=float)
        if sensory_input.shape != (self.num_nodes,):
            raise ValueError(
                f"sensory_input must have shape ({self.num_nodes},), "
                f"got {sensory_input.shape}"
            )

        self.battery_level = max(
            self.battery_level - 0.1 * self.evolutionary_multiplier, 0.0
        )
        if neighbor_battery_status == "RECEIVING_POWER_TRANSFER":
            self.battery_level = min(
                self.battery_level + self.POWER_TRANSFER_AMOUNT, 100.0
            )

        base_stress = float(np.mean(np.abs(sensory_input)))
        if self.battery_level < 25.0:
            valence = -1.2
            status = "LOW_ENERGY_ALARM"
        else:
            valence = 1.0 - (base_stress * 0.4)
            status = "OPTIMAL_NAVIGATION"

        self.cortical_state = np.tanh(
            sensory_input * valence * self.evolutionary_multiplier
        )
        velocities = (
            np.tanh(self.cortical_state[:4])
            * 2.0
            * self.evolutionary_multiplier
        )
        return status, velocities


class ROS2SimulatorSwarmBridge(Node):
    """Connect simulated swarm decisions to ROS 2 simulator topics."""

    def __init__(self):
        super().__init__("ros2_simulator_swarm_bridge")
        self.drone_a = MultiDroneSwarmAgent(agent_id="Drone_Alpha")
        self.drone_b = MultiDroneSwarmAgent(agent_id="Drone_Beta")

        self.sim_telemetry_sub = self.create_subscription(
            Twist,
            "/simulator/current_telemetry",
            self.simulator_telemetry_callback,
            10,
        )
        self.drone_a_vel_pub = self.create_publisher(
            Twist, "/sim/drone_alpha/cmd_vel", 10
        )
        self.drone_b_vel_pub = self.create_publisher(
            Twist, "/sim/drone_beta/cmd_vel", 10
        )
        self.swarm_comms_pub = self.create_publisher(
            String, "/swarm/network_comms_bus", 10
        )
        self.chatbot_diagnostics_pub = self.create_publisher(
            String, "/swarm/chatbot_diagnostics", 10
        )

        self._last_telemetry_time = time.monotonic()
        self.timer = self.create_timer(0.1, self.orchestrate_integrated_swarm)
        self.get_logger().info(
            "Simulator bridge and multi-drone power network online."
        )

    def simulator_telemetry_callback(self, msg):
        """Integrate simulator velocity telemetry into the virtual positions."""
        now = time.monotonic()
        elapsed = max(now - self._last_telemetry_time, 0.0)
        self._last_telemetry_time = now

        self.drone_a.sim_x += msg.linear.x * elapsed
        self.drone_b.sim_x += msg.linear.x * elapsed * 1.5

    def orchestrate_integrated_swarm(self):
        status_for_a = "STABLE"
        status_for_b = "STABLE"

        if self.drone_a.battery_level < 30.0 and self.drone_b.battery_level > 60.0:
            status_for_a = "RECEIVING_POWER_TRANSFER"
            status_for_b = "TRANSFERRING_POWER_TO_ALPHA"
            self.drone_b.battery_level -= MultiDroneSwarmAgent.POWER_TRANSFER_AMOUNT
        elif self.drone_b.battery_level < 30.0 and self.drone_a.battery_level > 60.0:
            status_for_a = "TRANSFERRING_POWER_TO_BETA"
            status_for_b = "RECEIVING_POWER_TRANSFER"
            self.drone_a.battery_level -= MultiDroneSwarmAgent.POWER_TRANSFER_AMOUNT

        for drone in (self.drone_a, self.drone_b):
            if drone.battery_level < 15.0 and not drone.is_sleeping:
                drone.is_sleeping = True
                drone.evolutionary_multiplier += 0.05
            elif drone.is_sleeping and drone.battery_level >= 95.0:
                drone.is_sleeping = False

        mock_env_sensors = np.array([0.2, -0.1, 0.4, 0.3, -0.5, 0.1, 0.2, -0.3])
        status_a, vel_a = self.drone_a.calculate_internal_state(
            mock_env_sensors, status_for_a
        )
        status_b, vel_b = self.drone_b.calculate_internal_state(
            mock_env_sensors, status_for_b
        )

        msg_a = Twist()
        msg_b = Twist()
        if not self.drone_a.is_sleeping:
            msg_a.linear.x = float(vel_a[0])
            msg_a.linear.y = float(vel_a[1])
            msg_a.linear.z = float(vel_a[2])
            msg_a.angular.z = float(vel_a[3])
        if not self.drone_b.is_sleeping:
            msg_b.linear.x = float(vel_b[0])
            msg_b.linear.y = float(vel_b[1])
            msg_b.linear.z = float(vel_b[2])
            msg_b.angular.z = float(vel_b[3])

        self.drone_a_vel_pub.publish(msg_a)
        self.drone_b_vel_pub.publish(msg_b)

        comms = String()
        comms.data = json.dumps(
            {
                "drone_alpha": status_for_a,
                "drone_beta": status_for_b,
            }
        )
        self.swarm_comms_pub.publish(comms)

        diagnostics = (
            "=== SIMULATED SWARM NETWORK HUB ===\n"
            f"[Drone_Alpha] -> Mode: {status_a:<20} | "
            f"Vitals: {self.drone_a.battery_level:.1f}% | "
            f"Comms: {status_for_a}\n"
            f"[Drone_Beta]  -> Mode: {status_b:<20} | "
            f"Vitals: {self.drone_b.battery_level:.1f}% | "
            f"Comms: {status_for_b}\n"
            f"Simulator Sync: Drone_Alpha virtual X position: "
            f"{self.drone_a.sim_x:.2f} meters."
        )
        log_msg = String()
        log_msg.data = diagnostics
        self.chatbot_diagnostics_pub.publish(log_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ROS2SimulatorSwarmBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

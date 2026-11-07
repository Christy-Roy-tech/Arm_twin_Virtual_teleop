#!/usr/bin/env python3
"""
Joint Command Publisher (Bridge) Node.

This node bridges the keyboard teleop output to the subsystems that
actually move the robot:

* **RViz** – listens on ``/joint_states`` (sensor_msgs/JointState).
* **Gazebo** – listens on ``/set_joint_trajectory``
  (trajectory_msgs/JointTrajectory).

Subscriptions
-------------
  /joint_commands  (sensor_msgs/JointState)

Publications
------------
  /joint_states           (sensor_msgs/JointState)
  /set_joint_trajectory   (trajectory_msgs/JointTrajectory)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration


class JointCommandPublisher(Node):
    """Republishes /joint_commands to /joint_states and /set_joint_trajectory."""

    def __init__(self):
        super().__init__('joint_command_publisher')

        # ── Subscriber ───────────────────────────────────────────────
        self.sub = self.create_subscription(
            JointState,
            '/joint_commands',
            self._command_callback,
            10,
        )

        # ── Publishers ───────────────────────────────────────────────
        # For robot_state_publisher / RViz
        self.joint_state_pub = self.create_publisher(
            JointState, '/joint_states', 10)

        # For Gazebo (position-based trajectory controller)
        self.trajectory_pub = self.create_publisher(
            JointTrajectory, '/set_joint_trajectory', 10)

        # Cache the latest command so we can re-publish at a steady rate
        self._latest_cmd: JointState | None = None

        # Publish at 50 Hz to keep RViz smooth even between keyboard
        # events (the keyboard node publishes at 10 Hz).
        self.timer = self.create_timer(0.02, self._timer_callback)

        self.get_logger().info(
            'Joint command publisher ready  '
            '(/joint_commands → /joint_states, /set_joint_trajectory)')

    # ── callbacks ────────────────────────────────────────────────────
    def _command_callback(self, msg: JointState):
        """Cache the latest command from the teleop node."""
        self._latest_cmd = msg

    def _timer_callback(self):
        """Republish the cached command to downstream topics."""
        if self._latest_cmd is None:
            return

        # 1) /joint_states  (for robot_state_publisher / RViz)
        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = list(self._latest_cmd.name)
        js.position = list(self._latest_cmd.position)
        self.joint_state_pub.publish(js)

        # 2) /set_joint_trajectory  (for Gazebo trajectory controller)
        traj = JointTrajectory()
        traj.header.stamp = self.get_clock().now().to_msg()
        traj.joint_names = list(self._latest_cmd.name)

        point = JointTrajectoryPoint()
        point.positions = list(self._latest_cmd.position)
        # Zero velocities – we want the arm to hold the target pose
        point.velocities = [0.0] * len(self._latest_cmd.position)
        # Reach the target within 0.5 s for smooth motion
        point.time_from_start = Duration(sec=0, nanosec=500_000_000)
        traj.points = [point]

        self.trajectory_pub.publish(traj)


def main(args=None):
    rclpy.init(args=args)
    node = JointCommandPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()

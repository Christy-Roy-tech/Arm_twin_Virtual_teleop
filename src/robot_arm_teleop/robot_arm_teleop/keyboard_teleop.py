#!/usr/bin/env python3
"""
Keyboard Teleoperation Node for a 5-DOF Robotic Arm.

Reads non-blocking keyboard input from the terminal and publishes
joint commands on the /joint_commands topic (sensor_msgs/JointState).

Key Bindings
------------
  1-5      Select joint 1-5 (waist, shoulder, elbow, wrist_pitch, wrist_roll)
  g        Select gripper (controls both left & right prismatic fingers)
  w / ↑    Increase the selected joint angle by one step
  s / ↓    Decrease the selected joint angle by one step
  + / =    Increase step size by 0.01 rad
  - / _    Decrease step size by 0.01 rad (min 0.01)
  h        Home – reset every joint to zero
  q        Quit
"""

import math
import sys
import select
import termios
import tty

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


# ── Joint configuration ──────────────────────────────────────────────
# Names MUST match exactly what is defined in the URDF (robot_arm.urdf.xacro)
JOINT_NAMES = [
    'joint1_waist',           # waist rotation
    'joint2_shoulder',        # shoulder pitch
    'joint3_elbow',           # elbow pitch
    'joint4_wrist_pitch',     # wrist pitch
    'joint5_wrist_roll',      # wrist roll
    'joint6_gripper_left',    # gripper left  (prismatic)
    'joint7_gripper_right',   # gripper right (prismatic, mimic of joint6)
]

# (lower_limit, upper_limit) for each joint – same order as JOINT_NAMES
JOINT_LIMITS = [
    (-math.pi,     math.pi),      # joint1_waist
    (-math.pi / 2, math.pi / 2),  # joint2_shoulder
    (-math.pi / 2, math.pi / 2),  # joint3_elbow
    (-math.pi / 2, math.pi / 2),  # joint4_wrist_pitch
    (-math.pi,     math.pi),      # joint5_wrist_roll
    (0.0,          0.015),        # joint6_gripper_left  (prismatic)
    (0.0,          0.015),        # joint7_gripper_right (prismatic – mimic)
]

FRIENDLY_NAMES = [
    'Waist', 'Shoulder', 'Elbow', 'Wrist Pitch', 'Wrist Roll',
    'Gripper L', 'Gripper R',
]

# ANSI escape sequences for arrow keys (after '\x1b[')
ARROW_UP = 'A'
ARROW_DOWN = 'B'

# Default step sizes
DEFAULT_JOINT_STEP = 0.05     # radians
DEFAULT_GRIPPER_STEP = 0.001  # metres


class KeyboardTeleop(Node):
    """Publishes joint position commands driven by keyboard input."""

    def __init__(self):
        super().__init__('keyboard_teleop')

        # ── Publisher ────────────────────────────────────────────────
        self.pub = self.create_publisher(JointState, '/joint_commands', 10)

        # ── State ────────────────────────────────────────────────────
        self.positions = [0.0] * len(JOINT_NAMES)
        self.selected_index = 0          # 0-4 → joints, 5 → gripper
        self.joint_step = DEFAULT_JOINT_STEP
        self.gripper_step = DEFAULT_GRIPPER_STEP

        # ── Terminal raw-mode setup ──────────────────────────────────
        self.old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

        # ── 10 Hz publish timer ──────────────────────────────────────
        self.timer = self.create_timer(0.1, self._timer_callback)

        self._print_banner()
        self._print_state()

    # ── helpers ──────────────────────────────────────────────────────
    @property
    def _step(self) -> float:
        """Return the step for the currently selected joint/gripper."""
        return self.gripper_step if self.selected_index == 5 else self.joint_step

    def _clamp(self, index: int, value: float) -> float:
        lo, hi = JOINT_LIMITS[index]
        return max(lo, min(hi, value))

    # ── keyboard reading (non-blocking) ──────────────────────────────
    def _get_key(self) -> str | None:
        """Return a single key press or ``None`` if nothing is available."""
        if select.select([sys.stdin], [], [], 0.0)[0]:
            ch = sys.stdin.read(1)
            # Handle ANSI escape sequences (arrow keys)
            if ch == '\x1b':
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        if select.select([sys.stdin], [], [], 0.05)[0]:
                            ch3 = sys.stdin.read(1)
                            return f'ARROW_{ch3}'
                return None  # lone ESC – ignore
            return ch
        return None

    # ── main loop (called by timer) ──────────────────────────────────
    def _timer_callback(self):
        key = self._get_key()
        if key is not None:
            self._handle_key(key)

        # Always publish the current state at 10 Hz
        self._publish()

    def _handle_key(self, key: str):
        # ── Joint selection (1-5) ────────────────────────────────────
        if key in ('1', '2', '3', '4', '5'):
            self.selected_index = int(key) - 1
            self.get_logger().info(
                f'Selected {FRIENDLY_NAMES[self.selected_index]} '
                f'(joint_{int(key)})')

        # ── Gripper selection ────────────────────────────────────────
        elif key in ('g', 'G'):
            self.selected_index = 5  # gripper (joint_6 & joint_7)
            self.get_logger().info('Selected Gripper')

        # ── Increase position (w / ↑) ───────────────────────────────
        elif key in ('w', 'W', f'ARROW_{ARROW_UP}'):
            self._move_selected(+1)

        # ── Decrease position (s / ↓) ───────────────────────────────
        elif key in ('s', 'S', f'ARROW_{ARROW_DOWN}'):
            self._move_selected(-1)

        # ── Step size adjustment ─────────────────────────────────────
        elif key in ('+', '='):
            self.joint_step += 0.01
            self.gripper_step = min(self.gripper_step + 0.0005, 0.015)
            self.get_logger().info(
                f'Step ↑  joint={self.joint_step:.3f} rad  '
                f'gripper={self.gripper_step:.4f} m')

        elif key in ('-', '_'):
            self.joint_step = max(0.01, self.joint_step - 0.01)
            self.gripper_step = max(0.0005, self.gripper_step - 0.0005)
            self.get_logger().info(
                f'Step ↓  joint={self.joint_step:.3f} rad  '
                f'gripper={self.gripper_step:.4f} m')

        # ── Home position ────────────────────────────────────────────
        elif key in ('h', 'H'):
            self.positions = [0.0] * len(JOINT_NAMES)
            self.get_logger().info('Moved to HOME (all joints → 0)')

        # ── Quit ─────────────────────────────────────────────────────
        elif key in ('q', 'Q'):
            self.get_logger().info('Quitting keyboard teleop …')
            self._restore_terminal()
            raise SystemExit

        self._print_state()

    def _move_selected(self, direction: int):
        """Move the currently selected joint (or gripper pair) by ±step."""
        if self.selected_index <= 4:
            # Single revolute joint
            idx = self.selected_index
            self.positions[idx] = self._clamp(
                idx, self.positions[idx] + direction * self._step)
        else:
            # Gripper: joint_6 and mimic joint_7 move together
            val = self._clamp(
                5, self.positions[5] + direction * self._step)
            self.positions[5] = val
            self.positions[6] = val  # mimic

    # ── publishing ───────────────────────────────────────────────────
    def _publish(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(JOINT_NAMES)
        msg.position = list(self.positions)
        self.pub.publish(msg)

    # ── terminal helpers ─────────────────────────────────────────────
    @staticmethod
    def _print_banner():
        print('\n' + '=' * 60)
        print('  5-DOF Robotic Arm – Keyboard Teleop')
        print('=' * 60)
        print('  1-5  : select joint 1-5')
        print('  g    : select gripper')
        print('  w/↑  : increase joint value')
        print('  s/↓  : decrease joint value')
        print('  +/-  : adjust step size')
        print('  h    : home (all zeros)')
        print('  q    : quit')
        print('=' * 60)

    def _print_state(self):
        """Print a compact table of joint values to the terminal."""
        lines = ['\n  Joint Values:']
        for i, (name, pos) in enumerate(zip(FRIENDLY_NAMES, self.positions)):
            marker = ' >>' if (i == self.selected_index or
                               (self.selected_index == 5 and i in (5, 6))) \
                          else '   '
            if i >= 5:
                lines.append(f'{marker} {name:14s}: {pos:+.4f} m')
            else:
                lines.append(
                    f'{marker} {name:14s}: {pos:+.4f} rad  '
                    f'({math.degrees(pos):+7.2f}°)')
        lines.append(
            f'  Step: {self.joint_step:.3f} rad | '
            f'{self.gripper_step:.4f} m')
        print('\n'.join(lines))

    def _restore_terminal(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    def destroy_node(self):
        self._restore_terminal()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardTeleop()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()

"""
display.launch.py — RViz-only visualization of the 5-DOF robotic arm.

Launches:
  • xacro  → processes the URDF/Xacro model
  • robot_state_publisher → publishes /robot_description and TF frames
  • joint_state_publisher_gui → GUI sliders to set joint angles
  • rviz2  → 3-D visualisation with a saved config
"""

import os
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # ── Package paths ───────────────────────────────────────────────────
    description_pkg = get_package_share_directory('robot_arm_description')

    # ── URDF via xacro ──────────────────────────────────────────────────
    xacro_file = os.path.join(description_pkg, 'urdf', 'robot_arm.urdf.xacro')
    robot_description = ParameterValue(
        Command(['xacro "', xacro_file, '"']),
        value_type=str,
    )

    # ── RViz config ─────────────────────────────────────────────────────
    rviz_config = os.path.join(description_pkg, 'rviz', 'config.rviz')

    # ── Nodes ───────────────────────────────────────────────────────────
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}],
    )

    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
    )

    # ── Launch description ──────────────────────────────────────────────
    return LaunchDescription([
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz_node,
    ])

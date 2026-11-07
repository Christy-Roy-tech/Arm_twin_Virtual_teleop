"""
teleop.launch.py — Full teleoperation / digital-twin mode for the 5-DOF arm.

Combines everything from gazebo.launch.py and adds joint_state_publisher_gui
so the operator can drive each joint via GUI sliders while observing the
robot simultaneously in Gazebo and RViz.

Launches:
  • xacro  → processes the URDF/Xacro model
  • robot_state_publisher → publishes /robot_description and TF frames
  • gazebo (via gazebo_ros) → Gazebo Classic with the custom world
  • spawn_entity.py → spawns the robot model in Gazebo
  • joint_state_publisher_gui → GUI sliders for manual joint control
  • rviz2  → 3-D visualisation
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # ── Package paths ───────────────────────────────────────────────────
    description_pkg = get_package_share_directory('robot_arm_description')
    bringup_pkg = get_package_share_directory('robot_arm_bringup')
    gazebo_ros_pkg = get_package_share_directory('gazebo_ros')

    # ── URDF via xacro ──────────────────────────────────────────────────
    xacro_file = os.path.join(description_pkg, 'urdf', 'robot_arm.urdf.xacro')
    robot_description = ParameterValue(
        Command(['xacro "', xacro_file, '"']),
        value_type=str,
    )

    # ── World file ──────────────────────────────────────────────────────
    world_file = os.path.join(bringup_pkg, 'worlds', 'robot_arm_world.sdf')

    # ── RViz config ─────────────────────────────────────────────────────
    rviz_config = os.path.join(description_pkg, 'rviz', 'config.rviz')

    # ── Teleop config ───────────────────────────────────────────────────
    teleop_config = os.path.join(bringup_pkg, 'config', 'teleop_config.yaml')

    # ── Nodes & includes ────────────────────────────────────────────────
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}],
    )

    # Start Gazebo Classic gzserver with the custom world
    gzserver_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_pkg, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world_file, 'verbose': 'true'}.items(),
    )

    # Start Gazebo Classic gzclient (GUI)
    gzclient_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_pkg, 'launch', 'gzclient.launch.py')
        ),
    )

    # Spawn the robot into Gazebo
    spawn_entity_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_entity',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'robot_arm',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.0',
        ],
    )

    # Joint-state publisher GUI for slider-based teleoperation
    # Remapped to publish to /joint_commands so it doesn't conflict with Gazebo's /joint_states
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
        parameters=[teleop_config],
        remappings=[('joint_states', 'joint_commands')],
    )

    # Bridge node: converts /joint_commands into /set_joint_trajectory for Gazebo
    joint_command_publisher_node = Node(
        package='robot_arm_teleop',
        executable='joint_command_publisher',
        name='joint_command_publisher',
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
        gzserver_launch,
        gzclient_launch,
        spawn_entity_node,
        joint_state_publisher_gui_node,
        joint_command_publisher_node,
        rviz_node,
    ])

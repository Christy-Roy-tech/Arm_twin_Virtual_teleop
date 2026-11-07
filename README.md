# 5-DOF Robotic Arm — Digital Twin & Simulation Guide

A complete, beginner-friendly guide to building, simulating, and teleoperating a **5-DOF Robotic Arm with a Mechanical Gripper** in **ROS 2 Humble** and **Gazebo Classic**, fully integrated with real **SolidWorks CAD STL meshes**.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [The 3 Packages We Created](#2-the-3-packages-we-created)
3. [From CAD to Simulation: What to Do After Exporting Your Arm in STL](#3-from-cad-to-simulation-what-to-do-after-exporting-your-arm-in-stl)
   - [Exporting from SolidWorks / CAD](#31-exporting-from-solidworks--cad)
   - [Handling File Names and Directory Spaces](#32-handling-file-names-and-directory-spaces)
   - [Renaming & Standardizing Meshes](#33-renaming--standardizing-meshes)
   - [Matching CAD Assembly Mates & Pivot Centers](#34-matching-cad-assembly-mates--pivot-centers)
4. [Commands That Worked (Step-by-Step Runbook)](#4-commands-that-worked-step-by-step-runbook)
   - [Installing Prerequisites](#41-installing-prerequisites)
   - [Building the Workspace](#42-building-the-workspace)
   - [Launching RViz Visualization](#43-launching-rviz-visualization)
   - [Launching Gazebo Simulation](#44-launching-gazebo-simulation)
   - [Launching Digital Twin Teleoperation](#45-launching-digital-twin-teleoperation)
5. [How RViz Visualization Works](#5-how-rviz-visualization-works)
6. [How Teleoperation Works](#6-how-teleoperation-works)
   - [GUI Sliders (`joint_state_publisher_gui`)](#61-gui-sliders-joint_state_publisher_gui)
   - [Keyboard Control (`robot_arm_teleop`)](#62-keyboard-control-robot_arm_teleop)
7. [Kinematic Chain & Joint Specifications](#7-kinematic-chain--joint-specifications)
8. [Troubleshooting & Lessons Learned](#8-troubleshooting--lessons-learned)

---

## 1. Project Overview

This project turns a physical 5-DOF robotic arm designed in SolidWorks into an interactive, physics-driven **digital twin**. 

Instead of relying on basic primitive shapes (cylinders and boxes), this workspace displays and simulates the **exact high-detail 3D CAD parts** exported from SolidWorks:
- **Base platform**
- **Waist rotating turntable**
- **Shoulder link (Link 1)**
- **Elbow link (Link 2)**
- **Wrist pitch bracket (Link 3)**
- **Complete 1-DOF mechanical gripper assembly**

The arm can be visualized in **RViz 2**, simulated with physical mass and gravity in **Gazebo Classic**, and commanded interactively using either on-screen sliders or keyboard shortcuts.

---

## 2. The 3 Packages We Created

The workspace follows standard modular ROS 2 architecture, divided into three specialized packages inside `src/`:

```
5_Dof_robotic_arm_simulation/src/
├── robot_arm_description/     # 3D models, kinematics, URDF/xacro, and meshes
├── robot_arm_bringup/         # Launch files, worlds, and RViz configurations
└── robot_arm_teleop/          # Custom python nodes for keyboard and joint control
```

### 1. `robot_arm_description` (The Robot's Body)
- **`urdf/robot_arm.urdf.xacro`**: The core robot blueprint. It defines every link, joint type (revolute, prismatic, fixed), pivot origin coordinates (`xyz`), rotation axes (`axis`), joint limits (angles, velocity, effort), visual STL meshes, and simplified collision geometry.
- **`urdf/robot_arm_gazebo.xacro`**: Adds Gazebo physics properties, friction parameters, colors, and the `gazebo_ros_joint_state_publisher` and trajectory controller plugins.
- **`meshes/`**: Stores the high-detail STL mesh files exported from CAD, with standard ROS names and aliases.

### 2. `robot_arm_bringup` (The Launch Center)
- **`launch/display.launch.py`**: The fastest way to inspect your robot. Launches `robot_state_publisher`, `joint_state_publisher_gui` (sliders), and `rviz2`.
- **`launch/gazebo.launch.py`**: Spawns the arm inside Gazebo Classic with gravity, physics, and a workspace table.
- **`launch/teleop.launch.py`**: Launches the complete digital twin system (Gazebo + RViz + joint control simultaneously).
- **`rviz/robot_arm.rviz`**: Pre-configured RViz display profile with the camera focused on the arm.

### 3. `robot_arm_teleop` (The Control Node)
- **`keyboard_teleop.py`**: A lightweight Python node that listens to your keyboard presses (1-5 to pick joints, `w`/`s` or arrow keys to move, `g` for gripper) and publishes control commands.
- **`joint_command_publisher.py`**: Bridge node that translates user commands into smooth joint trajectories for Gazebo.

---

## 3. From CAD to Simulation: What to Do After Exporting Your Arm in STL

Exporting CAD files to ROS is where 90% of robotics developers run into issues (such as parts appearing 1000× too large, parts pointing backwards, or joints pivoting around the wrong point). Here is the exact procedure to follow:

### 3.1 Exporting from SolidWorks / CAD

When exporting from SolidWorks:
1. **Always export two things:**
   - **Individual Link STLs**: Each moving part (`Base.SLDPRT`, `Waist.SLDPRT`, `Link_1.SLDPRT`, etc.) saved as an individual `.STL` file.
   - **The Full Assembly STL**: Open your complete assembly (`.SLDASM`) with all mates solved, and save the entire assembly as a single `.STL` file (e.g., `5 DOF Robotic Arm with 1 DOF Mechanical Gripper.STL`). **This full assembly serves as the ground-truth reference for exact joint positions.**
2. **Units Matter (Meters vs Millimeters):**
   - SolidWorks defaults to exporting STLs in **millimeters**.
   - ROS 2 and URDF work strictly in **meters** ($1\text{ m} = 1000\text{ mm}$).
   - *Option A:* If exported in mm, set `<mesh filename="..." scale="0.001 0.001 0.001"/>` in the URDF.
   - *Option B (Recommended):* In SolidWorks **File → Save As → STL → Options**, set **Output unit: Meters** and select **Binary**. The scale in your URDF is then simply `scale="1 1 1"`.
3. **Format (Binary vs ASCII):**
   - Binary STLs are ~5x smaller in file size and load significantly faster in RViz.

---

### 3.2 Handling File Names and Directory Spaces

> **CRITICAL ROS 2 BUG TO AVOID:**
> ROS 2's underlying resource retriever (`resource_retriever` / `urdfdom`) has a known issue parsing paths that contain spaces (e.g. `/home/christy/5_Dof_robotic _arm simulation`). It treats the space as an invalid URL character and RViz fails to load meshes with:
> `[rviz2]: Error retrieving file [file:///home/christy/5_Dof_robotic _arm simulation/...]`

**The Fix:** Create a clean symlink to your workspace without spaces:
```bash
ln -s "/home/christy/5_Dof_robotic _arm simulation" /home/christy/robot_arm_ws
```
Always run `colcon build` and source your workspace through this clean symlink:
```bash
cd /home/christy/robot_arm_ws
```

---

### 3.3 Renaming & Standardizing Meshes

SolidWorks files usually have spaces and capital letters (e.g., `Base of Robotic Arm.STL`, `Link_1.STL`). In ROS, clean lowercase naming with underscores is the standard.

Here is the mapping implemented in `src/robot_arm_description/meshes/`:

| Original SolidWorks File | Standard ROS Mesh Name | Alias / Fallback | URDF Link |
|:---|:---|:---|:---|
| `Base of Robotic Arm.STL` | `base_link.stl` | `base.stl` | `base_link` |
| `Waist 1.STL` | `waist_link.stl` | `waist.stl` | `waist_link` |
| `Link_1.STL` | `shoulder_link.stl` | `link1_shoulder.stl` | `shoulder_link` |
| `Link_2.STL` | `elbow_link.stl` | `link2_elbow.stl` | `elbow_link` |
| `Link_3.STL` | `wrist_pitch_link.stl` | `link3_wrist.stl` | `wrist_pitch_link` |
| `Gripper assembly.STL` | `gripper_assembly.stl` | `gripper_base_link.stl` | `gripper_base_link` |

---

### 3.4 Matching CAD Assembly Mates & Pivot Centers

In CAD, each part has its own coordinate system origin (`0, 0, 0`), which is often arbitrary (e.g., corner of a sketch or center of mass). But in ROS URDF:
- A link's visual mesh should ideally have `(0, 0, 0)` right at the **joint pivot point**.
- The joint `origin xyz="..."` specifies where that pivot sits relative to the parent link.

#### How we aligned the arm with sub-millimeter precision:
1. We read the full CAD assembly STL (`5 DOF Robotic Arm with 1 DOF Mechanical Gripper.STL`) into Python using `open3d`.
2. We transformed the CAD coordinate frame into ROS coordinates (SolidWorks uses $Y$-up; ROS uses $Z$-up).
3. We registered each individual part STL to its exact matching submesh in the assembly using ICP (Iterative Closest Point) algorithms.
4. **Fixing the Wrist Pitch (Link 3):**
   - The initial placement of Link 3 was flipped 180° pointing backwards into Link 2.
   - We extracted Link 3's exact orientation matrix from the CAD assembly, achieving a $0.0001\text{ mm}$ mean error match (1.0 fitness score).
   - Re-exported `wrist_pitch_link.stl` with its origin placed directly at the Joint 4 pivot hole.

---

## 4. Commands That Worked (Step-by-Step Runbook)

Open a terminal on your Ubuntu system and run through these commands:

### 4.1 Installing Prerequisites

```bash
# Update system package list
sudo apt update

# Install ROS 2 Humble packages needed for simulation, visualization, and URDF parsing
sudo apt install -y \
  ros-humble-joint-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-robot-state-publisher \
  ros-humble-rviz2 \
  ros-humble-xacro \
  ros-humble-gazebo-ros-pkgs
```

---

### 4.2 Building the Workspace

```bash
# 1. Source ROS 2 system setup
source /opt/ros/humble/setup.bash

# 2. Go to workspace via clean symlink (no spaces in path)
cd /home/christy/robot_arm_ws

# 3. Build all 3 packages with symlink install (fast rebuilds)
colcon build --symlink-install

# 4. Source the workspace overlay
source install/setup.bash
```

> **Verification:** You can verify your URDF syntax anytime with:
> ```bash
> xacro src/robot_arm_description/urdf/robot_arm.urdf.xacro > /tmp/arm.urdf && check_urdf /tmp/arm.urdf
> ```
> Output should show: `Successfully Parsed XML` and a clean tree from `world` down to `gripper_finger_right`.

---

### 4.3 Launching RViz Visualization

To inspect the 3D robot model with the integrated CAD meshes and interactive joint sliders:

```bash
source /opt/ros/humble/setup.bash
source /home/christy/robot_arm_ws/install/setup.bash

ros2 launch robot_arm_bringup display.launch.py
```

**What you will see:**
- An RViz window showing the complete 5-DOF robotic arm on a reference grid.
- A small `joint_state_publisher_gui` dialog with sliders for each joint:
  - `joint1_waist`
  - `joint2_shoulder`
  - `joint3_elbow`
  - `joint4_wrist_pitch`
  - `joint5_wrist_roll`
  - `joint6_gripper_left`

Drag the sliders, and the arm moves smoothly in real-time in the 3D window!

---

### 4.4 Launching Gazebo Simulation

To simulate the arm with realistic physics, inertia, and gravity:

```bash
source /opt/ros/humble/setup.bash
source /home/christy/robot_arm_ws/install/setup.bash

ros2 launch robot_arm_bringup gazebo.launch.py
```

The robot spawns on a work table inside Gazebo Classic with physics enabled.

---

### 4.5 Launching Digital Twin Teleoperation

To run the complete digital twin (simulating in Gazebo while viewing in RViz with slider teleoperation):

```bash
source /opt/ros/humble/setup.bash
source /home/christy/robot_arm_ws/install/setup.bash

ros2 launch robot_arm_bringup teleop.launch.py
```

---

## 5. How RViz Visualization Works

Understanding the data flow makes debugging effortless:

```
┌──────────────────────────────┐
│  robot_arm.urdf.xacro        │ ──(Processed by xacro)──┐
└──────────────────────────────┘                         ▼
                                             ┌───────────────────────┐
                                             │ robot_state_publisher │
                                             └───────────┬───────────┘
                                                         │
  ┌─────────────────────────────┐                        │ /tf & /tf_static
  │ joint_state_publisher_gui   │                        │ (Joint frames)
  │ (User moves slider)         │                        │
  └──────────────┬──────────────┘                        ▼
                 │ /joint_states                   ┌───────────┐
                 └────────────────────────────────►│   RViz2   │◄── Loads STL meshes
                                                   │ (3D View) │
                                                   └───────────┘
```

1. **`robot_state_publisher`**: Reads the URDF file and calculates forward kinematics. It publishes:
   - `/robot_description`: Full URDF XML text.
   - `/tf_static`: Static transforms (e.g. world to base).
   - `/tf`: Dynamic coordinate frames for every moving link.
2. **`joint_state_publisher_gui`**: Broadcasts the current angle of every joint to `/joint_states`.
3. **`rviz2`**: Subscribes to `/tf` and `/robot_description`. It loads each `.stl` file from `robot_arm_description/meshes/` and renders it at the exact 3D coordinates dictated by `/tf`.

---

## 6. How Teleoperation Works

### 6.1 GUI Sliders (`joint_state_publisher_gui`)
- Comes pre-configured with min/max angular limits matching the physical robot servos.
- Automatically calculates symmetrical motion for the parallel gripper fingers using a **mimic joint** (`joint7_gripper_right` automatically mimics `joint6_gripper_left` in opposite direction).

### 6.2 Keyboard Control (`robot_arm_teleop`)
For fine-grained incremental control:

```bash
# Terminal 1: Launch simulation
ros2 launch robot_arm_bringup gazebo.launch.py

# Terminal 2: Run keyboard teleop
ros2 run robot_arm_teleop keyboard_teleop
```

**Keymap:**
| Key | Action |
|:---:|:---|
| `1` – `5` | Select Joint 1 (Waist) through Joint 5 (Wrist Roll) |
| `g` | Select Gripper |
| `w` or `↑` | Increment joint angle |
| `s` or `↓` | Decrement joint angle |
| `+` / `-` | Increase / decrease step size |
| `h` | Home position (return all joints to 0.0) |
| `q` | Quit |

---

## 7. Kinematic Chain & Joint Specifications

The exact CAD-matched kinematic parameters defined in `robot_arm.urdf.xacro`:

| Joint Name | Parent Link | Child Link | Joint Type | Pivot Origin `xyz` (m) | Axis `xyz` | Range |
|:---|:---|:---|:---:|:---:|:---:|:---:|
| `fixed_world` | `world` | `base_link` | fixed | `0 0 0` | — | Stationary |
| `joint1_waist` | `base_link` | `waist_link` | revolute | `0 0 0.0560` | `0 0 1` | ±180° |
| `joint2_shoulder`| `waist_link` | `shoulder_link` | revolute | `-0.0040 -0.0104 0.0499` | `-0.5948 0.6550 -0.4660` | ±90° |
| `joint3_elbow` | `shoulder_link`| `elbow_link` | revolute | `0.0104 0.0089 0.1145` | `-0.2549 0.9635 0.0824` | ±90° |
| `joint4_wrist_pitch`| `elbow_link` | `wrist_pitch_link`| revolute | `-0.07397 -0.07358 -0.00532`| `-0.6698 0.7424 -0.0088` | ±90° |
| `joint5_wrist_roll` | `wrist_pitch_link`| `wrist_roll_link` | revolute | `-0.04414 -0.04642 0.00664`| `-0.0313 -0.0164 0.9994` | ±180° |
| `gripper_base_joint`| `wrist_roll_link` | `gripper_base_link` | fixed | `0 0 0` | — | Fixed mount |
| `joint6_gripper_left`| `gripper_base_link`| `gripper_finger_left` | prismatic| `0 0 0` | `0 1 0` | 0 – 15 mm |
| `joint7_gripper_right`| `gripper_base_link`| `gripper_finger_right`| prismatic| `0 0 0` | `0 -1 0` | 0 – 15 mm (mimic) |

---

## 8. Troubleshooting & Lessons Learned

| Issue / Error | Root Cause | Solution |
|:---|:---|:---|
| `rviz2: Error retrieving file [file:///...]` | Directory path contains a space (`5_Dof_robotic _arm simulation`). | Create and use a symlink without spaces: `ln -s "/path/with space" ~/robot_arm_ws`. |
| Arm appears 1000x too large in RViz | STL exported in millimeters instead of meters. | In SolidWorks STL Options, select **Output units: Meters**, or set `scale="0.001 0.001 0.001"` in the URDF visual geometry. |
| Open3D `Write STL failed: compute normals first` | Open3D triangle meshes require computed normals before exporting binary STL. | Call `mesh.compute_triangle_normals()` and `mesh.compute_vertex_normals()` before `o3d.io.write_triangle_mesh`. |
| Mesh inverted or pointing backwards | CAD part coordinate system rotated relative to the assembly mate. | Extract the transformation from the reference assembly STL using ICP registration to find the exact relative rotation matrix. |
| `Package [robot_arm_...] not found` | Workspace overlay environment not sourced in current shell. | Run `source /opt/ros/humble/setup.bash` followed by `source install/setup.bash`. |

---

*Enjoy simulating your 5-DOF robotic arm digital twin!* 🚀

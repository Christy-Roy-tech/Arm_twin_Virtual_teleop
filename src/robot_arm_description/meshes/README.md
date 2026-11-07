# Mesh Files for 5-DOF Robotic Arm

## Integrated SolidWorks Meshes

The SolidWorks exported STL files from `meshes/stl files/` have been mapped, renamed, and integrated into `robot_arm.urdf.xacro`:

| Original SolidWorks STL | Renamed Mesh in `meshes/` | Robot Link | Scale |
|-------------------------|--------------------------|------------|-------|
| `Base of Robotic Arm.STL` | `base_link.stl` (alias `base.stl`) | `base_link` | `1 1 1` (meters) |
| `Waist 1.STL` | `waist_link.stl` (alias `waist.stl`) | `waist_link` | `1 1 1` (meters) |
| `Link_1.STL` | `shoulder_link.stl` (alias `link1_shoulder.stl`) | `shoulder_link` | `1 1 1` (meters) |
| `Link_2.STL` | `elbow_link.stl` (alias `link2_elbow.stl`) | `elbow_link` | `1 1 1` (meters) |
| `Link_3.STL` | `wrist_pitch_link.stl` (alias `link3_wrist.stl`) | `wrist_pitch_link` | `1 1 1` (meters) |
| `Blue Servo.STL` | `wrist_roll_link.stl` (alias `wrist_roll.stl`) | `wrist_roll_link` | `1 1 1` (meters) |
| `Gripper assembly.STL` | `gripper_assembly.stl` (alias `gripper_base_link.stl`) | `gripper_base_link` | `1 1 1` (meters) |

> **Note:** The original raw STL exports are preserved in `meshes/stl files/`.

### Using Meshes in the URDF

The robot model in `robot_arm.urdf.xacro` is configured with:
```xml
<xacro:property name="use_mesh" value="true"/>
```
This enables full 3D CAD mesh rendering for all links in RViz and Gazebo. To switch back to primitive geometry (for lightweight simulation), set `use_mesh` to `false`.

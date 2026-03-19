# OBS-3 — Obstacle Avoidance in Autonomous Navigation with ROS 2

**Project Group:** OBS-3  
**University:** Frankfurt University of Applied Sciences  
**Department:** Information Technology  
**Module:** Autonomous Intelligent Systems (AIS)  
**Supervisor:** Prof. Dr. Peter Nauth  
**Students:** Md Mushfiqul Islam · Rezoyana Islam Bonna  

---

## Report And Other Documents: 
https://github.com/mushfiq5900/AIS_OBS_Project/tree/main/Documents


## What This Project Does

This project implements and evaluates the **MPPI (Model Predictive Path Integral)** controller
as the primary local planner for robot obstacle avoidance in ROS 2, compared against a
**DWA-equivalent baseline** using the Regulated Pure Pursuit Controller (RPP).

> **Why MPPI instead of TEB?**  
> The project originally targeted the Timed Elastic Band (TEB) planner. However, TEB does not
> provide a stable ROS 2 Jazzy release due to breaking API changes in `libg2o` and `nav2_core`.
> MPPI was adopted as the primary planner — it is natively supported in ROS 2 Jazzy and offers
> conceptually similar trajectory optimisation via stochastic sampling. This incompatibility is
> documented as a finding in the project report.

A TurtleBot3 Burger robot is simulated in **Gazebo Harmonic** across four scenarios:

| Scenario | Description |
|----------|-------------|
| `static` | Five fixed box obstacles between start (0,0) and goal (4.0, 0.0) |
| `narrow` | Two pairs of walls forming sequential corridors with a ~0.6 m gap |
| `dynamic` | Two moving cylinders crossing the robot's path (0.4 m/s and 0.3 m/s) |
| `mixed` | Static boxes + moving cylinders combined |

Performance metrics (path length, time to goal, near-collisions, minimum obstacle distance,
smoothness, replanning count) are collected automatically per run and saved to CSV.

---

## System Requirements

| Item | Requirement |
|------|-------------|
| OS | **Ubuntu 24.04 LTS** (Noble) |
| ROS 2 | **Jazzy Jalisco** |
| Gazebo | **Harmonic** (via `ros-jazzy-ros-gz`) |
| RAM | ≥ 8 GB |
| Disk | ≥ 10 GB free |
| Python | 3.12+ |

---

## PART 1 — Install ROS 2 Jazzy (Ubuntu 24.04)

Open a terminal. Run each block one at a time.

### 1.1 Set locale

```bash
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### 1.2 Add ROS 2 repository

```bash
sudo apt install -y software-properties-common curl
sudo add-apt-repository universe

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu \
  $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

### 1.3 Install ROS 2 Desktop + tools

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ros-jazzy-desktop ros-dev-tools python3-colcon-common-extensions
```

### 1.4 Source ROS 2 in every terminal (add to .bashrc once)

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## PART 2 — Environment Setup

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "export TURTLEBOT3_MODEL=burger" >> ~/.bashrc
echo "export GAZEBO_MODEL_PATH=/usr/share/gazebo-11/models:$GAZEBO_MODEL_PATH" >> ~/.bashrc
source ~/.bashrc
```

Verify everything is set:

```bash
printenv ROS_DISTRO        # jazzy
gz sim --version           # Gazebo Sim, version 8.x.x
echo $TURTLEBOT3_MODEL     # burger
```

---

## PART 3 — Install All Project Dependencies

```bash
# Navigation stack
sudo apt install -y \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup

# TurtleBot3 robot packages
sudo apt install -y \
    ros-jazzy-turtlebot3 \
    ros-jazzy-turtlebot3-simulations

# Gazebo Harmonic + ROS-GZ bridge
sudo apt install -y \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-ros-gz-sim

# Extra Nav2 utilities
sudo apt install -y \
    ros-jazzy-nav2-map-server \
    ros-jazzy-nav2-lifecycle-manager \
    ros-jazzy-tf2-ros

# Python tools
pip3 install transforms3d
```

---

## PART 4 — Set Up the Workspace

### 3.1 Create workspace and copy the package

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# If you downloaded the zip, extract and copy the package:
cp -r /path/to/teb_obstacle_avoidance ~/ros2_ws/src/
```

### 3.2 Verify the package structure

```
~/ros2_ws/
└── src/
    └── teb_obstacle_avoidance/
        ├── CMakeLists.txt
        ├── package.xml
        ├── teb_obstacle_avoidance/
        │   └── __init__.py
        ├── launch/
        │   └── nav_simulation.launch.py
        ├── config/
        │   ├── nav2_params_teb.yaml      ← MPPI controller config
        │   └── nav2_params_dwa.yaml      ← RPP (DWA-equivalent) config
        ├── worlds/
        │   ├── scenario_static.world
        │   ├── scenario_narrow.world
        │   ├── scenario_dynamic.world
        │   └── scenario_mixed.world
        ├── maps/
        │   ├── map.pgm
        │   └── map.yaml
        └── scripts/
            ├── collect_metrics.py
            ├── dynamic_obstacle_spawner.py
            ├── goal_sender.py
            └── run_experiments.sh
```

---

## PART 5 — Build the Workspace

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
```

Expected output (last lines):
```
Summary: 1 packages finished [...]
```

If you see dependency errors, run:
```bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```

---

## PART 6 — Configure Your Shell (do once)

Add these lines to `~/.bashrc` so every new terminal is ready:

```bash
cat >> ~/.bashrc << 'EOF'

# ROS 2 OBS-3 Project
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
EOF

source ~/.bashrc
```

---

## PART 7 — Running a Simulation

Each simulation run requires **two terminals** — one for the launch and one for the
Gazebo Harmonic Twist bridge. This bridge is required because Nav2 publishes
`geometry_msgs/Twist` while Gazebo Harmonic expects `geometry_msgs/TwistStamped`.

---

### Terminal 1 — Launch the simulation

First kill any leftover processes from a previous run, then launch:

```bash
killall ruby gz rviz2 python3 2>/dev/null; sleep 3
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=teb scenario:=static
```

Replace `planner:=teb` with `planner:=dwa` and `scenario:=static` with any of
`narrow`, `dynamic`, or `mixed` as needed.

> Wait ~15 seconds after launching before moving to Terminal 2.

---

### Terminal 2 — Start the Twist bridge (Gazebo Harmonic compatibility)

Open a new terminal and run:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run ros_gz_bridge parameter_bridge \
    /cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist
```

Keep this terminal open for the entire run. The robot will not move without it.

---

### The 8 experiment runs

Repeat the Terminal 1 + Terminal 2 steps for each combination below:

```bash
# --- MPPI (primary planner) ---
# planner:=teb uses the MPPI config (nav2_params_teb.yaml)
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=teb scenario:=static
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=teb scenario:=narrow
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=teb scenario:=dynamic
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=teb scenario:=mixed

# --- DWA/RPP (baseline planner) ---
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=dwa scenario:=static
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=dwa scenario:=narrow
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=dwa scenario:=dynamic
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=dwa scenario:=mixed
```

> **Note:** `planner:=teb` loads `nav2_params_teb.yaml` which configures the **MPPI controller**.
> The filename is kept for historical reasons (TEB was the original intended planner).

---

## PART 8 — Operating RViz (for each run)

After both terminals are running:

### Step A — Set the robot's initial pose

1. In the RViz window, click **"2D Pose Estimate"** (top toolbar)
2. Click on the robot's position in the map view (near the origin)
3. Hold and drag the mouse in the direction the robot faces (positive X = right)
4. Release — the cyan LiDAR scan dots should align with the map

### Step B — Send the navigation goal

**Option 1 — Click in RViz (recommended for demos):**
1. Click **"Nav2 Goal"** in the toolbar
2. Click on the destination (approximately x=4, y=0) and drag to set heading
3. The robot will plan a path and start moving

**Option 2 — Command line (for scripted experiments):**

Open a third terminal (sourced), then:
```bash
ros2 run teb_obstacle_avoidance goal_sender.py \
    --ros-args -p x:=4.0 -p y:=0.0 -p yaw:=0.0
```

### Step C — Watch and record

- Watch the robot navigate in both Gazebo and RViz
- Metrics are logged automatically to CSV when the run ends
- The Nav2 panel in RViz shows live distance to goal and elapsed time

### Step D — Stop and reset

Press **Ctrl+C** in Terminal 1 to stop everything, then kill Terminal 2 as well.
Before the next run always execute the cleanup command first:

```bash
killall ruby gz rviz2 python3 2>/dev/null; sleep 3
```

---

## PART 9 — Metrics and Results

### Where results are saved

```bash
ls ~/obs3_results/
# metrics_teb_static.csv
# metrics_teb_narrow.csv
# metrics_teb_dynamic.csv
# metrics_teb_mixed.csv
# metrics_dwa_static.csv
# metrics_dwa_narrow.csv
# metrics_dwa_dynamic.csv
# metrics_dwa_mixed.csv
```

### View results

```bash
cat ~/obs3_results/metrics_teb_static.csv
```

### CSV columns

| Column | Description |
|--------|-------------|
| `timestamp` | ISO-8601 wall-clock time of run completion |
| `planner` | `teb` (MPPI) or `dwa` (RPP) |
| `scenario` | `static`, `narrow`, `dynamic`, or `mixed` |
| `path_length_m` | Total distance driven (metres) |
| `time_to_goal_s` | Seconds from launch to goal reached |
| `near_collisions` | Laser readings < 0.30 m (proximity events) |
| `collisions` | Laser readings < 0.12 m (contact events) |
| `min_obstacle_dist_m` | Minimum laser range seen during run (metres) |
| `smoothness_rad_s2` | Cumulative angular velocity changes — lower is smoother |
| `replan_count` | Number of path replanning events |
| `success` | `1` = goal reached, `0` = failed / aborted |

---

## PART 10 — Automated Batch Experiments (Optional)

To run all 8 combinations automatically:

```bash
chmod +x ~/ros2_ws/src/teb_obstacle_avoidance/scripts/run_experiments.sh
~/ros2_ws/src/teb_obstacle_avoidance/scripts/run_experiments.sh
```

> This takes approximately 30–40 minutes. Each run waits 20 s for Nav2 to initialise,
> sends the goal, waits up to 120 s for completion, then kills the simulation and moves
> to the next combination. Remember to also start the Twist bridge (Terminal 2) before
> running the batch script.

---

## PART 11 — Troubleshooting

### Problem: Robot does not move at all after setting the goal
The Twist bridge (Terminal 2) is likely not running. Start it:
```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run ros_gz_bridge parameter_bridge \
    /cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist
```

### Problem: Leftover processes from a previous run
```bash
killall ruby gz rviz2 python3 2>/dev/null; sleep 3
```

### Problem: Gazebo opens but robot is invisible
```bash
export TURTLEBOT3_MODEL=burger
# Then relaunch
```

### Problem: "No map received" in RViz
```bash
# Check map_server is running:
ros2 node list | grep map_server

# Check the map topic:
ros2 topic echo /map --once
```

### Problem: Nav2 starts but robot does not move after goal
- Make sure you set the **2D Pose Estimate** first in RViz
- Confirm the Twist bridge terminal is running
- Check the static TF is being published: `ros2 run tf2_ros tf2_echo map odom`

### Problem: `colcon build` fails
```bash
cd ~/ros2_ws
rm -rf build/ install/ log/
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
```

### Problem: Gazebo Harmonic crashes or freezes
```bash
killall ruby gz rviz2 python3 2>/dev/null; sleep 3
# Then relaunch
```

---

## Scenario Reference

| Scenario | Robot start | Navigation goal | Obstacles |
|----------|-------------|-----------------|-----------|
| `static` | x=0, y=0 | x=4.0, y=0.0 | 5 fixed boxes |
| `narrow` | x=0, y=0 | x=4.0, y=0.0 | 2 wall pairs (0.6 m gap) |
| `dynamic` | x=0, y=0 | x=4.0, y=0.0 | 2 moving cylinders |
| `mixed` | x=0, y=0 | x=4.0, y=0.0 | Static boxes + moving cylinders |

---

## Quick Reference Card

```
SOURCE (every terminal):
  source /opt/ros/jazzy/setup.bash
  source ~/ros2_ws/install/setup.bash
  export TURTLEBOT3_MODEL=burger

BUILD:
  cd ~/ros2_ws && colcon build --symlink-install

CLEANUP (before every run):
  killall ruby gz rviz2 python3 2>/dev/null; sleep 3

LAUNCH (Terminal 1):
  ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=teb scenario:=static

TWIST BRIDGE (Terminal 2 — required):
  source /opt/ros/jazzy/setup.bash
  source ~/ros2_ws/install/setup.bash
  ros2 run ros_gz_bridge parameter_bridge \
      /cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist

SEND GOAL (Terminal 3 — optional):
  ros2 run teb_obstacle_avoidance goal_sender.py --ros-args -p x:=4.0 -p y:=0.0

VIEW RESULTS:
  cat ~/obs3_results/metrics_teb_static.csv
```

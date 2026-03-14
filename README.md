# OBS-3 — Obstacle Avoidance in Autonomous Navigation with ROS 2

**Project Group:** OBS-3  
**University:** Frankfurt University of Applied Sciences (Fra-UAS)  
**Department:** Autonomous and Intelligent Systems (AIS)  
**Supervisor:** Prof. Dr. Peter Nauth  
**Students:** Md Mushfiqul Islam · Rezoyana Islam Bonna  
**Period:** 1 December 2025 – 20 March 2026  

---

## What This Project Does

This project implements and evaluates the **TEB (Timed Elastic Band)** local
planner for robot obstacle avoidance in ROS 2, compared against a **DWA
(Dynamic Window Approach)** baseline. A TurtleBot3 Burger robot is simulated
in Gazebo Classic across four scenarios:

| Scenario | Description |
|----------|-------------|
| `static` | Five fixed box obstacles between start and goal |
| `narrow` | Two narrow wall-gated corridors (~0.6 m gap) |
| `dynamic` | Two moving cylinder obstacles crossing the robot's path |
| `mixed` | Static boxes + moving cylinders combined |

Performance metrics (path length, time, collisions, smoothness, replans)
are collected automatically and saved to CSV for analysis.

---

## System Requirements

| Item | Requirement |
|------|------------|
| OS | **Ubuntu 22.04 LTS** (Jammy) — recommended |
| ROS 2 | **Humble Hawksbill** — most stable for TEB + TurtleBot3 |
| Gazebo | Classic 11 (installed with Humble) |
| RAM | ≥ 8 GB |
| Disk | ≥ 10 GB free |
| Python | 3.10+ |

> **Why Ubuntu 22.04 + Humble?**  
> The `teb_local_planner` apt package is most reliably available for
> ROS 2 Humble. If you are on Ubuntu 24.04, use ROS 2 Jazzy and follow
> the Jazzy-specific notes below.

---

## PART 1 — Install ROS 2 Humble (Ubuntu 22.04)

Open a terminal. Run each block one at a time. Do not skip any step.

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
sudo apt install -y ros-humble-desktop ros-dev-tools python3-colcon-common-extensions
```

### 1.4 Source ROS 2 in every terminal (add to .bashrc once)

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## PART 2 — Install All Project Dependencies

Run all of these in one go:

```bash
# Navigation stack
sudo apt install -y \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup

# TEB local planner (the main planner this project evaluates)
sudo apt install -y ros-humble-teb-local-planner

# TurtleBot3 robot + Gazebo simulation packages
sudo apt install -y \
    ros-humble-turtlebot3 \
    ros-humble-turtlebot3-simulations \
    ros-humble-turtlebot3-gazebo

# Gazebo Classic + ROS bridge
sudo apt install -y \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-gazebo-ros

# Extra Nav2 utilities
sudo apt install -y \
    ros-humble-slam-toolbox \
    ros-humble-nav2-map-server \
    ros-humble-nav2-lifecycle-manager

# Python tools
pip3 install transforms3d
```

> **On ROS 2 Jazzy (Ubuntu 24.04)** replace every `humble` above with `jazzy`.

---

## PART 3 — Set Up the Workspace

### 3.1 Create workspace and copy the package

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# If you downloaded the zip, extract it and copy the package:
cp -r /path/to/teb_obstacle_avoidance  ~/ros2_ws/src/

# If you are using Git:
# git clone https://github.com/YOUR_USERNAME/AIS_OBS3_Project.git
# cp -r AIS_OBS3_Project/ros2_ws/src/teb_obstacle_avoidance  ~/ros2_ws/src/
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
        │   ├── nav2_params_teb.yaml
        │   └── nav2_params_dwa.yaml
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

## PART 4 — Build the Workspace

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
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

## PART 5 — Configure Your Shell (do once)

Add these lines to `~/.bashrc` so every new terminal is ready:

```bash
cat >> ~/.bashrc << 'EOF'

# ROS 2 OBS-3 Project
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger
export GAZEBO_MODEL_PATH=/opt/ros/humble/share/turtlebot3_gazebo/models:$GAZEBO_MODEL_PATH
EOF

source ~/.bashrc
```

---

## PART 6 — Running a Simulation

### Launch command

```bash
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py \
    planner:=<teb|dwa> \
    scenario:=<static|narrow|dynamic|mixed>
```

### The 8 experiment runs

```bash
# --- TEB planner ---
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=teb scenario:=static
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=teb scenario:=narrow
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=teb scenario:=dynamic
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=teb scenario:=mixed

# --- DWA baseline ---
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=dwa scenario:=static
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=dwa scenario:=narrow
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=dwa scenario:=dynamic
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=dwa scenario:=mixed
```

---

## PART 7 — Operating RViz (for each run)

After the launch command, **wait ~15 seconds** for all windows to open.

### Step A — Set the robot's initial pose

1. In the RViz window, click **"2D Pose Estimate"** (top toolbar)
2. Click on the robot's position in the map view (near the centre/origin)
3. **Hold and drag** the mouse in the direction the robot faces (positive X = right)
4. Release — the green laser scan dots should align with the map

### Step B — Send the navigation goal

**Option 1 — Click in RViz (recommended for demos):**
1. Click **"Nav2 Goal"** or **"2D Goal Pose"** in the toolbar
2. Click on the destination (approximately x=4, y=0) and drag to set heading
3. The robot will plan a path and start moving

**Option 2 — Command line (for scripted experiments):**

Open a second terminal (already sourced), then:
```bash
ros2 run teb_obstacle_avoidance goal_sender.py \
    --ros-args -p x:=4.0 -p y:=0.0 -p yaw:=0.0
```

### Step C — Watch and record

- Watch the robot navigate in both Gazebo and RViz
- The terminal running the launch will show metrics logging
- When the robot reaches the goal (or fails), a CSV row is written automatically

### Step D — Stop and reset

Press **Ctrl+C** in the launch terminal to stop everything, then start the
next scenario.

---

## PART 8 — Metrics and Results

### Where results are saved

```bash
ls ~/obs3_results/
# metrics_teb_static.csv
# metrics_teb_narrow.csv
# metrics_teb_dynamic.csv
# metrics_teb_mixed.csv
# metrics_dwa_static.csv
# ... etc.
```

### View results

```bash
cat ~/obs3_results/metrics_teb_static.csv
```

### CSV columns

| Column | Description |
|--------|-------------|
| `timestamp` | ISO-8601 wall-clock time |
| `planner` | `teb` or `dwa` |
| `scenario` | `static`, `narrow`, `dynamic`, or `mixed` |
| `path_length_m` | Total distance driven (metres) |
| `time_to_goal_s` | Seconds from launch to goal reached |
| `near_collisions` | Laser readings < 0.30 m (proximity events) |
| `collisions` | Laser readings < 0.12 m (contact events) |
| `min_obstacle_dist_m` | Minimum laser range seen (metres) |
| `smoothness_rad_s2` | Cumulative angular velocity changes (lower = smoother) |
| `replan_count` | Number of path replanning events |
| `success` | `1` = goal reached, `0` = failed/aborted |

---

## PART 9 — Automated Batch Experiments (Optional)

To run all 8 combinations automatically:

```bash
chmod +x ~/ros2_ws/src/teb_obstacle_avoidance/scripts/run_experiments.sh
~/ros2_ws/src/teb_obstacle_avoidance/scripts/run_experiments.sh
```

> This takes approximately 30–40 minutes. Each run waits 20 s for Nav2
> to initialise, sends the goal, waits up to 120 s for completion, then
> kills the simulation and moves to the next combination.

---

## PART 10 — Troubleshooting

### Problem: Gazebo opens but robot is invisible
```bash
# Make sure TurtleBot3 model path is exported:
export TURTLEBOT3_MODEL=burger
export GAZEBO_MODEL_PATH=/opt/ros/humble/share/turtlebot3_gazebo/models
# Then relaunch
```

### Problem: "No map received" in RViz or AMCL not localising
```bash
# Check if map_server is running:
ros2 node list | grep map_server

# Check if the map topic is being published:
ros2 topic echo /map --once
```

### Problem: TEB plugin not found
```bash
sudo apt install -y ros-humble-teb-local-planner
# Then rebuild:
cd ~/ros2_ws && colcon build --symlink-install
```

### Problem: Nav2 starts but robot doesn't move after goal
- Make sure you set the **2D Pose Estimate** first
- Wait for the laser scan (green dots) to appear and align with the map
- Check that AMCL is running: `ros2 node list | grep amcl`

### Problem: "colcon build" fails
```bash
cd ~/ros2_ws
rm -rf build/ install/ log/
source /opt/ros/humble/setup.bash
colcon build --symlink-install
```

### Problem: Leftover Gazebo processes after Ctrl+C
```bash
killall gzserver gzclient
```

---

## PART 11 — Git Setup

### First time (create the repo)

```bash
cd ~/ros2_ws/src/teb_obstacle_avoidance
git init
git add .
git commit -m "Initial commit: OBS-3 TEB vs DWA obstacle avoidance project"

# Push to GitHub/GitLab — create the repo online first, then:
git remote add origin https://github.com/YOUR_USERNAME/AIS_OBS3_Project.git
git push -u origin main
```

### .gitignore (already included in the zip)

The `.gitignore` at the repo root excludes:
```
build/
install/
log/
__pycache__/
*.pyc
obs3_results/
```

---

## Scenario Goals Reference

| Scenario | Robot start | Navigation goal |
|----------|-------------|-----------------|
| `static` | x=0, y=0 | x=4.0, y=0.0 |
| `narrow` | x=0, y=0 | x=4.5, y=0.0 |
| `dynamic`| x=0, y=0 | x=4.0, y=0.0 |
| `mixed`  | x=0, y=0 | x=4.0, y=0.0 |

---

## Quick Reference Card

```
SOURCE (every terminal):
  source /opt/ros/humble/setup.bash
  source ~/ros2_ws/install/setup.bash
  export TURTLEBOT3_MODEL=burger

BUILD:
  cd ~/ros2_ws && colcon build --symlink-install

LAUNCH TEB + STATIC:
  ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=teb scenario:=static

LAUNCH DWA + DYNAMIC:
  ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=dwa scenario:=dynamic

SEND GOAL (in second terminal):
  ros2 run teb_obstacle_avoidance goal_sender.py --ros-args -p x:=4.0 -p y:=0.0

VIEW RESULTS:
  cat ~/obs3_results/metrics_teb_static.csv
```

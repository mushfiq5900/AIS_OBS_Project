# OBS-3 | Obstacle Avoidance with ROS 2 — Setup & Run Guide

**Group:** OBS-3 | **Members:** Md Mushfiqul Islam, Rezoyana Islam Bonna  
**Supervisor:** Prof. Dr. Peter Nauth | **University:** Fra-UAS Frankfurt

---

## Before You Start — Run This First

Open a terminal and run:

```bash
bash check_system.sh
```

This tells you exactly what is installed and what needs to be fixed.

---

## Step 1 — Install Everything (One Command)

```bash
bash install.sh
```

This installs:
- ROS 2 Jazzy (correct version for Ubuntu 24.04)
- Gazebo (simulation)
- Nav2 (navigation stack)
- TurtleBot3 (robot model)
- TEB local planner
- All Python dependencies

**Time:** ~10–20 minutes depending on internet speed.

After it finishes:

```bash
source ~/.bashrc
```

---

## Step 2 — Verify Installation

```bash
bash check_system.sh
```

All items should show `[PASS]`. If any show `[FAIL]`, re-run `install.sh`.

---

## Step 3 — Run a Simulation

### Basic usage:

```bash
bash run_scenario.sh <planner> <scenario>
```

| `planner` | `scenario` | Description |
|---|---|---|
| `teb` | `static` | TEB planner, fixed box obstacles |
| `teb` | `narrow` | TEB planner, narrow passages |
| `teb` | `dynamic` | TEB planner, moving obstacles |
| `teb` | `mixed` | TEB planner, static + dynamic |
| `dwa` | `static` | DWA planner (baseline), fixed obstacles |
| `dwa` | `narrow` | DWA planner, narrow passages |
| `dwa` | `dynamic` | DWA planner, moving obstacles |
| `dwa` | `mixed` | DWA planner, static + dynamic |

### Examples:

```bash
# Run TEB with static obstacles
bash run_scenario.sh teb static

# Run DWA with dynamic obstacles (for comparison)
bash run_scenario.sh dwa dynamic

# Run ALL scenarios for TEB automatically
bash run_scenario.sh teb all
```

### What you will see:

1. **Gazebo window** opens — shows the simulated world with robot and obstacles
2. **RViz2 window** opens — shows the robot's map, planned path (green line), and sensor data
3. Robot starts navigating automatically toward goal (4.0, 0.0)
4. When the robot reaches the goal (or fails), the run ends
5. Results are saved to `results/` folder as a CSV file

---

## Step 4 — Run Full Experiment (All 8 Combinations)

For the project you need 5 trials per planner per scenario = 40 total runs.

```bash
# TEB - all scenarios
bash run_scenario.sh teb all

# DWA - all scenarios
bash run_scenario.sh dwa all
```

Or run individual scenarios and repeat 5 times each manually for your trials.

---

## Step 5 — View Results

```bash
ls results/
cat results/teb_static_*.csv
```

Each CSV has one row per run:

| Column | Meaning |
|---|---|
| `path_length_m` | Total distance robot traveled |
| `time_to_goal_s` | Seconds from start to goal |
| `near_collisions` | Times robot was closer than 0.30 m to obstacle |
| `collisions` | Times robot actually hit something |
| `min_obstacle_dist_m` | Closest the robot got to any obstacle |
| `smoothness_rad_s2` | Sum of angular velocity changes (lower = smoother) |
| `replan_count` | How many times the planner recalculated |
| `success` | 1 = reached goal, 0 = failed |

---

## Troubleshooting

### Gazebo doesn't open / black screen

```bash
# Try software rendering (for VMs without GPU)
export LIBGL_ALWAYS_SOFTWARE=1
bash run_scenario.sh teb static
```

### "Package not found" error

```bash
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
```

### TEB planner package not found

```bash
sudo apt install ros-jazzy-teb-local-planner
```

### Build fails

```bash
cd ros2_ws
colcon build --symlink-install 2>&1 | tail -30
```

Look for the error line and copy it — most issues are missing dependencies solved by:

```bash
rosdep install --from-paths src --ignore-src -r -y
```

### Nav2 doesn't start / timeout

Gazebo needs a few seconds. The launch file already waits 5 seconds. If Nav2 still times out:

```bash
# In one terminal: launch Gazebo only
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# In another terminal: launch Nav2 only
ros2 launch teb_obstacle_avoidance nav_simulation.launch.py planner:=teb scenario:=static
```

---

## Git Repository Setup

```bash
cd ~
git init obs3-project
cd obs3-project
cp -r /path/to/this/folder/* .
git add .
git commit -m "Initial commit: OBS-3 TEB vs DWA obstacle avoidance"
git remote add origin https://github.com/YOUR_USERNAME/obs3-project.git
git push -u origin main
```

Both members should clone:

```bash
git clone https://github.com/YOUR_USERNAME/obs3-project.git
cd obs3-project
bash install.sh
```

---

## Project Structure

```
obs3_project/
├── install.sh                   ← Run once to install everything
├── check_system.sh              ← Run to verify setup
├── run_scenario.sh              ← Run simulations
├── results/                     ← CSV metric outputs (auto-created)
├── docs/
│   └── functional_diagram.md   ← System architecture diagram
├── report/                      ← IEEE report (Word file)
└── ros2_ws/
    └── src/
        └── teb_obstacle_avoidance/
            ├── config/
            │   ├── nav2_params_teb.yaml   ← TEB planner settings
            │   └── nav2_params_dwa.yaml   ← DWA planner settings
            ├── launch/
            │   └── nav_simulation.launch.py
            ├── worlds/
            │   ├── scenario_static.world
            │   ├── scenario_narrow.world
            │   ├── scenario_dynamic.world
            │   └── scenario_mixed.world
            └── scripts/
                ├── collect_metrics.py      ← Records performance to CSV
                ├── dynamic_obstacle_spawner.py  ← Moves obstacles in Gazebo
                └── goal_sender.py          ← Sends navigation goals
```

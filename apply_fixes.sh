#!/usr/bin/env bash
# OBS-3 Fix Script — applies all config fixes, rebuilds and launches
# Usage: bash apply_fixes.sh [teb|dwa] [static|narrow|dynamic|mixed]
set -e

PLANNER="${1:-teb}"
SCENARIO="${2:-static}"
WS="$HOME/AIS_OBS_Project/ros2_ws"
CONFIG="$WS/src/teb_obstacle_avoidance/config"

echo "=============================================="
echo " OBS-3: Applying config fixes"
echo "  Planner  : $PLANNER"
echo "  Scenario : $SCENARIO"
echo "  Workspace: $WS"
echo "=============================================="

# ── 1. Copy fixed config files ─────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/nav2_params_teb.yaml" "$CONFIG/nav2_params_teb.yaml"
cp "$SCRIPT_DIR/nav2_params_dwa.yaml" "$CONFIG/nav2_params_dwa.yaml"
echo "[OK] Config files updated."

# ── 2. Source ROS 2 Jazzy ──────────────────────────────────────────────────
source /opt/ros/jazzy/setup.bash

# ── 3. Rebuild only the custom package (fast, no need to rebuild teb/costmap)
cd "$WS"
colcon build --packages-select teb_obstacle_avoidance --symlink-install
echo "[OK] Workspace rebuilt."

# ── 4. Source the workspace ────────────────────────────────────────────────
source "$WS/install/setup.bash"
echo "[OK] Workspace sourced."

# ── 5. Launch ──────────────────────────────────────────────────────────────
echo ""
echo "Starting simulation: planner=$PLANNER  scenario=$SCENARIO"
echo "Gazebo + Nav2 + RViz will open. Press Ctrl-C to stop."
echo ""
export TURTLEBOT3_MODEL=burger

ros2 launch teb_obstacle_avoidance nav_simulation.launch.py \
    planner:="$PLANNER" \
    scenario:="$SCENARIO" \
    use_sim_time:=true

#!/bin/bash
# =============================================================================
# OBS-3 — Scenario Runner
# Usage:  bash run_scenario.sh <planner> <scenario>
#
#   planner:   teb | dwa
#   scenario:  static | narrow | dynamic | mixed
#
# Examples:
#   bash run_scenario.sh teb static
#   bash run_scenario.sh dwa dynamic
#   bash run_scenario.sh teb all     ← runs all 4 scenarios sequentially
# =============================================================================

CYAN='\033[0;36m'; GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

PLANNER="${1:-teb}"
SCENARIO="${2:-static}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Validate args
if [[ ! "$PLANNER" =~ ^(teb|dwa)$ ]]; then
  echo -e "${RED}Error: planner must be 'teb' or 'dwa'. Got: $PLANNER${NC}"; exit 1
fi
if [[ ! "$SCENARIO" =~ ^(static|narrow|dynamic|mixed|all)$ ]]; then
  echo -e "${RED}Error: scenario must be static|narrow|dynamic|mixed|all. Got: $SCENARIO${NC}"; exit 1
fi

# Source ROS 2 and workspace
source /opt/ros/jazzy/setup.bash
source "$SCRIPT_DIR/ros2_ws/install/setup.bash"
export TURTLEBOT3_MODEL=burger
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/opt/ros/jazzy/share/turtlebot3_gazebo/models

# Software rendering fallback (for VMs without GPU)
if ! glxinfo 2>/dev/null | grep -q "OpenGL renderer"; then
  echo -e "${YELLOW}No GPU detected — enabling software rendering (LIBGL_ALWAYS_SOFTWARE=1)${NC}"
  export LIBGL_ALWAYS_SOFTWARE=1
fi

run_one() {
  local planner="$1"; local scenario="$2"
  echo -e "\n${CYAN}============================================${NC}"
  echo -e "${CYAN}  Launching: planner=${planner}  scenario=${scenario}${NC}"
  echo -e "${CYAN}============================================${NC}"
  echo -e "${YELLOW}This opens multiple windows. Close them all when done with this run.${NC}\n"

  # Make results directory
  mkdir -p "$SCRIPT_DIR/results"

  # Launch simulation in background
  ros2 launch teb_obstacle_avoidance nav_simulation.launch.py \
    planner:="$planner" \
    scenario:="$scenario" \
    &
  SIM_PID=$!

  echo -e "${GREEN}Simulation started (PID $SIM_PID)${NC}"
  echo -e "Waiting 8 seconds for Gazebo + Nav2 to initialize..."
  sleep 8

  # Start metric collection
  echo -e "${CYAN}Starting metric collection...${NC}"
  RUN_ID="${planner}_${scenario}_$(date +%Y%m%d_%H%M%S)"
  python3 "$SCRIPT_DIR/ros2_ws/src/teb_obstacle_avoidance/scripts/collect_metrics.py" \
    --ros-args \
    -p output_file:="$SCRIPT_DIR/results/${RUN_ID}.csv" \
    -p planner:="$planner" \
    -p scenario:="$scenario" \
    &
  METRICS_PID=$!

  # Send navigation goal
  echo -e "${CYAN}Sending navigation goal...${NC}"
  sleep 2
  python3 "$SCRIPT_DIR/ros2_ws/src/teb_obstacle_avoidance/scripts/goal_sender.py" \
    --ros-args -p x:=4.0 -p y:=0.0

  echo -e "${GREEN}Goal reached or timed out. Stopping...${NC}"
  kill $METRICS_PID 2>/dev/null || true
  kill $SIM_PID 2>/dev/null || true
  pkill -f "ros2 launch" 2>/dev/null || true
  pkill -f "gz sim" 2>/dev/null || true
  pkill -f "gazebo" 2>/dev/null || true
  sleep 2
  echo -e "${GREEN}Results saved to: results/${RUN_ID}.csv${NC}"
}

if [ "$SCENARIO" = "all" ]; then
  for sc in static narrow dynamic mixed; do
    run_one "$PLANNER" "$sc"
    echo "Waiting 5 seconds before next scenario..."
    sleep 5
  done
  echo -e "\n${GREEN}All scenarios complete! Check results/ folder.${NC}"
else
  run_one "$PLANNER" "$SCENARIO"
fi

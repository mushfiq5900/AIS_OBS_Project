#!/usr/bin/env bash
# =============================================================================
# OBS-3: Automated experiment runner
# Runs all 8 combinations: 4 scenarios × 2 planners
# Each run: launch simulation → wait for ready → send goal → wait → kill
#
# Usage:
#   chmod +x run_experiments.sh
#   ./run_experiments.sh
#
# Results are saved to ~/obs3_results/metrics_<planner>_<scenario>.csv
# =============================================================================

set -e

RESULTS_DIR="$HOME/obs3_results"
mkdir -p "$RESULTS_DIR"

PLANNERS=("teb" "dwa")
SCENARIOS=("static" "narrow" "dynamic" "mixed")

# Goal position for all scenarios (robot starts at 0,0)
GOAL_X=4.0
GOAL_Y=0.0

echo "========================================"
echo " OBS-3 Experiment Runner"
echo " Results → $RESULTS_DIR"
echo "========================================"

for PLANNER in "${PLANNERS[@]}"; do
  for SCENARIO in "${SCENARIOS[@]}"; do

    echo ""
    echo "----------------------------------------"
    echo " Planner: $PLANNER  |  Scenario: $SCENARIO"
    echo "----------------------------------------"

    # Launch simulation in background
    ros2 launch teb_obstacle_avoidance nav_simulation.launch.py \
        planner:=$PLANNER scenario:=$SCENARIO &
    LAUNCH_PID=$!

    # Wait for Nav2 to come up (adjust if your machine is slower)
    echo "Waiting 20 s for Nav2 to initialise..."
    sleep 20

    # Set initial pose (robot starts at origin facing +X)
    ros2 topic pub --once /initialpose \
        geometry_msgs/msg/PoseWithCovarianceStamped \
        '{header: {frame_id: "map"},
          pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0},
                        orientation: {w: 1.0}},
                 covariance: [0.25,0,0,0,0,0,
                              0,0.25,0,0,0,0,
                              0,0,0,0,0,0,
                              0,0,0,0,0,0,
                              0,0,0,0,0,0,
                              0,0,0,0,0,0.068]}}}' \
        2>/dev/null || true

    sleep 3

    # Send navigation goal
    echo "Sending goal x=$GOAL_X y=$GOAL_Y ..."
    ros2 run teb_obstacle_avoidance goal_sender.py \
        --ros-args -p x:=$GOAL_X -p y:=$GOAL_Y -p yaw:=0.0 &
    GOAL_PID=$!

    # Wait up to 120 s for goal to complete
    TIMEOUT=120
    WAITED=0
    while kill -0 $GOAL_PID 2>/dev/null; do
        sleep 2
        WAITED=$((WAITED + 2))
        if [ $WAITED -ge $TIMEOUT ]; then
            echo "Timeout reached — killing run"
            kill $GOAL_PID 2>/dev/null || true
            break
        fi
    done

    # Shut down the launch
    echo "Stopping simulation..."
    kill $LAUNCH_PID 2>/dev/null || true
    sleep 5   # allow Gazebo to fully exit

    echo "Run complete. CSV updated at $RESULTS_DIR/"

  done
done

echo ""
echo "========================================"
echo " All experiments complete!"
echo " Check results:"
echo "   ls $RESULTS_DIR/"
echo "   cat $RESULTS_DIR/metrics_teb_static.csv"
echo "========================================"

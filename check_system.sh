#!/bin/bash
# =============================================================================
# OBS-3 — System Diagnostic Script
# Run this FIRST to check your machine is ready:  bash check_system.sh
# =============================================================================

CYAN='\033[0;36m'; GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
PASS=0; FAIL=0; WARN=0

check() {
  local label="$1"; local cmd="$2"; local required="$3"
  if eval "$cmd" &>/dev/null; then
    echo -e "  ${GREEN}[PASS]${NC} $label"
    ((PASS++))
  elif [ "$required" = "required" ]; then
    echo -e "  ${RED}[FAIL]${NC} $label  ← REQUIRED"
    ((FAIL++))
  else
    echo -e "  ${YELLOW}[WARN]${NC} $label  ← optional"
    ((WARN++))
  fi
}

echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}  OBS-3 System Diagnostic            ${NC}"
echo -e "${CYAN}======================================${NC}"

echo -e "\n${CYAN}── OS ─────────────────────────────────${NC}"
echo "  $(lsb_release -d | cut -f2)"
echo "  Kernel: $(uname -r)"

echo -e "\n${CYAN}── ROS 2 ──────────────────────────────${NC}"
check "ROS 2 installed"      "which ros2"                          required
check "ROS 2 Jazzy"         "ros2 --version 2>&1 | grep -i jazzy" required
check "source setup.bash"   "test -f /opt/ros/jazzy/setup.bash"   required
check "Nav2 installed"      "ros2 pkg list 2>/dev/null | grep -q navigation2" required
check "TurtleBot3 installed""ros2 pkg list 2>/dev/null | grep -q turtlebot3_gazebo" required
check "TEB planner"         "ros2 pkg list 2>/dev/null | grep -q teb_local_planner" required
check "colcon"              "which colcon"                         required

echo -e "\n${CYAN}── Simulation ─────────────────────────${NC}"
check "Gazebo (gz)"         "which gz"                            optional
check "Gazebo (classic)"    "which gazebo"                        optional
check "ros-gz bridge"       "ros2 pkg list 2>/dev/null | grep -q ros_gz_bridge" optional

echo -e "\n${CYAN}── Display / GPU ──────────────────────${NC}"
check "DISPLAY set"         "test -n \"\$DISPLAY\""               optional
check "WAYLAND set"         "test -n \"\$WAYLAND_DISPLAY\""       optional
check "OpenGL (glxinfo)"    "glxinfo 2>/dev/null | grep -q 'OpenGL renderer'" optional
if glxinfo 2>/dev/null | grep -q "OpenGL renderer"; then
  echo "    Renderer: $(glxinfo 2>/dev/null | grep 'OpenGL renderer' | cut -d: -f2 | xargs)"
fi

echo -e "\n${CYAN}── Python ─────────────────────────────${NC}"
check "Python 3"            "python3 --version"                   required
check "rclpy"               "python3 -c 'import rclpy'"           required

echo -e "\n${CYAN}── Workspace ──────────────────────────${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
check "Workspace built"     "test -d $SCRIPT_DIR/ros2_ws/install" required
check "Package visible"     "ros2 pkg list 2>/dev/null | grep -q teb_obstacle_avoidance" required

echo ""
echo -e "${CYAN}======================================${NC}"
echo -e "  Results: ${GREEN}${PASS} passed${NC}  ${YELLOW}${WARN} warnings${NC}  ${RED}${FAIL} failed${NC}"
echo -e "${CYAN}======================================${NC}"

if [ $FAIL -gt 0 ]; then
  echo -e "\n${RED}Some required checks failed. Run:  bash install.sh${NC}"
elif [ $WARN -gt 0 ]; then
  if check "DISPLAY set" "test -n \"\$DISPLAY\"" optional 2>/dev/null; then
    echo -e "\n${GREEN}Ready! Run: bash run_scenario.sh teb static${NC}"
  else
    echo -e "\n${YELLOW}No display detected. Gazebo will use software rendering.${NC}"
    echo -e "${YELLOW}Run: export LIBGL_ALWAYS_SOFTWARE=1 && bash run_scenario.sh teb static${NC}"
  fi
else
  echo -e "\n${GREEN}All checks passed! Run: bash run_scenario.sh teb static${NC}"
fi

#!/bin/bash
# =============================================================================
# OBS-3 Project — Full Install Script
# Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic + Nav2 + TurtleBot3
# Run this ONCE on your machine:  bash install.sh
# =============================================================================

set -e  # Stop on any error
CYAN='\033[0;36m'; GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  OBS-3 Install Script — ROS 2 Jazzy   ${NC}"
echo -e "${CYAN}========================================${NC}"

# ── 1. System check ───────────────────────────────────────────────────────────
echo -e "\n${CYAN}[1/8] Checking Ubuntu version...${NC}"
VER=$(lsb_release -rs)
if [[ "$VER" != "24.04" ]]; then
  echo -e "${RED}ERROR: This script requires Ubuntu 24.04. Detected: $VER${NC}"
  exit 1
fi
echo -e "${GREEN}  Ubuntu 24.04 confirmed.${NC}"

# ── 2. Locale ─────────────────────────────────────────────────────────────────
echo -e "\n${CYAN}[2/8] Setting locale...${NC}"
sudo apt update -qq
sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# ── 3. ROS 2 Jazzy ────────────────────────────────────────────────────────────
echo -e "\n${CYAN}[3/8] Adding ROS 2 Jazzy repository...${NC}"
sudo apt install -y software-properties-common curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update -qq
echo -e "\n${CYAN}[3/8] Installing ROS 2 Jazzy Desktop...${NC}"
sudo apt install -y ros-jazzy-desktop

# ── 4. Nav2 + TurtleBot3 ──────────────────────────────────────────────────────
echo -e "\n${CYAN}[4/8] Installing Nav2, TurtleBot3, TEB...${NC}"
sudo apt install -y \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-turtlebot3 \
  ros-jazzy-turtlebot3-simulations \
  ros-jazzy-teb-local-planner \
  ros-jazzy-slam-toolbox \
  ros-jazzy-gazebo-ros-pkgs \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-pip

# ── 5. Gazebo Harmonic ────────────────────────────────────────────────────────
echo -e "\n${CYAN}[5/8] Installing Gazebo Harmonic...${NC}"
sudo apt install -y gz-harmonic ros-jazzy-ros-gz-bridge ros-jazzy-ros-gz-sim \
  || echo "Trying alternate Gazebo install..."
  
# Fallback: classic Gazebo
if ! which gz &>/dev/null && ! which gazebo &>/dev/null; then
  sudo apt install -y gazebo ros-jazzy-gazebo-ros-pkgs
fi

# ── 6. Environment setup ──────────────────────────────────────────────────────
echo -e "\n${CYAN}[6/8] Configuring environment...${NC}"

# Add to .bashrc only if not already there
add_to_bashrc() {
  grep -qxF "$1" ~/.bashrc || echo "$1" >> ~/.bashrc
}

add_to_bashrc "source /opt/ros/jazzy/setup.bash"
add_to_bashrc "export TURTLEBOT3_MODEL=burger"
add_to_bashrc "export GAZEBO_MODEL_PATH=\$GAZEBO_MODEL_PATH:/opt/ros/jazzy/share/turtlebot3_gazebo/models"

source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=burger

# ── 7. Build workspace ────────────────────────────────────────────────────────
echo -e "\n${CYAN}[7/8] Building ROS 2 workspace...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/ros2_ws"

sudo rosdep init 2>/dev/null || true
rosdep update
rosdep install --from-paths src --ignore-src -r -y

colcon build --symlink-install
source install/setup.bash
add_to_bashrc "source $SCRIPT_DIR/ros2_ws/install/setup.bash"

# ── 8. Display check ──────────────────────────────────────────────────────────
echo -e "\n${CYAN}[8/8] Checking display / GPU support...${NC}"
if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
  echo -e "${GREEN}  Display found: ${DISPLAY}${WAYLAND_DISPLAY}${NC}"
  glxinfo 2>/dev/null | grep "OpenGL renderer" || echo "  (glxinfo not installed, install with: sudo apt install mesa-utils)"
else
  echo -e "${RED}  WARNING: No display detected. Gazebo will run in headless mode.${NC}"
  echo -e "  Add LIBGL_ALWAYS_SOFTWARE=1 before launch commands if needed."
fi

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}  Installation complete!${NC}"
echo -e "${GREEN}  Run: source ~/.bashrc${NC}"
echo -e "${GREEN}  Then: bash run_scenario.sh teb static${NC}"
echo -e "${GREEN}============================================${NC}"

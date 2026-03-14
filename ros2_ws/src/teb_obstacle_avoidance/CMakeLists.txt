cmake_minimum_required(VERSION 3.8)
project(teb_obstacle_avoidance)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)

# Install Python package
ament_python_install_package(${PROJECT_NAME})

# Install executable scripts
install(
  PROGRAMS
    scripts/collect_metrics.py
    scripts/dynamic_obstacle_spawner.py
    scripts/goal_sender.py
    scripts/run_experiments.sh
  DESTINATION lib/${PROJECT_NAME}
)

# Install resource directories
install(
  DIRECTORY launch config worlds maps
  DESTINATION share/${PROJECT_NAME}
)

ament_package()

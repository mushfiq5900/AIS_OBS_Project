cmake_minimum_required(VERSION 3.8)
project(obs3_navigation)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  config launch worlds maps
  DESTINATION share/${PROJECT_NAME}
)

ament_package()

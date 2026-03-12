import os
from ament_python_cmake import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('obs3_navigation')
    nav2_bringup = get_package_share_directory('nav2_bringup')

    params_file = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    map_file    = os.path.join(pkg_share, 'maps', 'obs3_map.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': map_file,
            'use_sim_time': use_sim_time,
            'params_file': params_file,
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        nav2_launch,
    ])

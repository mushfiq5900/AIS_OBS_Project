#!/usr/bin/env python3
"""
OBS-3 — nav_simulation.launch.py
Launches each Nav2 node individually to avoid Jazzy compatibility issues
with route_server and docking_server.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
    SetEnvironmentVariable,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    pkg          = get_package_share_directory('teb_obstacle_avoidance')
    tb3_gz_dir   = get_package_share_directory('turtlebot3_gazebo')

    planner      = LaunchConfiguration('planner').perform(context)
    scenario     = LaunchConfiguration('scenario').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)

    world_files = {
        'static':  os.path.join(pkg, 'worlds', 'scenario_static.world'),
        'narrow':  os.path.join(pkg, 'worlds', 'scenario_narrow.world'),
        'dynamic': os.path.join(pkg, 'worlds', 'scenario_dynamic.world'),
        'mixed':   os.path.join(pkg, 'worlds', 'scenario_mixed.world'),
    }
    world_file  = world_files.get(scenario, world_files['static'])
    map_file    = os.path.join(pkg, 'maps', 'map.yaml')
    params_file = os.path.join(pkg, 'config', f'nav2_params_{planner}.yaml')

    results_dir = os.path.join(os.path.expanduser('~'), 'obs3_results')
    os.makedirs(results_dir, exist_ok=True)

    # Common parameters
    nav2_params = [params_file, {'use_sim_time': True}]

    # ------------------------------------------------------------------ #
    # 1. Gazebo + Robot
    # ------------------------------------------------------------------ #
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb3_gz_dir, 'launch', 'turtlebot3_world.launch.py')
        ),
        launch_arguments={'world': world_file}.items(),
    )

    robot_state_pub = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb3_gz_dir, 'launch', 'robot_state_publisher.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )

    # ------------------------------------------------------------------ #
    # 2. Map server
    # ------------------------------------------------------------------ #
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{'use_sim_time': True, 'yaml_filename': map_file}],
    )

    # ------------------------------------------------------------------ #
    # 3. Static TF: map -> odom (robot starts at origin, no AMCL needed)
    # ------------------------------------------------------------------ #
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_map_odom_tf',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    # ------------------------------------------------------------------ #
    # 4. Nav2 nodes (only the ones needed — skip route_server/docking)
    # ------------------------------------------------------------------ #
    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        output='screen',
        parameters=nav2_params,
        remappings=[('cmd_vel', 'cmd_vel_nav')],
    )

    smoother_server = Node(
        package='nav2_smoother',
        executable='smoother_server',
        output='screen',
        parameters=nav2_params,
    )

    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=nav2_params,
    )

    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        output='screen',
        parameters=nav2_params,
    )

    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=nav2_params,
    )

    waypoint_follower = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        output='screen',
        parameters=nav2_params,
    )

    velocity_smoother = Node(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        output='screen',
        parameters=nav2_params,
        remappings=[
            ('cmd_vel', 'cmd_vel_nav'),
            ('cmd_vel_smoothed', 'cmd_vel'),
        ],
    )

    # ------------------------------------------------------------------ #
    # 5. Lifecycle manager — only manages the nodes we actually launch
    # ------------------------------------------------------------------ #
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names': [
                'map_server',
                'controller_server',
                'smoother_server',
                'planner_server',
                'behavior_server',
                'bt_navigator',
                'waypoint_follower',
                'velocity_smoother',
            ],
        }],
    )

    # ------------------------------------------------------------------ #
    # 6. RViz2
    # ------------------------------------------------------------------ #
    nav2_dir    = get_package_share_directory('nav2_bringup')
    rviz_config = os.path.join(nav2_dir, 'rviz', 'nav2_default_view.rviz')
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    # ------------------------------------------------------------------ #
    # 7. Dynamic obstacle spawner
    # ------------------------------------------------------------------ #
    dynamic_spawner = Node(
        package='teb_obstacle_avoidance',
        executable='dynamic_obstacle_spawner.py',
        name='dynamic_obstacle_spawner',
        output='screen',
        condition=IfCondition(
            PythonExpression(["'", scenario, "' in ['dynamic', 'mixed']"])
        ),
    )

    # ------------------------------------------------------------------ #
    # 8. Metrics collector
    # ------------------------------------------------------------------ #
    metrics_node = Node(
        package='teb_obstacle_avoidance',
        executable='collect_metrics.py',
        name='metrics_collector',
        output='screen',
        parameters=[{
            'planner':   planner,
            'scenario':  scenario,
            'output_file': os.path.join(
                results_dir, f'metrics_{planner}_{scenario}.csv'),
            'proximity_threshold': 0.30,
        }],
    )

    # ------------------------------------------------------------------ #
    # Staggered startup
    # ------------------------------------------------------------------ #
    return [
        gazebo,
        robot_state_pub,
        TimerAction(period=3.0, actions=[static_tf]),
        TimerAction(period=3.0, actions=[map_server]),
        TimerAction(period=4.0, actions=[controller_server]),
        TimerAction(period=4.0, actions=[smoother_server]),
        TimerAction(period=4.0, actions=[planner_server]),
        TimerAction(period=4.0, actions=[behavior_server]),
        TimerAction(period=4.0, actions=[bt_navigator]),
        TimerAction(period=4.0, actions=[waypoint_follower]),
        TimerAction(period=4.0, actions=[velocity_smoother]),
        TimerAction(period=5.0, actions=[lifecycle_manager]),
        TimerAction(period=10.0, actions=[rviz]),
        TimerAction(period=12.0, actions=[dynamic_spawner]),
        TimerAction(period=13.0, actions=[metrics_node]),
    ]


def generate_launch_description():
    return LaunchDescription([
        SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger'),
        SetEnvironmentVariable(
            'GAZEBO_MODEL_PATH',
            '/opt/ros/jazzy/share/turtlebot3_gazebo/models',
        ),
        DeclareLaunchArgument('planner',      default_value='teb'),
        DeclareLaunchArgument('scenario',     default_value='static'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        OpaqueFunction(function=launch_setup),
    ])

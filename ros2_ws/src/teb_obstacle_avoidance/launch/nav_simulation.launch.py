import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                             TimerAction, SetEnvironmentVariable, OpaqueFunction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def launch_setup(context, *args, **kwargs):
    pkg       = get_package_share_directory('teb_obstacle_avoidance')
    nav2_dir  = get_package_share_directory('nav2_bringup')
    tb3_gz    = get_package_share_directory('turtlebot3_gazebo')
    planner      = LaunchConfiguration('planner').perform(context)
    scenario     = LaunchConfiguration('scenario').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)
    world_map = {
        'static':  os.path.join(pkg, 'worlds', 'scenario_static.world'),
        'narrow':  os.path.join(pkg, 'worlds', 'scenario_narrow.world'),
        'dynamic': os.path.join(pkg, 'worlds', 'scenario_dynamic.world'),
        'mixed':   os.path.join(pkg, 'worlds', 'scenario_mixed.world'),
    }
    world_file = world_map.get(scenario, world_map['static'])
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb3_gz, 'launch', 'turtlebot3_world.launch.py')
        ),
        launch_arguments={'world': world_file}.items()
    )
    robot_state_pub = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb3_gz, 'launch', 'robot_state_publisher.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )
    nav2_teb = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file':  os.path.join(pkg, 'config', 'nav2_params_teb.yaml'),
        }.items(),
        condition=IfCondition(PythonExpression(["'", planner, "' == 'teb'"]))
    )
    nav2_dwa = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file':  os.path.join(pkg, 'config', 'nav2_params_dwa.yaml'),
        }.items(),
        condition=IfCondition(PythonExpression(["'", planner, "' == 'dwa'"]))
    )
    rviz_config = os.path.join(nav2_dir, 'rviz', 'nav2_default_view.rviz')
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )
    dynamic_spawner = Node(
        package='teb_obstacle_avoidance',
        executable='dynamic_obstacle_spawner.py',
        name='dynamic_obstacle_spawner',
        output='screen',
        condition=IfCondition(
            PythonExpression(["'", scenario, "' in ['dynamic', 'mixed']"])
        )
    )
    return [
        gazebo,
        robot_state_pub,
        TimerAction(period=5.0,  actions=[nav2_teb]),
        TimerAction(period=5.0,  actions=[nav2_dwa]),
        TimerAction(period=6.0,  actions=[rviz]),
        TimerAction(period=8.0,  actions=[dynamic_spawner]),
    ]

def generate_launch_description():
    return LaunchDescription([
        SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger'),
        SetEnvironmentVariable('GAZEBO_MODEL_PATH',
            '/opt/ros/jazzy/share/turtlebot3_gazebo/models'),
        DeclareLaunchArgument('planner',      default_value='teb',
                              description='Local planner: teb or dwa'),
        DeclareLaunchArgument('scenario',     default_value='static',
                              description='Scenario: static | narrow | dynamic | mixed'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        OpaqueFunction(function=launch_setup),
    ])

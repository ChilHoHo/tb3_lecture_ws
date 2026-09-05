#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cartographer SLAM mapping with automatic patrol.

Run after `sim.launch.py` is up (robot topics exist). Starts:
  - Cartographer (cartographer_node + occupancy grid) from turtlebot3_cartographer,
  - RViz (Cartographer config) to watch the map build,
  - the patrol node to drive the robot around the hall automatically.

When the patrol node finishes (after `duration` seconds, default 180) the map
should cover the room. Save it with scripts/03_save_map.sh.

Usage:
  ros2 launch tb3_lecture mapping.launch.py
  ros2 launch tb3_lecture mapping.launch.py duration:=120 patrol:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

os.environ.setdefault('TURTLEBOT3_MODEL', 'waffle_pi')


def generate_launch_description():
    carto = get_package_share_directory('turtlebot3_cartographer')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    patrol = LaunchConfiguration('patrol', default='true')
    duration = LaunchConfiguration('duration', default='180.0')

    cartographer = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(carto, 'launch', 'cartographer.launch.py')),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'use_rviz': use_rviz,
        }.items(),
    )

    patrol_node = Node(
        package='tb3_lecture',
        executable='patrol_node',
        name='patrol_node',
        output='screen',
        parameters=[{'duration': duration}],
        condition=IfCondition(patrol),
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('patrol', default_value='true'),
        DeclareLaunchArgument('duration', default_value='180.0'),
        cartographer,
        patrol_node,
    ])

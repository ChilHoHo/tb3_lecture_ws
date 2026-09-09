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
    pkg_dir = get_package_share_directory('tb3_lecture')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    patrol = LaunchConfiguration('patrol', default='true')
    duration = LaunchConfiguration('duration', default='180.0')
    # 使用本包定制的小厅 SLAM 配置（config/cartographer_lecture.lua）
    config_dir = os.path.join(pkg_dir, 'config')
    config_basename = 'cartographer_lecture.lua'

    cartographer = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(carto, 'launch', 'cartographer.launch.py')),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'use_rviz': use_rviz,
            'cartographer_config_dir': config_dir,
            'configuration_basename': config_basename,
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

    # IMU 帧别名：gz 仿真把 IMU 传感器帧发成模型前缀的怪异名字
    #   (waffle_pi/imu_link/tb3_imu)，而 Cartographer 用 tracking_frame=imu_link。
    #   加一个恒等静态变换，让 Cartographer 能查到该源帧、把 IMU 航向真正融合进来。
    imu_frame_alias = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0',
                   'imu_link', 'waffle_pi/imu_link/tb3_imu'],
        name='imu_frame_alias',
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('patrol', default_value='true'),
        DeclareLaunchArgument('duration', default_value='180.0'),
        imu_frame_alias,
        cartographer,
        patrol_node,
    ])

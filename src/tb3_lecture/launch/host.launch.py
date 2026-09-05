#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Host/upper-computer view: RViz overview + lecture_control.

Run on top of sim + Cartographer + live Nav2. Shows the real-time map, robot,
podium goal marker and live status; accepts go/stop/replan/return commands.

Usage:
  ros2 launch tb3_lecture host.launch.py
  ros2 topic pub --once /lecture/cmd std_msgs/msg/String data: go
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

os.environ.setdefault('TURTLEBOT3_MODEL', 'waffle_pi')


def generate_launch_description():
    pkg = get_package_share_directory('tb3_lecture')
    rviz = os.path.join(pkg, 'rviz', 'tb3_lecture.rviz')
    return LaunchDescription([
        Node(package='rviz2', executable='rviz2', name='rviz2', output='screen',
             arguments=['-d', rviz], parameters=[{'use_sim_time': True}]),
        Node(package='tb3_lecture', executable='lecture_control',
             name='lecture_control', output='screen'),
    ])

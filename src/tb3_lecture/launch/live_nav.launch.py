#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal live Nav2 bring-up for SLAM-based navigation (no static map).

Only the nodes really needed for `navigate_to_pose` are started, which avoids
the extra (docking_server / route_server / waypoint / …) nodes of the stock
bringup that caused flaky lifecycle bring-up under load:

    controller_server  (DWB local planner, publishes /cmd_vel directly)
    planner_server     (Navfn global planner; global costmap subscribes the
                        live Cartographer /map via its static layer)
    behavior_server    (spin/backup/drive_on_heading recovery actions that the
                        navigate_to_pose BT expects)
    bt_navigator       (NavigateToPose action server; BT does replan/recover)

Run this on top of an already running `sim.launch.py` + Cartographer SLAM
(mapping.launch.py patrol:=false). map -> odom comes from Cartographer, so
AMCL / map_server are intentionally absent.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

os.environ.setdefault('TURTLEBOT3_MODEL', 'waffle_pi')


def generate_launch_description():
    pkg = get_package_share_directory('tb3_lecture')
    params_file = LaunchConfiguration(
        'params_file',
        default=os.path.join(pkg, 'config', 'nav2_waffle_pi.yaml'))
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    autostart = LaunchConfiguration('autostart', default='true')
    log_level = LaunchConfiguration('log_level', default='info')

    nodes = ['controller_server', 'planner_server', 'behavior_server', 'bt_navigator']
    common = {'--ros-args', '--log-level', log_level}

    def server(pkgname, exe, name):
        # no /tf remapping: we run in the global namespace so Nav2 must see the
        # gz /tf (odom->base_footprint) and robot_state_publisher /tf_static
        return Node(
            package=pkgname, executable=exe, name=name, output='screen',
            parameters=[params_file, {'use_sim_time': True}],
            arguments=['--ros-args', '--log-level', log_level],
        )

    return LaunchDescription([
        DeclareLaunchArgument('params_file', default_value=params_file),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('log_level', default_value='info'),
        server('nav2_controller', 'controller_server', 'controller_server'),
        server('nav2_planner', 'planner_server', 'planner_server'),
        server('nav2_behaviors', 'behavior_server', 'behavior_server'),
        server('nav2_bt_navigator', 'bt_navigator', 'bt_navigator'),
        Node(
            package='nav2_lifecycle_manager', executable='lifecycle_manager',
            name='lifecycle_manager_navigation', output='screen',
            parameters=[{'autostart': autostart,
                         'node_names': nodes,
                         'bond_timeout': 20.0}],
        ),
    ])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launch the campus multi-function hall in gz sim and spawn the TurtleBot3
Waffle Pi just inside the door, plus the ros_gz bridge and the TF tree.

Model is chosen by the TURTLEBOT3_MODEL environment variable (default waffle_pi).

Usage:
  ros2 launch tb3_lecture sim.launch.py            # with gz GUI
  ros2 launch tb3_lecture sim.launch.py gui:=false # headless (for testing)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

import yaml

MODEL = 'waffle_pi'
os.environ.setdefault('TURTLEBOT3_MODEL', MODEL)


def _spawn_pose():
    """Return (x, y, yaw) for the door spawn, from config/podium.yaml if present."""
    try:
        pkg = get_package_share_directory('tb3_lecture')
        cfg = os.path.join(pkg, 'config', 'podium.yaml')
        with open(cfg) as f:
            s = yaml.safe_load(f)['start_door']
        return float(s['x']), float(s['y']), float(s['yaw'])
    except Exception:
        return 0.7, 3.0, 0.0   # fallback: door centre, facing +x


def generate_launch_description():
    tb3_gz = get_package_share_directory('turtlebot3_gazebo')
    pkg_dir = get_package_share_directory('tb3_lecture')
    ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world = os.path.join(pkg_dir, 'worlds', 'lecture_hall.world')
    robot_sdf = os.path.join(tb3_gz, 'models', 'turtlebot3_' + MODEL, 'model.sdf')
    bridge_yaml = os.path.join(tb3_gz, 'params', 'turtlebot3_' + MODEL + '_bridge.yaml')

    # Make sure gz sim can resolve model://lecture_hall (our models dir) and
    # model://turtlebot3_common / turtlebot3_* (official models dir).
    model_dirs = [
        os.path.join(pkg_dir, 'models'),
        os.path.join(tb3_gz, 'models'),
    ]
    existing = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    os.environ['GZ_SIM_RESOURCE_PATH'] = os.pathsep.join(
        [d for d in model_dirs + [existing] if d])

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    gui = LaunchConfiguration('gui', default='true')
    sx, sy, syaw = _spawn_pose()

    # ------------------------------------------------------------------ #
    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': ['-r -s -v2 ', world],
            'on_exit_shutdown': 'true',
        }.items(),
    )

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        # closing the GUI window must NOT tear down the whole simulation
        launch_arguments={'gz_args': '-g -v2 ', 'on_exit_shutdown': 'false'}.items(),
        condition=IfCondition(gui),
    )

    # Spawn robot at the door with heading; retry until the world is up.
    spawn = ExecuteProcess(
        cmd=[
            'bash', '-c',
            'for i in $(seq 1 60); do '
            f'if ros2 run ros_gz_sim create -name {MODEL} '
            f'-file {robot_sdf} -x {sx} -y {sy} -z 0.01 -Y {syaw} '
            '>/dev/null 2>&1; then echo "[spawn] robot spawned"; break; fi; '
            'echo "[spawn] waiting for world ($i)"; sleep 1; done',
        ],
        name='spawn_turtlebot3',
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='parameter_bridge',
        output='screen',
        arguments=['--ros-args', '-p', 'config_file:={}'.format(bridge_yaml)],
    )

    image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        name='image_bridge',
        output='screen',
        arguments=['/camera/image_raw'],
    )

    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb3_gz, 'launch', 'robot_state_publisher.launch.py')),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('gui', default_value='true'),
        gzserver,
        gzclient,
        spawn,
        bridge,
        image_bridge,
        rsp,
    ])

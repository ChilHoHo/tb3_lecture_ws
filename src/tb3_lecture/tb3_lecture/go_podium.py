#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键导航到讲台 (navigate the robot to the podium / 讲演位).

Assumes Nav2 is already running with the saved map (frame "map"), and that the
robot is starting at the door (map origin = door spawn, i.e. pose (0,0,0)).

What it does:
  1. publishes an initial-pose estimate at the door so AMCL localises quickly;
  2. sends a NavigateToPose action goal to the podium pose read from
     config/podium.yaml (map frame; yaw points the robot back at the audience);
  3. waits for the result and exits with a clear status.

Usage:
  ros2 run tb3_lecture go_podium
  ros2 run tb3_lecture go_podium --goal "6.5 0.0 3.1415"
"""

import argparse
import math
import os
import time

import rclpy
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node

from ament_index_python.packages import get_package_share_directory

from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose

import yaml


def _q_from_yaw(yaw):
    return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))


def _load_pose_config():
    """Return (start_map, targets). targets = via waypoints then final goal.

    Cartographer anchors a fresh map at the robot's first pose (the door), so
    map coordinates = world coordinates - door spawn (same yaw).
    """
    pkg = get_package_share_directory('tb3_lecture')
    path = os.path.join(pkg, 'config', 'podium.yaml')
    with open(path) as f:
        cfg = yaml.safe_load(f)
    s = cfg['start_door']
    targets = []
    for w in cfg.get('via_world', []):
        targets.append({'x': w['x'] - s['x'], 'y': w['y'] - s['y'], 'yaw': w.get('yaw', 0.0)})
    g = cfg['goal_podium']
    targets.append({'x': g['x'] - s['x'], 'y': g['y'] - s['y'], 'yaw': g['yaw']})
    start_map = {'x': 0.0, 'y': 0.0, 'yaw': s['yaw']}
    return start_map, targets


class GoPodium(Node):
    def __init__(self, start, targets):
        super().__init__('go_podium')
        self.start = start
        self.targets = targets
        self._pose_pub = self.create_publisher(
            PoseWithCovarianceStamped, '/initialpose', 10)
        self._client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

    # ------------------------------------------------------------------ #
    def send_initial_pose(self):
        p = PoseWithCovarianceStamped()
        p.header.frame_id = 'map'
        p.header.stamp = self.get_clock().now().to_msg()
        p.pose.pose.position.x = self.start['x']
        p.pose.pose.position.y = self.start['y']
        qx, qy, qz, qw = _q_from_yaw(self.start['yaw'])
        p.pose.pose.orientation.x, p.pose.pose.orientation.y = qx, qy
        p.pose.pose.orientation.z, p.pose.pose.orientation.w = qz, qw
        c = p.pose.covariance
        c[0] = 0.25 ** 2          # x
        c[7] = 0.25 ** 2          # y
        c[35] = 0.10 ** 2         # yaw
        for _ in range(8):        # publish a few times so AMCL picks it up
            self._pose_pub.publish(p)
            self.get_clock().sleep_for(Duration(nanoseconds=0.2e9))
        self.get_logger().info(
            f"initial pose sent: ({self.start['x']:.2f}, {self.start['y']:.2f}, "
            f"{math.degrees(self.start['yaw']):.1f}°)")

    def _drive(self, target, label):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = target['x']
        goal_msg.pose.pose.position.y = target['y']
        qx, qy, qz, qw = _q_from_yaw(target['yaw'])
        goal_msg.pose.pose.orientation.x, goal_msg.pose.pose.orientation.y = qx, qy
        goal_msg.pose.pose.orientation.z, goal_msg.pose.pose.orientation.w = qz, qw
        self.get_logger().info(
            f"sending {label} ({target['x']:.2f}, {target['y']:.2f}, "
            f"{math.degrees(target['yaw']):.1f}°)")

        send_goal = self._client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_goal, timeout_sec=10.0)
        if not send_goal.done():
            self.get_logger().error('failed to send goal (timeout)')
            return 2
        goal_handle = send_goal.result()
        if not goal_handle.accepted:
            self.get_logger().error('goal was rejected by Nav2')
            return 2
        self.get_logger().info(f'{label} accepted, driving ...')

        result_fut = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_fut, timeout_sec=300.0)
        if not result_fut.done():
            self.get_logger().error('navigation timed out (300 s)')
            self._client.goal_cancel(goal_handle)   # best-effort stop
            return 1
        status = result_fut.result().status
        self.get_logger().info(f'{label} finished, status={status}')
        return 0 if status == 4 else 1             # 4 == SUCCEEDED

    def run(self):
        self.get_logger().info('waiting for /navigate_to_pose action server ...')
        if not self._client.wait_for_server(timeout_sec=30.0):
            self.get_logger().error(
                'Nav2 action server not available - is navigation running with a map?')
            return 2
        self.send_initial_pose()
        for i, t in enumerate(self.targets):
            last = i == len(self.targets) - 1
            label = 'goal 讲演位' if last else f'waypoint {i + 1}/{len(self.targets) - 1}'
            code = self._drive(t, label)
            if code != 0:
                self.get_logger().error(f'{label} failed, stopping')
                return code
        return 0


def main(args=None):
    rclpy.init(args=args)
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('--goal', default=None,
                        help='override goal as "x y yaw" (map frame)')
    parser.add_argument('--initial', default=None,
                        help='override initial pose as "x y yaw" (map frame)')
    argv = rclpy.utilities.remove_ros_args()
    ns, _ = parser.parse_known_args(argv[1:])

    start_map, targets = _load_pose_config()
    if ns.goal:
        x, y, yaw = map(float, ns.goal.split())
        targets[-1] = {'x': x, 'y': y, 'yaw': yaw}
    if ns.initial:
        x, y, yaw = map(float, ns.initial.split())
        start_map = {'x': x, 'y': y, 'yaw': yaw}

    node = GoPodium(start_map, targets)
    try:
        code = node.run()
    except KeyboardInterrupt:
        code = 130
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    os._exit(code)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上位机控制/状态节点 (host brain) for the lecture demo.

Acts as the "host display + remote control" layer:
  * draws the podium goal / waypoints / live status in RViz (MarkerArray
    `/lecture/markers`)
  * publishes a status string on `/lecture/status`
  * accepts commands on `/lecture/cmd` (std_msgs/String):
      "go"     -> drive along [waypoints..., podium] (re-plan allowed anytime)
      "stop"   -> cancel the current navigation goal and stop the robot
      "return" -> drive back to the door (map origin)

Commands may be sent anytime: a new "go" while moving = re-plan to the target
list; "stop" = emergency stop (cancels Nav2 + zero velocity).
"""

import math

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped, TwistStamped
from nav2_msgs.action import NavigateToPose
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String
from visualization_msgs.msg import Marker, MarkerArray

LATCHED = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                     durability=DurabilityPolicy.TRANSIENT_LOCAL)

import yaml


def _q(yaw):
    return (0.0, 0.0, math.sin(yaw / 2), math.cos(yaw / 2))


class LectureControl(Node):
    def __init__(self):
        super().__init__('lecture_control')
        pkg = get_package_share_directory('tb3_lecture')
        with open(pkg + '/config/podium.yaml') as f:
            cfg = yaml.safe_load(f)
        s = cfg['start_door']
        self.name = cfg.get('robot_model', 'robot')
        self.route = []                       # map-frame targets: vias + goal
        for w in cfg.get('via_world', []):
            self.route.append({'x': w['x'] - s['x'], 'y': w['y'] - s['y'],
                               'yaw': w.get('yaw', 0.0), 'tag': 'waypoint'})
        g = cfg['goal_podium']
        self.route.append({'x': g['x'] - s['x'], 'y': g['y'] - s['y'],
                           'yaw': g['yaw'], 'tag': 'goal'})
        self.door = {'x': 0.0, 'y': 0.0, 'yaw': s['yaw']}

        self.client = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self.marker_pub = self.create_publisher(MarkerArray, '/lecture/markers', 10)
        self.status_pub = self.create_publisher(String, '/lecture/status', LATCHED)
        self.cmd_pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self.create_subscription(String, '/lecture/cmd', self.on_cmd, 10)

        self.status = 'IDLE'
        self.gh = None            # active goal handle
        self.seq = []             # remaining targets
        self.i = 0
        self.timer = self.create_timer(0.5, self.heartbeat)
        self.set_status('IDLE')

    # ------------------------------------------------------------------ #
    def set_status(self, st):
        self.status = st
        msg = String()
        msg.data = st
        self.status_pub.publish(msg)
        self.get_logger().info(f'status -> {st}')

    def zero(self):
        t = TwistStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        self.cmd_pub.publish(t)

    def on_cmd(self, msg):
        c = msg.data.strip().lower()
        self.get_logger().info(f'cmd = {c}')
        if c == 'go':
            self.seq = list(self.route)
            self.i = 0
            self.set_status('NAVIGATING')
            self.drive_next()
        elif c == 'replan':
            self.zero()
            if self.gh:
                self.gh.cancel_goal_async()
                self.gh = None
            self.seq = list(self.route)
            self.i = 0
            self.set_status('NAVIGATING')
            self.drive_next()
        elif c in ('stop', 'cancel'):
            self.zero()
            if self.gh:
                self.gh.cancel_goal_async()
                self.gh = None
            self.set_status('STOPPED')
        elif c == 'return':
            self.zero()
            if self.gh:
                self.gh.cancel_goal_async()
            # 回程走"去程的逆路线"(经中途点走道)；直接"讲台→门口"直线会横穿座椅场，
            # 导致 DWB 被近场密集障碍围死("No valid trajectories")而 abort。
            vias = [dict(w, tag='waypoint') for w in reversed(self.route[:-1])]
            self.seq = vias + [dict(self.door, tag='door')]
            self.i = 0
            self.set_status('RETURNING')
            self.drive_next()

    # ------------------------------------------------------------------ #
    def drive_next(self):
        if self.i >= len(self.seq):
            self.set_status('ARRIVED' if self.seq else 'IDLE')
            return
        t = self.seq[self.i]
        gm = NavigateToPose.Goal()
        gm.pose = PoseStamped()
        gm.pose.header.frame_id = 'map'
        gm.pose.header.stamp = self.get_clock().now().to_msg()
        gm.pose.pose.position.x = t['x']
        gm.pose.pose.position.y = t['y']
        qx, qy, qz, qw = _q(t['yaw'])
        gm.pose.pose.orientation.x, gm.pose.pose.orientation.y = qx, qy
        gm.pose.pose.orientation.z, gm.pose.pose.orientation.w = qz, qw
        self.get_logger().info(
            f'drive to {t["tag"]} ({t["x"]:.2f}, {t["y"]:.2f})')
        f = self.client.send_goal_async(gm)
        f.add_done_callback(self._goal_accepted)

    def _goal_accepted(self, fut):
        gh = fut.result()
        if not gh.accepted:
            self.get_logger().error('goal rejected')
            self.set_status('ERROR')
            return
        self.gh = gh
        rf = gh.get_result_async()
        rf.add_done_callback(self._goal_done)

    def _goal_done(self, fut):
        if self.status == 'STOPPED':
            return
        status = fut.result().status
        if status == 4:                        # SUCCEEDED
            self.gh = None
            self.i += 1
            if self.i >= len(self.seq):
                self.set_status('ARRIVED')
            else:
                self.drive_next()
        else:
            self.gh = None
            self.get_logger().error(f'segment failed status={status}')
            self.set_status('ERROR')

    # ------------------------------------------------------------------ #
    def heartbeat(self):
        self.get_logger().info('hb', throttle_duration_sec=1.0)
        try:
            self.publish_markers()
            s = String()
            s.data = self.status
            self.status_pub.publish(s)     # latched -> late joiners see it
        except Exception as e:             # keep the node alive
            self.get_logger().warn(f'heartbeat error: {e!r}')

    def publish_markers(self):
        ma = MarkerArray()
        ns = 'lecture'
        colors = {'IDLE': (0.7, 0.7, 0.2), 'NAVIGATING': (0.2, 0.9, 0.2),
                  'RETURNING': (0.2, 0.7, 1.0), 'ARRIVED': (0.1, 1.0, 0.4),
                  'STOPPED': (1.0, 0.4, 0.1), 'ERROR': (1.0, 0.1, 0.1)}
        base = 0
        # waypoints / goal spheres
        for j, t in enumerate(self.route):
            m = Marker()
            m.header.frame_id = 'map'
            m.header.stamp = self.get_clock().now().to_msg()
            m.ns = ns; m.id = base + j
            m.type = Marker.SPHERE
            m.action = Marker.ADD
            m.scale.x = m.scale.y = m.scale.z = 0.22
            m.pose.position.x = t['x']; m.pose.position.y = t['y']; m.pose.position.z = 0.12
            r, g, b = colors.get(self.status, (0.5, 0.5, 0.5))
            m.color.r, m.color.g, m.color.b, m.color.a = 0.3, 0.95, 0.4, 0.9
            if t['tag'] == 'goal':
                m.scale.x = m.scale.y = 0.5; m.scale.z = 0.08
                m.type = Marker.CYLINDER
                m.color.r, m.color.g, m.color.b = 0.9, 0.2, 0.2
            ma.markers.append(m)
        # status text over the podium
        t = Marker()
        t.header.frame_id = 'map'
        t.header.stamp = self.get_clock().now().to_msg()
        t.ns = ns; t.id = 100
        t.type = Marker.TEXT_VIEW_FACING
        t.action = Marker.ADD
        t.pose.position.x = self.route[-1]['x']
        t.pose.position.y = self.route[-1]['y']
        t.pose.position.z = 1.6
        t.scale.z = 0.5
        r, g, b = colors.get(self.status, (1, 1, 1))
        t.color.r, t.color.g, t.color.b, t.color.a = r, g, b, 1.0
        t.text = f'{self.name}: {self.status}'
        ma.markers.append(t)
        self.marker_pub.publish(ma)


def main(args=None):
    rclpy.init(args=args)
    n = LectureControl()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    finally:
        n.zero()
        n.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auto-patrol (自动巡游) node used while Cartographer builds the map.

A small reactive bumper/roamer:
  - subscribes to /scan and publishes TwistStamped on /cmd_vel (Jazzy standard);
  - drives forward while the way is reasonably clear;
  - when an obstacle is close ahead, turns in place towards the most open side;
  - prefers headings that keep it moving into new area (mild forward bias +
    small hysteresis so it does not oscillate in open space);
  - stops and reports after `duration` seconds (default 180) or when told via
    the `stop` service (/patrol_stop).

Safe for the bounded multi-function hall; never needs the map.
"""

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter

from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from std_srvs.srv import Empty

# --------------------------------------------------------------------------- #
# behaviour parameters
LINEAR = 0.18          # forward speed (m/s)
ROT = 0.45             # in-place rotation speed (rad/s)
STOP_FRONT = 0.55      # if obstacle nearer than this straight ahead -> turn
TURN_FRONT = 0.80      # begin slowing/turning when obstacle nearer than this
SIDE_CLEAR = 0.45      # minimum lateral clearance while driving (wall-follow trim)
TICK = 0.10            # control period (s)
DEFAULT_DURATION = 180.0  # seconds of patrolling before auto-stop (0 = forever)

# candidate headings (degrees, CCW from the laser frame's +x = robot front)
CANDIDATES = [0.0, -20.0, 20.0, -45.0, 45.0, -90.0, 90.0, -135.0, 135.0, 180.0]
WEDGE = 15.0           # half width (deg) averaged for each candidate
HEADING_HYSTERESIS = 0.35  # (rad) cost added to switching to a different heading


def angdiff(a, b):
    """smallest signed difference a-b, both in radians."""
    d = (a - b + math.pi) % (2 * math.pi) - math.pi
    return d


class PatrolNode(Node):
    def __init__(self):
        super().__init__('patrol_node')
        # duration arrives as int/float from the launch param file; declare as
        # string so any numeric form is accepted, then parse to float
        self.declare_parameter('duration', str(DEFAULT_DURATION))
        self.duration = float(self.get_parameter('duration').value)

        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.on_scan, 5)
        self.cmd_pub = self.create_publisher(TwistStamped, '/cmd_vel', 5)
        self.stop_srv = self.create_service(Empty, '/patrol_stop', self.on_stop)

        self.range = []          # current scan ranges
        self.angle_min = 0.0
        self.angle_inc = 0.0
        self.last_scan = 0.0
        self.turn_bias = 1.0     # remember last turn direction (avoid oscillation)
        self.turn_until = 0.0    # keep turning until this time
        self.heading = 0.0       # our (relative) aim direction
        self.start = time.monotonic()
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.on_odom, 5)
        self.dist = 0.0
        self.last_pose = None
        self._halt = False
        self._timer = self.create_timer(TICK, self.tick)

    # ------------------------------------------------------------------ #
    def on_scan(self, msg: LaserScan):
        self.range = list(msg.ranges)
        self.angle_min = float(msg.angle_min)
        self.angle_inc = float(msg.angle_increment)
        self.last_scan = time.monotonic()

    def on_odom(self, msg):
        p = msg.pose.pose.position
        # crude travelled-distance integrator (2D)
        if self.last_pose is not None:
            self.dist += math.hypot(p.x - self.last_pose[0], p.y - self.last_pose[1])
        self.last_pose = (p.x, p.y)

    def on_stop(self, _req, _res):
        self.get_logger().info('patrol stop requested')
        self._halt = True
        return Empty.Response()

    # ------------------------------------------------------------------ #
    def sector_mean(self, deg):
        """mean range over [deg-WEDGE, deg+WEDGE] (degrees, CCW)."""
        if not self.range:
            return float('inf')
        n = len(self.range)
        tot, cnt = 0.0, 0
        for off in range(-int(WEDGE), int(WEDGE) + 1):
            idx = int(round((deg + off) / math.degrees(self.angle_inc))) % n
            r = self.range[idx]
            if r == float('inf') or r != r:
                r = 3.5  # treat out-of-range as far (matches LDS max)
            tot += max(0.0, r)
            cnt += 1
        return tot / max(1, cnt)

    def choose_heading(self):
        best = None
        for c in CANDIDATES:
            fr = self.sector_mean(c)
            cost = 0.0
            if best is not None:
                # hysteresis: switching aim costs a bit so we do not flicker
                d = abs(angdiff(math.radians(c), self.heading))
                cost = HEADING_HYSTERESIS * d
            score = fr - cost
            if best is None or score > best[1]:
                best = (c, score)
        return best[0]

    # ------------------------------------------------------------------ #
    def _stop(self, lx, az):
        tw = TwistStamped()
        tw.header.stamp = self.get_clock().now().to_msg()
        tw.header.frame_id = 'base_link'
        tw.twist.linear.x = float(lx)
        tw.twist.angular.z = float(az)
        self.cmd_pub.publish(tw)

    def tick(self):
        if self._halt:
            self._stop(0.0, 0.0)
            return
        # auto-stop after duration
        if self.duration > 0 and time.monotonic() - self.start >= self.duration:
            self._stop(0.0, 0.0)
            self.get_logger().info(
                'patrol finished after %.0f s, approx distance travelled %.1f m',
                self.duration, self.dist)
            self._halt = True
            return
        if not self.range or time.monotonic() - self.last_scan > 1.0:
            self._stop(0.0, 0.0)  # no data -> hold
            return

        front = min(self.sector_mean(0.0),
                    self.sector_mean(0.0))  # straight ahead clearance
        left = self.sector_mean(90.0)
        right = self.sector_mean(-90.0)
        tnow = time.monotonic()

        if tnow < self.turn_until or front < STOP_FRONT:
            # ----- rotate towards the more open side -----------------
            if tnow >= self.turn_until:   # pick direction only once per turn
                self.turn_bias = 1.0 if left >= right else -1.0
                self.turn_until = tnow + 1.2
            az = self.turn_bias * ROT
            self._stop(0.0, az)
            self.heading = math.radians(90.0 * self.turn_bias)
            return

        # ----- drive, trimming toward open space (avoid hugging walls) ---
        # mild preference for the heading that keeps the most free space
        c = self.choose_heading()
        self.heading = self.heading * 0.7 + math.radians(c) * 0.3

        # forward speed reduced if not very clear ahead
        lx = LINEAR
        if front < TURN_FRONT:
            lx *= max(0.25, (front - 0.15) / (TURN_FRONT - 0.15))
        # trim angular velocity proportional to side imbalance
        trim = (left - right)
        trim = max(-0.5, min(0.5, trim * 0.12))
        az = angdiff(self.heading, 0.0) * 0.5 + trim
        az = max(-ROT, min(ROT, az))
        self._stop(lx, az)


def main(args=None):
    rclpy.init(args=args)
    node = PatrolNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._stop(0.0, 0.0)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

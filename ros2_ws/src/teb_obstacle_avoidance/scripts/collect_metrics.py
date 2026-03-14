#!/usr/bin/env python3
"""
OBS-3: Metrics Collector Node
==============================
Subscribes to odometry, laser scan, global plan, and navigation action
status topics. On every completed navigation run it writes one CSV row
with the following columns:

  timestamp           ISO-8601 wall-clock time of run completion
  planner             'teb' or 'dwa'
  scenario            'static' | 'narrow' | 'dynamic' | 'mixed'
  path_length_m       Total odometry distance driven (metres)
  time_to_goal_s      Elapsed wall-clock seconds start→end
  near_collisions     Laser readings < proximity_threshold (0.30 m)
  collisions          Laser readings < 0.12 m  (physical contact zone)
  min_obstacle_dist_m Minimum laser range seen during run (metres)
  smoothness_rad_s2   Cumulative |Δω| — proxy for angular jerk
  replan_count        Number of distinct /plan messages received
  success             1 = goal reached, 0 = aborted / cancelled

Usage (auto-launched by nav_simulation.launch.py):
  ros2 run teb_obstacle_avoidance collect_metrics.py \
      --ros-args -p planner:=teb -p scenario:=static \
                 -p output_file:=$HOME/obs3_results/metrics_teb_static.csv
"""

import csv
import math
import os
import time
from datetime import datetime

import rclpy
from rclpy.node import Node
from action_msgs.msg import GoalStatus, GoalStatusArray
from nav_msgs.msg import Odometry, Path
from sensor_msgs.msg import LaserScan


class MetricsCollector(Node):

    def __init__(self):
        super().__init__('metrics_collector')

        # ---- Parameters ------------------------------------------------
        self.declare_parameter('output_file',         'metrics.csv')
        self.declare_parameter('planner',             'teb')
        self.declare_parameter('scenario',            'static')
        self.declare_parameter('proximity_threshold', 0.30)

        self._out_file  = self.get_parameter('output_file').value
        self._planner   = self.get_parameter('planner').value
        self._scenario  = self.get_parameter('scenario').value
        self._prox_thr  = self.get_parameter('proximity_threshold').value

        # ---- Run state -------------------------------------------------
        self._path_len        = 0.0
        self._prev_pos        = None
        self._start_time      = time.time()
        self._elapsed         = None
        self._near_coll       = 0
        self._coll            = 0
        self._ang_jerk        = 0.0
        self._prev_omega      = 0.0
        self._replan_cnt      = 0
        self._prev_plan_stamp = None
        self._active          = True
        self._success         = None
        self._min_dist        = float('inf')

        # ---- Subscriptions ---------------------------------------------
        self.create_subscription(Odometry,        '/odom',  self._odom_cb,   10)
        self.create_subscription(LaserScan,       '/scan',  self._scan_cb,   10)
        self.create_subscription(Path,            '/plan',  self._plan_cb,   10)
        self.create_subscription(
            GoalStatusArray,
            '/navigate_to_pose/_action/status',
            self._status_cb, 10,
        )

        # ---- CSV file --------------------------------------------------
        out_dir = os.path.dirname(self._out_file)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        write_header = not os.path.exists(self._out_file)
        self._csv    = open(self._out_file, 'a', newline='')
        self._writer = csv.writer(self._csv)
        if write_header:
            self._writer.writerow([
                'timestamp', 'planner', 'scenario',
                'path_length_m', 'time_to_goal_s',
                'near_collisions', 'collisions',
                'min_obstacle_dist_m', 'smoothness_rad_s2',
                'replan_count', 'success',
            ])
            self._csv.flush()

        self.get_logger().info(
            f'MetricsCollector started | planner={self._planner}'
            f' | scenario={self._scenario} | output={self._out_file}'
        )

    # ------------------------------------------------------------------ #
    # Callbacks
    # ------------------------------------------------------------------ #

    def _odom_cb(self, msg: Odometry):
        if not self._active:
            return
        pos   = msg.pose.pose.position
        omega = msg.twist.twist.angular.z
        if self._prev_pos is not None:
            dx = pos.x - self._prev_pos[0]
            dy = pos.y - self._prev_pos[1]
            self._path_len += math.hypot(dx, dy)
        self._prev_pos   = (pos.x, pos.y)
        self._ang_jerk  += abs(omega - self._prev_omega)
        self._prev_omega = omega

    def _scan_cb(self, msg: LaserScan):
        if not self._active:
            return
        valid = [r for r in msg.ranges if msg.range_min < r < msg.range_max]
        if not valid:
            return
        min_r = min(valid)
        self._min_dist = min(self._min_dist, min_r)
        if min_r < self._prox_thr:
            self._near_coll += 1
        if min_r < 0.12:
            self._coll += 1

    def _plan_cb(self, msg: Path):
        if not self._active:
            return
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if self._prev_plan_stamp is not None and stamp != self._prev_plan_stamp:
            self._replan_cnt += 1
        self._prev_plan_stamp = stamp

    def _status_cb(self, msg: GoalStatusArray):
        if not self._active or not msg.status_list:
            return
        latest = msg.status_list[-1]
        if latest.status in (
            GoalStatus.STATUS_SUCCEEDED,
            GoalStatus.STATUS_ABORTED,
            GoalStatus.STATUS_CANCELED,
        ):
            self._success = (latest.status == GoalStatus.STATUS_SUCCEEDED)
            self._elapsed = time.time() - self._start_time
            self._active  = False
            self._save_row()
            self.get_logger().info(
                f'Run finished | success={self._success}'
                f' | path={self._path_len:.2f} m'
                f' | time={self._elapsed:.1f} s'
                f' | near_coll={self._near_coll}'
                f' | replans={self._replan_cnt}'
            )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _save_row(self):
        self._writer.writerow([
            datetime.now().isoformat(),
            self._planner,
            self._scenario,
            round(self._path_len,  3),
            round(self._elapsed,   2) if self._elapsed else 'N/A',
            self._near_coll,
            self._coll,
            round(self._min_dist,  3) if self._min_dist != float('inf') else 'N/A',
            round(self._ang_jerk,  4),
            self._replan_cnt,
            int(self._success) if self._success is not None else 'N/A',
        ])
        self._csv.flush()

    def destroy_node(self):
        if self._active and self._prev_pos is not None:
            # Save partial data on Ctrl-C
            self._elapsed  = time.time() - self._start_time
            self._success  = False
            self._active   = False
            self._save_row()
        self._csv.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MetricsCollector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

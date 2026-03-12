#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry, Path
from sensor_msgs.msg import LaserScan
from action_msgs.msg import GoalStatusArray, GoalStatus
import math, csv, os, time
from datetime import datetime

class MetricsCollector(Node):
    def __init__(self):
        super().__init__('metrics_collector')
        self.declare_parameter('output_file', 'metrics.csv')
        self.declare_parameter('planner', 'teb')
        self.declare_parameter('scenario', 'static')
        self.declare_parameter('proximity_threshold', 0.30)

        self.output_file  = self.get_parameter('output_file').value
        self.planner      = self.get_parameter('planner').value
        self.scenario     = self.get_parameter('scenario').value
        self.prox_thresh  = self.get_parameter('proximity_threshold').value

        self._path_length       = 0.0
        self._prev_pos          = None
        self._start_time        = time.time()
        self._elapsed_time      = None
        self._near_collisions   = 0
        self._collisions        = 0
        self._angular_jerk      = 0.0
        self._prev_omega        = 0.0
        self._replan_count      = 0
        self._prev_plan_stamp   = None
        self._run_active        = True
        self._success           = None
        self._min_obstacle_dist = float('inf')

        self.create_subscription(Odometry, '/odom', self._odom_cb, 10)
        self.create_subscription(LaserScan, '/scan', self._scan_cb, 10)
        self.create_subscription(Path, '/plan', self._plan_cb, 10)
        self.create_subscription(GoalStatusArray,
            '/navigate_to_pose/_action/status', self._status_cb, 10)

        os.makedirs(os.path.dirname(self.output_file) if os.path.dirname(self.output_file) else '.', exist_ok=True)
        write_header = not os.path.exists(self.output_file)
        self._csv_file = open(self.output_file, 'a', newline='')
        self._writer   = csv.writer(self._csv_file)
        if write_header:
            self._writer.writerow([
                'timestamp','planner','scenario',
                'path_length_m','time_to_goal_s',
                'near_collisions','collisions',
                'min_obstacle_dist_m','smoothness_rad_s2',
                'replan_count','success'
            ])
        self.get_logger().info(f'Metrics collector started | planner={self.planner} | scenario={self.scenario}')

    def _odom_cb(self, msg):
        if not self._run_active: return
        pos   = msg.pose.pose.position
        omega = msg.twist.twist.angular.z
        if self._prev_pos is not None:
            dx = pos.x - self._prev_pos[0]
            dy = pos.y - self._prev_pos[1]
            self._path_length += math.hypot(dx, dy)
        self._prev_pos = (pos.x, pos.y)
        self._angular_jerk += abs(omega - self._prev_omega)
        self._prev_omega = omega

    def _scan_cb(self, msg):
        if not self._run_active: return
        valid = [r for r in msg.ranges if msg.range_min < r < msg.range_max]
        if not valid: return
        min_r = min(valid)
        if min_r < self._min_obstacle_dist:
            self._min_obstacle_dist = min_r
        if min_r < self.prox_thresh:
            self._near_collisions += 1
        if min_r < 0.12:
            self._collisions += 1

    def _plan_cb(self, msg):
        if not self._run_active: return
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if self._prev_plan_stamp is not None and stamp != self._prev_plan_stamp:
            self._replan_count += 1
        self._prev_plan_stamp = stamp

    def _status_cb(self, msg):
        if not self._run_active or not msg.status_list: return
        latest = msg.status_list[-1]
        if latest.status in (GoalStatus.STATUS_SUCCEEDED,
                             GoalStatus.STATUS_ABORTED,
                             GoalStatus.STATUS_CANCELED):
            self._success      = (latest.status == GoalStatus.STATUS_SUCCEEDED)
            self._elapsed_time = time.time() - self._start_time
            self._run_active   = False
            self._save_row()
            self.get_logger().info(
                f'Run complete | success={self._success} | '
                f'path={self._path_length:.2f}m | time={self._elapsed_time:.1f}s')

    def _save_row(self):
        self._writer.writerow([
            datetime.now().isoformat(), self.planner, self.scenario,
            round(self._path_length, 3),
            round(self._elapsed_time, 2) if self._elapsed_time else 'N/A',
            self._near_collisions, self._collisions,
            round(self._min_obstacle_dist, 3),
            round(self._angular_jerk, 4),
            self._replan_count,
            int(self._success) if self._success is not None else 'N/A',
        ])
        self._csv_file.flush()

    def destroy_node(self):
        self._csv_file.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = MetricsCollector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node._run_active:
            node._elapsed_time = time.time() - node._start_time
            node._success = False
            node._save_row()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

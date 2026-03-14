#!/usr/bin/env python3
"""
OBS-3: Goal Sender Utility
============================
Sends a single NavigateToPose goal to Nav2 and waits for the result.
Used for scripted / repeatable experiments.

Usage (after sourcing workspace):
  ros2 run teb_obstacle_avoidance goal_sender.py \
      --ros-args -p x:=4.0 -p y:=0.0 -p yaw:=0.0

Default goal: x=4.0, y=0.0, yaw=0.0  (4 m ahead of robot start)
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped


class GoalSender(Node):

    def __init__(self):
        super().__init__('goal_sender')

        self.declare_parameter('x',   4.0)
        self.declare_parameter('y',   0.0)
        self.declare_parameter('yaw', 0.0)   # radians

        x   = self.get_parameter('x').value
        y   = self.get_parameter('y').value
        yaw = self.get_parameter('yaw').value

        self._client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.get_logger().info('Waiting for navigate_to_pose action server...')
        self._client.wait_for_server()
        self.get_logger().info(
            f'Sending goal → x={x:.2f} m, y={y:.2f} m, '
            f'yaw={math.degrees(yaw):.1f}°'
        )
        self._send(x, y, yaw)

    def _send(self, x: float, y: float, yaw: float):
        goal          = NavigateToPose.Goal()
        goal.pose     = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp    = self.get_clock().now().to_msg()
        goal.pose.pose.position.x    = x
        goal.pose.pose.position.y    = y
        goal.pose.pose.position.z    = 0.0
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

        future = self._client.send_goal_async(goal)
        future.add_done_callback(self._on_accepted)

    def _on_accepted(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().error('Goal REJECTED by Nav2.')
            rclpy.shutdown()
            return
        self.get_logger().info('Goal ACCEPTED — navigating...')
        handle.get_result_async().add_done_callback(self._on_done)

    def _on_done(self, future):
        self.get_logger().info('Navigation complete.')
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = GoalSender()
    rclpy.spin(node)


if __name__ == '__main__':
    main()

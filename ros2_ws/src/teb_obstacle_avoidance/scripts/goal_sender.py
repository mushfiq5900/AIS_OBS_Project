#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
import math

class GoalSender(Node):
    def __init__(self):
        super().__init__('goal_sender')
        self.declare_parameter('x',   4.0)
        self.declare_parameter('y',   0.0)
        self.declare_parameter('yaw', 0.0)
        x   = self.get_parameter('x').value
        y   = self.get_parameter('y').value
        yaw = self.get_parameter('yaw').value
        self._client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.get_logger().info('Waiting for navigate_to_pose action server...')
        self._client.wait_for_server()
        self.get_logger().info(f'Sending goal: x={x}, y={y}, yaw={yaw}')
        self._send_goal(x, y, yaw)

    def _send_goal(self, x, y, yaw):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)
        future = self._client.send_goal_async(goal_msg)
        future.add_done_callback(self._goal_response_cb)

    def _goal_response_cb(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().error('Goal REJECTED')
            return
        self.get_logger().info('Goal ACCEPTED — navigating...')
        handle.get_result_async().add_done_callback(self._result_cb)

    def _result_cb(self, future):
        self.get_logger().info('Navigation finished!')
        rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = GoalSender()
    rclpy.spin(node)

if __name__ == '__main__':
    main()

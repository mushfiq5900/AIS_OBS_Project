#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import SetEntityState
from gazebo_msgs.msg import EntityState
from geometry_msgs.msg import Pose, Twist, Point, Quaternion
import math

class DynamicObstacleController(Node):
    def __init__(self):
        super().__init__('dynamic_obstacle_spawner')
        self.cli = self.create_client(SetEntityState, '/gazebo/set_entity_state')
        while not self.cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().info('Waiting for /gazebo/set_entity_state...')
        self.obstacles = [
            {'name': 'dyn_obs_1',
             'waypoints': [(-1.5, 2.0),(4.5, 2.0),(4.5, 2.0),(-1.5, 2.0)],
             'speed': 0.4},
            {'name': 'dyn_obs_2',
             'waypoints': [(3.0,-2.5),(1.0,1.5),(1.0,1.5),(3.0,-2.5)],
             'speed': 0.3},
        ]
        self._states = {o['name']: {'wp_idx': 0,
            'x': o['waypoints'][0][0], 'y': o['waypoints'][0][1]}
            for o in self.obstacles}
        self.create_timer(0.1, self.update_obstacles)
        self.get_logger().info('Dynamic obstacle controller started.')

    def update_obstacles(self):
        dt = 0.1
        for obs in self.obstacles:
            name  = obs['name']
            speed = obs['speed']
            wps   = obs['waypoints']
            state = self._states[name]
            tx, ty = wps[state['wp_idx']]
            dx, dy  = tx - state['x'], ty - state['y']
            dist    = math.hypot(dx, dy)
            if dist < 0.05:
                state['wp_idx'] = (state['wp_idx'] + 1) % len(wps)
            else:
                step = min(speed * dt, dist)
                state['x'] += step * dx / dist
                state['y'] += step * dy / dist
            self._send_state(name, state['x'], state['y'])

    def _send_state(self, name, x, y):
        req = SetEntityState.Request()
        req.state = EntityState()
        req.state.name = name
        req.state.pose = Pose(
            position=Point(x=x, y=y, z=0.25),
            orientation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0))
        req.state.twist = Twist()
        req.state.reference_frame = 'world'
        self.cli.call_async(req)

def main(args=None):
    rclpy.init(args=args)
    node = DynamicObstacleController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

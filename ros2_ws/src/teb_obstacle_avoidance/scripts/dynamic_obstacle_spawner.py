#!/usr/bin/env python3
"""
OBS-3: Dynamic Obstacle Controller
====================================
Moves pre-spawned Gazebo cylinder models along waypoint paths using the
/gazebo/set_entity_state service (Gazebo Classic).

Obstacle motion:
  dyn_obs_1 — sweeps horizontally across the arena at y=2.0 (speed 0.4 m/s)
  dyn_obs_2 — sweeps diagonally                              (speed 0.3 m/s)

Both obstacles loop continuously back and forth between their waypoints.
The controller fires at 10 Hz (dt=0.1 s).
"""

import math
import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import SetEntityState
from gazebo_msgs.msg import EntityState
from geometry_msgs.msg import Pose, Twist, Point, Quaternion


class DynamicObstacleController(Node):

    def __init__(self):
        super().__init__('dynamic_obstacle_spawner')

        # Wait up to 30 s for the Gazebo service to become available
        self._cli = self.create_client(SetEntityState, '/gazebo/set_entity_state')
        waited = 0.0
        while not self._cli.wait_for_service(timeout_sec=2.0):
            waited += 2.0
            self.get_logger().info('Waiting for /gazebo/set_entity_state ...')
            if waited >= 30.0:
                self.get_logger().error(
                    'Gazebo set_entity_state service not available — '
                    'dynamic obstacles will not move.'
                )
                return

        # Obstacle definitions
        # Each entry: name (must match the model name in the .world file),
        #             waypoints [(x, y), ...],  speed (m/s)
        self._obstacles = [
            {
                'name':      'dyn_obs_1',
                'waypoints': [(-1.5, 2.0), (4.5, 2.0), (4.5, 2.0), (-1.5, 2.0)],
                'speed':     0.4,
            },
            {
                'name':      'dyn_obs_2',
                'waypoints': [(3.0, -2.5), (1.0, 1.5), (1.0, 1.5), (3.0, -2.5)],
                'speed':     0.3,
            },
        ]

        # Runtime state for each obstacle
        self._states = {
            obs['name']: {
                'wp_idx': 0,
                'x':      obs['waypoints'][0][0],
                'y':      obs['waypoints'][0][1],
            }
            for obs in self._obstacles
        }

        # 10 Hz update loop
        self.create_timer(0.1, self._update)
        self.get_logger().info('Dynamic obstacle controller started.')

    def _update(self):
        dt = 0.1
        for obs in self._obstacles:
            name  = obs['name']
            speed = obs['speed']
            wps   = obs['waypoints']
            st    = self._states[name]

            # Target waypoint
            tx, ty = wps[st['wp_idx']]
            dx = tx - st['x']
            dy = ty - st['y']
            dist = math.hypot(dx, dy)

            if dist < 0.05:
                # Reached waypoint — advance to next
                st['wp_idx'] = (st['wp_idx'] + 1) % len(wps)
            else:
                step   = min(speed * dt, dist)
                st['x'] += step * dx / dist
                st['y'] += step * dy / dist

            self._move(name, st['x'], st['y'])

    def _move(self, name: str, x: float, y: float):
        req             = SetEntityState.Request()
        req.state       = EntityState()
        req.state.name  = name
        req.state.pose  = Pose(
            position    = Point(x=x, y=y, z=0.25),
            orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
        )
        req.state.twist           = Twist()
        req.state.reference_frame = 'world'
        self._cli.call_async(req)   # fire-and-forget at 10 Hz


def main(args=None):
    rclpy.init(args=args)
    node = DynamicObstacleController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

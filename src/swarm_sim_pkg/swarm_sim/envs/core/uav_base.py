
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan, Imu
import numpy as np
from swarm_sim.common.battery import Battery

class UAVBase:
    """
    Base helper class for interfacing a single UAV with ROS 2.
    Handles Pub/Sub for CmdVel, Odom, and Lidar.
    """
    def __init__(self, node: Node, agent_id: str, namespace: str = ""):
        self.node = node
        self.agent_id = agent_id
        
        # Topic naming convention: /{namespace}/{model_name}/... or just /{model_name}/...
        # Adjust based on your Gazebo bridge config
        prefix = f"{namespace}/{agent_id}" if namespace else f"/{agent_id}"
        
        # Publishers
        self.pub_cmd_vel = self.node.create_publisher(Twist, f"{prefix}/cmd_vel", 10)
        
        # Subscribers
        self.sub_odom = self.node.create_subscription(Odometry, f"{prefix}/odometry", self._odom_cb, 10)
        self.sub_scan = self.node.create_subscription(LaserScan, f"{prefix}/scan", self._scan_cb, 10)
        self.sub_imu = self.node.create_subscription(Imu, f"{prefix}/sensors/imu", self._imu_cb, 10)
        
        # State
        self.position = np.zeros(3)
        self.velocity = np.zeros(3)
        self.orientation = np.zeros(4) # Quaternion
        self.lidar_ranges = np.zeros(360) # Default size
        self.battery = Battery(capacity=100.0)
        
        self.imu_data = np.zeros(6) # [acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z]
        
        self.first_odom = False

    def _odom_cb(self, msg):
        self.first_odom = True
        p = msg.pose.pose.position
        v = msg.twist.twist.linear
        o = msg.pose.pose.orientation
        
        self.position = np.array([p.x, p.y, p.z])
        self.velocity = np.array([v.x, v.y, v.z])
        self.orientation = np.array([o.x, o.y, o.z, o.w])

    def _imu_cb(self, msg):
        self.imu_data = np.array([
            msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z,
            msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z
        ])

    def _scan_cb(self, msg):
        # Handle Inf values
        ranges = np.array(msg.ranges)
        ranges[ranges == float('inf')] = msg.range_max
        self.lidar_ranges = ranges

    def apply_action(self, vel_action):
        """
        vel_action: [vx, vy, vz, wz]
        """
        # Drain battery based on movement magnitude
        move_cost = np.linalg.norm(vel_action[:3]) * 0.1 + 0.01
        self.battery.consume(move_cost)
        
        if self.battery.is_empty():
            # Stop if empty logic can be here or in Env
            pass
        msg = Twist()
        msg.linear.x = float(vel_action[0])
        msg.linear.y = float(vel_action[1])
        msg.linear.z = float(vel_action[2])
        msg.angular.z = float(vel_action[3])
        self.pub_cmd_vel.publish(msg)

    def get_state(self):
        """Returns flattened state: [pos(3), vel(3), bat(1)]"""
        # We add battery to state for RL
        return np.concatenate([self.position, self.velocity, [self.battery.get_percentage()]])

#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

class OdomTfBroadcaster(Node):
    def __init__(self):
        super().__init__('odom_tf_broadcaster')
        # Get namespace from node name or param (assuming node is run in namespace)
        # But we need to subscribe to /uav_X/odometry
        
        self.declare_parameter('scan_topic', 'odometry')
        self.declare_parameter('parent_frame', 'world')
        self.declare_parameter('child_frame_suffix', '/base_link') # uav_X + suffix

        # We need to know who we are. 
        # Strategy: This node is launched PER DRONE in the namespace.
        # So topic is 'odometry' (relative).
        
        self.subscription = self.create_subscription(
            Odometry,
            'odometry',
            self.odom_callback,
            10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.get_logger().info("Odom TF Broadcaster Started")

    def odom_callback(self, msg):
        t = TransformStamped()

        # Read Current Time
        t.header.stamp = self.get_clock().now().to_msg()
        
        # Parent Frame: world (Fixed)
        t.header.frame_id = 'world'
        
        # Child Frame: uav_X/base_link (Derived from msg or namespace)
        # Msg frame_id usually comes from Gazebo as "world" (if we set it)
        # Child frame_id comes as "base_link" (if we set it).
        # But we used Namespace in URDF! uav_X/base_link.
        # So we want to broadcast: world -> uav_X/base_link.
        
        # Let's extract the uav name from the node namespace if possible, 
        # or rely on the message.
        # But the Gazebo message might say child_frame_id = "base_link".
        # We need "uav_X/base_link".
        
        ns = self.get_namespace().strip('/') # e.g. "uav_0"
        t.child_frame_id = f"{ns}/base_link"

        # Copy Position
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z

        # Copy Orientation
        t.transform.rotation = msg.pose.pose.orientation

        # Publish
        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = OdomTfBroadcaster()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

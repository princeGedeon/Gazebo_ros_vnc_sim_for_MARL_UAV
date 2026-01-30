import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import time
import sys

class DebugTakeoff(Node):
    def __init__(self):
        super().__init__('debug_takeoff_node')
        
        self.publisher = self.create_publisher(Twist, '/uav_0/cmd_vel', 10)
        self.subscription = self.create_subscription(
            Odometry,
            '/uav_0/odometry',
            self.odom_callback,
            10
        )
        self.start_time = time.time()
        self.max_z = -999.0
        
        # Timer to publish commands
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info("Debug Node Started: Sending UP command...")

    def timer_callback(self):
        msg = Twist()
        msg.linear.z = 2.0  # Strong UP command
        self.publisher.publish(msg)
        
        elapsed = time.time() - self.start_time
        if elapsed > 10.0:
            self.get_logger().info(f"Test Finished. Max Altitude Reached: {self.max_z:.2f}m")
            if self.max_z > 0.5:
                self.get_logger().info("SUCCESS: Drone took off!")
            else:
                self.get_logger().error("FAILURE: Drone did not take off.")
            sys.exit(0)

    def odom_callback(self, msg):
        current_z = msg.pose.pose.position.z
        if current_z > self.max_z:
            self.max_z = current_z
        
        # Print every 1m of altitude change approximately
        # self.get_logger().info(f"Alt: {current_z:.2f}")

def main(args=None):
    rclpy.init(args=args)
    node = DebugTakeoff()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    except Exception as e:
        print(e)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

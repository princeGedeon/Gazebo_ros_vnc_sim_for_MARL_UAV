
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import PointCloud2, Image, Imu
from std_msgs.msg import String

import time
import threading

class SystemVerifier(Node):
    def __init__(self):
        super().__init__('system_verifier')
        self.get_logger().info("Starting System Verification...")
        
        self.lidar_count = 0
        self.camera_count = 0
        self.imu_count = 0
        
        # QOS: Best Effort meant for Sensor Data
        best_effort_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        # Lidar (Best Effort)
        self.create_subscription(PointCloud2, '/uav_0/sensors/lidar', self.lidar_cb, best_effort_qos)
        
        # Camera (Best Effort)
        self.create_subscription(Image, '/uav_0/camera/image_raw', self.camera_cb, best_effort_qos)
        
        # IMU (Best Effort)
        self.create_subscription(Imu, '/uav_0/sensors/imu', self.imu_cb, best_effort_qos)

        # Robot Description (Transient Local)
        transient_local_qos = QoSProfile(
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            depth=1
        )
        self.create_subscription(String, '/uav_0/robot_description', self.desc_cb, transient_local_qos)
        self.has_desc = False

    def lidar_cb(self, msg):
        self.lidar_count += 1
        
    def camera_cb(self, msg):
        self.camera_count += 1
        
    def imu_cb(self, msg):
        self.imu_count += 1

    def desc_cb(self, msg):
        self.has_desc = True

def main(args=None):
    rclpy.init(args=args)
    node = SystemVerifier()
    
    # Spin in a separate thread for 5 seconds
    thread = threading.Thread(target=rclpy.spin, args=(node,))
    thread.start()
    
    print("\n[VERIFIER] Listening for 5 seconds...\n")
    time.sleep(5.0)
    
    rclpy.shutdown()
    thread.join()
    
    print("="*40)
    print("      SYSTEM VERIFICATION REPORT      ")
    print("="*40)
    
    # Check Lidar
    if node.lidar_count > 0:
        print(f"[PASS] Lidar Data Received: {node.lidar_count} msgs")
    else:
        print(f"[FAIL] NO Lidar Data! Check Bridge or Gazebo (Active?)")
        print("       -> Hint: Ensure Bridge QoS matches.")

    # Check Camera
    if node.camera_count > 0:
        print(f"[PASS] Front Camera Received: {node.camera_count} msgs")
    else:
        print(f"[FAIL] NO Camera Data!")

    # Check IMU
    if node.imu_count > 0:
        print(f"[PASS] IMU Data Received: {node.imu_count} msgs")
    else:
        print(f"[FAIL] NO IMU Data!")

    # Check Description
    if node.has_desc:
        print(f"[PASS] Robot Description Found (/uav_0/robot_description)")
    else:
        print(f"[FAIL] Robot Description NOT Found!")
        print("       -> Hint: robot_state_publisher might be missing or namespace wrong.")

    print("\n[TIP] If Lidar passes here but shows 0 in RViz:")
    print("      Set RViz 'Reliability Policy' to 'Best Effort'.")
    print("="*40)

if __name__ == '__main__':
    main()

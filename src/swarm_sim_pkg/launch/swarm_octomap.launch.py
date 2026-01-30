
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('resolution', default_value='0.1'),
        DeclareLaunchArgument('frame_id', default_value='world'),
        
        Node(
            package='octomap_server',
            executable='octomap_server_node',
            name='octomap_server',
            output='screen',
            parameters=[{
                'resolution': 0.1,
                'frame_id': 'world',
                'sensor_model/max_range': 100.0,
                'latch': False,
                # Tuning for Ouster OS1-64
                'pointcloud_min_z': 0.2,
                'pointcloud_max_z': 100.0,
                'occupancy_min_z': 0.2,
                'occupancy_max_z': 100.0,
                'filter_ground': False, # We want to map ground too? Or just obstacles?
                                      # Usually for flying, ground is an obstacle.
            }],
            remappings=[
                # Input: The Centralized Merged Pointcloud OR Single Drone
                # Ideally, we merge all drones. But for now, let's map uav_0
                # OR use the global /tf if we have multiple.
                # Let's map uav_0's High/Fidelity Lidar
                ('cloud_in', '/uav_0/velodyne_points') 
            ]
        )
    ])

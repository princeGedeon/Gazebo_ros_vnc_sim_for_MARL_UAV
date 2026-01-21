
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    
    # Octomap Server for 3D Occupancy Grid
    # We will assume a merge of all UAV points or separate instances.
    # The user asked for "ensemble" (ensemble/together) or decentralized.
    # Let's launch one server that listens to a merged topic /all_points
    # OR launch one per drone.
    
    # Strategy: One server per drone (Decentralized mapping)
    
    nodes = []
    
    for i in range(3): # Hardcoded for now, ideally loop based on arg
        name = f"uav_{i}"
        
        octomap_node = Node(
            package='octomap_server',
            executable='octomap_server_node',
            name=f'octomap_server_{name}',
            namespace=name,
            parameters=[{
                'resolution': 0.2,
                'frame_id': 'world', # Map frame
                'base_frame_id': f'{name}/base_link', # Robot frame (needs TF)
                'latch': False,
                'use_sim_time': use_sim_time,
                'filter_ground': True,
                # 'ground_filter/distance': 0.1,
                # 'ground_filter/plane_distance': 0.1
            }],
            remappings=[
                ('cloud_in', f'/{name}/sensors/lidar'), # Input PointCloud2
                ('octomap_binary', 'octomap_binary'),
                ('octomap_full', 'octomap_full'),
                ('projected_map', 'map') # 2D Occupancy Grid
            ],
            output='screen'
        )
        nodes.append(octomap_node)

    # Note: For this to work, we need TF transforms from world -> uav_i/base_link.
    # Gazebo Bridge provides /model/uav_i/pose usually, or we need a TF publisher.
    # The 'ros_gz_bridge' parameter_bridge can bridge TF.
    # We need to ensure TF is bridged.
    
    return LaunchDescription(nodes)

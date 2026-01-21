
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import PushRosNamespace
from ament_index_python.packages import get_package_share_directory

def launch_setup(context, *args, **kwargs):
    # Args
    num_drones = int(context.launch_configurations['num_drones'])
    
    # Paths
    # We assume 'cslam_experiments' is installed after the user runs setup script
    try:
        pkg_cslam_experiments = get_package_share_directory('cslam_experiments')
    except:
        print("Warning: cslam_experiments package not found. Did you run setup_real_slam.sh?")
        return []

    cslam_launch = os.path.join(pkg_cslam_experiments, 'launch', 'cslam', 'cslam_lidar.launch.py')
    
    nodes = []
    
    for i in range(num_drones):
        robot_id = i
        namespace = f"uav_{i}"
        
        # Swarm-SLAM Group
        group = GroupAction([
            PushRosNamespace(namespace),
            
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(cslam_launch),
                launch_arguments={
                    'robot_id': str(robot_id),
                    'max_nb_robots': str(num_drones),
                    'namespace': namespace,
                    'config_file': 'kitti_lidar.yaml'
                }.items()
            )
        ])
        nodes.append(group)

    return nodes

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('num_drones', default_value='3', description='Number of drones'),
        OpaqueFunction(function=launch_setup)
    ])

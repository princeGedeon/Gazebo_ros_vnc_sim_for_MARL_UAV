
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_swarm_sim = get_package_share_directory('swarm_sim')
    sdf_path = os.path.join(pkg_swarm_sim, 'assets', 'models', 'ground_station.sdf')

    # Spawning 3 Stations aligned on X axis (10m spacing)
    # Station 0 (Center)
    spawn_s0 = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'station_0', '-file', sdf_path, '-x', '0.0', '-y', '0.0', '-z', '0.0'],
        output='screen'
    )

    # Station 1 (Right)
    spawn_s1 = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'station_1', '-file', sdf_path, '-x', '10.0', '-y', '0.0', '-z', '0.0'],
        output='screen'
    )

    # Station 2 (Left)
    spawn_s2 = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'station_2', '-file', sdf_path, '-x', '-10.0', '-y', '0.0', '-z', '0.0'],
        output='screen'
    )

    return LaunchDescription([
        spawn_s0,
        spawn_s1,
        spawn_s2
    ])

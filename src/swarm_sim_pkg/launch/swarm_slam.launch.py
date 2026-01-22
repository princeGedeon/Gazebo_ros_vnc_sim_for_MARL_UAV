import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def launch_setup(context, *args, **kwargs):
    num_drones = int(context.launch_configurations['num_drones'])
    pkg_mrg_slam = get_package_share_directory('mrg_slam')
    
    nodes = []
    
    for i in range(num_drones):
        name = f"uav_{i}"
        
        # Initial positions from multi_ops.launch.py logic
        # x_pos = float(i) * 2.0
        x_init = float(i) * 2.0
        y_init = 0.0
        z_init = 0.24 # Drone start height
        
        print(f"Planning SLAM for {name} at x={x_init}")
        
        # Launch MRG SLAM for this drone
        # ros2 launch mrg_slam mrg_slam.launch.py model_namespace:=atlas x:=0.0 ...
        slam_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_mrg_slam, 'launch', 'mrg_slam.launch.py')
            ),
            launch_arguments={
                'model_namespace': name,
                'use_sim_time': 'true',
                'x': str(x_init),
                'y': str(y_init),
                'z': str(z_init),
                'roll': '0.0',
                'pitch': '0.0',
                'yaw': '0.0'
            }.items()
        )
        
        # Stagger launches to avoid CPU spike?
        nodes.append(TimerAction(
            period=float(i)*2.0,
            actions=[slam_launch]
        ))
        
    return nodes

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('num_drones', default_value='3', description='Number of drones'),
        OpaqueFunction(function=launch_setup)
    ])

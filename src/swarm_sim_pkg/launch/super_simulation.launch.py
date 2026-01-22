
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition

def generate_launch_description():
    pkg_swarm_sim = get_package_share_directory('swarm_sim')
    
    # Args
    num_drones = LaunchConfiguration('num_drones')
    map_type = LaunchConfiguration('map_type')
    map_file = LaunchConfiguration('map_file')
    open_rviz = LaunchConfiguration('open_rviz')
    run_slam = LaunchConfiguration('slam')
    
    # 1. Main Simulation (Multi Ops)
    main_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_swarm_sim, 'launch', 'multi_ops.launch.py')
        ),
        launch_arguments={
            'num_drones': num_drones,
            'map_type': map_type,
            'map_file': map_file
        }.items()
    )

    # 1.1 Swarm SLAM (Optional)
    # 1.1 Swarm SLAM (Optional - Disabled for Multi-Container)
    # swarm_slam = IncludeLaunchDescription(...)
    # Removed to avoid "No such file" error since we deleted swarm_slam.launch.py
    
    # 2. RViz
    rviz_config = os.path.join(pkg_swarm_sim, 'default.rviz')
    
    rviz_process = ExecuteProcess(
        cmd=['rviz2', '-d', rviz_config],
        output='screen',
        condition=IfCondition(open_rviz)
    )

    return LaunchDescription([
        DeclareLaunchArgument('num_drones', default_value='3', description='Number of drones'),
        DeclareLaunchArgument('map_type', default_value='world', description='Map Type'),
        DeclareLaunchArgument('map_file', default_value='city.sdf', description='Map File'),
        DeclareLaunchArgument('open_rviz', default_value='true', description='Open RViz?'),
        DeclareLaunchArgument('slam', default_value='false', description='Run Swarm SLAM?'),
        
        main_sim,
        
        # Spawn Physical Ground Stations
        IncludeLaunchDescription(
             PythonLaunchDescriptionSource(
                 os.path.join(pkg_swarm_sim, 'launch', 'spawn_stations.launch.py')
             )
        ),
        
        # swarm_slam,
        rviz_process
    ])


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
            'num_stations': '3', # CRITICAL: Ensure multi_ops knows there are 3 stations so it spawns drones atop them
            'map_type': map_type,
            'map_file': map_file
        }.items()
    )

    # 1.1 Swarm SLAM (Optional)
    # 1.1 Swarm SLAM (Optional)
    swarm_slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_swarm_sim, 'launch', 'swarm_slam.launch.py')
        ),
        launch_arguments={
            'num_drones': num_drones,
            'map_cloud_update_interval': '2.0'
        }.items(),
        condition=IfCondition(run_slam)
    )
    
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
        DeclareLaunchArgument('slam', default_value='true', description='Run Swarm SLAM?'),
        DeclareLaunchArgument('octomap', default_value='false', description='Run OctoMap Server?'),
        
        main_sim,
        
        # Spawn Physical Ground Stations
        IncludeLaunchDescription(
             PythonLaunchDescriptionSource(
                 os.path.join(pkg_swarm_sim, 'launch', 'spawn_stations.launch.py')
             )
        ),
        
        swarm_slam,
        
        # OctoMap Server
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_swarm_sim, 'launch/swarm_octomap.launch.py')),
            condition=IfCondition(LaunchConfiguration('octomap'))
        ),

        rviz_process
    ])

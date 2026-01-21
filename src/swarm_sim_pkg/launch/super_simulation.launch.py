
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    pkg_swarm_sim = get_package_share_directory('swarm_sim')
    
    # Args
    num_drones = LaunchConfiguration('num_drones')
    map_type = LaunchConfiguration('map_type')
    map_file = LaunchConfiguration('map_file')
    open_rviz = LaunchConfiguration('open_rviz')
    
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
    
    # 2. RViz
    rviz_node = ExecuteProcess(
        cmd=['rviz2', '-d', os.path.join(pkg_swarm_sim, 'swarm_sim/common/viz_utils.py')], # Placeholder config?
        # Better: use default empty or specific config if we had one.
        # But user wants "visualize everything".
        # Let's verify if we have a config or just launch empty. 
        # User said "rviz2 explain how visualize".
        # I will launch empty rviz2 for now, but in docs explain which config to load if any.
        # Or better: I will try to save a default config? No, I don't have X11 access to save.
        # I will launch standard rviz2.
        condition=LaunchConfiguration('open_rviz'), # This condition logic requires specific action type or just if check
        output='screen'
    )
    # The condition kwarg works on specific actions like Node, but ExecuteProcess? Yes.
    # However, 'condition' expects a Condition object (IfCondition).
    
    from launch.conditions import IfCondition
    rviz_process = ExecuteProcess(
        cmd=['rviz2'],
        output='screen',
        condition=IfCondition(open_rviz)
    )

    return LaunchDescription([
        DeclareLaunchArgument('num_drones', default_value='3', description='Number of drones'),
        DeclareLaunchArgument('map_type', default_value='world', description='Map Type'),
        DeclareLaunchArgument('map_file', default_value='city.sdf', description='Map File'),
        DeclareLaunchArgument('open_rviz', default_value='true', description='Open RViz?'),
        
        main_sim,
        rviz_process
    ])

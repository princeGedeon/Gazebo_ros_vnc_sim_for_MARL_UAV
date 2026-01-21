
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node

def launch_setup(context, *args, **kwargs):
    pkg_swarm_sim = get_package_share_directory('swarm_sim')
    
    # Get number of UAVs
    num_uavs = LaunchConfiguration('num_uavs').perform(context)
    try:
        num_uavs = int(num_uavs)
    except ValueError:
        num_uavs = 1
    
    nodes_to_start = []
    
    # Path to Xacro Model
    xacro_file = os.path.join(pkg_swarm_sim, 'assets', 'models', 'x500_sensors.sdf.xacro')
    
    # Bridge arguments accumulator
    bridge_args = [
        # Clock (Global)
        '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
    ]
    
    # Spawn loop
    for i in range(num_uavs):
        name = f"uav_{i}"
        
        # Position offset: Line them up along X axis
        x_pos = float(i) * 2.0
        
        # Process Xacro to generate unique SDF for this UAV
        robot_desc = Command(['xacro ', xacro_file, ' namespace:=', name])

        # Spawn Node using the generated XML string
        spawn_node = Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-world', 'urban_city',
                '-name', name,
                '-string', robot_desc,
                '-x', str(x_pos), '-y', '0', '-z', '1.0'
            ],
            output='screen'
        )
        nodes_to_start.append(spawn_node)

        # Robot State Publisher - Publishes TF and robot_description
        # We need to republish the description so RViz can pick it up
        rsp_node = Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            namespace=name,
            output='screen',
            parameters=[{
                'robot_description': robot_desc,
                'use_sim_time': True,
                'frame_prefix': f'{name}/'
            }]
        )
        nodes_to_start.append(rsp_node)
        
        # Bridge Topics for this UAV
        bridge_args.extend([
            f'/model/{name}/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            f'/model/{name}/odometry@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            
            # Sensors
            f'/model/{name}/lidar/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked',
            # Bridge Sonar as LaserScan (or PointCloud2 if preferred, but Scan is closer to range)
            # Actually, the sensor type is gpu_lidar, so it outputs PointCloudPacked or LaserScan depending on configuration.
            # In 'gpu_lidar' simulation, if we want LaserScan, we need to treat it as such.
            # But 3D Lidar -> PointCloud2.
            # The 'Sonar' with small FOV is also a lidar. Let's bridge it as PointCloud2 for generic vis,
            # OR as LaserScan if we assume it's flat. The cone is 3D.
            f'/model/{name}/sonar/range@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked',
            
            f'/model/{name}/camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            f'/model/{name}/camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
            
            # TF Bridge: Publish all link poses from Gz to ROS TF
            f'/model/{name}/pose@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V',
        ])
        
    # Create single bridge node
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=bridge_args,
        output='screen'
    )
    nodes_to_start.append(bridge)
    
    # TF: Publish Map -> World static transform
    map_to_world_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'world'],
        output='screen'
    )
    nodes_to_start.append(map_to_world_tf)
    
    return nodes_to_start

def generate_launch_description():
    pkg_swarm_sim = get_package_share_directory('swarm_sim')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Arguments
    num_uavs_arg = DeclareLaunchArgument(
        'num_uavs',
        default_value='1',
        description='Number of UAVs to spawn'
    )

    # 1. World
    world_file = os.path.join(pkg_swarm_sim, 'assets', 'worlds', 'city.sdf')
    
    # 2. Gazebo
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f"-r {world_file}"}.items(),
    )

    return LaunchDescription([
        num_uavs_arg,
        gz_sim,
        OpaqueFunction(function=launch_setup)
    ])

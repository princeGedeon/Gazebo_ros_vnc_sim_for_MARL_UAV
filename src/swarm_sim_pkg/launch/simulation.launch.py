
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
    # Path to Xacro Model (Uniformized)
    xacro_file = os.path.join(pkg_swarm_sim, 'assets', 'models', 'x500_sensors.sdf.xacro')
    
    # Bridge arguments accumulator
    bridge_args = [
        # Clock (Global)
        '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
    ]
    
    # Remappings for the bridge
    remappings = []

    # Spawn loop
    for i in range(num_uavs):
        name = f"uav_{i}"
        
        # Position offset: Line them up along X axis
        x_pos = float(i) * 2.0
        
        # Process Xacro to generate unique SDF for this UAV
        # strict_mode=true to ensure safety
        robot_desc = Command(['xacro ', xacro_file, ' namespace:=', name])

        # Spawn Node using the generated XML string
        spawn_node = Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-world', 'urban_city',
                '-name', name,
                '-string', robot_desc,
                '-x', str(x_pos), '-y', '0', '-z', '0.24'
            ],
            output='screen'
        )
        nodes_to_start.append(spawn_node)

        # Robot State Publisher - Needed for RViz Visuals and TF
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
            f'/model/{name}/sonar/range@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked',
            f'/model/{name}/camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            f'/model/{name}/camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
            
            # Down Camera
            f'/model/{name}/down_camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            f'/model/{name}/down_camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
            f'/model/{name}/imu@sensor_msgs/msg/Imu@gz.msgs.IMU',
            
            # TF Bridge: Publish all link poses from Gz to ROS TF
            # Gz Topic: /model/uav_X/pose (Pose_V) -> ROS Topic: /tf (TFMessage)
            f'/model/{name}/pose@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V',
        ])

        # Remappings for standard topic names (optional but good for consistency)
        # Note: simulation.launch.py didn't have remappings before for bridge arg loop,
        # but `ros_gz_bridge` topics with @ syntax usually don't need remapping if using default.
        # However, to be uniform with multi_ops:
        remappings.extend([
            (f"/model/{name}/lidar/points", f"/{name}/sensors/lidar"),
            (f"/model/{name}/sonar/range", f"/{name}/sensors/sonar"),
            (f"/model/{name}/camera/image_raw", f"/{name}/camera/image_raw"),
            (f"/model/{name}/camera/camera_info", f"/{name}/camera/camera_info"),
            (f"/model/{name}/down_camera/image_raw", f"/{name}/down_camera/image_raw"),
            (f"/model/{name}/down_camera/camera_info", f"/{name}/down_camera/camera_info"),
            (f"/model/{name}/imu", f"/{name}/sensors/imu"),
            (f"/model/{name}/pose", "/tf")
        ])
        
        # TF Fix: We need to handle TFs.
        # Ideally we bridge /model/{name}/tf to /tf, but Gazebo OdometryPublisher mainly handles odom->base_link.
        # For the users "Could not transform to [map]" error:
        # We need a static transform map -> world (or map -> uav_X/odom).
        # We will add that globally once.
        
    # Create single bridge node
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=bridge_args,
        remappings=remappings,
        output='screen'
    )
    nodes_to_start.append(bridge)
    
    # TF: Publish Map -> World static transform to satisfy RViz "map" frame requirement
    map_to_world_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'world'],
        output='screen'
    )
    nodes_to_start.append(map_to_world_tf)
    
    from launch.actions import TimerAction

    # Retain the bridge and TF publisher as immediate or also delayed? 
    # Better to delay everything to be safe, especially bridge which needs topics.
    
    return [
        TimerAction(
            period=15.0,
            actions=nodes_to_start
        )
    ]

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

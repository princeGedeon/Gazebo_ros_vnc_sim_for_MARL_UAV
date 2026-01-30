
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def launch_setup(context, *args, **kwargs):
    pkg_swarm_sim = get_package_share_directory('swarm_sim')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Get Args
    num_drones = int(context.launch_configurations['num_drones'])
    map_type = context.launch_configurations['map_type'] # 'world' or 'model'
    map_file = context.launch_configurations['map_file'] # 'city.sdf' or path

    # 1. World Logic
    gz_args = ""
    world_path = ""
    
    # helper to find asset deep in nested install if needed
    def find_asset(subpath):
        # Check standard path
        p1 = os.path.join(pkg_swarm_sim, subpath)
        if os.path.exists(p1): return p1
        # Check nested path (due to recursive glob in setup.py)
        p2 = os.path.join(pkg_swarm_sim, 'swarm_sim', subpath)
        if os.path.exists(p2): return p2
        return p1 # Default return

    if map_type == 'world':
        # If absolute path, use it, else lookup in swarm_sim assets
        if map_file.startswith('/'):
            world_path = map_file
        else:
            world_path = find_asset(os.path.join('assets', 'worlds', map_file))
        gz_args = f"-r {world_path}"
    else:
        # map_type == 'model' -> Load empty.sdf
        world_path = find_asset(os.path.join('assets', 'worlds', 'empty.sdf'))
        
        # Fallback to city if empty missing (should not happen now)
        if not os.path.exists(world_path):
             print(f"WARNING: empty.sdf not found at {world_path}, falling back to city.sdf")
             world_path = find_asset(os.path.join('assets', 'worlds', 'city.sdf'))
        
        gz_args = f"-r {world_path}"

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': gz_args}.items(),
    )

    nodes = [gz_sim]

    # If map_type is model, we assume we need to spawn it into the empty world
    if map_type == 'model':
        spawn_map = Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-name', 'external_map',
                '-file', map_file, # Expecting absolute path for external model
                '-x', '0', '-y', '0', '-z', '0'
            ],
            output='screen'
        )
        nodes.append(spawn_map)

    # 2. Global TFs & Ground Station
    bridge_tf = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                   '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'],
        output='screen'
    )
    nodes.append(bridge_tf)

    # 2.1 Static TF (map -> world) for RViz
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'world'],
        output='screen'
    )
    nodes.append(static_tf)

    # Ground Stations Layout (Simple Grid/List)
    num_stations = int(context.launch_configurations['num_stations'])
    station_positions = [
        (0.0, 0.0),      # Center
        (10.0, 0.0),     # Right
        (-10.0, 0.0),    # Left
        (0.0, 10.0),     # Top
        (0.0, -10.0),    # Bottom
        (10.0, 10.0),
        (-10.0, -10.0),
        (10.0, -10.0),
        (-10.0, 10.0)
    ]
    
    gs_file = find_asset(os.path.join('assets', 'models', 'ground_station.sdf'))
    
    for i in range(min(num_stations, len(station_positions))):
        pos = station_positions[i]
        spawn_gs = Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-name', f'ground_station_{i}',
                '-file', gs_file,
                '-x', str(pos[0]), '-y', str(pos[1]), '-z', '0'
            ],
            output='screen'
        )
        nodes.append(spawn_gs)

    # 3. Spawn Drones
    # Path to Xacro Model
    # Path to Xacro Model (SDF for Gazebo)
    xacro_file = os.path.join(pkg_swarm_sim, 'assets', 'models', 'x500_sensors.sdf.xacro')
    # Path to URDF Model (for Robot State Publisher / RViz)
    urdf_file = os.path.join(pkg_swarm_sim, 'assets', 'models', 'x500.urdf.xacro')

    for i in range(num_drones):
        name = f"uav_{i}"
        
        # Position offset: Line them up along X axis
        # Start on ground (z=0.1) or low hover? User asked for ground start or "not floating in air".
        # x500 origin is at center, legs are below. z=0.25 (approx) might be needed to sit on ground.
        if num_stations > 1:
            # Spaced out logic: Match station positions
            # Assuming station_positions logic: 
            # (-10, 0), (0, 0), (10, 0) for 3 stations
            if i < len(station_positions):
                x_pos = station_positions[i][0]
                y_pos = station_positions[i][1]
            else:
                x_pos = float(i) * 2.0
                y_pos = 0.0
        else:
             # Standard line
             x_pos = float(i) * 2.0
             y_pos = 0.0
        
        # Process Xacro (SDF)
        robot_desc = Command(['xacro ', xacro_file, ' namespace:=', name])
        # Process URDF (for RSP)
        robot_desc_urdf = Command(['xacro ', urdf_file, ' namespace:=', name])

        # Spawn
        spawn = Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-name', name,
                '-string', robot_desc,
                '-x', str(x_pos), '-y', str(y_pos), '-z', '0.24' # Start on ground
            ],
            output='screen'
        )
        nodes.append(spawn)



        # Odom TF Broadcaster (REMOVED: Causing conflict with Bridge TF)
        # We rely on ros_gz_bridge to publish /model/{name}/pose -> /tf
        # tf_broadcaster = Node(...)
        

        # Robot State Publisher - Needed for RViz Visuals and TF
        rsp_node = Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            namespace=name,
            output='screen',
            parameters=[{
                'robot_description': ParameterValue(robot_desc_urdf, value_type=str),
                'use_sim_time': True
            }]
        )
        nodes.append(rsp_node)
        
        # Bridge
        bridge = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name=f'bridge_{name}',
            arguments=[
                # Minimal Bridge for SLAM & Visualization
                f"/model/{name}/lidar/points/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked",
                f"/model/{name}/lidar_down/points/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked",
                f"/model/{name}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
                f"/model/{name}/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
                f"/model/{name}/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
                f"/model/{name}/down_camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
                f"/model/{name}/down_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
                f"/model/{name}/navsat@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat",
                f"/model/{name}/pose@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",
                f"/model/{name}/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry",
                f"/model/{name}/imu@sensor_msgs/msg/Imu[gz.msgs.IMU"
            ],
            parameters=[{'qos_overrides./model': {'reliability': 'best_effort'}}],
            output='screen',
            remappings=[
                # SLAM Inputs
                (f"/model/{name}/cmd_vel", f"/{name}/cmd_vel"),
                (f"/model/{name}/lidar/points/points", f"/{name}/velodyne_points"),
                (f"/model/{name}/lidar_down/points/points", f"/{name}/lidar_down/points"),
                (f"/model/{name}/camera/image_raw", f"/{name}/camera/image_raw"),
                (f"/model/{name}/camera/camera_info", f"/{name}/camera/camera_info"),
                (f"/model/{name}/down_camera/image_raw", f"/{name}/down_camera/image_raw"),
                (f"/model/{name}/down_camera/camera_info", f"/{name}/down_camera/camera_info"),
                (f"/model/{name}/navsat", f"/{name}/gps"),
                # IMU
                (f"/model/{name}/imu", f"/{name}/imu"),
                # Odometry
                (f"/model/{name}/odometry", f"/{name}/odometry"),
                # TF for Ground Truth (RobotModel)
                (f"/model/{name}/pose", "/tf")
            ]
        )
        nodes.append(bridge)


    return nodes

from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, AppendEnvironmentVariable

# ... imports ...

def generate_launch_description():
    pkg_swarm_sim = get_package_share_directory('swarm_sim')
    
    # Standard asset path (now that setup.py is fixed)
    base_assets = os.path.join(pkg_swarm_sim, 'assets')
    
    # Paths to external maps
    ext_maps = os.path.join(base_assets, 'external_maps')
    comp_maps = os.path.join(base_assets, 'external_maps', 'competition_2021add')
    kepco_maps = os.path.join(base_assets, 'external_maps', 'kepco')
    
    return LaunchDescription([
        # Update GZ Resource Path
        AppendEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            os.path.join(base_assets, 'models')
        ),
        AppendEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            ext_maps
        ),
        AppendEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            comp_maps
        ),
        AppendEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            kepco_maps
        ),

        DeclareLaunchArgument('num_drones', default_value='3', description='Number of drones'),
        DeclareLaunchArgument('num_drones', default_value='3', description='Number of drones'),
        DeclareLaunchArgument('num_stations', default_value='3', description='Number of ground stations'),
        DeclareLaunchArgument('map_type', default_value='world', description='world OR model'),
        DeclareLaunchArgument(
        'map_file',
        default_value='generated_city_rich.sdf',
        description='SDF World File'
    ),
        OpaqueFunction(function=launch_setup)
    ])

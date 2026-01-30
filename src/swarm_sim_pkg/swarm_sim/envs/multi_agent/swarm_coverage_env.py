
from pettingzoo import ParallelEnv
from gymnasium import spaces
import numpy as np
import rclpy
import sys
import os
import subprocess
import time

from swarm_sim.common.voxel_manager import VoxelManager  # Keep for SLAM compatibility if needed
from swarm_sim.common.occupancy_grid_2d import OccupancyGrid2D
from swarm_sim.common.grid_viz_2d import Grid2DVisualizer
from swarm_sim.common.rewards import RewardEngine
from swarm_sim.envs.core.uav_base import UAVBase
from swarm_sim.common.viz_utils import VoxelVisualizer

class SwarmCoverageEnv(ParallelEnv):
    """
    PettingZoo Parallel Env for Multi-UAV Cooperative 2D Coverage with Fixed Altitude.
    
    Architecture:
    - RL controls (vx, vy, yaw) for 2D coverage optimization
    - Altitude controller maintains Z = Z_optimal automatically
    - SLAM (mrg_slam) continues to build full 3D maps (unchanged)
    """
    metadata = {"render_modes": ["human"], "name": "swarm_coverage_v0"}

    def __init__(self, num_drones=3, station_config=None, max_steps=1000, 
                 min_height=1.5, max_height=3.5, nfz_config='default', use_cbf=False):
        self.num_drones = num_drones
        self.station_config = station_config
        self.max_steps = max_steps
        
        self.use_cbf = use_cbf # Case 3: Layered CBF
        
        # Safety & Constraints
        self.min_height = min_height
        self.max_height = max_height
        self.nfz_config = nfz_config 
        self.nfz_list = [] 
        
        # Workspace Limits (Ultra Hard Boundary)
        # User Request: "réduis pour il apprend mieux 200m" -> +/- 100m
        self.x_min, self.x_max = -100.0, 100.0
        self.y_min, self.y_max = -100.0, 100.0

        self.possible_agents = [f"uav_{i}" for i in range(self.num_drones)]
        self.agents = self.possible_agents[:]
        
        # 1. 2D Coverage Maps (for RL)
        # Storage Simulation
        self.MAX_STORAGE = 500 # Cell Capacity (2D cells)
        self.agents_storage = {a: 0 for a in self.agents}
        
        # Global Truth (for evaluation/global reward) - Now 2D!
        self.global_map = OccupancyGrid2D(
            x_range=(self.x_min, self.x_max),
            y_range=(self.y_min, self.y_max),
            resolution=0.5
        )
        
        # Central Station Map (Realistic Output - Only updates on offload)
        self.central_map = OccupancyGrid2D(
            x_range=(self.x_min, self.x_max),
            y_range=(self.y_min, self.y_max),
            resolution=0.5
        )
        
        # Local Beliefs (Decentralized) - Each UAV has its own 2D map
        self.local_maps = {
            agent: OccupancyGrid2D(
                x_range=(self.x_min, self.x_max),
                y_range=(self.y_min, self.y_max),
                resolution=0.5
            )
            for agent in self.possible_agents
        }
        
        # Calculate Optimal Altitude (based on sensor specs)
        # LiDAR Down: 15m range, ~30° FOV
        # Calculate Optimal Altitude (based on sensor specs)
        # LiDAR Down: 15m range, ~30° FOV
        # z_raw = self.global_map.calculate_optimal_altitude(...)
        
        # CRITICAL: User requested fixed altitude of 2.5m for street-level coverage
        self.z_optimal = 2.5
        
        # Override clamp check since we set it explicitly
        print(f"[SwarmEnv] ✓ Optimal Altitude Fixed Z = {self.z_optimal:.2f}m (User Request)")
        
        self.reward_engine = RewardEngine()
        
        # 2. Spaces
        # Action: 2D Velocity + Yaw (vz is automatic)
        # OLD: (vx, vy, vz, yaw) = 4D
        # NEW: (vx, vy, yaw) = 3D
        self.action_spaces = {
            agent: spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
            for agent in self.possible_agents
        }
        
        # Observation: Local 2D Map + State
        # OLD: 3D voxel patch (7×7×5 = 245) + state(13) + lidar(16)
        # NEW: 2D grid patch (11×11 = 121) + state(10) + lidar(16)
        self.local_map_dim_2d = (11 * 11)  # 2D patch
        # State: x, y, z_error, vx, vy, battery, dist_station, yaw, neighbors, storage = 10
        # LiDAR: 16 rays
        # Map: 11×11 = 121
        # Total: 10 + 16 + 121 = 147
        obs_dim = 10 + 16 + self.local_map_dim_2d
        self.observation_spaces = {
            agent: spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)
            for agent in self.possible_agents
        }
        
        # 3. ROS
        if not rclpy.ok():
            rclpy.init()
        self.node = rclpy.create_node("swarm_coverage_node")
        self.viz = VoxelVisualizer()
        
        # 2D Grid Visualizer for RViz
        self.grid_viz = Grid2DVisualizer(self.node, self.global_map, frame_id='map')
        
        # Ground Stations Config (User Request)
        # station_config can be an int (count) or list of [x, y]
        if station_config is None:
            # Default: 3 Stations aligned on X-axis (10m spacing)
            self.station_positions = np.array([
                [-10.0, 0.0],
                [0.0, 0.0],
                [10.0, 0.0]
            ])
        elif isinstance(station_config, int):
            # Generate N random stations (simple heuristic)
            self.station_positions = np.random.uniform(-15, 15, size=(station_config, 2))
        elif isinstance(station_config, list) or isinstance(station_config, np.ndarray):
            self.station_positions = np.array(station_config)
        else:
             self.station_positions = np.array([[0.0, 0.0]])

        self.uavs = {}
        for agent in self.possible_agents:
            # Assuming model names are uav_0, uav_1... in Gazebo
            self.uavs[agent] = UAVBase(self.node, agent_id=agent, namespace="")

    # --- PettingZoo API Compliance ---
    def observation_space(self, agent):
        return self.observation_spaces[agent]

    def action_space(self, agent):
        return self.action_spaces[agent]

    def save_occupancy_map(self, filename="outputs/associative_map.npy"):
        """Save the Central Station Map. Supports .npy, .laz, .ply"""
        # Ensure output directory exists
        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        pc = self.central_map.get_sparse_pointcloud() # (N, 3) Ints (Indices)
        
        # Convert Indices to Meters (Local Frame)
        px = self.central_map.x_min + (pc[:,0] + 0.5) * self.central_map.resolution
        py = self.central_map.y_min + (pc[:,1] + 0.5) * self.central_map.resolution
        pz = self.central_map.z_min + (pc[:,2] + 0.5) * self.central_map.resolution
        
        points_metric = np.stack([px, py, pz], axis=1)

        if filename.endswith(".npy"):
            np.save(filename, pc) # Save INDICES (Raw Data)
            
        elif filename.endswith(".laz") or filename.endswith(".las"):
            try:
                import laspy
                import utm
                
                # Create LAS Header
                header = laspy.LasHeader(point_format=3, version="1.2")
                
                # Check for Georeferencing Origin (Default: Paris)
                lat0 = getattr(self, 'geo_origin_lat', 48.8566)
                lon0 = getattr(self, 'geo_origin_lon', 2.3522)
                alt0 = getattr(self, 'geo_origin_alt', 0.0)
                
                # Convert Origin to UTM
                easting0, northing0, zone_num, zone_letter = utm.from_latlon(lat0, lon0)
                
                # Apply Offset to Points (Local (0,0) -> UTM Origin)
                # x (Right) -> Easting ? Verify ENU vs NED
                # Sim is usually ENU: x=East, y=North, z=Up or similar.
                # Assuming ENU for standard ROS/Gazebo.
                
                utm_easting = easting0 + points_metric[:, 0]
                utm_northing = northing0 + points_metric[:, 1]
                abs_altitude = alt0 + points_metric[:, 2]
                
                # Configure Header Scales/Offsets for high precision
                # UTM coordinates are large (millions), so we need offsets.
                header.offsets = [np.min(utm_easting), np.min(utm_northing), np.min(abs_altitude)]
                header.scales = [0.01, 0.01, 0.01] # 1cm precision
                
                header.add_extra_dims([
                    laspy.ExtraBytesParams(name="voxel_x", type=np.int32),
                    laspy.ExtraBytesParams(name="voxel_y", type=np.int32),
                    laspy.ExtraBytesParams(name="voxel_z", type=np.int32)
                ])
                
                las = laspy.LasData(header)
                las.x = utm_easting
                las.y = utm_northing
                las.z = abs_altitude
                
                # Store Indices as extra fields
                las.voxel_x = pc[:, 0]
                las.voxel_y = pc[:, 1]
                las.voxel_z = pc[:, 2]
                
                las.write(filename)
                print(f"[SwarmEnv] Saved Georeferenced LAZ to {filename} (Origin: {lat0}, {lon0} | Zone: {zone_num}{zone_letter})")
                
            except ImportError as e:
                print(f"[SwarmEnv] Error: {e}. saving as .npy instead.")
                np.save(filename.replace(".laz", ".npy"), pc)

        elif filename.endswith(".ply"):
             # Simple PLY ASCII writer
             with open(filename, 'w') as f:
                 f.write("ply\nformat ascii 1.0\n")
                 f.write(f"element vertex {len(points_metric)}\n")
                 f.write("property float x\nproperty float y\nproperty float z\n")
                 f.write("end_header\n")
                 for p in points_metric:
                     f.write(f"{p[0]:.3f} {p[1]:.3f} {p[2]:.3f}\n")
             print(f"[SwarmEnv] Saved PLY to {filename}")
        
        else:
            # Default to npy
            np.save(filename, pc)
        
        full_path = os.path.abspath(filename)
        print(f"[SwarmEnv] Central Station Map (Sparse) saved to: {full_path} | shape: {pc.shape}")
        # Hint for User
        print(f"[SwarmEnv] To visualize in Python: data = np.load('{full_path}')")

    def reset(self, seed=None, options=None):
        self.agents = self.possible_agents[:]
        
        # 0. HARD RESET POSES (Fix Frozen/Crash Issue)
        self._reset_poses()
        
        self.global_map.reset()

        for m in self.local_maps.values():
            m.reset()
        self.step_count = 0
        
        # 2. Generate No-Fly Zones (NFZ)
        self.nfz_list = []
        if self.nfz_config == 'default':
            # Create 1 random NFZ (Red Zone)
            # Avoid origin (0,0) where stations/drones usually are
            x = np.random.choice([-10, 10]) + np.random.uniform(-3, 3)
            y = np.random.choice([-10, 10]) + np.random.uniform(-3, 3)
            r = np.random.uniform(2.0, 5.0) # Random surface area
            self.nfz_list.append((x, y, r))
            
        elif isinstance(self.nfz_config, int):
            # Generate N random NFZs
            count = self.nfz_config
            for _ in range(count):
                x = np.random.uniform(-15, 15)
                y = np.random.uniform(-15, 15)
                # Ensure not too close to center (Station)
                if np.linalg.norm([x, y]) < 5.0:
                    x += 10 # Shift away
                    
                r = np.random.uniform(2.0, 5.0)
                self.nfz_list.append((x, y, r))
                
        elif isinstance(self.nfz_config, list):
            self.nfz_list = self.nfz_config[:]
        
        # Wait for data
        rclpy.spin_once(self.node, timeout_sec=0.1)
        
        # Detailed Logging (User Request)
        print(f"\n[SwarmEnv] Reset Complete using Seed: {seed}")
        print(f"[SwarmEnv] Active Drones: {self.num_drones} | Agents: {self.possible_agents}")
        if self.step_count == 0:
            print(f"[SwarmEnv] Map Config: {self.global_map.__class__.__name__} | Bounds: ({self.global_map.x_min}, {self.global_map.x_max})")
            print(f"[SwarmEnv] Station Mode: {self.station_config}")
            print(f"[SwarmEnv] Altitude Limits: [{self.min_height}, {self.max_height}]")
        print(f"[SwarmEnv] Ground Stations: {len(self.station_positions)}")
        print(f"[SwarmEnv] Active NFZs: {len(self.nfz_list)}")
        
        # Ensure Battery Reset (Start at 60% to encourage finding stations early)
        for agent in self.agents:
            self.uavs[agent].battery.reset()
            self.uavs[agent].battery.current_charge = self.uavs[agent].battery.capacity * 0.6
        
        # Wait a bit for settling
        rclpy.spin_once(self.node, timeout_sec=0.5)
        
        # 3. AUTO TAKEOFF (Fix Frozen Issue)
        self._auto_takeoff()
        
        print("[SwarmEnv] Reset Done. Drones Airborne. (Float32 Fix Applied)")
        
        # Explicitly cast to float32 to silence Gymnasium warnings
        observations = {
            agent: self._get_obs(agent).astype(np.float32) 
            for agent in self.agents
        }
        infos = {agent: {} for agent in self.agents}
        
        # DEBUG: Strict Check for Observation Space Mismatch
        for agent, obs in observations.items():
            if not self.observation_space(agent).contains(obs):
                print(f"[SwarmEnv] CRITICAL WARNING: Agent {agent} Obs mismatch!")
                print(f"  - Obs Shape: {obs.shape}")
                print(f"  - Space Shape: {self.observation_space(agent).shape}")
                print(f"  - Space Dtype: {self.observation_space(agent).dtype}")
                # Check bounds
                low = self.observation_space(agent).low
                high = self.observation_space(agent).high
                if np.any(obs < low):
                     print(f"  - Values below LOW detected! Count: {np.sum(obs < low)}")
                if np.any(obs > high):
                     print(f"  - Values above HIGH detected! Count: {np.sum(obs > high)}")
                if np.any(np.isnan(obs)):
                     print(f"  - NaNs detected!")
                if np.any(np.isinf(obs)):
                     print(f"  - Infs detected!")
        
        return observations, infos

    def _reset_poses(self):
        """
        Force-reset all drones to start positions using Gazebo Service.
        This fixes the issue where drones stay crashed/tipped over.
        """
        print("[SwarmEnv] Resetting Poses via Gazebo Service...")
        
        # 0. CRITICAL: Wait for Gazebo to be Ready
        print("[SwarmEnv] Waiting for Gazebo services to become available...")
        max_init_wait = 30  # Max 30 seconds
        gazebo_ready = False
        for wait_attempt in range(max_init_wait):
            try:
                cmd_check = ". /opt/ros/jazzy/setup.sh && gz service -l"
                res = subprocess.run(cmd_check, shell=True, capture_output=True, text=True, timeout=2)
                if res.returncode == 0 and "/world/" in res.stdout:
                    gazebo_ready = True
                    print(f"[SwarmEnv] Gazebo ready after {wait_attempt+1}s")
                    break
            except:
                pass
            time.sleep(1)
        
        if not gazebo_ready:
            print("[SwarmEnv] WARNING: Gazebo services not detected. Reset may fail.")
        
        # 1. Dynamically find World Name
        world_name = "urban_city_rich" # Default
        try:
             # List services to find /world/<name>/set_pose
             cmd_list = ". /opt/ros/jazzy/setup.sh && gz service -l"
             res = subprocess.run(cmd_list, shell=True, capture_output=True, text=True)
             if res.returncode == 0:
                 for line in res.stdout.split('\n'):
                     if "/set_pose" in line and "/world/" in line:
                         # Extract world name: /world/NAME/set_pose
                         parts = line.split('/')
                         # parts[0]='', parts[1]='world', parts[2]=NAME, parts[3]='set_pose'
                         if len(parts) >= 4:
                             world_name = parts[2]
                             # print(f"[SwarmEnv] Auto-detected World Name: {world_name}")
                             break
        except Exception as e:
             print(f"[SwarmEnv] Warning: Could not detect world name ({e}). Using default: {world_name}")

        # 2. Reset Loop
        args_setup = ". /opt/ros/jazzy/setup.sh"
        
        for i, agent in enumerate(self.agents):
            if i < len(self.station_positions):
                pos = self.station_positions[i]
            else:
                pos = [0, 0]
                
            # Spawn EXACTLY on station (User Request: "uav doit appratere sur ça")
            # Station height is low, so z=0.2 is fine to sit on top.
            x, y = pos[0], pos[1]
            z = 0.2
            
            # Construct CLI command
            # gz service -s /world/<world_name>/set_pose ...
            
            cmd = f"{args_setup} && gz service -s /world/{world_name}/set_pose --reqtype gz.msgs.Pose_V --reptype gz.msgs.Boolean --timeout 5000 --req 'pose: {{name: \"{agent}\", position: {{x: {x}, y: {y}, z: {z}}}, orientation: {{x: 0, y: 0, z: 0, w: 1}} }}'"
            
            # Retry mechanism
            success = False
            for attempt in range(3):
                try:
                    result = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0 and "true" in result.stdout.lower():
                         success = True
                         break
                    else:
                        # Wait longer before retry (Gazebo may be slow)
                        time.sleep(2.0)
                except Exception as e:
                    print(f"[SwarmEnv] Reset attempt {attempt+1} exception: {e}")
                    time.sleep(2.0)
            
            if not success:
                 print(f"[SwarmEnv] Reset Failed for {agent} after 3 attempts.")
                 if 'result' in locals():
                     print(f"   Last STDOUT: {result.stdout[:200]}")  # Show first 200 chars
                     print(f"   Last STDERR: {result.stderr[:200]}")
            else:
                 pass # Success
            
        # Wait for physics to settle
        time.sleep(0.5)
                
        # Wait for physics to settle
        time.sleep(0.5)

    def _auto_takeoff(self):
        """
        Blindly send UP commands to ensure drones are not on the ground
        when RL takes over.
        """
        print("[SwarmEnv] Auto-Takeoff Sequence Initiated...")
        takeoff_cmd = {
            agent: np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32) # Pure Up
            for agent in self.agents
        }
        
        # Run for 0.5 seconds (approx 5-10 steps) - Reduced from 1.5s to prevent overshoot
        for _ in range(10):
             # Just apply action, no step logic
             for agent in self.agents:
                 self.uavs[agent].apply_action(takeoff_cmd[agent])
             rclpy.spin_once(self.node, timeout_sec=0.05)
             time.sleep(0.05)

    def _enforce_sandbox(self, agent, action):
        """
        HARD CONSTRAINTS (Sandbox).
        Prevent drone from ever leaving the playable area.
        Overrides any RL or CBF command if violating safety.
        """
        uav = self.uavs[agent]
        pos = uav.position
        vel_cmd = action[:3]
        
        safe_action = action.copy()
        
        # 1. World Bounds (Hard Stop)
        limit = 18.0 # Stricter buffer (Max 20.0)
        
        # X Axis
        if pos[0] > limit and vel_cmd[0] > 0: safe_action[0] = -2.0 # Stronger Push Back
        elif pos[0] < -limit and vel_cmd[0] < 0: safe_action[0] = 2.0
        
        # Y Axis
        if pos[1] > limit and vel_cmd[1] > 0: safe_action[1] = -2.0
        elif pos[1] < -limit and vel_cmd[1] < 0: safe_action[1] = 2.0
        
        # Z Axis (Ground safety)
        if pos[2] < 0.5 and vel_cmd[2] < 0: \
            safe_action[2] = 1.0 # Anti-Crash
        elif pos[2] > (self.max_height): 
            # AGGRESSIVE CLAMP: If above max height, force DOWN hard.
            # Regardless of what RL or PID wants.
            safe_action[2] = -2.0 # Force descent
            # print(f"[{agent}] ⚠️ High Altitude Clamp! Z={pos[2]:.2f} > {self.max_height} -> Vz=-2.0")
        
        # EMERGENCY TELEPORT (If simple physics pushed it out anyway)
        # If > 21.0, just reset to 0,0,10 (Penalty handled by out_of_bounds reward)
        if abs(pos[0]) > 21.0 or abs(pos[1]) > 21.0:
             print(f"[{agent}] ⚠️ ESCAPED WORLD! Teleporting back to center.")
             # We can't easily teleport inside step() without service call.
             # Just kill velocity hard.
             safe_action = np.array([0., 0., 0., 0.], dtype=np.float32)
        
        return safe_action

    def _apply_cbf(self, agent, action):
        """
        Simple Control Barrier Function (CBF) Filter.
        Intervenes if action would push drone out of bounds or into NFZ.
        """
        uav = self.uavs[agent]
        pos = uav.position
        vel_cmd = action[:3] # vx, vy, vz
        
        safe_action = action.copy()
        
        # 1. Boundary CBF (Box)
        # h(x) = dist_to_boundary
        # h_dot >= -gamma * h(x)
        margin = 2.0 
        
        # Check X
        if pos[0] > (self.x_max - margin) and vel_cmd[0] > 0:
            safe_action[0] = -0.5 # Repel
        if pos[0] < (self.x_min + margin) and vel_cmd[0] < 0:
            safe_action[0] = 0.5 
            
        # Check Y
        if pos[1] > (self.y_max - margin) and vel_cmd[1] > 0:
            safe_action[1] = -0.5
        if pos[1] < (self.y_min + margin) and vel_cmd[1] < 0:
            safe_action[1] = 0.5 
            
        # Check Z (Altitude)
        if pos[2] > (self.max_height - margin) and vel_cmd[2] > 0:
             safe_action[2] = -0.5
        if pos[2] < (self.min_height + 1.0) and vel_cmd[2] < 0:
             # Allowed if near station?
             dists = np.linalg.norm(self.station_positions - pos[:2], axis=1)
             if np.min(dists) > 3.0:
                 safe_action[2] = 0.5 # Force UP
                 
        return safe_action

    def _altitude_controller(self, agent):
        """
        PID controller to automatically maintain altitude at Z_optimal.
        
        Special Cases:
        - At station: Descend to Z=0.5m for landing/recharging
        - Otherwise: Maintain Z = Z_optimal (e.g. 7.5m)
        
        Returns:
            vz: Vertical velocity command [-1.0, 1.0]
        """
        uav = self.uavs[agent]
        pos = uav.position
        
        # Find nearest station
        dists = np.linalg.norm(self.station_positions - pos[:2], axis=1)
        min_dist = np.min(dists)
        
        # Determine target altitude
        if min_dist < 2.5:
            # At station: Land for recharge
            target_z = 0.5
        else:
            # Normal flight: Maintain optimal altitude
            target_z = self.z_optimal
        
        # PID Controller
        # P gain: Proportional to error
        # D gain: Damping based on current vertical velocity
        error_z = target_z - pos[2]
        
        # Tuned for ~0.5s settling time (REDUCED GAINS to prevent overshoot)
        kp = 1.0  # Was 1.5
        kd = 0.5  # Was 0.3
        
        # Deadband / Lock (Stability Fix)
        if abs(error_z) < 0.15: # If within 15cm
            # Lock altitude (Hover)
            # If we send 0.0, the drone should hover if gravity compensation is internal
            # or if it's velocity control.
            vz = 0.0
        else:
            vz = kp * error_z + kd * (-uav.velocity[2])
        
        # Clamp to action space limits (Reduce max vertical speed)
        vz = np.clip(vz, -0.5, 0.5) # Was -1.0, 1.0
        
        return vz

    def _check_auto_rtb(self, agent, current_action):
        """
        Calculates if the agent MUST return to base now to survive.
        If current_battery < (dist_to_station * energy_per_m * safety_factor),
        Override action to fly to nearest station.
        """
        uav = self.uavs[agent]
        pos = uav.position
        bat_level = uav.battery.get_percentage()
        
        # 1. Find Nearest Station
        dists = np.linalg.norm(self.station_positions - pos[:2], axis=1)
        nearest_idx = np.argmin(dists)
        dist = dists[nearest_idx]
        station_pos = self.station_positions[nearest_idx]
        
        # 2. Estimate Energy Needed
        # We know move_cost ~ 0.3 * speed. Max speed ~ 1.0. 
        # So cost per meter ~ 0.3% of capacity? 
        # Actually in uav_base: consume(norm(vel)*0.3 + 0.002)
        # Capacity is 100.
        # So 1m @ 1m/s costs 0.3 units. 0.3 / 100 = 0.003 (0.3%)
        # Let's say we need 0.5% per meter to be safe (headwinds, startup, etc)
        energy_per_meter = 0.005 # 0.5% battery per meter
        buffer = 0.05 # 5% buffer for landing/maneuvers
        
        required_bat = (dist * energy_per_meter) + buffer
        
        # 3. Check Condition
        if bat_level < required_bat:
            # TRIGGER RTB
            # print(f"[{agent}] ⚠️ AUTO-RTB TRIGGERED! Bat: {bat_level:.2f} < Req: {required_bat:.2f} (Dist: {dist:.1f}m)")
            
            # Compute Vector to Station
            # Target is Station (x,y) + Altitude (2.5m max)
            # Simple Logic: Fly at current height (or safe height) towards station.
            
            target = np.array([station_pos[0], station_pos[1], 2.5]) 
            
            # If we are close (2D), drop down
            if dist < 1.0:
                 target[2] = 0.5 # Landing
            
            # 1. Team Coverage (Positive Driver)
            # GLOBAL COVERAGE OBJECTIVE: Maximize total area explored
            global_coverage_ratio = self.global_map.get_coverage_ratio()
            r_global_coverage = global_coverage_ratio * 100.0  # Scale: 0-100 for full coverage
            
            # Team coverage (incremental new discoveries)
            # Assuming coverage_new and coverage_old are defined elsewhere or need to be defined
            # For now, using placeholders. This part might need context from the user.
            coverage_new = 0 # Placeholder
            coverage_old = 1 # Placeholder to avoid division by zero
            coverage_increment = coverage_new / max(1, coverage_old)
            r_team_coverage = coverage_increment * 50.0  # Incentive for discovering new areas
            
            # Combined coverage reward
            r_coverage = r_global_coverage * 0.3 + r_team_coverage * 0.7  # Blend global + local # P=1
            
            # P Controller
            err = target - pos
            vel_cmd = err * 1.0 # P=1
            
            # Clamp velocity
            speed = np.linalg.norm(vel_cmd)
            if speed > 1.0:
                vel_cmd = (vel_cmd / speed) * 1.0
                
            # Construct 4D action
            rtb_action = np.array([vel_cmd[0], vel_cmd[1], vel_cmd[2], 0.0], dtype=np.float32)
            return rtb_action, True
            
        return current_action, False

    def step(self, actions):
        self.step_count += 1
        
        # Apply Actions
        for agent, action in actions.items():
            if agent in self.uavs:
                # === NEW: 2D+Z ARCHITECTURE ===
                # RL provides 3D action: [vx, vy, yaw]
                # Altitude controller adds vz automatically
                
                # 0. CHECK BATTERY DEATH
                if self.uavs[agent].battery.is_empty():
                     # CRITICAL: Dead Battery -> Fall (override everything)
                     # User Request: "Cut motors" -> Simulate free fall constraints
                     final_action = np.array([0.0, 0.0, -20.0, 0.0], dtype=np.float32)
                else:
                    # Extract RL action (3D)
                    vx_rl = action[0]
                    vy_rl = action[1]
                    yaw_rl = action[2]
                    
                    # Calculate vz automatically
                    vz_auto = self._altitude_controller(agent)
                    
                    # Construct full 4D action
                    action_4d = np.array([vx_rl, vy_rl, vz_auto, yaw_rl], dtype=np.float32)
                    
                    # Apply safety filters (CBF or Sandbox)
                    if self.use_cbf:
                        # CASE 3: LAYERED CBF
                        final_action = self._apply_cbf(agent, action_4d)
                    else:
                        final_action = action_4d
                    
                    # --- AUTO-RTB OVERRIDE (User Request) ---
                    # If Auto-RTB takes over, it calculates full 4D (including vz)
                    rtb_action, is_rtb_active = self._check_auto_rtb(agent, final_action)
                    if is_rtb_active:
                        final_action = rtb_action  # RTB overrides altitude controller
                    # ----------------------------------------
                    
                    # ALWAYS ENFORCE SANDBOX (Final safety layer)
                    if not self.uavs[agent].battery.is_empty():
                        final_action = self._enforce_sandbox(agent, final_action)
                
                # DEBUG: Watch for Runaway Drones
                if self.uavs[agent].position[2] > 5.0:
                     print(f"[{agent}] CRITICAL HIGH ALTITUDE: {self.uavs[agent].position[2]:.2f}m. Cmd: {final_action}")

                self.uavs[agent].apply_action(final_action)
                
        # Step World
        rclpy.spin_once(self.node, timeout_sec=0.1)
        
        # Update Logic
        # 1. Update each agent's local 2D map and the global map
        uav_positions = {}
        for agent in self.agents:
            uav = self.uavs[agent]
            pos = uav.position
            uav_positions[agent] = pos
            
            # === NEW: 2D MAP UPDATE ===
            # Extract agent ID (e.g., "uav_0" -> 0)
            agent_id = int(agent.split('_')[1])
            
            # 1. Mark current position as visited (2D projection)
            self.local_maps[agent].update_from_position(agent_id, pos[0], pos[1])
            self.global_map.update_from_position(agent_id, pos[0], pos[1])
            
            # 2. Update from LiDAR hits (project 3D points to 2D)
            try:
                hits_world = uav.get_transformed_down_lidar()
                if hits_world is not None and len(hits_world) > 0:
                    # Project to 2D and update (OccupancyGrid2D handles projection internally)
                    self.local_maps[agent].update_from_pointcloud(hits_world, uav_id=agent_id)
                    self.global_map.update_from_pointcloud(hits_world, uav_id=agent_id)
            except Exception as e:
                # Gracefully handle parsing errors
                if self.step_count % 100 == 0:
                    print(f"[{agent}] Warning: Lidar parsing failed: {e}")


        # 2. Decentralized Map Merging (Swarm-SLAM Logic)
        # Verify connectivity
        comm_range = 5.0 # meters
        merged_pairs = []
        
        agent_ids = self.agents
        for i in range(len(agent_ids)):
            for j in range(i + 1, len(agent_ids)):
                id1, id2 = agent_ids[i], agent_ids[j]
                pos1 = uav_positions[id1]
                pos2 = uav_positions[id2]
                
                dist = np.linalg.norm(pos1 - pos2)
                if dist < comm_range:
                    # CONTACT! Exchange Maps
                    # Merge Logic: Map A |= Map B
                    new_for_1 = self.local_maps[id1].merge_from(self.local_maps[id2])
                    new_for_2 = self.local_maps[id2].merge_from(self.local_maps[id1])
                    merged_pairs.append((id1, id2))

        # Cooperative coverage: Global gain
        # We calculate global new cells by tracking global map changes
        # But for RL reward, we often use the *Global* progress to encourage teamwork
        
        new_cells = self.global_map.visited_count # This is total, need delta? 
        # Actually in previous code 'update' returned delta.
        # Let's trust global map delta logic if we kept it.
        # For simplicity, let's recalculate delta manually or assume Step-Based reward mechanism
        # Simpler: Reward = Count of (Global Map - Previous Global Map)
        # But we didn't store previous.
        # Let's stick to the previous 'update' return value if we can, or just use current coverage count.
        
        # Re-calc delta from global map isn't easy unless we stored old count.
        # Let's modify VoxelManager to return delta on update? Yes it does.
        # Wait, I called update([pos]) above individually.
        # We need to sum them up or track total.
        
        current_global_count = self.global_map.visited_count
        # Hack: We need a prev_count property in env to calc delta
        if not hasattr(self, 'prev_global_count'): self.prev_global_count = 0
        
        delta_cells = current_global_count - self.prev_global_count
        self.prev_global_count = current_global_count
        
        
        # Global Coverage Reward (Total new cells this step for the TEAM)
        cov_reward_total = delta_cells * 5.0
        # Shared equally or individually? User asked for "objectifs global coverage"
        # Let's give team reward to all
        r_team_coverage = cov_reward_total / len(self.agents)

        rewards = {}
        terminations = {}
        truncations = {}
        infos = {}
        
        for agent in self.agents:
            uav = self.uavs[agent]
            lidar_min = np.min(uav.lidar_ranges) if len(uav.lidar_ranges) > 0 else 10.0
            
            # Extract position and orientation data
            z_height = uav.position[2]
            uav_pos_2d = uav.position[:2]
            
            # Calculate tilt magnitude from IMU (roll, pitch components)
            roll = uav.imu_data[3] if len(uav.imu_data) > 3 else 0.0
            pitch = uav.imu_data[4] if len(uav.imu_data) > 4 else 0.0
            tilt_magnitude = np.sqrt(roll**2 + pitch**2)
            
            # Check boundary violations
            is_out_of_bounds = (uav.position[0] < self.x_min or uav.position[0] > self.x_max or
                               uav.position[1] < self.y_min or uav.position[1] > self.y_max)
            
            # 1. Collision (Strong Penalty)
            collision = lidar_min < 0.3
            r_collision = -100.0 if collision else 0.0
            
            # 2. Battery & RTB Logic
            bat_level = uav.battery.get_percentage() # 0.0 to 1.0
            r_energy = 0.0
            
            # Find nearest station
            dists = np.linalg.norm(self.station_positions - uav_pos_2d, axis=1)
            min_dist = np.min(dists)
            
            # Initialize reward components
            r_ground = 0.0
            r_boundary = -1000.0 if is_out_of_bounds else 0.0
            
            # Check if moving while critical
            is_moving = np.linalg.norm(uav.velocity) > 0.1
            
            # PROGRESSIVE PAIN (Warning Signal)
            if bat_level < 0.20:
                r_energy -= 1.0 # Constant nagging pain
                # Approach Incentive
                r_energy -= (min_dist * 0.2) 
                
            if bat_level < 0.05:
                # Critical Alarm
                r_energy -= 5.0
                if is_moving: r_energy -= 5.0 # Don't just wander
            
            # DEATH PENALTY
            if bat_level <= 0.0:
                r_energy -= 500.0 # Same as Collision
            
            # --- LOGIC: STORAGE & RETURN TO BASE ---
            # NOTE: Map updates already done above (lines 340-350)
            
            # Fill Buffer
            # ...
            
            # 3. Offload & Recharge (The "Carrot")
            r_storage = 0.0
            # STRICT RECHARGE: Must be close AND on the ground
            is_at_station = (min_dist < 2.0) and (z_height < 0.5)
            
            if is_at_station:
                uav.battery.recharge()
                
                # DATA OFFLOAD (Learning the News)
                # Huge Reward for Completing the Cycle
                new_knowledge = self.central_map.merge_from(self.local_maps[agent])
                
                if new_knowledge > 0:
                     # BIG PAYOUT for Mission Success
                     r_storage = 200.0 + (new_knowledge * 0.1) 
                     print(f"[{agent}] 🌟 RECHARGED & OFFLOADED {new_knowledge} voxels! (+200 Reward)")
                else:
                     # Maintenance Reward for just Recharging
                     r_storage = 10.0
                     # print(f"[{agent}] Recharged (No new data).")
                
                # Reset Buffer
                self.agents_storage[agent] = 0

            
            # 3. Decentralized Loop Closure Sharing
            neighbors = self._get_neighbors(agent)
            # Find neighbors < 3m (excluding self=0)
            close_mask = (neighbors > 0) & (neighbors < 3.0)
            if np.any(close_mask):
                # Mock "Map Merge" - in reality, we assume this improves map quality
                # We give a small bonus for successful communication/rendezvous
                r_loop_closure = 1.0 
                # Here is where you'd call: self.shared_map.merge(agent_i, agent_j)
            else:
                r_loop_closure = 0.0
            
            r_time = -0.05
            
            # --- 4. Stability & Ground Safety ---
            r_stab = -0.5 * tilt_magnitude
            
            # --- NEW: Literature-Based "Hard & Good" Structure ---
            
            # A. Survival Bonus (The "Good"):
            # "N'aie pas peur de tester": Reward for simply being airborne and safe.
            # encouraging the agent to staying active rather than hiding on the ground.
            r_survival = 0.0
            if z_height > 1.0 and not collision and not is_out_of_bounds:
                r_survival = 0.1 
            
            # B. Proximity Shaping (The Gradient):
            # Penalize getting close BEFORE the crash.
            # dists_to_neighbors = neighbors (already calculated)
            r_proximity = 0.0
            if len(neighbors) > 0:
                min_neighbor_dist = np.min(neighbors[neighbors > 0]) # Exclude self 0
                if min_neighbor_dist < 2.0:
                    # Exponential penalty: -1.0 at 1m, -Infinity at 0m
                    r_proximity -= (2.0 - min_neighbor_dist) * 1.0

            # C. Hard Constraints (The "Hard"):
            # Collision
            if collision:
                 r_collision = -500.0 # Was -100. Severe crash.
            
            # NFZ
            r_nfz = 0.0
            in_nfz = False
            for (nx, ny, nr) in self.nfz_list:
                dist_to_nfz = np.linalg.norm(uav_pos_2d - np.array([nx, ny]))
                if dist_to_nfz < (nr + 0.5):
                    r_nfz -= 100.0 # Was -10. Strong "Don't go here" signal.
                    in_nfz = True

            # Boundary (Already -1000)
            
            # Altitude Logic (Existing: Incentive + Penalty)
            # Re-tuning:
            r_altitude = 0.0
            if z_height < self.max_height: r_altitude += z_height * 0.05 # Reduced slightly to balance survival
            if z_height > self.max_height: r_altitude -= (z_height - self.max_height) * 20.0
            if z_height < self.min_height:
                if min_dist < 3.0: pass
                else: r_altitude -= (self.min_height - z_height) * 20.0

            # ... Cost calc ...
            cost = 1.0 if (collision or is_out_of_bounds or in_nfz or 
                          (z_height > self.max_height) or (z_height < self.min_height and min_dist >= 2.5)) else 0.0

            # 5. Total Reward
            # Note: We sum up the shaped components + sparse events
            total_reward = (r_team_coverage + r_time + r_collision + r_energy + 
                           r_loop_closure + r_stab + r_ground + r_altitude + 
                           r_boundary + r_nfz + r_survival + r_proximity)
            
            rewards[agent] = total_reward
            
            # Termination
            is_tipped = (z_height < 0.3) and (tilt_magnitude > 1.0)
            
            # CASE 1/2: Terminate on Catastrophe (Collision/Boundary) to stop bad learning
            # But usually we let them continue to learn recovery unless it's impossible.
            # With -500/-1000, the episode return is destroyed anyway.
            terminations[agent] = collision or (bat_level <= 0.0) or is_tipped or (is_out_of_bounds and not self.use_cbf)
            truncations[agent] = self.step_count >= self.max_steps
            
            infos[agent] = {
                "collision": collision,
                "cost": cost,
                "coverage": self.local_maps[agent].get_coverage_ratio(),
                "battery": bat_level,
                "r_breakdown": {
                    "cov": r_team_coverage,
                    "surv": r_survival,
                    "prox": r_proximity,
                    "col": r_collision,
                    "nfz": r_nfz,
                    "bound": r_boundary
                }
            }
            
            # --- REAL-TIME LOGGING (User Request) ---
            # Print status every step (or every N steps)
            if self.step_count % 5 == 0: 
                print(f"[{agent} | Step {self.step_count}] "
                      f"Bat: {bat_level*100:.1f}% | "
                      f"Pos: {np.round(uav.position, 1)} | "
                      f"Rew: {total_reward:.2f} "
                      f"[Cov:{r_team_coverage:.2f} | Col:{r_collision:.0f} | Eny:{r_energy:.2f} | Store:{r_storage:.2f}]")
                if collision:
                    print(f"!!! [{agent}] CRITICAL: COLLISION DETECTED !!!")
                if bat_level < 0.2:
                    print(f"!!! [{agent}] WARNING: BATTERY LOW (RTB Penalty Applied) !!!")
                if is_out_of_bounds: print(f"!!! [{agent}] OUT OF BOUNDS! Penalty applied. !!!")
        
        if any(terminations.values()):
            for a in self.agents: terminations[a] = True
            
        # Visualization (RViz) - Publish Global Truth for Debug
        if self.step_count % 2 == 0: 
             self.viz.publish_voxels(self.global_map.get_sparse_pointcloud(), 
                                   self.global_map.resolution,
                                   self.global_map.x_min,
                                   self.global_map.y_min,
                                   self.global_map.z_min)
             
             # Publish 2D Projection for clearer view (User Request)
             self.viz.publish_2d_map(
                self.global_map.get_sparse_pointcloud(),
                self.global_map.resolution,
                self.global_map.x_min, self.global_map.y_min, 0.0,
                self.global_map.x_max, self.global_map.y_max
             )
             
             # Publish Communication Range (Ellipses)
             positions = {a: self.uavs[a].position for a in self.agents}
             self.viz.publish_comm_range(positions, range_radius=5.0)
             
             # Publish Stations (Green Spheres)
             self.viz.publish_stations(self.station_positions)
             
             # Publish NFZs (Red Zones)
             self.viz.publish_nfz(self.nfz_list)

             # Publish Workspace Boundaries (White Lines + Red Planes)
             self.viz.publish_boundaries(
                 self.global_map.x_min, self.global_map.x_max,
                 self.global_map.y_min, self.global_map.y_max,
                 self.min_height, self.max_height
             )
             
            # Publish Lidar Cones (Red Pyramids)
             # We need current states
             states = {a: self.uavs[a].get_state() for a in self.agents} # Assuming state[:3] is pos
             self.viz.publish_lidar_cone(states)

        # Compute observations for next step
        observations = {agent: self._get_obs(agent) for agent in self.agents}
            
        # === RViz VISUALIZATION (2D Grid) ===
        # Publish every 10 steps to avoid spam
        if self.step_count % 10 == 0:
            try:
                self.grid_viz.publish_global_map()
                self.grid_viz.publish_all_agents(self.num_drones)
            except Exception as e:
                if self.step_count % 100 == 0:
                    print(f"[Viz] Warning: Grid visualization failed: {e}")
        
        # Cast obs to float32
        observations = {a: observations[a].astype(np.float32) for a in self.agents}
        
        return observations, rewards, terminations, truncations, infos

    def _check_recharge(self, uav):
        uav_pos_2d = uav.position[:2]
        # Check distance to ALL known stations
        dists = np.linalg.norm(self.station_positions - uav_pos_2d, axis=1)
        z = uav.position[2]
        
        # PASSIVE CHARGING RULES:
        # 1. Close to station (< 1.0m)
        # 2. On the ground (z < 0.5m)
        # 3. NOT Flying (speed < 0.1) -> "quand c'est pas démarré"
        speed = np.linalg.norm(uav.velocity)
        
        if np.any(dists < 1.0) and z < 0.5:
             # Accelerate charging if idle? Or just standard recharge.
             # User said: "augmenter la batterie comme ça il pourra commencer"
             uav.battery.recharge()

    def _get_neighbors(self, uav_id):
        # Returns distance vector to other agents
        me = self.uavs[uav_id].position
        dists = []
        for other_id in self.possible_agents:
            if other_id == uav_id:
                dists.append(0.0)
            else:
                dists.append(np.linalg.norm(me - self.uavs[other_id].position))
        return np.array(dists)

    def _get_obs(self, agent):
        """
        Build observation for 2D+Z architecture.
        
        Observation Structure (Total: 147):
        - State (10): x, y, z_error, vx, vy, battery, dist_station, yaw, neighbors_count, storage
        - LiDAR (16): Downsampled 360° scan
        - Local 2D Map (121): 11×11 grid patch
        
        Returns:
            obs: (147,) numpy array
        """
        uav = self.uavs[agent]
        pos = uav.position
        vel = uav.velocity
        
        # 1. STATE VECTOR (10 dimensions)
        # Normalize positions to [-1, 1] range
        x_norm = pos[0] / 100.0  # World is ±100m
        y_norm = pos[1] / 100.0
        
        # Z error from optimal altitude (should be ~0 if controller working)
        z_error = (pos[2] - self.z_optimal) / 5.0  # Normalize by expected deviation
        
        # Velocity
        vx = vel[0]
        vy = vel[1]
        
        # Battery
        battery = uav.battery.get_percentage()
        
        # Distance to nearest station
        dists = np.linalg.norm(self.station_positions - pos[:2], axis=1)
        dist_station = np.min(dists) / 50.0  # Normalize by half-world size
        
        # Yaw (orientation)
        yaw = uav.orientation[2] if len(uav.orientation) > 2 else 0.0
        
        # Neighbors count
        neighbors = self._get_neighbors(agent)
        neighbors_count = np.sum(neighbors > 0)  # Count non-zero (neighbors within range)
        
        # Storage (data buffer)
        storage = self.agents_storage[agent] / self.MAX_STORAGE
        
        state = np.array([
            x_norm, y_norm, z_error,
            vx, vy,
            battery, dist_station, yaw,
            neighbors_count, storage
        ], dtype=np.float32)
        
        # 2. LIDAR (16 sectors, downsampled from 360°)
        scan = uav.lidar_ranges
        if len(scan) >= 352:
            # Downsample to 16 sectors by averaging (360 / 16 = 22.5)
            scan_cut = scan[:352]  # 16*22 = 352
            scan_ds = np.mean(scan_cut.reshape(16, 22), axis=1)
        elif len(scan) > 0:
            # Fallback: Simple sampling
            indices = np.linspace(0, len(scan)-1, 16).astype(int)
            scan_ds = scan[indices].astype(np.float32)
        else:
            scan_ds = np.zeros(16, dtype=np.float32)
        
        # Normalize LiDAR (max range 50m)
        scan_ds = scan_ds / 50.0
        
        # 3. LOCAL 2D MAP PATCH (11×11 = 121)
        patch_2d = self.local_maps[agent].get_observation_2d(pos[0], pos[1], radius=5)
        patch_flat = patch_2d.flatten()  # (121,)
        
        # CONCATENATE ALL
        # Total: 10 + 16 + 121 = 147
        obs = np.concatenate([state, scan_ds, patch_flat]).astype(np.float32)
        
        # DEBUG: Check for NaNs
        if np.isnan(obs).any():
            print(f"[SwarmEnv] WARNING: Agent {agent} Obs contains NaNs! Replacing with 0.0")
            obs = np.nan_to_num(obs, nan=0.0, posinf=1.0, neginf=-1.0)
            
        # DEBUG: Check Shape
        if obs.shape != (147,):
             print(f"[SwarmEnv] CRITICAL: Agent {agent} Obs Shape mismatch! Expected (147,), got {obs.shape}")

        return obs

    def close(self):
        self.node.destroy_node()
        rclpy.shutdown()

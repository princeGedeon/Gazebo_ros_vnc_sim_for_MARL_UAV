
from pettingzoo import ParallelEnv
from gymnasium import spaces
import numpy as np
import rclpy
import sys
import os

from swarm_sim.common.voxel_manager import VoxelManager
from swarm_sim.common.rewards import RewardEngine
from swarm_sim.envs.core.uav_base import UAVBase
from swarm_sim.common.viz_utils import VoxelVisualizer

class SwarmCoverageEnv(ParallelEnv):
    """
    PettingZoo Parallel Env for Multi-UAV Cooperative 3D Coverage.
    """
    metadata = {"render_modes": ["human"], "name": "swarm_coverage_v0"}

    def __init__(self, num_drones=3, station_config=None, max_steps=1000, 
                 min_height=2.0, max_height=10.0, nfz_config='default'):
        self.num_drones = num_drones
        self.station_config = station_config
        self.max_steps = max_steps
        
        # Safety & Constraints
        self.min_height = min_height
        self.max_height = max_height
        self.nfz_config = nfz_config # 'default', int (count), or list [(x,y,r)]
        self.nfz_list = [] # Active NFZs [(x,y,r)]

        self.possible_agents = [f"uav_{i}" for i in range(self.num_drones)]
        self.agents = self.possible_agents[:]
        
        # 1. Logic
        # Storage Simulation
        self.MAX_STORAGE = 500 # Voxel Capacity
        self.agents_storage = {a: 0 for a in self.agents}
        # Global Truth (for evaluation/global reward)
        self.global_map = VoxelManager(x_range=(-20, 20), y_range=(-20, 20), z_range=(0,10))
        # Central Station Map (Realistic Output - Only updates on offload)
        self.central_map = VoxelManager(x_range=(-20, 20), y_range=(-20, 20), z_range=(0,10))
        
        # Local Beliefs (Decentralized)
        self.local_maps = {
            agent: VoxelManager(x_range=(-20, 20), y_range=(-20, 20), z_range=(0,10))
            for agent in self.possible_agents
        }
        
        self.reward_engine = RewardEngine()
        
        # 2. Spaces
        # Action: Velocity
        self.action_spaces = {
            agent: spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
            for agent in self.possible_agents
        }
        
        # Observation: Same as single agent (Local 3D Map)
        self.local_map_dim = (7 * 7 * 5)
        # Obs: state(6+1) + lidar(16) + map + imu(6) + neighbors(num_drones)
        obs_dim = 7 + 16 + self.local_map_dim + 6 + self.num_drones
        self.observation_spaces = {
            agent: spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)
            for agent in self.possible_agents
        }
        
        # 3. ROS
        if not rclpy.ok():
            rclpy.init()
        self.node = rclpy.create_node("swarm_coverage_node")
        self.viz = VoxelVisualizer()
        
        # Ground Stations Config (User Request)
        # station_config can be an int (count) or list of [x, y]
        if station_config is None:
            # Default: 1 Station at Origin (or matching launch defaults)
            self.station_positions = np.array([[0.0, 0.0]])
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
        
        observations = {agent: self._get_obs(agent) for agent in self.agents}
        infos = {agent: {} for agent in self.agents}
        
        return observations, infos

    def step(self, actions):
        self.step_count += 1
        
        # Apply Actions
        for agent, action in actions.items():
            if agent in self.uavs:
                self.uavs[agent].apply_action(action)
                
        # Step World
        rclpy.spin_once(self.node, timeout_sec=0.1)
        
        # Update Logic
        # 1. Update each agent's local map and the global map
        uav_positions = {}
        for agent in self.agents:
            uav = self.uavs[agent]
            pos = uav.position
            uav_positions[agent] = pos
            
            # Update Map using Downward Lidar if available, else Pos (fallback)
            # We assume VoxelManager can handle pointclouds or we convert them
            # For now, let's assume update() takes [pos] like before unless we change VoxelManager api
            # Start simpl: pass pos combined with lidar hits? 
            # Actually, `voxel_manager.update` typically takes "Points that are free" or "Points that are occupied".
            # If we want Raycasting, we need to pass the Origin + Hits.
            
            # Simple "IGN-Style" implementation:
            # If we have lidar_down_data (PointCloud2), we should parse it.
            # Parsing PC2 in Python is slow. 
            # Alternative: Assume simple "Cone" below drone is free/occupied based on altitude?
            # User wants "Lidar vs GPS". Let's stick to the previous simple logic for "Free Space"
            # BUT adding "Hits" from lidar_down would be the real upgrade.
            
            # Let's keep using 'update([pos])' which clears space around drone (blind clearing)
            # And ADD 'update_hits(points)' if we parsed PC2.
            # Given complexity of specific PC2 parsing here, let's stick to 'pos' for clearing
            # but mark it as "TODO: Parse PC2 for obstacles".
            
            # Reverting to simple update for stability, but we prepared the data channel.
            # self.local_maps[agent].update([pos])
            # self.global_map.update([pos])

            # --- NEW: FUSION LOGIC ---
            # 1. Update Free Space at Drone Position (Always true)
            self.local_maps[agent].update([pos])
            self.global_map.update([pos])
            
            # 2. Update Discovered Obstacles (From Down Lidar)
            # This fills the "Surface" of the map
            hits_world = uav.get_transformed_down_lidar()
            if hits_world is not None:
                # print(f"Fusing {len(hits_world)} pts from {agent}")
                self.local_maps[agent].update_from_pointcloud(hits_world)
                self.global_map.update_from_pointcloud(hits_world)
            # -------------------------


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
            
            # 1. Collision (Strong Penalty)
            collision = lidar_min < 0.3
            r_collision = -100.0 if collision else 0.0
            
            # 2. Battery & RTB Logic
            bat_level = uav.battery.get_percentage() # 0.0 to 1.0
            r_energy = 0.0
            
            # Find nearest station
            uav_pos_2d = uav.position[:2]
            dists = np.linalg.norm(self.station_positions - uav_pos_2d, axis=1)
            min_dist = np.min(dists)
            
            # Check if moving while critical
            is_moving = np.linalg.norm(uav.velocity) > 0.1
            if bat_level < 0.2:
                # Incentive to Return to Nearest Base
                r_energy -= (min_dist * 0.1) # Penalty for being far from NEAREST base
                
                if bat_level < 0.05 and is_moving:
                    r_energy -= 10.0 # Critical penalty for moving when dead
            
            # Recharge logic & Data Offload
            # self._check_recharge(uav) -> integrated below
            
            # --- LOGIC: STORAGE & RETURN TO BASE ---
            
            # 1. Update Storage & Fusion
            # NOTE: We partially fused earlier (global_map.update). 
            # We need to track NEW knowledge for this agent specifically for storage.
            # Rerun local update to get count?
            # Or better: Move the Fusion Logic from line 158 down here?
            # Creating a unified block for Map + Storage.
            
            new_knowledge = 0
            hits_world = uav.get_transformed_down_lidar()
            if hits_world is not None:
                new_knowledge = self.local_maps[agent].update_from_pointcloud(hits_world)
                self.global_map.update_from_pointcloud(hits_world)
            
            # Simple position update
            self.local_maps[agent].update([uav.position])
            self.global_map.update([uav.position])

            # Fill Buffer
            self.agents_storage[agent] += new_knowledge
            storage_pct = min(self.agents_storage[agent] / self.MAX_STORAGE, 1.0)
            
            # 2. Critical State Check (RTB Trigger)
            # RTB if Battery < 30% OR Storage > 80%
            is_rtb_needed = (bat_level < 0.30) or (storage_pct > 0.80)
            
            r_rtb = 0.0 
            
            if is_rtb_needed:
                # Shaping Reward: Encourage getting closer to NEAREST station
                # Use calculated 'min_dist'
                r_rtb -= (min_dist * 0.1) 
                r_rtb -= 0.5 
                
                # Block Exploration Reward if full
                if storage_pct >= 1.0:
                    r_team_coverage = 0.0 
            
            # 3. Offload & Recharge (At Station)
            r_storage = 0.0
            if min_dist < 2.0:
                uav.battery.recharge()
                
                # Offload to Central
                if self.agents_storage[agent] > 0:
                    dump_amount = self.agents_storage[agent]
                    self.central_map.merge_from(self.local_maps[agent])
                    
                    r_storage = 2.0 + (dump_amount * 0.05) 
                    print(f"[{agent}] 📥 OFFLOADED {dump_amount} voxels! Storage Empty.")
                    self.agents_storage[agent] = 0 
                else:
                    r_storage = 0.5 
            
            if min_dist < 2.0:
                # At Station!
                uav.battery.recharge()
                
                # DATA OFFLOAD LOGIC (Realistic Mode)
                # We merge the agent's Local Map into the Central Station Map
                # This simulates "uploading" the survey data.
                new_knowledge = self.central_map.merge_from(self.local_maps[agent])
                
                # Reward for bringing NEW data to the station
                # This transforms the problem into a "Data Mule" task.
                if new_knowledge > 0:
                     r_storage = 2.0 + (new_knowledge * 0.01) # Big bonus for dump
                     print(f"[{agent}] Offloaded {new_knowledge} new voxels to Central Station!")
                else:
                     r_storage = 0.5 # Small maintenance reward
            
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
            
            # --- 4. Stability & Ground Safety (New) ---
            # Get Orientation
            rpy = uav.get_rpy()
            roll, pitch, _ = rpy
            tilt_magnitude = abs(roll) + abs(pitch)
            
            # A. General Stability: Penalize any tilt (encourage flat hover)
            r_stab = -0.5 * tilt_magnitude
            
            # --- NEW: Altitude Constraints ---
            r_altitude = 0.0
            z_height = uav.position[2]
            
            # Max Height Penalty
            if z_height > self.max_height:
                r_altitude -= (z_height - self.max_height) * 2.0
            
            # Min Height Penalty (Unless near station for Landing)
            if z_height < self.min_height:
                # Check Station Proximity
                if min_dist < 2.5: # Station Zone
                    # Allowed to be low here (Landing/Takeoff)
                    pass 
                else:
                    # Penalty for flying too low in the field
                    r_altitude -= (self.min_height - z_height) * 2.0
            
            # --- NEW: No-Fly Zone (NFZ) ---
            r_nfz = 0.0
            in_nfz = False
            for (nx, ny, nr) in self.nfz_list:
                # Simple Cylinder Check (Infinite height or constrained?) 
                # Usually NFZ is all altitudes.
                dist_to_nfz = np.linalg.norm(uav_pos_2d - np.array([nx, ny]))
                if dist_to_nfz < (nr + 0.5): # +0.5 buffer for drone radius
                    r_nfz -= 10.0 # Heavy Penalty per step
                    in_nfz = True
                    # Optional: Terminate if deep inside?
            
            # B. Ground Instability (Crash/Tip-over Risk)
            # If close to ground (< 0.2m) and tilted (> 15 deg ~= 0.26 rad), HUGE Penalty
            r_ground = 0.0
            if z_height < 0.3:
                if tilt_magnitude > 0.26: 
                     r_ground = -5.0 # Penalize tipping on landing
                else: 
                     pass
            
            # 5. Total Reward
            total_reward = (r_team_coverage + r_time + r_collision + r_energy + 
                           r_loop_closure + r_stab + r_ground + r_altitude + r_nfz)
            rewards[agent] = total_reward
            
            # Termination: Collision OR Dead Battery OR Tipped Over
            is_tipped = (z_height < 0.3) and (tilt_magnitude > 1.0) # >60 deg tilt on ground = crashed
            
            terminations[agent] = collision or (bat_level <= 0.0) or is_tipped
            truncations[agent] = self.step_count >= self.max_steps
            
            # Info for Debug/Logging
            infos[agent] = {
                "collision": collision,
                "coverage": self.local_maps[agent].get_coverage_ratio(),
                "global_coverage": self.global_map.get_coverage_ratio(),
                "battery": bat_level,
                "tilt": tilt_magnitude,
                "r_breakdown": {
                    "cov": r_team_coverage,
                    "col": r_collision,
                    "energy": r_energy,
                    "loop": r_loop_closure,
                    "stab": r_stab,
                    "ground": r_ground
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
        
        if any(terminations.values()):
            for a in self.agents: terminations[a] = True
            
        # Visualization (RViz) - Publish Global Truth for Debug
        if self.step_count % 10 == 0: 
             self.viz.publish_voxels(self.global_map.get_sparse_pointcloud(), 
                                   self.global_map.resolution,
                                   self.global_map.x_min,
                                   self.global_map.y_min,
                                   self.global_map.z_min)
             
             # Publish Communication Range (Ellipses)
             positions = {a: self.uavs[a].position for a in self.agents}
             self.viz.publish_comm_range(positions, range_radius=5.0)
             
             # Publish Stations (Green Spheres)
             self.viz.publish_stations(self.station_positions)
             
             # Publish NFZs (Red Zones)
             self.viz.publish_nfz(self.nfz_list)

             # Publish Workspace Boundaries (White Lines)
             self.viz.publish_boundaries(
                 self.global_map.x_min, self.global_map.x_max,
                 self.global_map.y_min, self.global_map.y_max
             )
             
             # Publish Lidar Cones (Red Pyramids)
             # We need current states
             states = {a: self.uavs[a].get_state() for a in self.agents} # Assuming state[:3] is pos
             self.viz.publish_lidar_cone(states)

        # Compute observations for next step
        observations = {agent: self._get_obs(agent) for agent in self.agents}
            
        return observations, rewards, terminations, truncations, infos

    def _check_recharge(self, uav):
        uav_pos_2d = uav.position[:2]
        # Check distance to ALL known stations
        dists = np.linalg.norm(self.station_positions - uav_pos_2d, axis=1)
        if np.any(dists < 1.0):
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
        uav = self.uavs[agent]
        state = uav.get_state() # now includes battery
        
        # Lidar (360 -> 16 sectors)
        scan = uav.lidar_ranges
        if len(scan) >= 352:
            # Downsample to 16 sectors by averaging
            # 360 / 16 = 22.5. We truncate to 352 (16*22)
            scan_cut = scan[:352] 
            scan_ds = np.mean(scan_cut.reshape(16, 22), axis=1) # (16,)
        elif len(scan) > 0:
            # Fallback if scan is weird size (e.g. from different sensor)
            # Simple interpolation or just zeros
            scan_ds = np.zeros(16)
            # Try basic sampling
            indices = np.linspace(0, len(scan)-1, 16).astype(int)
            scan_ds = scan[indices]
        else:
            scan_ds = np.zeros(16)

            
        # Voxel Patch from LOCAL map
        patch = self.local_maps[agent].get_observation(state[0], state[1], state[2], r_xy=3, r_z=2)
        patch_flat = patch.flatten()
        
        neighbors = self._get_neighbors(agent)
        imu = uav.imu_data
        
        return np.concatenate([state, scan_ds, patch_flat, imu, neighbors]).astype(np.float32)

    def close(self):
        self.node.destroy_node()
        rclpy.shutdown()

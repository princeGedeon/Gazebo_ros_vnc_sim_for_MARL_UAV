# System Architecture

```mermaid
graph LR
    subgraph Host["Host Machine (Linux + GPU)"]
        
        subgraph Docker["Docker Container (ros:jazzy-sim)"]
            direction TB
            
            subgraph Simulation["Gazebo Harmonic"]
                direction TB
                World[/"City World / External Map"\]
                GroundStation("Charging Stations")
                Swarm("UAV Swarm (3 Drones)")
                
                UAV0("UAV 0 Link") --> Swarm
                UAV1("UAV 1 Link") --> Swarm
            end
            
            subgraph ROS2["ROS 2 Jazzy (Middleware)"]
                direction TB
                Bridge["ros_gz_bridge (Topics)"]
                
                subgraph SLAM["Decentralized SLAM Stack"]
                    Octomap["Octomap Server"]
                    CSLAM["Swarm-SLAM (Loop Closure)"]
                    Saver["Map Saver (GIS)"]
                end
            end
            
            subgraph Brain["RL Training (PettingZoo)"]
                direction TB
                Env["SwarmCoverageEnv"]
                Agent["PPO (StableBaselines3)"]
                
                subgraph Logic["Core Logic"]
                    VM["Voxel Manager"]
                    Bat["Battery Model"]
                end
            end
            
            %% Connections
            Swarm -- "Lidar/IMU" --> Bridge
            Bridge -- "/scan, /odom" --> SLAM
            Bridge -- "/odom" --> Env
            Env -- "/cmd_vel" --> Bridge
            
            SLAM -- "Map Data" --> VM
            Env --> Agent
        end
    end
    
    style Docker fill:#f9f,stroke:#333,stroke-width:2px
    style Simulation fill:#e1f5fe,stroke:#01579b
    style ROS2 fill:#e8f5e9,stroke:#2e7d32
    style Brain fill:#fff3e0,stroke:#ef6c00
```

## System Modules
1.  **Simulation**: Handles Physics, Sensor generation (Raycasting), and Battery drain visuals.
2.  **ROS 2 Bridge**: Translates Jazzy messages to Gazebo protobufs.
3.  **SLAM Layer**:
    -   **Octomap**: Generates the volumetric occupancy map (`.bt`).
    -   **Swarm-SLAM**: (In Progress) Handles decentralized loop closure detection.
4.  **Learning Environment**:
    -   **SwarmCoverageEnv**: PettingZoo interface.
    -   **VoxelManager**: Efficiently tracks visited voxels and handles "Merging" when agents meet.

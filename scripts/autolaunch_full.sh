#!/bin/bash
#
# AUTO-LAUNCH FULL SYSTEM
# Starts: Gazebo + ROS2 + SLAM + RViz + rqt_graph + Training
#
# Usage: ./scripts/autolaunch_full.sh [scenario]
# Scenarios: case_1 (MAPPO), case_2 (Lagrangian), case_3 (CBF)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCENARIO=${1:-case_1}
NUM_DRONES=3

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AUTO-LAUNCH FULL SYSTEM${NC}"
echo -e "${GREEN}  Scenario: ${SCENARIO}${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if inside Docker
if [ ! -f /.dockerenv ]; then
    echo -e "${YELLOW}WARNING: Not inside Docker container${NC}"
    echo "Run: docker exec -it <container> bash"
    exit 1
fi

# Source ROS2
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

# Kill any existing processes
echo -e "${YELLOW}[1/6] Cleaning existing processes...${NC}"
pkill -f gazebo || true
pkill -f rviz2 || true
pkill -f rqt_graph || true
# Fix RViz "map" frame issue by linking to uav_0/map (SLAM frame)
echo -e "${YELLOW}[1.5/6] Publishing Static TF (map -> uav_0/map)...${NC}"
ros2 run tf2_ros static_transform_publisher --frame-id map --child-frame-id uav_0/map --x 0 --y 0 --z 0 &> /dev/null &
TF_PID=$!
echo "TF PID: $TF_PID"

# 1.5 Generate World (Force Fresh)
echo -e "${YELLOW}[1.5/6] Generating Clean World...${NC}"
python3 src/swarm_sim_pkg/swarm_sim/assets/worlds/generate_city.py --output src/swarm_sim_pkg/swarm_sim/assets/worlds/generated_city.sdf --seed 42

# Launch Simulation (Gazebo + ROS2 + SLAM)
echo -e "${YELLOW}[2/6] Launching Gazebo + SLAM...${NC}"
ros2 launch swarm_sim super_simulation.launch.py \
    num_drones:=$NUM_DRONES \
    slam:=true \
    world_file:=/root/ros2_ws/src/swarm_sim_pkg/swarm_sim/assets/worlds/generated_city.sdf \
    &> /tmp/gazebo_launch.log &

GAZEBO_PID=$!
echo "Gazebo PID: $GAZEBO_PID"

# Wait for Gazebo to initialize
echo -e "${YELLOW}Waiting for Gazebo to start (30s)...${NC}"
sleep 30

# 4. Spawn Visuals (NFZ, Boundaries)
echo "[Launcher] Spawning Visuals (Constraints)..."
python3 scripts/spawn_visuals.py &

# 5. Generate Dynamic RViz Config
RVIZ_CONFIG="/root/ros2_ws/rviz_configs/dynamic_swarm.rviz"
echo "[Launcher] Generating RViz config for $NUM_DRONES drones..."
python3 scripts/generate_rviz.py $NUM_DRONES $RVIZ_CONFIG

# 6. Open RViz (Dynamic Config)
if [ "$OPEN_RVIZ" = true ]; then
    echo "[Launcher] 🎨 Starting RViz2 with Dynamic Config..."
    # Ensure display is set
    export DISPLAY=:1
    
    # Launch in background
    rviz2 -d $RVIZ_CONFIG &
    PID_RVIZ=$!
    echo "[Launcher] RViz PID: $PID_RVIZ"
else
    echo "[Launcher] RViz Disabled (Headless Mode)"
fi

# Launch rqt_graph for topic visualization
echo -e "${YELLOW}[4/6] Launching rqt_graph...${NC}"
rqt_graph &> /tmp/rqt_graph.log &
RQT_PID=$!
echo "rqt_graph PID: $RQT_PID"

# Wait for ROS2 topics to be ready
echo -e "${YELLOW}Waiting for ROS2 topics (10s)...${NC}"
sleep 10

# Verify topics
echo -e "${YELLOW}[5/6] Verifying topics...${NC}"
ros2 topic list | grep -E "(odom|lidar|coverage)" || echo -e "${RED}WARNING: Some topics missing${NC}"

# Launch Training
echo -e "${YELLOW}[6/6] Launching Training (${SCENARIO})...${NC}"

case "$SCENARIO" in
    case_1)
        python3 ~/ros2_ws/src/swarm_sim_pkg/swarm_sim/training/train_mappo.py \
            --num-drones 3 \
            --max-steps 1000 \
            --total-timesteps 500000 \
            --checkpoint-freq 50000 \
            --output-dir outputs/case_1 \
            &> /tmp/training.log &
        ;;
    case_2)
        python3 ~/ros2_ws/src/swarm_sim_pkg/swarm_sim/training/train_mappo_lagrangian.py \
            --num-drones 3 \
            --max-steps 1000 \
            --total-timesteps 500000 \
            --checkpoint-freq 50000 \
            --output-dir outputs/case_2 \
            &> /tmp/training.log &
        ;;
    case_3)
        python3 ~/ros2_ws/src/swarm_sim_pkg/swarm_sim/training/train_mappo_cbf.py \
            --num-drones 3 \
            --max-steps 1000 \
            --total-timesteps 500000 \
            --checkpoint-freq 50000 \
            --output-dir outputs/case_3 \
            &> /tmp/training.log &
        ;;
    *)
        echo -e "${RED}Unknown scenario: $SCENARIO${NC}"
        exit 1
        ;;
esac

TRAIN_PID=$!
echo "Training PID: $TRAIN_PID"

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ALL SYSTEMS LAUNCHED ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Process IDs:"
echo -e "  Gazebo:   ${GAZEBO_PID}"
echo -e "  RViz:     ${RVIZ_PID}"
echo -e "  rqt_graph: ${RQT_PID}"
echo -e "  Training: ${TRAIN_PID}"
echo ""
echo -e "Logs:"
echo -e "  Gazebo:   /tmp/gazebo_launch.log"
echo -e "  RViz:     /tmp/rviz.log"
echo -e "  Training: /tmp/training.log"
echo ""
echo -e "${YELLOW}To monitor training:${NC}"
echo -e "  tail -f /tmp/training.log"
echo ""
echo -e "${YELLOW}To stop all:${NC}"
echo -e "  pkill -f gazebo && pkill -f rviz2 && pkill -f rqt && pkill -f train_mappo"
echo ""
echo -e "${GREEN}Happy Training! 🚁${NC}"

# Keep script alive (wait for training)
wait $TRAIN_PID

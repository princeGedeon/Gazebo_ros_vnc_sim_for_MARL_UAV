# Project Scripts

This directory contains the utility scripts for the Swarm Coverage project.

## Main Scripts

### `launch_all.sh`
*   **Usage**: `./scripts/launch_all.sh train`
*   **Purpose**: The master entry point. It launches:
    1.  The Gazebo Simulation (via `super_simulation.launch.py`).
    2.  The MAPPO RL Agent (`train_mappo.py`).
*   **Note**: Run this from the project root or from the `scripts` folder.

### `test_map_export.py`
*   **Usage**: `python3 scripts/test_map_export.py`
*   **Purpose**: Verifies the Georeferencing logic. It mocks the environment and exports a test Point Cloud (.laz) to ensure libraries (`utm`, `laspy`) are working correctly.

### `check_deps.py`
*   **Usage**: `python3 scripts/check_deps.py`
*   **Purpose**: Simple diagnostic tool to check if required Python packages (`utm`, `laspy`) are installed in the current environment.

## Docker / Infrastructure Scripts

### `autolaunch.sh`
*   **Purpose**: Internal script used by the Docker container. It handles the build (`colcon build`) and sourcing of the workspace upon container startup.
*   **Caution**: Modifications here affect the Docker image build process.

### `setup_real_slam.sh`
*   **Purpose**: Installing dependencies for Real-World SLAM integration (Octomap, PCL).

### `start_training.sh`
*   **Purpose**: Helper to launch only the training node (without launching the full simulation pipeline if it's already running).

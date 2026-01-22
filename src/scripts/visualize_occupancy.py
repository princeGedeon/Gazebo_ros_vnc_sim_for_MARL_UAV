import numpy as np
import matplotlib.pyplot as plt
import sys
import os

def visualize(filename):
    print(f"Loading {filename}...")
    if not os.path.exists(filename):
        print("File not found.")
        return

    # Load data (N, 3) integers (Voxel Indices)
    data = np.load(filename)
    print(f"Loaded Shape: {data.shape}")
    
    if data.shape[0] == 0:
        print("Map is empty.")
        return

    # Check if data looks like floats (World) or Ints (Voxels)
    # VoxelManager saves ints.
    is_voxel = np.issubdtype(data.dtype, np.integer)
    
    print(f"Data Type: {data.dtype} (Is Voxel Indices: {is_voxel})")
    
    # 3D Plot
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot sparse points
    # Swap axes if needed for visual comparison with Gazebo
    # Gazebo: Z up. Matplotlib: Z up.
    xs = data[:, 0]
    ys = data[:, 1]
    zs = data[:, 2]
    
    scatter = ax.scatter(xs, ys, zs, c=zs, cmap='viridis', marker='s', s=5, alpha=0.6)
    
    ax.set_xlabel('X (Voxel Index)')
    ax.set_ylabel('Y (Voxel Index)')
    ax.set_zlabel('Z (Voxel Index)')
    ax.set_title(f'Associative Map Visualization\n{filename}')
    
    plt.colorbar(scatter, label='Height (Z)')
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to the output file
        # Try to find one in outputs
        default_path = "src/swarm_sim_pkg/swarm_sim/outputs/debug_map.npy"
        if os.path.exists(default_path):
             visualize(default_path)
        else:
             print("Usage: python3 visualize_occupancy.py <path_to_npy>")
             print(f"Could not find default: {default_path}")
    else:
        visualize(sys.argv[1])

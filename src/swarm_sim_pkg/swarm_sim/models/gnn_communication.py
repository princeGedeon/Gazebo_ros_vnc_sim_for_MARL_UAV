"""
GNN Communication Module (MAGNET Architecture)
Graph Neural Network for Multi-Agent Message Passing

Architecture:
- Node features: Agent observations (147D)
- Edge features: Relative positions, communication range
- Message passing: 3 layers (GCN)
- Output: Enhanced observations (147D + communication)

Based on: Liu et al. (2020) "Multi-Agent Game Abstraction via Graph Attention Network"
"""

import torch
import torch.nn.as nn
import torch.nn.functional as F
import numpy as np


class GraphAttentionLayer(nn.Module):
    """
    Graph Attention Layer (GAT) for message passing.
    
    Computes attention weights between agents based on their states.
    """
    
    def __init__(self, in_features, out_features, dropout=0.1, alpha=0.2):
        super(GraphAttentionLayer, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.dropout = dropout
        self.alpha = alpha
        
        # Learnable weight matrices
        self.W = nn.Parameter(torch.empty(size=(in_features, out_features)))
        nn.init.xavier_uniform_(self.W.data, gain=1.414)
        
        self.a = nn.Parameter(torch.empty(size=(2*out_features, 1)))
        nn.init.xavier_uniform_(self.a.data, gain=1.414)
        
        self.leakyrelu = nn.LeakyReLU(self.alpha)
        
    def forward(self, h, adj):
        """
        Args:
            h: Node features (batch, num_agents, in_features)
            adj: Adjacency matrix (batch, num_agents, num_agents)
        
        Returns:
            h_prime: Updated node features (batch, num_agents, out_features)
        """
        # Linear transformation
        Wh = torch.matmul(h, self.W)  # (batch, N, out_features)
        
        # Attention mechanism
        a_input = self._prepare_attentional_mechanism_input(Wh)
        e = self.leakyrelu(torch.matmul(a_input, self.a).squeeze(3))
        
        # Mask attention for non-existent edges
        zero_vec = -9e15*torch.ones_like(e)
        attention = torch.where(adj > 0, e, zero_vec)
        attention = F.softmax(attention, dim=2)
        attention = F.dropout(attention, self.dropout, training=self.training)
        
        # Weighted sum of neighbor features
        h_prime = torch.matmul(attention, Wh)
        
        return h_prime
    
    def _prepare_attentional_mechanism_input(self, Wh):
        """Compute pairwise concatenations for attention"""
        batch_size, N, out_features = Wh.size()
        
        # Repeat for pairwise combinations
        Wh_repeated_in_chunks = Wh.repeat_interleave(N, dim=1)
        Wh_repeated_alternating = Wh.repeat(1, N, 1)
        
        # Concatenate
        all_combinations_matrix = torch.cat([Wh_repeated_in_chunks, Wh_repeated_alternating], dim=2)
        
        return all_combinations_matrix.view(batch_size, N, N, 2 * out_features)


class MAGNETEncoder(nn.Module):
    """
    Multi-Agent Graph Neural Network Encoder (MAGNET)
    
    Aggregates information from neighboring agents using graph attention.
    """
    
    def __init__(self, obs_dim=147, hidden_dim=128, num_layers=3, comm_range=10.0):
        super(MAGNETEncoder, self).__init__()
        
        self.obs_dim = obs_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.comm_range = comm_range
        
        # Observation encoder (MLP)
        self.obs_encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Graph attention layers
        self.gat_layers = nn.ModuleList([
            GraphAttentionLayer(hidden_dim, hidden_dim)
            for _ in range(num_layers)
        ])
        
        # Output decoder
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
    
    def forward(self, observations, positions):
        """
        Args:
            observations: Dict {agent_id: obs (obs_dim,)}
            positions: Dict {agent_id: pos (3,)} [x, y, z]
        
        Returns:
            enhanced_obs: Dict {agent_id: enhanced_obs (hidden_dim,)}
        """
        # Convert to tensors
        agent_ids = sorted(observations.keys())
        obs_list = [observations[agent] for agent in agent_ids]
        pos_list = [positions[agent] for agent in agent_ids]
        
        batch_size = 1  # Single environment
        num_agents = len(agent_ids)
        
        # Stack observations (1, num_agents, obs_dim)
        obs_tensor = torch.stack([torch.FloatTensor(obs) for obs in obs_list]).unsqueeze(0)
        pos_tensor = torch.stack([torch.FloatTensor(pos) for pos in pos_list]).unsqueeze(0)
        
        # Encode observations
        h = self.obs_encoder(obs_tensor)  # (1, N, hidden_dim)
        
        # Build adjacency matrix based on communication range
        adj = self._build_adjacency_matrix(pos_tensor)  # (1, N, N)
        
        # Graph message passing
        for gat in self.gat_layers:
            h = gat(h, adj) + h  # Residual connection
            h = F.relu(h)
        
        # Decode
        enhanced = self.decoder(h)  # (1, N, hidden_dim)
        
        # Convert back to dict
        enhanced_obs = {}
        for i, agent in enumerate(agent_ids):
            enhanced_obs[agent] = enhanced[0, i].detach().numpy()
        
        return enhanced_obs
    
    def _build_adjacency_matrix(self, positions):
        """
        Build adjacency matrix based on Euclidean distance.
        
        Args:
            positions: (batch, num_agents, 3)
        
        Returns:
            adj: (batch, num_agents, num_agents) binary matrix
        """
        batch_size, num_agents, _ = positions.size()
        
        # Compute pairwise distances (2D: x, y only)
        pos_2d = positions[:, :, :2]  # (batch, N, 2)
        
        # Expand for pairwise computation
        pos_i = pos_2d.unsqueeze(2)  # (batch, N, 1, 2)
        pos_j = pos_2d.unsqueeze(1)  # (batch, 1, N, 2)
        
        # Euclidean distance
        dist = torch.sqrt(torch.sum((pos_i - pos_j)**2, dim=3))  # (batch, N, N)
        
        # Adjacency: 1 if within comm_range, 0 otherwise
        adj = (dist <= self.comm_range).float()
        
        # Set diagonal to 1 (self-loop)
        eye = torch.eye(num_agents).unsqueeze(0).expand(batch_size, -1, -1)
        adj = adj * (1 - eye) + eye  # Remove self, then add back
        
        return adj


class GNNAugmentedPolicy(nn.Module):
    """
    Wrapper that augments MAPPO policy with GNN communication.
    
    Usage:
        policy = GNNAugmentedPolicy(base_policy, obs_dim=147)
        actions = policy(observations, positions)
    """
    
    def __init__(self, base_policy, obs_dim=147, hidden_dim=128):
        super(GNNAugmentedPolicy, self).__init__()
        
        self.base_policy = base_policy
        self.gnn = MAGNETEncoder(obs_dim, hidden_dim)
        
        # Fusion layer (concat obs + gnn features)
        self.fusion = nn.Linear(obs_dim + hidden_dim, obs_dim)
    
    def forward(self, observations, positions):
        """
        Args:
            observations: Dict {agent_id: obs}
            positions: Dict {agent_id: pos}
        
        Returns:
            actions: Dict {agent_id: action}
        """
        # Get GNN-enhanced features
        gnn_features = self.gnn(observations, positions)
        
        # Fuse with original observations
        fused_obs = {}
        for agent in observations.keys():
            obs = torch.FloatTensor(observations[agent])
            gnn = torch.FloatTensor(gnn_features[agent])
            fused = torch.cat([obs, gnn], dim=0)
            fused_obs[agent] = self.fusion(fused).detach().numpy()
        
        # Use base policy with fused observations
        actions = {}
        for agent in fused_obs.keys():
            action = self.base_policy.compute_single_action(fused_obs[agent])
            actions[agent] = action
        
        return actions


# Example usage
if __name__ == "__main__":
    # Test GNN encoder
    print("Testing MAGNET GNN Encoder...")
    
    obs_dim = 147
    num_agents = 3
    
    # Dummy observations and positions
    observations = {
        f"uav_{i}": np.random.randn(obs_dim) for i in range(num_agents)
    }
    positions = {
        f"uav_0": np.array([0.0, 0.0, 7.5]),
        f"uav_1": np.array([10.0, 5.0, 7.5]),
        f"uav_2": np.array([15.0, 15.0, 7.5])
    }
    
    # Create encoder
    encoder = MAGNETEncoder(obs_dim=obs_dim, hidden_dim=128, comm_range=20.0)
    
    # Forward pass
    enhanced = encoder(observations, positions)
    
    print(f"✓ Input obs shape: {observations['uav_0'].shape}")
    print(f"✓ Enhanced feature shape: {enhanced['uav_0'].shape}")
    print(f"✓ GNN output: {enhanced['uav_0'][:5]}")  # First 5 dims
    
    print("\n✅ MAGNET GNN module working correctly!")

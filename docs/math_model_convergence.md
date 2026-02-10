# Mathematical Modeling & Convergence Proofs

This document presents the rigorous theoretical framework underpinning the project: Multi-Agent PPO (MAPPO), Lagrangian Constrained Optimization, and Control Barrier Functions (CBF).

## 1. Problem Formulation: Dec-POMDP

We model the multi-UAV navigation problem as a **Decentralized Partially Observable Markov Decision Process (Dec-POMDP)** defined by the tuple $\mathcal{M} = \langle \mathcal{N}, \mathcal{S}, \mathcal{A}, P, R, \Omega, O, \gamma \rangle$:

*   $\mathcal{N} = \{1, ..., n\}$: Set of agents.
*   $\mathcal{S}$: Global state space (positions, velocities of all agents).
*   $\mathcal{A} = \times_{i \in \mathcal{N}} \mathcal{A}^i$: Joint action space.
*   $P(s'|s, a)$: Transition dynamics (Physics).
*   $R(s, a) = \sum_i r_i(s, a)$: Shared global reward (Cooperative setting).
*   $\Omega^i$: Local observation space.
*   $\gamma \in [0, 1)$: Discount factor.

**Objective**: Find a joint policy $\pi(a|o) = \prod_i \pi^i(a^i|o^i)$ maximizing:
$$ J(\pi) = \mathbb{E}_{\tau \sim \pi} \left[ \sum_{t=0}^{\infty} \gamma^t R(s_t, a_t) \right] $$

## 2. MAPPO: Convergence Properties

We utilize MAPPO, which applies the PPO objective in a Centralized Training, Decentralized Execution (CTDE) framework.

### Monotonic Improvement Theorem
Lower bound on policy performance improvement (Schulman et al., 2015):
$$ J(\pi_{new}) \geq J(\pi_{old}) - C \cdot \max_s D_{KL}(\pi_{old}(\cdot|s) || \pi_{new}(\cdot|s)) $$
where $C = \frac{2\gamma \epsilon}{(1-\gamma)^2}$.

By clipping the probability ratio $r_t(\theta)$, PPO approximates this trust region constraint, ensuring that the policy update step size is safe, preventing performance collapse.

## 3. Lagrangian Relaxation for Safety Constraints

We impose safety constraints (e.g., collision probability) $C_k(\pi) \leq d_k$.

### Primal-Dual Optimization
We convert the Constrained MDP (CMDP) to a min-max problem:
$$ \min_{\lambda \succeq 0} \max_{\theta} L(\theta, \lambda) = J(\pi_\theta) - \sum_k \lambda_k (C_k(\pi_\theta) - d_k) $$

### Convergence Proof Sketch
The update rule follows a two-timescale stochastic approximation:
1.  **Actor (Fast scale)**: $\theta_{k+1} = \theta_k + \alpha_k \nabla_\theta L(\theta_k, \lambda_k)$
2.  **Dual (Slow scale)**: $\lambda_{k+1} = \Gamma_\lambda [\lambda_k - \beta_k \nabla_\lambda L(\theta_k, \lambda_k)]$

**Theorem**: If learning rates satisfy $\sum \alpha_t = \infty, \sum \alpha_t^2 < \infty$ and $\lim (\beta_t / \alpha_t) = 0$, the iterates $(\theta_t, \lambda_t)$ converge almost surely to a local Nash Equilibrium of the Lagrangian game (Bhatnagar et al., 2009).

## 4. Control Barrier Functions (CBF) - Hard Safety

Lagrangian methods only guarantee satisfaction in *expectation*. For strict safety, we wrap the policy with a CBF filter.

### Forward Invariance
A set $\mathcal{C} = \{x | h(x) \geq 0\}$ is forward invariant if $\dot{h}(x) \geq -\alpha(h(x))$ for a class $\mathcal{K}$ function $\alpha$.

### QP Formulation
At each timestep, we solve a Quadratic Program (QP) to find the closest safe action $u^*$ to the RL action $a_{RL}$:

$$
\min_{u \in \mathcal{A}} \frac{1}{2} ||u - a_{RL}||^2
$$
$$
s.t. \quad L_f h(x) + L_g h(x) u \geq -\alpha h(x)
$$

**Proof of Safety**: Since the constraints are linear in $u$, if the QP is feasible at $x_0 \in \mathcal{C}$, then the resulting control law $u^*(x)$ renders $\mathcal{C}$ forward invariant, guaranteeing $h(x(t)) \geq 0 \ \forall t$.

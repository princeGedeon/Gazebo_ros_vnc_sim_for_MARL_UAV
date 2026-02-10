# 🧪 Guide: Test Agent Aléatoire & Analyse des Rewards

Ce guide explique comment lancer la simulation avec 3 drones, exécuter un agent qui prend des décisions aléatoires, et récupérer les données de récompense (rewards) pour vérifier que l'environnement fonctionne correctement (pénalités de crash, zones interdites, etc.).

## 1. Lancer le Simulateur
Ouvrez un terminal (dans Docker) et lancez l'environnement Gazebo + ROS 2 :

```bash
ros2 launch swarm_sim super_simulation.launch.py
```
*Attendez que Gazebo soit ouvert et que les drones soient visibles.*

## 2. Lancer l'Enregistrement (Script)

Ouvrez un **deuxième terminal** et exécutez le script d'enregistrement que nous venons de créer. Ce script va :
1.  Connecter 3 agents aux drones.
2.  Envoyer des commandes aléatoires pendant 1000 pas de temps (steps).
3.  Enregistrer les récompenses, collisions et consommation d'énergie dans un fichier CSV.

```bash
python3 scripts/record_random_agent_rewards.py
```

## 3. Analyser les Résultats

Le script crée un fichier : `outputs/random_rewards.csv`.

### Format du CSV
| Step | Agent | TotalReward | Collision | Energy | Coverage | Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | uav_0 | -0.5 | 0 | -0.1 | 0.0 | 0.1 |
| ... | ... | ... | ... | ... | ... | ... |

### Exemple de Visualisation (Python)
Vous pouvez utiliser ce petit code python pour tracer la courbe des rewards :

```python
import pandas as pd
import matplotlib.pyplot as plt

# Lire le fichier
df = pd.read_csv("outputs/random_rewards.csv")

# Filtrer pour un drone
uav0 = df[df['Agent'] == 'uav_0']

# Tracer
plt.figure(figsize=(10,6))
plt.plot(uav0['Step'], uav0['TotalReward'], label='Total Reward')
plt.plot(uav0['Step'], uav0['Energy'], label='Energy Penalty', alpha=0.5)
plt.title("Évolution des Rewards (Agent Aléatoire)")
plt.xlabel("Steps")
plt.ylabel("Reward")
plt.legend()
plt.grid(True)
plt.show()
```

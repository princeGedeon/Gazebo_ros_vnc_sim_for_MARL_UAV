# Installation sur WSL (Windows Subsystem for Linux) - Recommandé 🐧

Si Windows natif ou Docker posent trop de problèmes, **WSL est la meilleure solution**. C'est un vrai Linux (Ubuntu) qui tourne directement dans Windows, sans les lenteurs de Docker et sans les galères de compilation Windows.

## 1. Installer WSL (si ce n'est pas déjà fait)

Oouvre PowerShell en **Administrateur** et tape :

```powershell
wsl --install -d Ubuntu-24.04
```

*Si tu as déjà WSL mais une vieille version, tu peux installer la 24.04 spécifiquement : `wsl --install Ubuntu-24.04`.*

Une fois fini, **redémarre ton PC**.
Au redémarrage, une fenêtre Ubuntu va s'ouvrir pour finir l'installation (création nom d'utilisateur/mot de passe).

## 2. Préparer l'environnement WSL

Dans ton terminal Ubuntu (WSL), lance ces commandes :

```bash
# Aller dans ton dossier Windows depuis Linux (c'est magique)
cd /mnt/c/Users/guedj/Desktop/Gazebo_ros_vnc_sim_for_MARL_UAV

# Convertir les scripts Windows en format Linux (au cas où)
sudo apt-get update && sudo apt-get install -y dos2unix
dos2unix install_linux.sh run_linux.sh scripts/*.sh

# Donner les permissions d'exécution
chmod +x install_linux.sh run_linux.sh
```

## 3. Lancer l'installation Automatique 🚀

J'ai mis à jour le script pour qu'il installe **TOUT** (ROS 2 Jazzy, Gazebo Harmonic, Python, etc.) tout seul.

```bash
./install_linux.sh
```

*Cela va prendre quelques minutes (téléchargement de ROS 2 + compilation).*

## 4. Lancer la Simulation

Une fois l'installation finie :

```bash
./run_linux.sh
```

If the screen is black or slow, check your Windows GPU drivers (WSL uses them directly).

---

## 4.5. 🔍 Mode Manuel & Dépannage (Si rien ne marche)

Si `./run_linux.sh` ne lance rien ou que Gazebo plante ("Requesting list of world names"), fais ces étapes une par une :

### Étape 1 : Générer le Monde (Ville)
```bash
source install/setup.bash
# Génère le fichier SDF dans assets/worlds/generated_city.sdf
python3 src/swarm_sim_pkg/swarm_sim/assets/worlds/generate_city.py \
    --output src/swarm_sim_pkg/swarm_sim/assets/worlds/generated_city.sdf \
    --seed 42
```
*Si tu vois des erreurs ici, le problème est Python/Lark.*

### Étape 2 : Lancer Gazebo seul
Lance ça pour voir si l'affichage Gazebo fonctionne (sans le reste) :
```bash
# Force l'IP locale pour éviter le bug WSL
export GZ_IP=127.0.0.1
export GZ_PARTITION=sim_partition

# Lance la simulation minimaliste avec la ville générée
ros2 launch swarm_sim multi_ops.launch.py \
    num_drones:=3 \
    map_type:=world \
    map_file:=generated_city.sdf
```
*Si Gazebo s'ouvre, c'est gagné ! Tu peux passer à l'entraînement.*

### Étape 3 : Lancer l'Entraînement (dans un autre terminal)
```bash
source install/setup.bash
source venv/bin/activate
python3 src/swarm_sim_pkg/swarm_sim/training/train_mappo.py --num-drones 3 --no-gui
```

---

## 5. 🧠 Guide de l'Entraînement (Reinforcement Learning)

L'environnement de simulation est prêt pour l'apprentissage par renforcement Multi-Agent (MARL).

### 📍 Lancer un Scénario d'Entraînement
Tu as 3 scénarios pré-configurés. Tu peux les lancer via le script principal :

| Scénario | Description | Commande |
| :--- | :--- | :--- |
| **Case 1** | **MAPPO Standard**<br>Entraînement collaboratif basique. | `./run_linux.sh case_1` |
| **Case 2** | **MAPPO Lagrangien**<br>Avec contraintes de sécurité (Lagrangian). | `./run_linux.sh case_2` |
| **Case 3** | **MAPPO CBF**<br>Avec Control Barrier Functions (Sécurité forte). | `./run_linux.sh case_3` |

### 🛠️ Lancer l'Entraînement Manuellement (Sans Interface Graphique)
Si tu veux juste entraîner le modèle (beaucoup plus rapide) sans voir les drones :

1.  **Ouvre un terminal** et charge l'environnement :
    ```bash
    source /opt/ros/jazzy/setup.bash
    source install/setup.bash
    source venv/bin/activate
    ```

2.  **Lance le script Python directement** :
    ```bash
    # Exemple pour Case 1 (MAPPO)
    python3 src/swarm_sim_pkg/swarm_sim/training/train_mappo.py \
        --num-drones 3 \
        --total-timesteps 1000000 \
        --no-gui
    ```

### 📊 Visualiser les Résultats (Ray / TensorBoard)

Comme tu ne veux pas lancer ça en parallèle ("je veux même pas fait tout pas parallèle"), voici comment analyser les résultats **après ou pendant** l'entraînement, dans un terminal séparé.

**1. TensorBoard (Courbes d'apprentissage)**
C'est l'outil standard pour voir si tes drones apprennent (Reward qui monte, Loss qui descend).
```bash
# Ouvre un NOUVEAU terminal
source venv/bin/activate
tensorboard --logdir outputs/
```
👉 Ensuite, ouvre ton navigateur Windows et tape : **http://localhost:6006**

**2. Ray Dashboard (Avancé)**
Si tu veux voir les processus Ray en détail (RAM, CPU par acteur) :
*   Ray lance un dashboard automatiquement sur **http://localhost:8265** pendant l'entraînement.
*   Tu peux l'ouvrir directement dans ton navigateur Windows tant que le script d'entraînement tourne.

---

## 🛑 Comment tout arrêter proprement (Nettoyage)
Si tu lances les choses manuellement dans plusieurs terminaux, il faut penser à tout killer à la fin :

```bash
pkill -f gazebo
pkill -f gz
pkill -f python3
pkill -f ros2
pkill -f rviz2
```

---

## 🐛 Dépannage
Si Gazebo ne s'ouvre pas ou reste bloqué sur "Requesting world names" :
1.  **TUE TOUT** (Commande magique) :
    ```bash
    pkill -f gazebo; pkill -f gz; pkill -f python3; pkill -f ros2
    ```
2.  **Relance** : `./run_linux.sh`

---
### 🎮 Contrôle Manuel (Test Physique)
Pour piloter un drone avec le clavier sans IA :
```bash
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/uav_0/cmd_vel
```
*(Touches : `i`=avancer, `k`=stop, `j`/`l`=tourner)*

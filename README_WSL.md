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

## 5. 🧠 Entraînement & Logs (Benchmark)

Le script lance automatiquement l'entraînement (MAPPO par défaut).

### 📍 Où sont les fichiers ?
- **Logs Textuels** : `/tmp/training.log` (pour voir ce qui se passe en direct)
- **Modèles & Stats** : `outputs/case_1` (sauvegardes, checkpoints, benchmarks)

### 📊 Suivre l'entraînement en direct
Dans un **nouveau terminal** WSL :
```bash
# Voir la progression en temps réel
tail -f /tmp/training.log
```

### 📈 Visualiser avec TensorBoard
Pour voir les courbes d'apprentissage (Reward, Loss, etc.) :

1. Oouvre un nouveau terminal WSL.
2. Active l'environnement :
   ```bash
   source venv/bin/activate
   ```
3. Lance TensorBoard :
   ```bash
   tensorboard --logdir outputs/
   ```
4. Oouvre ton navigateur Windows et va sur : **http://localhost:6006**

---

## 🛠️ Commandes Utiles

- **Arrêter tout** : `pkill -f gazebo && pkill -f python3`
- **Re-compiler (si tu changes du code C++)** : `./install_linux.sh`
- **Changer de scénario** :
  ```bash
  ./scripts/autolaunch_full.sh case_2  # Pour le scénario Lagrangien
  ```

---

## 🐛 Dépannage & Mode Manuel

Si Gazebo ne s'ouvre pas ou si tu veux déboguer :

### 1. Voir pourquoi Gazebo plante
Les logs sont cachés par défaut. Pour les voir en direct :
```bash
./run_linux.sh --debug
```
*Cela affichera toutes les erreurs dans le terminal. Cherche des lignes rouges parlant de "Ogre", "OpenGL" ou "Display".*

Si tu as des erreurs d'affichage (écran noir), essaie de forcer le rendu logiciel :
```bash
export LIBGL_ALWAYS_SOFTWARE=1
./run_linux.sh
```

### 2. Lancer composant par composant (Mode Debug)
Au lieu de tout lancer d'un coup, tu peux ouvrir plusieurs terminaux et lancer chaque partie séparément :

**Terminal 1 : Gazebo + ROS 2**
```bash
source venv/bin/activate
source install/setup.bash
# Lancer Gazebo sans le fondre en arrière-plan
ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true
```

**Terminal 2 : Entraînement (RL)**
```bash
source venv/bin/activate
source install/setup.bash
# Lancer l'entraînement seul
python3 src/swarm_sim_pkg/swarm_sim/training/train_mappo.py --num-drones 3 --no-gui
```

### 3. Contrôler un drone manuellement (Teleop)
Si tu veux piloter un drone avec le clavier pour tester la physique :
```bash
source install/setup.bash
# Piloter le drone n°0 (uav_0)
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/uav_0/cmd_vel
```
*(Utilise les touches : `i`=avancer, `k`=stop, `j`=gauche, `l`=droite)*

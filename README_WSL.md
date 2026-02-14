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

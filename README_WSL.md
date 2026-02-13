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

### 💡 Astuce pour l'affichage (GUI)
WSL 2 gère maintenant l'affichage graphique (WSLg) nativement sur Windows 10/11. Gazebo et RViz devraient s'ouvrir comme des fenêtres normales.
Si l'affichage est noir ou lent, vérifie que tes pilotes NVIDIA Windows sont à jour (WSL utilise les drivers GPU de Windows).

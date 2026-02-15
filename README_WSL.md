# Simulation Gazebo MARL sur WSL (Ubuntu 24.04) 🐧

> **Note :** La méthode **VNC** (Bureau Virtuel) est la seule méthode 100% fiable pour éviter les bugs d'affichage de WSLg (écrans noirs, fenêtres qui ne s'ouvrent pas).

---

## 🚀 Installation & Lancement (Méthode VNC)

### 1. Installation Automatique
Dans ton terminal Ubuntu :

```bash
# 1. Installe tout (ROS 2 + Gazebo + Dépendances)
./install_linux.sh

# 2. Installe le Bureau XFCE4 + VNC (Pour l'affichage)
./scripts/setup_wsl_vnc.sh
```

### 2. Lancer le Bureau Virtuel
Avant de lancer la simulation, démarre le bureau Linux :

```bash
./scripts/run_vnc_session.sh
```

👉 **Ouvre RealVNC Viewer sur Windows** et connecte-toi à : **`localhost:5901`**  
*(Mot de passe par défaut : `password`)*

### 3. Lancer la Simulation (DANS LE VNC)
Une fois dans le bureau VNC (fenêtre grise XFCE), ouvre un terminal (clic droit -> Open Terminal) et lance :

```bash
cd ~/Desktop/Gazebo_ros_vnc_sim_for_MARL_UAV
./run_linux.sh
```
*Cela va tout lancer : Gazebo + RViz + Entraînement.*

---

## 🛠️ Entraînement & Logs (Benchmark)

Les résultats sont sauvegardés dans le dossier `outputs/` à la racine :

*   **Logs en direct** : `tail -f /tmp/gazebo_sim.log`
*   **Visualisation (TensorBoard)** :
    ```bash
    source venv/bin/activate
    tensorboard --logdir outputs/
    ```
    (Ouvre `http://localhost:6006` sur Windows)

---

## 🐛 Dépannage
Si le build plante par manque de mémoire ("Killed"):
```bash
./install_linux.sh
```
*(Le script gère désormais la mémoire automatiquement).*

Si tu veux réinitialiser l'environnement :
```bash
rm -rf build install log venv
./cleanup_linux.sh
```

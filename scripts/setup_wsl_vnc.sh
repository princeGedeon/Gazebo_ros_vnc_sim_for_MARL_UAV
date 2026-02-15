#!/bin/bash
set -e

echo "🖥️ Installing VNC Server (XFCE4 + TigerVNC)..."

# 1. Update & Install Desktop Env
sudo apt-get update
sudo apt-get install -y xfce4 xfce4-goodies tigervnc-standalone-server tigervnc-common dbus-x11 xfonts-base x11-xserver-utils

# 2. Configure VNC Password
if [ ! -f ~/.vnc/passwd ]; then
    echo "🔑 Configuring VNC Password..."
    mkdir -p ~/.vnc
    # Set default password "password" (can be changed)
    echo "password" | vncpasswd -f > ~/.vnc/passwd
    chmod 600 ~/.vnc/passwd
fi

# 3. Configure xstartup
echo "⚙️ Configuring xstartup..."
mkdir -p ~/.vnc
cat > ~/.vnc/xstartup <<EOF
#!/bin/sh
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
[ -x /etc/vnc/xstartup ] && exec /etc/vnc/xstartup
[ -r \$HOME/.Xresources ] && xrdb \$HOME/.Xresources
xsetroot -solid grey
vncconfig -iconic &
dbus-launch --exit-with-session startxfce4 &
EOF
chmod +x ~/.vnc/xstartup

echo "✅ VNC Setup Complete."
echo "   Run './scripts/run_vnc.sh' to start the desktop."

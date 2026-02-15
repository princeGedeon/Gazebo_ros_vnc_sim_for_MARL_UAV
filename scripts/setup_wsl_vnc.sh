#!/bin/bash
set -e

echo "🖥️ Installing VNC Server (XFCE4 + TigerVNC)..."

# 1. Update & Install Desktop Env
sudo apt-get update
sudo apt-get install -y xfce4 xfce4-goodies tigervnc-standalone-server tigervnc-common dbus-x11

# 2. Configure VNC Password
if [ ! -f ~/.vnc/passwd ]; then
    echo "🔑 Configuring VNC Password..."
    mkdir -p ~/.vnc
    # Set default password "vscode" (can be changed)
    echo "password" | vncpasswd -f > ~/.vnc/passwd
    chmod 600 ~/.vnc/passwd
fi

# 3. Configure xstartup
echo "⚙️ Configuring xstartup..."
cat > ~/.vnc/xstartup <<EOF
#!/bin/sh
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec startxfce4
EOF
chmod +x ~/.vnc/xstartup

echo "✅ VNC Setup Complete."
echo "   Run './scripts/run_vnc.sh' to start the desktop."

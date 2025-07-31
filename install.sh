#!/usr/bin/env bash
set -euo pipefail

# Auto-detect the non-root user who invoked sudo (or current user)
INSTALL_USER="${SUDO_USER:-${USER}}"
USER_HOME="$(eval echo ~${INSTALL_USER})"

REPO_URL="https://github.com/greatgaga/PiFi"
PIFI_DIR="$USER_HOME/PiFi"
APP_DIR="$PIFI_DIR/web"
SERVICE_NAME="pifi-web"
PYTHON_CMD="python3"

# Accept any changed release info for Raspberry Pi repos
APT_OPTS="-o Acquire::AllowReleaseInfoChange::Origin=true -o Acquire::AllowReleaseInfoChange::Label=true"

echo "==> Detected install user: $INSTALL_USER"
echo "==> User home directory: $USER_HOME"

echo "==> 1. Clone repo if needed"
if [ ! -d "$PIFI_DIR" ]; then
  sudo -u "$INSTALL_USER" git clone "$REPO_URL" "$PIFI_DIR"
fi

echo "==> 2. Update & install system packages"
sudo apt-get update $APT_OPTS
sudo apt-get upgrade -y $APT_OPTS
sudo apt-get install -y $APT_OPTS \
    git \
    ${PYTHON_CMD} \
    ${PYTHON_CMD}-venv \
    ${PYTHON_CMD}-dev \
    build-essential \
    hostapd \
    dnsmasq \
    nmap \
    python3-netifaces \
    python3-pip \
    dos2unix \
    conntrack \
    iptables \
    iptables-persistent \
    netfilter-persistent

echo "==> 3. Stop any existing interference (optional)"
sudo pkill -f wpa_supplicant.*wlan1 || true

echo "==> 4. Set up Python venv & install packages"
cd "$APP_DIR"
${PYTHON_CMD} -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install \
    flask \
    flask-socketio \
    eventlet \
    scapy \
    python-nmap \
    netifaces \
    dnslib

echo "==> 5. Create systemd service to run app.py on boot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
sudo tee "$SERVICE_FILE" >/dev/null <<EOF
[Unit]
Description=PiFi Flask Web + Evil Twin (app only)
After=network.target

[Service]
Type=simple
User=${INSTALL_USER}
WorkingDirectory=${USER_HOME}/PiFi
Environment=PATH=${APP_DIR}/venv/bin:\${PATH}
ExecStart=/bin/bash -c 'PYTHONPATH=\$(pwd) ${PYTHON_CMD} web/app.py'
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "==> 6. Enable and start the pifi-web service"
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl start ${SERVICE_NAME}

echo "✅ Installation complete—on reboot, only app.py will run as service under $INSTALL_USER"

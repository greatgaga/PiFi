#!/usr/bin/env bash
set -euo pipefail

# Detect invoking user
INSTALL_USER="${SUDO_USER:-${USER}}"
USER_HOME="$(eval echo ~${INSTALL_USER})"

REPO_URL="https://github.com/greatgaga/pifi"
PIFI_DIR="$USER_HOME/pifi"
APP_DIR="$PIFI_DIR/web"
SERVICE_NAME="pifi-web"
PYTHON_CMD="python3"

APT_OPTS="-o Acquire::AllowReleaseInfoChange::Origin=true -o Acquire::AllowReleaseInfoChange::Label=true"

echo "==> Detected install user: $INSTALL_USER"
echo "==> User home directory: $USER_HOME"

echo "==> 1. Clone repo if not present"
if [ ! -d "$PIFI_DIR" ]; then
  sudo -u "$INSTALL_USER" git clone "$REPO_URL" "$PIFI_DIR"
fi

echo "==> 2. Update and install system packages"
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

echo "==> 3. Stop conflicting services"
sudo systemctl stop wpa_supplicant.service || true
sudo pkill -f wpa_supplicant.*wlan1 || true

echo "==> 4. Set up Python virtual environment"
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

echo "==> 5. Create systemd service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
sudo tee "$SERVICE_FILE" >/dev/null <<EOF
[Unit]
Description=PiFi Flask Web + Evil Twin (app.py)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${INSTALL_USER}
WorkingDirectory=${PIFI_DIR}
Environment=PATH=${APP_DIR}/venv/bin:\${PATH}
ExecStart=${PYTHON_CMD} web/app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "==> 6. Reload systemd and enable service"
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl restart ${SERVICE_NAME}

echo "✅ PiFi installation complete. Service '${SERVICE_NAME}' will run at boot."

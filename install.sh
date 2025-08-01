#!/usr/bin/env bash
set -euo pipefail

# Detect invoking user
INSTALL_USER="${SUDO_USER:-${USER}}"
USER_HOME="$(eval echo ~${INSTALL_USER})"

REPO_URL="https://github.com/greatgaga/pifi"
PIFI_DIR="$USER_HOME/pifi"
APP_DIR="$PIFI_DIR/web"
PYTHON_CMD="python3"
LOG_FILE="$USER_HOME/pifi_cron.log"

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

echo "==> 3. Disable hostapd and stop conflicting services"
sudo systemctl disable hostapd.service || true
sudo systemctl stop hostapd.service || true
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

echo "==> 5. Add cron @reboot task"
CRON_LINE="@reboot cd $PIFI_DIR && PYTHONPATH=\$(pwd) $APP_DIR/venv/bin/python3 web/app.py >> $LOG_FILE 2>&1"

# Remove any existing similar lines to avoid duplication
( sudo crontab -l 2>/dev/null | grep -v 'web/app.py' ; echo "$CRON_LINE" ) | sudo crontab -

echo "✅ PiFi installation complete."
echo "ℹ️  'app.py' will run at startup using cron (@reboot), and output will be logged to: $LOG_FILE"
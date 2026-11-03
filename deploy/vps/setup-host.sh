#!/usr/bin/env bash
# One-time preparation of a fresh Ubuntu 24.04 VPS (e.g. AWS Lightsail) for RAISE.
# Run once as the default sudo user:  sudo bash deploy/vps/setup-host.sh
# Idempotent: safe to re-run.
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo: sudo bash $0" >&2
  exit 1
fi
OPERATOR="${SUDO_USER:-ubuntu}"

echo "==> OS updates"
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get upgrade -y -q
apt-get install -y -q ca-certificates curl git openssl unattended-upgrades
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "==> Docker Engine + Compose plugin (official apt repository)"
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -q
  apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

echo "==> Docker log rotation (prevents container logs filling the disk)"
mkdir -p /etc/docker
if [[ ! -f /etc/docker/daemon.json ]]; then
  cat > /etc/docker/daemon.json <<'JSON'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "5" }
}
JSON
fi
systemctl enable --now docker
systemctl restart docker
usermod -aG docker "$OPERATOR"

echo "==> 2 GB swap (headroom for the first knowledge bootstrap)"
if ! swapon --show | grep -q '/swapfile'; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  sysctl -w vm.swappiness=10
  echo 'vm.swappiness=10' > /etc/sysctl.d/99-raise-swap.conf
fi

echo "==> Application directory"
mkdir -p /opt/raise
chown "$OPERATOR:$OPERATOR" /opt/raise

echo
echo "Done. Log out and back in (so '$OPERATOR' picks up the docker group), then:"
echo "  cd /opt/raise && git clone https://github.com/NizarSH98/Farmers_Chatbot_V2.git ."
docker --version
docker compose version

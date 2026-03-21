#!/bin/bash

# ==============================================================
# Minimal setup script for Ubuntu Server 24.04 LTS
# Installs: Docker Engine 29.3.0, .NET 10 SDK, OpenSSH
# Disables: unnecessary background services
# Optimizes: CPU governor, swap, journald
# ==============================================================


set -e

echo "=== Updating system ==="
sudo apt update -y
sudo apt upgrade -y



# ==============================================================
# SSH — enable remote access
# ==============================================================

echo "=== Enabling SSH ==="

sudo apt install -y openssh-server
sudo systemctl enable --now ssh



# ==============================================================
# Disable unnecessary services to reduce background noise
# during benchmark execution
# ==============================================================

echo "=== Disabling unnecessary services ==="

for svc in \
    unattended-upgrades \
    snapd \
    avahi-daemon \
    cups \
    cups-browsed \
    bluetooth \
    ModemManager \
    multipathd \
    thermald; do
    sudo systemctl disable --now "$svc" 2>/dev/null || true
done



# ==============================================================
# CPU governor — set to performance mode
# Prevents dynamic frequency scaling from causing jitter in results
# ==============================================================

echo "=== Setting CPU governor to performance ==="

sudo apt install -y cpufrequtils
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpufrequtils

for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance | sudo tee "$cpu"
done


# ==============================================================
# Disable swap
# Swap activity during benchmark would distort timing measurements
# ==============================================================

echo "=== Disabling swap ==="

sudo swapoff -a
# Comment out swap entries in fstab to persist across reboots
sudo sed -i '/\bswap\b/ s/^/#/' /etc/fstab



# ==============================================================
# Journald — store logs in RAM only
# Reduces disk I/O during benchmark execution
# ==============================================================

echo "=== Configuring journald ==="

sudo sed -i 's/^#*Storage=.*/Storage=volatile/' /etc/systemd/journald.conf
sudo systemctl restart systemd-journald



# ==============================================================
# Install Docker Engine 29.3.0 (latest stable, March 2026)
# ==============================================================

echo "=== Installing Docker Engine 29.3.0 ==="

sudo apt install -y ca-certificates curl

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update -y

# Install exact version
DOCKER_VERSION="5:29.3.0-1~ubuntu.24.04~noble"
sudo apt install -y \
    docker-ce=$DOCKER_VERSION \
    docker-ce-cli=$DOCKER_VERSION \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

# Pin Docker version to prevent accidental upgrades
sudo apt-mark hold docker-ce docker-ce-cli

# Add current user to docker group to allow running Docker without sudo
sudo usermod -aG docker "$USER"


# ==============================================================
# Install .NET 10 SDK (LTS, supported until November 2028)
# ==============================================================

sudo apt install -y dotnet-sdk-10.0



# ==============================================================

echo "=== Setup complete ==="
echo "REBOOT REQUIRED to apply Docker group changes."
echo "After reboot, run: sudo dotnet run --project <benchmark_project>"
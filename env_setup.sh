#!/bin/bash

# ==============================================================
# Setup script for Ubuntu Server 24.04 LTS
# Installs: Docker Engine 29.3.0, .NET 10 SDK, OpenSSH
# Disables: unnecessary background services
# Optimizes: CPU governor, swap, journald
# ==============================================================

set -e

echo -e "\n=== Updating system ==="
sudo apt update -y
sudo apt upgrade -y

# ==============================================================
# SSH — enable remote access
# ==============================================================
echo -e "\n=== Installing and enabling SSH ==="
sudo apt install -y openssh-server
sudo systemctl enable --now ssh


# ==============================================================
# Disable unnecessary services, sockets, and timers
# to reduce background noise during benchmark execution
# ==============================================================
echo -e "\n=== Disabling unnecessary services, sockets, and timers ==="

# Disable standard services
for svc in unattended-upgrades.service snapd.service multipathd.service thermald.service bluetooth.service ModemManager.service avahi-daemon.service cups.service cups-browsed.service; do
    if systemctl list-unit-files | grep -q "^${svc}"; then
        sudo systemctl disable --now "${svc}"
        if systemctl list-unit-files | grep -q "^$svc.socket"; then
            sudo systemctl disable --now "$svc.socket"
        fi
        echo "$svc -> disabled"
    else
        echo "$svc -> not installed, skipped"
    fi
done

# Disable timers
for timer in apt-daily.timer apt-daily-upgrade.timer motd-news.timer fstrim.timer snapd.snap-repair.timer systemd-sysupdate.timer; do
    if systemctl list-unit-files | grep -q "^$timer"; then
        sudo systemctl disable --now "$timer"
        echo "$timer -> disabled"
    else
        echo "$timer -> not installed, skipped"
    fi
done

# Disable crash reporting and cloud-init services
for svc in apport.service apport-autoreport.path apport-forward.socket cloud-init cloud-config cloud-final cloud-init-local pollinate.service; do
    if systemctl list-unit-files | grep -q "^$svc"; then
        sudo systemctl disable --now "$svc"
        echo "$svc -> disabled"
    else
        echo "$svc -> not installed, skipped"
    fi
done

# Show status of main disabled services
echo -e "\n=== Status of disabled services ==="
for svc in unattended-upgrades snapd multipathd thermald; do
    echo -n "$svc -> "
    echo "enabled=$(systemctl is-enabled "$svc" 2>/dev/null) active=$(systemctl is-active "$svc" 2>/dev/null)"
done


# ==============================================================
# Disable Transparent Huge Pages (for stable latency in benchmarks)
# ==============================================================
echo -e "\n=== Disabling Transparent Huge Pages ==="

if [ -f /sys/kernel/mm/transparent_hugepage/enabled ]; then
    echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
    echo never | sudo tee /sys/kernel/mm/transparent_hugepage/defrag
fi

sudo tee /etc/systemd/system/disable-thp.service > /dev/null <<'EOF'
[Unit]
Description=Disable Transparent Huge Pages
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'echo never > /sys/kernel/mm/transparent_hugepage/enabled; echo never > /sys/kernel/mm/transparent_hugepage/defrag'

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now disable-thp.service



# ==============================================================
# CPU governor — set to performance mode
# Prevents dynamic frequency scaling from causing jitter in benchmark results
# ==============================================================
echo -e "\n=== Setting CPU governor to performance ==="
sudo apt install -y cpufrequtils
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpufrequtils

for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance | sudo tee "$cpu"
done

# ==============================================================
# Ensure CPU governor is set to performance after every reboot
# ==============================================================
echo -e "\n=== Creating systemd service for CPU performance governor ==="
sudo tee /etc/systemd/system/perf-cpu.service > /dev/null <<'EOF'
[Unit]
Description=Set CPU governor to performance
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance | tee $cpu; done'

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now perf-cpu.service

# ==============================================================
# Disable swap
# Swap activity during benchmark would distort timing measurements
# ==============================================================
echo -e "\n=== Disabling swap ==="
sudo swapoff -a
sudo sed -i '/\bswap\b/ s/^/#/' /etc/fstab

# ==============================================================
# Journald — store logs in RAM only
# Reduces disk I/O during benchmark execution
# ==============================================================
echo -e "\n=== Configuring journald to volatile storage (RAM) ==="
sudo sed -i 's/^#*Storage=.*/Storage=volatile/' /etc/systemd/journald.conf
sudo systemctl restart systemd-journald

# ==============================================================
# Install Docker Engine 29.3.0 (latest stable, March 2026)
# ==============================================================
echo -e "\n=== Installing Docker Engine 29.3.0 ==="
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

DOCKER_VERSION="5:29.3.0-1~ubuntu.24.04~noble"
sudo apt install -y \
    docker-ce=$DOCKER_VERSION \
    docker-ce-cli=$DOCKER_VERSION \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

# Pin Docker version to prevent accidental upgrades
sudo apt-mark hold docker-ce docker-ce-cli
sudo usermod -aG docker $(logname)

# ==============================================================
# Install .NET 10 SDK (specific version for reproducibility)
# ==============================================================

echo -e "\n=== Installing .NET 10 SDK ==="

DOTNET_VERSION="10.0.104-0ubuntu1~24.04.1"

sudo apt install -y dotnet-sdk-10.0=$DOTNET_VERSION

# Lock SDK to prevent upgrades
sudo apt-mark hold dotnet-sdk-10.0

# ==============================================================
echo -e "\n=== Setup complete ==="
echo "REBOOT REQUIRED to apply Docker group changes."
echo "After reboot, run: sudo dotnet run --project <benchmark_project>"
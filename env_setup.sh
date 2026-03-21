#!/bin/bash

# ==============================================================
# Setup script for Ubuntu Server environment for DB benchmarks
# ==============================================================

echo "=== Updating system ==="
sudo apt update -y
sudo apt upgrade -y

# to do

echo "=== Setup complete ==="
echo "Reboot recommended to apply user group changes for Docker."
#!/bin/bash
set -e


if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo: sudo ./run_benchmark.sh"
  exit 1
fi


ACTUAL_USER="${SUDO_USER:-$USER}"
export REPO_ROOT=$(pwd)


docker compose -f benchmark_scr/db_setup/docker-compose.yml up -d


echo "=========================================="
echo "1. Building the C# application (Release)"
echo "=========================================="


rm -rf benchmark_scr/bin benchmark_scr/obj benchmark_scr/BenchmarkDotNet.Bin benchmark_scr/BenchmarkDotNet.Artifacts

sudo -u "$ACTUAL_USER" dotnet publish benchmark_scr/benchmark_scr.csproj -c Release -r linux-x64 /p:PublishSingleFile=true


echo "========================================"
echo "2. Running Performance Benchmarks"
echo "========================================"

cd benchmark_scr
BASE_DIR="bin/Release/net9.0/linux-x64/publish"
DATASETS=("1k" "10k" "100k")

chmod +x "$BASE_DIR/benchmark_scr"

for size in "${DATASETS[@]}"; do
    echo ""

    if [ "$size" == "1k" ]; then
        FOLDER_NAME="small"
    elif [ "$size" == "10k" ]; then
        FOLDER_NAME="medium"
    elif [ "$size" == "100k" ]; then
        FOLDER_NAME="large"
    fi

    echo "Cleaning up old results for $size ($FOLDER_NAME)..."
    rm -rf "$REPO_ROOT/results/$FOLDER_NAME"

    echo ">>> Testing dataset: $size <<<"
    "./$BASE_DIR/benchmark_scr" "$size"
done

cd "$REPO_ROOT"


echo "========================================"
echo "3. Generating Charts"
echo "========================================"

chown -R "$ACTUAL_USER:$ACTUAL_USER" results/

add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.13 python3.13-venv

cd analysis_scr
sudo -u "$ACTUAL_USER" python3.13 -m venv .venv
sudo -u "$ACTUAL_USER" .venv/bin/pip install matplotlib pandas scipy
sudo -u "$ACTUAL_USER" .venv/bin/python scr.py


echo "===================================================="
echo "SUCCESS! Benchmarks finished and charts generated."
echo "===================================================="

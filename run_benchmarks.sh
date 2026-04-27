#!/bin/bash
set -e


echo "=========================================="
echo "1. Building the C# application (Release)"
echo "=========================================="

dotnet publish -c Release -r linux-x64 --self-contained true /p:PublishSingleFile=true benchmark_scr/benchmark_scr.csproj



echo "========================================"
echo "2. Running Performance Benchmarks"
echo "========================================"


BASE_DIR="benchmark_scr/bin/Release/net9.0/linux-x64"
DATASETS=("1k" "10k" "100k")

chmod +x "$BASE_DIR/benchmark_scr"

echo "Cleaning up old results..."
sudo rm -rf benchmark_scr/artifacts/
echo ""

for size in "${DATASETS[@]}"; do
    echo ">>> Testing dataset: $size <<<"
    sudo "$BASE_DIR/benchmark_scr" "$size"
done


# Because C# ran as root, the CSVs and logs are owned by root.
# This reverts ownership of the 'artifacts' folder back to the current user.
sudo chown -R $USER:$USER benchmark_scr/artifacts/


echo "========================================"
echo "4. Generating Charts"
echo "========================================"

sudo apt update
sudo apt install -y python3.13 python3.13-venv

cd charts
python3.13 -m venv .venv
source .venv/bin/activate
pip install matplotlib pandas

python generate_charts.py


echo "===================================================="
echo "SUCCESS! Benchmarks finished and charts generated."
echo "===================================================="
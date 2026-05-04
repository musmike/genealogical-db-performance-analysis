#!/bin/bash
set -e


if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo: sudo ./run_benchmark.sh"
  exit 1
fi


ACTUAL_USER="${SUDO_USER:-$USER}"
export REPO_ROOT=$(pwd)


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
    nice -n -10 "./$BASE_DIR/benchmark_scr" "$size"
done

cd "$REPO_ROOT"


echo "========================================"
echo "3. Generating Charts"
echo "========================================"

chown -R "$ACTUAL_USER:$ACTUAL_USER" results/

cd analysis_scr
sudo -u "$ACTUAL_USER" .venv/bin/python scr.py
cd ..


echo "========================================"
echo "4. Saving Environment Snapshot"
echo "========================================"

docker start postgres_db neo4j_db >/dev/null 2>&1

ENV_FILE="$REPO_ROOT/results/environment.txt"
mkdir -p "$REPO_ROOT/results"

{
    echo "=================================================="
    echo " BENCHMARK ENVIRONMENT SNAPSHOT"
    echo " Generated: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "=================================================="

    echo ""
    echo "--- Operating System ---"
    lsb_release -d -s 2>/dev/null || grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"' || true
    echo "Kernel: $(uname -r)"
    echo "Architecture: $(uname -m)"

    echo ""
    echo "--- CPU ---"
    CPU_MODEL=$(grep -m1 "model name" /proc/cpuinfo | cut -d: -f2 | xargs || true)
    CPU_CORES=$(nproc --all)
    echo "Model: $CPU_MODEL"
    echo "Logical cores: $CPU_CORES"

    echo "Frequency per core (MHz):"
    for cpu in /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq; do
        core=$(echo "$cpu" | grep -oP 'cpu\d+' || true)
        freq_khz=$(cat "$cpu" 2>/dev/null || echo "N/A")
        if [ "$freq_khz" != "N/A" ] &&[ -n "$freq_khz" ]; then
            echo "  $core: $((freq_khz / 1000)) MHz"
        else
            echo "  $core: N/A"
        fi
    done

    echo "Governor: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo 'N/A')"
    max_freq=$(cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq 2>/dev/null || echo 'N/A')
    if [ "$max_freq" != "N/A" ] && [ -n "$max_freq" ]; then
        echo "Max frequency (cpu0): $((max_freq / 1000)) MHz"
    else
        echo "Max frequency (cpu0): N/A"
    fi

    echo "Turbo Boost / Core Performance Boost:"
    if [ -f /sys/devices/system/cpu/intel_pstate/no_turbo ]; then
        if [ "$(cat /sys/devices/system/cpu/intel_pstate/no_turbo)" -eq 0 ]; then
            echo "  Enabled (Intel)"
        else
            echo "  Disabled (Intel)"
        fi
    elif [ -f /sys/devices/system/cpu/cpufreq/boost ]; then
        if [ "$(cat /sys/devices/system/cpu/cpufreq/boost)" -eq 1 ]; then
            echo "  Enabled (AMD/General)"
        else
            echo "  Disabled (AMD/General)"
        fi
    else
        echo "  Status unknown / Not supported by current driver"
    fi

    echo ""
    echo "--- Memory ---"
    MEM_TOTAL=$(free -h | awk '/^Mem:/ {print $2}')
    MEM_FREE=$(free -h | awk '/^Mem:/ {print $7}') # $7 to 'Available'
    echo "Total RAM: $MEM_TOTAL"
    echo "Available at snapshot time: $MEM_FREE"
    SWAP_STATUS=$(swapon --show 2>/dev/null | grep -v "^NAME" | wc -l || echo 0)
    echo "Swap: $([ "$SWAP_STATUS" -eq 0 ] && echo 'disabled' || swapon --show)"

    echo ""
    echo "--- Storage ---"
    echo "Block devices:"
    lsblk -d -o NAME,MODEL,SIZE,ROTA,TYPE 2>/dev/null | grep -v "^loop" || true
    echo ""
    echo "Mount points:"
    df -h --output=source,fstype,size,used,avail,target 2>/dev/null | grep -E "^/dev" || true

    echo ""
    echo "--- Kernel Settings & Background Services ---"
    echo "Transparent Huge Pages: $(cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || echo 'N/A')"
    echo "THP defrag: $(cat /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null || echo 'N/A')"
    echo "journald: $(grep "^Storage=" /etc/systemd/journald.conf 2>/dev/null || echo 'Storage=not set')"
    echo "Dirty ratio: $(cat /proc/sys/vm/dirty_ratio 2>/dev/null)% (default: 20%)"
    echo "Swappiness: $(cat /proc/sys/vm/swappiness 2>/dev/null) (default: 60)"
    echo ""
    echo "Disabled Services Status (should be 'inactive' or 'not installed'):"
    for svc in unattended-upgrades snapd multipathd thermald bluetooth cups avahi-daemon; do
        st=$(systemctl is-active "$svc" 2>/dev/null || true)
        if [ -z "$st" ] || [ "$st" = "unknown" ]; then
            st="not installed"
        fi
        printf "  %-25s %s\n" "$svc:" "$st"
    done

    echo ""
    echo "--- Software Versions ---"
    echo ".NET SDK: $(sudo -u "$ACTUAL_USER" dotnet --version 2>/dev/null || echo 'N/A')"
    echo "Python: $(python3.13 --version 2>/dev/null || echo 'N/A')"
    echo "Docker Engine: $(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1 || echo 'N/A')"
    echo "docker compose: $(docker compose version | grep -oP '\d+\.\d+\.\d+' | head -1 || echo 'N/A')"
    echo "PostgreSQL DB: $(docker exec postgres_db postgres -V 2>/dev/null || echo 'N/A')"
    echo "Neo4j DB: $(docker exec neo4j_db cypher-shell --version 2>/dev/null || echo 'N/A')"

    echo ""
    echo "--- C# NuGet Packages (from .csproj) ---"
    grep -oP '(?<=PackageReference Include=")[^"]+(?="[^>]+Version="[^"]+)' benchmark_scr/benchmark_scr.csproj | while read -r pkg; do
        ver=$(grep "PackageReference Include=\"$pkg\"" benchmark_scr/benchmark_scr.csproj | grep -oP '(?<=Version=")[^"]+' || true)
        echo "$pkg: $ver"
    done || true

    echo ""
    echo "--- Python Packages (analysis_scr venv) ---"
    sudo -u "$ACTUAL_USER" analysis_scr/.venv/bin/pip show matplotlib pandas scipy 2>/dev/null \
        | grep -E "^(Name|Version):" \
        | paste - - \
        | awk '{print $2 ": " $4}' || echo "N/A"

    echo ""
    echo "--- Python Packages (data_generator venv) ---"
    sudo -u "$ACTUAL_USER" data_generator/.venv/bin/pip show matplotlib 2>/dev/null \
        | grep -E "^(Name|Version):" \
        | paste - - \
        | awk '{print $2 ": " $4}' || echo "N/A"

    echo ""
    echo "--- Docker Containers at Benchmark Time ---"
    docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" 2>/dev/null | grep -E "^(NAMES|postgres_db|neo4j_db)" || echo "N/A"

    echo ""
    echo "--- Docker Container Resource Limits ---"
    for container in postgres_db neo4j_db; do
        echo "[$container]"
        MEM=$(docker inspect "$container" --format '{{.HostConfig.Memory}}' 2>/dev/null || true)
        CPUSET=$(docker inspect "$container" --format '{{.HostConfig.CpusetCpus}}' 2>/dev/null || true)
        MEMSWAP=$(docker inspect "$container" --format '{{.HostConfig.MemorySwap}}' 2>/dev/null || true)

        MEM=${MEM:-0}
        MEMSWAP=${MEMSWAP:-0}

        if [ "$MEM" -gt 0 ]; then
            echo "  Memory limit: $((MEM / 1024 / 1024 / 1024)) GB"
        else
            echo "  Memory limit: No limit"
        fi

        if [ "$MEMSWAP" -gt 0 ] &&[ "$MEMSWAP" -ne "$MEM" ]; then
            echo "  Memory+swap limit: $((MEMSWAP / 1024 / 1024 / 1024)) GB"
        elif [ "$MEMSWAP" -eq "$MEM" ] && [ "$MEM" -gt 0 ]; then
            echo "  Memory+swap limit: $((MEMSWAP / 1024 / 1024 / 1024)) GB (Swap DISABLED explicitly)"
        else
            echo "  Memory+swap limit: No limit"
        fi

        echo "  CPUset: ${CPUSET:-No restriction}"
    done

} | tee "$ENV_FILE"

chown "$ACTUAL_USER:$ACTUAL_USER" "$ENV_FILE"
echo ""
echo "Environment snapshot saved to: $ENV_FILE"

echo "===================================================="
echo "SUCCESS! Benchmarks finished and charts generated."
echo "===================================================="

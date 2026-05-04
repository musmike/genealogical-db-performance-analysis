# Database Benchmark Setup and Measurement

This guide explains how to replicate the database performance study environment.

## Experimental Environment

The benchmarks were conducted using the following hardware and software stack. To ensure the reproducibility of the results, it is recommended to run the tests in a closely matched environment:

| Category | Component | Specification |
| :--- | :--- | :--- |
| **Hardware** | **CPU** | Intel Core i7-10700K, 3.8 GHz, up to 5.10 GHz, 16M Cache |
| | **RAM** | Kingston FURY 32GB (2x16GB) 3600MHz CL16 |
| | **Storage** | Samsung 1TB M.2 PCIe NVMe 970 EVO Plus |
| **System** | **OS** | Ubuntu Server 24.04.04 LTS (minimized) |
| | **Kernel** | Linux 6.8.0-110-generic |
| **Docker** | **Engine** | 29.3.0 |
| | **Container Limits** | 8 GB RAM, 8 CPUs (shared, one database active at a time) |
| | **Docker Compose** | 5.1.3 |
| **Software** | **PostgreSQL** | 17.9 |
| | **Neo4j** | 5.26.23-enterprise (LTS) |
| | **.NET SDK** | 9.0.116 |
| | **Npgsql (C#)** | 10.0.2 |
| | **Neo4j.Driver (C#)** | 6.0.0 |
| | **BenchmarkDotNet (C#)** | 0.15.8 |
| | **Python** | 3.13.13 |
| | **Matplotlib (Python)** | 3.10.1 |
| | **Pandas (Python)** | 2.3.0 |
| | **SciPy (Python)** | 1.15.1 |


## 1. Install Ubuntu Server 24.04 LTS

During the installation, choose the following options:

- **Ubuntu Server (minimized)** – only essential packages installed, no GUI.  
- **Do not search for third-party drivers unless necessary** – keep the system clean.
- **Partitioning** – use a single ext4 partition for `/` (e.g., 150 GB).  
- **Do not select any featured server snaps** – avoid unnecessary background services.  


## 2. Clone the repository

Before cloning the repository, make sure Git is installed:

```bash
sudo apt update
sudo apt install -y git
```

Then clone the repository containing the benchmark scripts:

```bash
git clone <repository_url>
cd <repository_folder>
```


## 3. Set up the environment

Run the environment setup script `env_setup.sh` to install all required dependencies (including Docker, Python and the .NET SDK) and apply system-level optimizations to ensure stable and reproducible benchmark results. You will be required to enter your sudo password during execution, as administrative privileges are needed.

```bash
chmod +x env_setup.sh
./env_setup.sh
```

Once the script completes, **reboot the system** to apply group changes:

```bash
sudo reboot
```


## 4. Run the benchmark

After reboot, you can run the entire benchmark suite using the orchestrator script. 
This script will automatically build the C# project, run tests for all dataset sizes (1k, 10k, 100k), and generate the final charts.

```bash
chmod +x run_benchmark.sh
sudo ./run_benchmark.sh
```

> The script requires `sudo` privileges to allow the benchmark tool to read Docker's RAM usage metrics (cgroups). Once finished, the results (charts and CSV data) will be available in the results directory.


## Generate charts only (optional)

If you already have the benchmark results and only want to regenerate the charts without re-running the entire performance test suite, you can run the analysis script manually.

```bash
# Install Python 3.13 if not already installed
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.13 python3.13-venv

# Navigate to the analysis directory and set up the environment
cd analysis_scr
python3.13 -m venv .venv
source .venv/bin/activate

# Install required packages and generate charts
pip install matplotlib==3.10.1 pandas==2.3.0 scipy==1.15.1
python scr.py
```
*Note: The generated charts will be saved in your `results/` directory.*


## Generate data (optional)

This step is only required if you want to regenerate the simulation data.
The repository already contains pre-generated data in `data_generator/output/`.

### Requirements

- Python 3.13 — install via your system package manager:
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.13 python3.13-venv
```

### Setup
```bash
cd data_generator
python3.13 -m venv .venv
source .venv/bin/activate
pip install matplotlib==3.10.1
```

### Run Data Generator
```bash
python main.py
```

This will generate three datasets into data_generator/output/ and automatically create multiple diagnostic charts (e.g., population_growth.png, network_topology.png), a detailed dataset summary, and an expected results directory with query validation parameters. The expected results will be provided in two places: in a descriptive form inside the output directory, and additionally as structured JSON and CSV files located in the benchmark script directory. It will also automatically patch the benchmark SQL/Cypher queries with valid parameters for each dataset.

| Directory | Population | Generations |
|-----------|-----------|-------------|
| `1k/`     | 1,000     | ~10         |
| `10k/`    | 10,000    | ~20         |
| `100k/`   | 100,000   | ~50         |

Generation takes approximately 1 minute depending on hardware.

### Find Optimal Parameters (Advanced)

If you want to modify the target population behaviors or need to generate a completely new valid seed that meets strict benchmark constraints (exponential growth curve, exact tree depth), you can run the parameter search utility:

```bash
python parameter_search.py
```
This script will test hundreds of configurations and output a Python snippet that you can paste directly into `config.py` to replace the existing `SEED` and `SCENARIOS`.


## Notes

* This setup ensures a clean and minimal environment for reproducible benchmark results.
* Docker is used to isolate database instances, ensuring consistent testing conditions.
* Any additional system packages can be installed later if required for debugging or auxiliary tools.

# Database Benchmark Setup and Measurement

This guide explains how to replicate the database performance study environment.

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

Run the environment setup script `env_setup.sh` to install all required dependencies (including Docker and the .NET SDK) and apply system-level optimizations to ensure stable and reproducible benchmark results. You will be required to enter your sudo password during execution, as administrative privileges are needed.

```bash
chmod +x env_setup.sh
./env_setup.sh
```

Once the script completes, **reboot the system** to apply group changes (e.g., Docker permissions):

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
pip install matplotlib pandas scipy
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
pip install matplotlib
```

### Run Data Generator
```bash
python main.py
```

This will generate three datasets into `data_generator/output/` and automatically create multiple diagnostic charts (e.g., `population_growth.png`, `network_topology.png`), a detailed dataset summary, an expected results directory with query validation parameters, and automatically patch the benchmark SQL/Cypher queries with valid parameters for each dataset:

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

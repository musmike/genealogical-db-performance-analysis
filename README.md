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
````

Then clone the repository containing the benchmark scripts:

```bash
git clone <repository_url>
cd <repository_folder>
```


## 3. Set up the environment

Run the environment setup script `env_setup.sh` to install required packages, Docker, and other dependencies:

```bash
chmod +x env_setup.sh
./env_setup.sh
```

Once the script completes, **reboot the system** to apply group changes (e.g., Docker permissions):

```bash
sudo reboot
```


## 4. Build and run the benchmark

After reboot, build the benchmark binary:
```bash
cd <repository_folder>
dotnet publish -c Release -r linux-x64 --self-contained true /p:PublishSingleFile=true \
  -o query_performance_benchmark \
  query_performance_benchmark/benchmark_scr/benchmark_scr.csproj
```

Then run it:
```bash
chmod +x query_performance_benchmark/benchmark_scr
sudo ./query_performance_benchmark/benchmark_scr
```

> The binary connects to the database containers and executes the performance tests.


## Generate data (optional)

This step is only required if you want to regenerate the simulation data.
The repository already contains pre-generated data in `data_generator/output/`.

### Requirements

- Python 3.13 — install via your system package manager:
```bash
sudo apt install -y python3.13 python3.13-venv
```

### Setup
```bash
cd data_generator
python3.13 -m venv .venv
source .venv/bin/activate
```

### Run
```bash
python main.py
```

This will generate three datasets into `data_generator/output/`:

| Directory | Population | Generations |
|-----------|-----------|-------------|
| `1k/`     | 1,000     | ~10         |
| `10k/`    | 10,000    | ~20         |
| `100k/`   | 100,000   | ~50         |

Generation takes approximately 1 minute depending on hardware.


## Notes

* This setup ensures a clean and minimal environment for reproducible benchmark results.
* Docker is used to isolate database instances, ensuring consistent testing conditions.
* Any additional system packages can be installed later if required for debugging or auxiliary tools.

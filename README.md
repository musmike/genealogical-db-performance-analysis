# Database Benchmark Setup and Measurement

This guide explains how to replicate the database performance study environment.

## 1. Install Ubuntu Server 24.04 LTS

During the installation, choose the following options:

- **Ubuntu Server (minimized)** – only essential packages installed, no GUI.  
- **Do not search for third-party drivers unless necessary** – keep the system clean.
- **Partitioning** – use a single ext4 partition for `/` (e.g., 150 GB).  
- **Do not select any featured server snaps** – avoid unnecessary background services.  


---

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

---

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

---

## 4. Run the benchmark script

After reboot, navigate to the repository folder and run the measurement script written in C#:

```bash
cd <repository_folder>
dotnet run --project <benchmark_project>
```

> The script will configure and start the database containers and then execute the performance tests.

---

## Notes

* This setup ensures a clean and minimal environment for reproducible benchmark results.
* Docker is used to isolate database instances, ensuring consistent testing conditions.
* Any additional system packages can be installed later if required for debugging or auxiliary tools.

# Minikube Setup Guide (Kubeflow Native Stack)

This stack (Istio + Knative + KFP + KServe + Ollama) is resource-intensive.

## 1. Resource Requirements

| Resource | Minimum | Recommended | Why? |
| :--- | :--- | :--- | :--- |
| **RAM** | **16 GB** | **24 GB+** | Istio (~4GB), Kubeflow (~4GB), Ollama + LLM (~6GB), Knative (~2GB). |
| **CPUs** | **6 Cores** | **8+ vCPUs**| Service Mesh sidecars and multiple controllers (operators) need CPU. |
| **Disk** | **60 GB** | **100 GB** | Docker images for Kubeflow are large. |

### FAQ: Resource Locking
*   **Memory**: Minikube (Docker Driver) does **not** instantly lock 24GB. It sets a *limit*. Usage grows dynamically as you deploy pods. However, due to Java (Spark/Elasticsearch) and ML workloads, expect it to actually typically use 16GB+.
*   **Host Safety**: On a 32GB machine, allocating 24GB leaves 8GB for your OS. This is safe, but close heavy browser tabs.
*   **CPU**: Cores are shared, not locked. Your mouse won't freeze unless the cluster is at 100% load.

## 2. Prerequisites by OS

### Option A: Docker Desktop for Windows (WSL2 Backend)
*Most common setup. You run `docker` in WSL, but it talks to Docker Desktop on Windows.*
**GPU Support:** ✅ YES (Managed by Desktop)
1.  **Windows**: Install NVIDIA Drivers.
2.  **Windows**: Create `%UserProfile%/.wslconfig` (See "Ryzen 5 7600X" note below).
3.  **Docker Desktop Settings**: Verification:
    *   Settings -> General -> "Use the WSL 2 based engine": **Checked**.
    *   Settings -> Resources -> WSL Integration -> "Ubuntu-24.04": **Toggled ON**.
4.  **Verify GPU**: Run this in your WSL terminal:
    ```bash
    docker run --rm --gpus all ubuntu nvidia-smi
    ```
    *If this prints a table showing your GPU, you are ready. You do NOT need to install `nvidia-container-toolkit` inside WSL.*

### Option B: Native Docker Engine in WSL
*Refers to running `dockerd` directly inside Ubuntu via systemd.*
1.  **Windows**: Create `%UserProfile%/.wslconfig`.
2.  **Ubuntu**: Install NVIDIA Container Toolkit as defined in NVIDIA docs.
3.  **Ubuntu**: Configure runtime to `docker` and restart daemon.

### Ryzen 5 7600X Config (For .wslconfig)
```ini
[wsl2]
memory=26GB  # Unlocks access to 26GB
processors=12 # Exposes all 12 Loop threads to WSL
```
*Remember to run `wsl --shutdown` after creating/editing this file.*

## 3. The Startup Command (Linux/WSL2/Desktop)
*Note: We request 10 CPUs to leave 2 threads breathing room for Windows.*
```bash
minikube start \
  --driver=docker \
  --cpus=10 \
  --memory=24576 \
  --disk-size=100g \
  --gpus=all
```

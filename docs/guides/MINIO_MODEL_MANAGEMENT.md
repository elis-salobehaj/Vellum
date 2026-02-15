# MinIO Model Management for KServe

This guide explains how to manage LLM models in MinIO for our KServe-based `llm-service`.

## Prerequisites

1.  **MinIO Client (`mc`)**: You need the MinIO client installed and configured interact with the in-cluster MinIO.

    ```bash
    # Install mc (Linux)
    curl https://dl.min.io/client/mc/release/linux-amd64/mc \
      --create-dirs \
      -o /usr/local/bin/mc
    chmod +x /usr/local/bin/mc
    ```

2.  **Port Forwarding**: Expose the MinIO service to your local machine.

    ```bash
    # In a separate terminal
    kubectl port-forward svc/minio-service -n kubeflow 9000:9000
    ```

## 1. Configure MinIO Alias

Set up an alias to connect to the local forwarded port. Source credentials are standard for Kubeflow default install.

```bash
# Alias name: minio
# URL: http://localhost:9000
# User: minio
# Pass: minio123
mc alias set minio http://localhost:9000 minio minio123
```

## 2. Managing Models

### Create Bucket
Models are stored in the `models` bucket.

```bash
mc mb minio/models
```

### Set Public Access (Optional/Debugging)
If you encounter 403 errors within the cluster, you can verify access policies. Note that our `llm-service` uses embedded credentials in the URL (`http://minio:minio123@...`) to bypass this requirement for the downloader, but public access helps for debugging with `curl`.

```bash
mc anonymous set download minio/models
```

### Upload a Model (GGUF Format)
To upload a new model (e.g., `TinyLlama` or `Mistral`):

1.  **Download Locally**:
    ```bash
    curl -L -o /tmp/model.gguf <huggingface_url>
    ```

2.  **Upload to MinIO**:
    ```bash
    mc cp /tmp/model.gguf minio/models/tinyllama.gguf
    ```

## 3. Using Models in KServe

Update `deployment/llm-service.yaml` to point to the new model:

```yaml
    initContainers:
      - name: model-downloader
        image: minio/mc:latest
        command: ["/bin/sh", "-c"]
        args:
          - |
            echo "Configuring MinIO..."
            mc alias set local http://minio-service.kubeflow.svc.cluster.local:9000 minio minio123
            echo "Downloading model..."
            # Update 'tinyllama.gguf' to your new filename
            mc cp local/models/tinyllama.gguf /mnt/models/model.gguf
            echo "Download complete."
```

Apply the changes:
```bash
kubectl apply -f deployment/llm-service.yaml
```

## 4. Swapping Models using KServe (Zero Down Time)

To switch models without rebuilding Docker images, update the `llm-service` manifest.

### Example: Switching to Llama 3.2 3B

1.  **Download & Upload Model**:
    ```bash
    curl -L -o /tmp/llama-3.2-3b.gguf https://huggingface.co/lmstudio-community/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf
    mc cp /tmp/llama-3.2-3b.gguf minio/models/llama-3.2-3b.gguf
    ```

2.  **Update Manifest**:
    Change the download URL in `deployment/llm-service.yaml`:
    ```yaml
            echo "Downloading model..."
            mc cp local/models/llama-3.2-3b.gguf /mnt/models/model.gguf
    ```

3.  **Apply**:
    ```bash
    kubectl apply -f deployment/llm-service.yaml
    ```
    KServe/Kubernetes will start a new pod with the new model. The old pod remains active until the new one is Ready.

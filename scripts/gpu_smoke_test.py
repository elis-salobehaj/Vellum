import ray

# Connect to the Ray cluster via the port-forwarded Dashboard client port
# 10001 is the default client port matching ray-cluster.yaml
print("Connecting to Ray cluster...")
ray.init("ray://localhost:10001")

@ray.remote(num_gpus=1)
def gpu_test():
    try:
        import torch
        return f"GPU available: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}"
    except ImportError:
        return "PyTorch not installed on Ray worker, but scheduled successfully on a GPU node!"

print("Submitting GPU task to Ray...")
result = ray.get(gpu_test.remote())
print(f"Result from Ray worker: {result}")

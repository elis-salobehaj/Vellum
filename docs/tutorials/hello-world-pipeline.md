# Tutorial: Running Your First "Hello World" Pipeline

This guide will walk you through creating, compiling, and running a simple Kubeflow Pipeline on the Vellum infrastructure.

## Prerequisites

1.  **Python Environment**: You need Python 3.8+ installed locally.
2.  **KFP SDK**: Install the Kubeflow Pipelines SDK.
    ```bash
    pip install kfp==2.2.0
    ```
3.  **UI Access**: Ensure you have port-forwarded the KFP UI:
    ```bash
    kubectl port-forward -n kubeflow svc/ml-pipeline-ui 3000:80
    ```
    Access at: [http://localhost:3000](http://localhost:3000)

## Step 1: Write the Pipeline Code

We have created a simple example script at `examples/kfp/hello_world.py`.

**Concepts**:
*   **`@dsl.component`**: Decorator that turns a Python function into a Pipeline Component. This function will run inside a Docker container (default is python:3.7) on the cluster.
*   **`@dsl.pipeline`**: Decorator that defines the workflow topology (how components connect).
*   **`compiler.Compiler()`**: Translates your Python code into the standard KFP YAML format (IR - Intermediate Representation).

## Step 2: Compile the Pipeline

Run the script to generate the YAML definition:

```bash
cd examples/kfp
python3 hello_world.py
```

You should see a file named `hello_world_pipeline.yaml` generated in the directory.

## Step 3: Upload and Run via UI

1.  Open the Dashboard at [http://localhost:3000](http://localhost:3000).
2.  Click **Pipelines** in the sidebar.
3.  Click **+ Upload Pipeline**.
4.  Select via **Upload a file** and choose `hello_world_pipeline.yaml`.
5.  Name it `Hello World v1` and click **Create**.
6.  Once created, click **Create Run**.
7.  In the Run configuration:
    *   **Run Name**: `test-run-1`
    *   **Parameters**: You can modify the `recipient` parameter (Default: "World").
8.  Click **Start**.

## Step 4: Monitor the Run

1.  Click on the run name (`test-run-1`) to view the details.
2.  **Graph View**: You will see a box representing the `say-hello` task.
3.  **Status**: It will start as "Pending" (Grey) -> "Running" (Blue) -> "Succeeded" (Green).
4.  **Logs**: Click on the `say-hello` node and open the **Logs** tab in the side panel. You should see:
    ```
    Hello, World!
    ```

## Troubleshooting

*   **Run Stuck in Pending**: This usually means the cluster cannot schedule the pod (resource limits) or cannot pull the image. Check pod status: `kubectl get pods -n kubeflow`.
*   **ImagePullBackOff**: Ensure your cluster has internet access to pull `python:3.7`.
*   **Upload Fails**: Ensure the UI version matches the Backend compatibility. We are using KFP 2.2.0.

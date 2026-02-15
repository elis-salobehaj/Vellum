FROM vellum-backend:latest

WORKDIR /app

# Copy dependency definition
COPY kubeflow/pipelines/ingestion/pyproject.toml ./

# Install dependencies using uv (which is available in vellum-backend)
RUN uv sync --no-dev

# Use the virtual environment from uv sync
ENV PATH="/app/.venv/bin:$PATH"

COPY kubeflow/pipelines/ingestion/scripts/run_ingestion.py /app/run_ingestion.py

# Redefine entrypoint for the ingestion task
ENTRYPOINT ["python", "/app/run_ingestion.py"]

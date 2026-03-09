FROM vellum-backend:latest

WORKDIR /app

# Copy dependency definition
COPY kubeflow/pipelines/ingestion/pyproject.toml ./
COPY kubeflow/pipelines/ingestion/vellum_ingestion ./vellum_ingestion

# Install dependencies using uv (which is available in vellum-backend)
RUN uv sync --no-dev

# KFP lightweight components expect pip to exist in the runtime image.
RUN /app/.venv/bin/python -m ensurepip --upgrade

# Use the virtual environment from uv sync
ENV PATH="/app/.venv/bin:$PATH"

COPY kubeflow/pipelines/ingestion/scripts/run_ingestion.py /app/run_ingestion.py

# Redefine entrypoint for the ingestion task
ENTRYPOINT ["python", "/app/run_ingestion.py"]

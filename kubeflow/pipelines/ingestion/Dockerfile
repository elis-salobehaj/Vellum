FROM vellum-backend:latest

WORKDIR /app

# Ensure we have the latest ingestion script and required readers
RUN pip install llama-index-readers-s3
COPY kubeflow/pipelines/ingestion/scripts/run_ingestion.py /app/run_ingestion.py

# Redefine entrypoint for the ingestion task
ENTRYPOINT ["python", "/app/run_ingestion.py"]

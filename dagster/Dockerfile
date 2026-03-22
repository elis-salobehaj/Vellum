FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY dagster_vellum/ dagster_vellum/
RUN pip install --no-cache-dir ".[dev]"

ENV DAGSTER_HOME=/dagster_home
RUN mkdir -p /dagster_home /data/documents

# Workspace entrypoint: dagster webserver or dagster-daemon
CMD ["dagster", "dev", "-m", "dagster_vellum.definitions", "--host", "0.0.0.0", "--port", "3000"]

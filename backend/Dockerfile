# Stage 1: Base with uv
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONPATH=. \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV="/app/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Stage 2: Builder
FROM base AS builder
# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files for dependency resolution
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
# Create empty app directory to satisfy setuptools/uv during sync
RUN mkdir -p app && touch app/__init__.py

ARG BUILD_MODE="production"
# Install dependencies using uv
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$BUILD_MODE" = "ci" ]; then \
        echo "CI Mode: Installing with dev dependencies for testing"; \
        uv sync --frozen; \
    else \
        echo "Production Mode: Installing without dev dependencies"; \
        uv sync --frozen --no-dev; \
    fi

# Stage 3: Test (CI)
FROM base AS test
# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

COPY backend/ .
COPY kubeflow/ kubeflow/
# Using -m ensures we use the python interpreter in the venv and avoids shebang path issues
CMD ["python", "-m", "pytest"]

# Stage 4: Production
FROM base AS production
# Copy the virtual environment from builder (prod only)
COPY --from=builder /app/.venv /app/.venv

COPY backend/ .
COPY kubeflow/ kubeflow/
EXPOSE 8000
# Using -m avoids shebang path issues with the uvicorn binary
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 1: Base
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONPATH=. \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_BREAK_SYSTEM_PACKAGES=1

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Builder
FROM base AS builder
# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
COPY backend/requirements-test.txt .

ARG BUILD_MODE="production"
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "$BUILD_MODE" = "ci" ]; then \
        echo "CI Mode: Installing lightweight dependencies"; \
        pip install --prefix=/install -r requirements-test.txt; \
    else \
        echo "Production Mode: Installing full dependencies"; \
        pip install --prefix=/install -r requirements.txt; \
    fi

# Stage 3: Test (CI)
FROM base AS test
ENV PYTHONPATH=/app
# Copy installed dependencies to system path
COPY --from=builder /install /usr/local
COPY backend/ .
COPY kubeflow/ kubeflow/
CMD ["pytest"]

# Stage 4: Production
FROM base AS production
# Copy installed dependencies (prod only) to system path
COPY --from=builder /install /usr/local
COPY backend/ .
COPY kubeflow/ kubeflow/
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

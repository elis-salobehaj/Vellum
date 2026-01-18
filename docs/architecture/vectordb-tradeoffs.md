# Vector Database Trade-off Analysis

## Objective
Select a "Production Grade" Vector Database for the Vellum Platform Upgrade (Phase 3).

## Candidates

### 1. ChromaDB (Current)
-   **Architecture**: Python/Clickhouse (or DuckDB for local).
-   **Pros**: Extremely easy developer experience (DX). "Just works" in python notebooks.
-   **Cons**:
    -   Distributed mode involves running a full Clickhouse cluster (heavy Ops).
    -   Single-node mode (our current setup) is not truly fault-tolerant.
    -   Resource usage can spike with large ingestion in Python.

### 2. Qdrant (Recommended)
-   **Architecture**: Rust.
-   **Pros**:
    -   **Performance**: Extremely high throughput and low latency (Rust).
    -   **Ops**: Single binary / docker image. scalable.
    -   **K8s Native**: Excellent Helm chart and Operator support.
    -   **Filtering**: Best-in-class metadata filtering engine.
-   **Cons**: Slightly stricter API than Chroma (gRPC/REST vs "Python function").

### 3. Apache Spark?
-   **Clarification**: Spark is a **Processing Engine** (like "Databricks"), not a real-time Vector Database.
-   **Use Case**: You use Spark to *create* embeddings for 1 Billion documents (Batch ETL), then you load them into Qdrant/Milvus for serving.
-   **Verdict**: Not a replacement for the DB.

### 4. Other Mentions
-   **Milvus**: Excellent but requires many components (Etcd, Pulsar/Kafka, MinIO, Proxy). Overkill for <100M vectors.
-   **Weaviate**: Solid Go-based alternative, similar tier to Qdrant.
-   **Pgvector**: Good if we already had a massive Postgres cluster.

## Comparison Matrix

| Feature | ChromaDB | **Qdrant** | usage |
| :--- | :--- | :--- | :--- |
| **Language** | Python | Rust | |
| **Memory Footprint** | Medium | **Low/Efficient** | Qdrant wins on 512Mi limit |
| **Cold Start** | Fast | **Instant** | |
| **Kubernetes Ops** | StatefulSet (Custom) | **Helm Chart (Standard)** | Qdrant is easier to manage in Prod |
| **Ingestion Speed** | Medium | **High** | |

## Recommendation
**Switch to Qdrant.**
-   It aligns with the "SRE/Platform" goal (Rust, efficiency, stability).
-   It fits perfectly in our resource-constrained Minikube (very light on RAM compared to JVM implementations).
-   We can deploy it alongside Kubeflow.

### Impact on Code
-   **Ingestion Pipeline**: Requires changing `ChromaVectorStore` to `QdrantVectorStore`.
-   **Backend API**: Requires updating the query client.
-   **Effort**: Low (~1 hour refactor). LlamaIndex supports both natively.

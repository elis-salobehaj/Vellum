from kfp import dsl
from kfp import compiler

@dsl.component(
    base_image='vellum-ingest:local',
    packages_to_install=[]
)
def ingest_documents_op(
    bucket: str,
    prefix: str = "",
    minio_endpoint: str = "minio-service.kubeflow.svc:9000",
    minio_access_key: str = "minio",
    minio_secret_key: str = "minio123",
    chroma_host: str = "chroma-service.kubeflow.svc.cluster.local",
    chroma_port: int = 8000,
    chunk_size: int = 1024,
    chunk_overlap: int = 20,
    splitter_mode: str = "fixed",
    breakpoint_threshold: int = 95,
    max_docs: int = 5
):
    import subprocess
    import sys
    
    print(f"Launching ingestion from MinIO {bucket}/{prefix}")
    
    # Call the script that resides at /app/run_ingestion.py (from Dockerfile)
    cmd = [
        "python", 
        "/app/run_ingestion.py",
        "--bucket", bucket,
        "--prefix", prefix,
        "--minio_endpoint", minio_endpoint,
        "--minio_access_key", minio_access_key,
        "--minio_secret_key", minio_secret_key,
        "--chroma_host", chroma_host,
        "--chroma_port", str(chroma_port),
        "--chunk_size", str(chunk_size),
        "--chunk_overlap", str(chunk_overlap),
        "--splitter_mode", splitter_mode,
        "--breakpoint_threshold", str(breakpoint_threshold),
        "--max_docs", str(max_docs)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr, file=sys.stderr)
        
    if result.returncode != 0:
        raise RuntimeError(f"Ingestion failed with code {result.returncode}")

@dsl.pipeline(
    name='vellum-ingestion-pipeline',
    description='Ingests documents from MinIO to ChromaDB using LlamaIndex'
)
def ingestion_pipeline(
    bucket: str = "documents",
    prefix: str = "",
    minio_endpoint: str = "minio-service.kubeflow.svc:9000",
    chroma_host: str = "chroma-service.kubeflow.svc.cluster.local",
    chunk_size: int = 1024,
    chunk_overlap: int = 20,
    splitter_mode: str = "fixed",
    breakpoint_threshold: int = 95,
    max_docs: int = 5
):
    # Create the task
    task = ingest_documents_op(
        bucket=bucket,
        prefix=prefix,
        minio_endpoint=minio_endpoint,
        chroma_host=chroma_host,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        splitter_mode=splitter_mode,
        breakpoint_threshold=breakpoint_threshold,
        max_docs=max_docs
    )
    
    # Force use of local image in Minikube
    # task.set_image_pull_policy("Never") # Not supported in V2 SDK directly on task
    # We rely on Minikube finding the image locally.

if __name__ == '__main__':
    compiler.Compiler().compile(
        pipeline_func=ingestion_pipeline,
        package_path='ingestion_pipeline.yaml'
    )

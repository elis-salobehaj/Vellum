import time
from kfp import Client

def submit_run(chunk_size=512, chunk_overlap=40, max_docs=2, top_k=2, splitter_mode="semantic", model_name="BAAI/bge-small-en-v1.5", enable_cache=False):
    client = Client(host='http://localhost:8888', namespace='kubeflow-user-example-com')
    
    # Aggressively inject header into all underlying API clients
    # SDK v2 hides the raw api_client, but it's used inside _run_api, _experiment_api, etc.
    for key, value in client.__dict__.items():
        if hasattr(value, 'api_client'):
            print(f"Injecting auth header into {key}...")
            value.api_client.default_headers['kubeflow-userid'] = 'user@example.com'
    
    print("🚀 Submitting Ingestion Pipeline...")
    run = client.create_run_from_pipeline_package(
        pipeline_file='ingestion_pipeline.yaml',
        arguments={
            'bucket': 'documents',
            'minio_endpoint': 'minio-service.kubeflow.svc:9000',
            'qdrant_host': 'qdrant.qdrant.svc.cluster.local',
            'qdrant_port': 6333,
            'chunk_size': chunk_size,
            'chunk_overlap': chunk_overlap,
            'max_docs': max_docs,
            'top_k': top_k,
            'splitter_mode': splitter_mode,
            'model_name': model_name,
            'enable_cache': enable_cache
        },
        run_name=f'ingestion-run-{int(time.time())}'
    )
    print(f"✅ Run submitted! ID: {run.run_id}")
    print(f"🔗 View run: http://localhost:8080/_/pipeline/?ns=kubeflow-user-example-com#/runs/details/{run.run_id}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--chunk_size', type=int, default=512)
    parser.add_argument('--chunk_overlap', type=int, default=40)
    parser.add_argument('--max_docs', type=int, default=2)
    parser.add_argument('--top_k', type=int, default=2)
    parser.add_argument('--splitter_mode', type=str, default="semantic")
    parser.add_argument('--model_name', type=str, default="BAAI/bge-small-en-v1.5")
    parser.add_argument('--enable_cache', action='store_true', help="Enable KFP caching")
    args = parser.parse_args()

    submit_run(args.chunk_size, args.chunk_overlap, args.max_docs, args.top_k, args.splitter_mode, args.model_name, args.enable_cache)

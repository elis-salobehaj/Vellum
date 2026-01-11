import time
from kfp import Client

def submit_run():
    client = Client(host='http://localhost:3000') # Connects via port-forward
    
    print("🚀 Submitting Ingestion Pipeline...")
    run = client.create_run_from_pipeline_package(
        pipeline_file='ingestion_pipeline.yaml',
        arguments={
            'bucket': 'documents',
            'minio_endpoint': 'minio-service.kubeflow.svc:9000',
            'chroma_host': 'chroma-service.kubeflow.svc.cluster.local'
        },
        run_name=f'ingestion-run-{int(time.time())}'
    )
    print(f"✅ Run submitted! ID: {run.run_id}")
    print(f"🔗 View run: http://localhost:3000/#/runs/details/{run.run_id}")

if __name__ == '__main__':
    submit_run()

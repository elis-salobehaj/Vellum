import time
import requests
import kfp
import qdrant_client
from kfp import dsl
from kfp import compiler

# --- Configuration ---
QDRANT_URL = "http://localhost:6333"
KFP_HOST = "http://localhost:8888" # We will port-forward this
PIPELINE_FILE = "ingestion_pipeline.yaml"

def check_qdrant():
    print(f"🔍 Checking Qdrant at {QDRANT_URL}...")
    try:
        client = qdrant_client.QdrantClient(url=QDRANT_URL)
        cols = client.get_collections()
        print(f"   Collections: {cols}")
        
        # Check if vellum_vectors exists
        exists = any(c.name == "vellum_vectors" for c in cols.collections)
        if not exists:
            print("   ⚠️ 'vellum_vectors' collection does not exist yet.")
            return False
            
        count = client.count(collection_name="vellum_vectors").count
        print(f"   Vector Count: {count}")
        return count > 0
    except Exception as e:
        print(f"   ❌ Failed to connect to Qdrant: {e}")
        return False

def compile_pipeline():
    print("🔨 Compiling Pipeline...")
    # Import dynamically to ensure we use the local modified file
    import sys
    import os
    sys.path.append(os.getcwd() + "/pipelines/ingestion")
    from pipeline import ingestion_pipeline
    
    compiler.Compiler().compile(
        pipeline_func=ingestion_pipeline,
        package_path=PIPELINE_FILE
    )
    print(f"   Compiled to {PIPELINE_FILE}")

def run_pipeline():
    print(f"🚀 Connecting to KFP at {KFP_HOST}...")
    # Add User ID Header for Auth
    # Kubeflow in multi-user mode requires identifying the user
    client = kfp.Client(host=KFP_HOST, existing_token="dummy") 
    # Monkey patch or set headers if supported? 
    # KFP SDK v2 might handle this differently, but let's try standard approach or use the headers in the underlying API
    # Actually, KFP Client accepts 'existing_token' or we can set headers on the context.
    
    # Newer KFP SDK approach for headers:
    # client._client.api_client.default_headers['kubeflow-userid'] = 'user@example.com'
    
    # Let's try passing it via cookies or verify if we need to authenticate via Dex.
    # Since we are port-forwarding to ml-pipeline service directly (bypassing Istio Gateway), 
    # we might be hitting the Metadata Envoy or API which expects headers.
    
    # Correction: The error "User identity is empty" comes from the KFP API server validating the header.
    # We must inject it.
    
    client = kfp.Client(host=KFP_HOST)
    
    # KFP SDK v2 Compatibility Hack: Inject headers into underlying API clients
    apis = ['_experiment_api', '_run_api', '_job_api', '_upload_api', '_pipelines_api']
    for api_name in apis:
        if hasattr(client, api_name):
            api_instance = getattr(client, api_name)
            if hasattr(api_instance, 'api_client'):
                print(f"DEBUG: Setting header on {api_name}")
                api_instance.api_client.default_headers["kubeflow-userid"] = "user@example.com"
            else:
                print(f"DEBUG: {api_name} has no api_client")
    
    # Create Experiment
    experiment = client.create_experiment(name="End-to-End Verification", namespace="kubeflow-user-example-com")
    print(f"DEBUG: Experiment object: {experiment}")
    # Handle different object types
    exp_id = getattr(experiment, 'id', getattr(experiment, 'experiment_id', None))
    
    # Submit Run
    run = client.run_pipeline(
        experiment_id=exp_id,
        job_name=f"verify-ingest-{int(time.time())}",
        pipeline_package_path=PIPELINE_FILE,
        params={
            "bucket": "documents",
            "max_docs": 1, 
            "chunk_size": 1024
        }
    )
    print(f"DEBUG: Run object: {run}")
    run_id = getattr(run, 'run_id', getattr(run, 'id', None))
    print(f"   Run submitted! ID: {run_id}")
    print(f"   View: {KFP_HOST}/#/runs/details/{run_id}")
    
    # Wait for completion
    print("⏳ Waiting for run to complete...")
    run_result = client.wait_for_run_completion(run_id=run_id, timeout=300)
    
    print(f"DEBUG: Run Result: {run_result}")
    status = getattr(run_result, 'state', getattr(run_result, 'status', 'Unknown'))
    print(f"   Run finished with status: {status}")
    
    if status not in ["Succeeded", "SUCCEEDED"]:
        raise RuntimeError(f"Pipeline run failed with status: {status}")

if __name__ == "__main__":
    compile_pipeline()
    
    if check_qdrant():
        print("Note: Qdrant already has data. This run will add more.")
        
    try:
        run_pipeline()
        
        print("🔍 Verifying Data in Qdrant...")
        if check_qdrant():
            print("✅ VERIFICATION SUCCESSFUL!")
        else:
            print("❌ Verification Failed: No data in Qdrant.")
            exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

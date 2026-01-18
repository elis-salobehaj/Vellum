import requests
import json

def verify_chat_api():
    print("🚀 Verifying Chat API Endpoint (Minikube Proxy)...")
    
    url = "http://localhost:9090/api/v1/chat"
    
    # We need a running backend for this. 
    # Since we are in an agent session, we might not have a running backend exposed.
    # But usually backend is running as a service.
    # If not, this script will fail connection.
    # Assuming backend runs on default port 8000.
    
    payload = {
        "message": "What is Agentic AI?",
        "model_id": "Qwen2.5-1.5B-Instruct", # ID might need to match config
        "session_id": "test-session-123"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        print("\n✅ API Response Received:")
        print(json.dumps(data, indent=2))
        
        answer = data.get("response", "")
        if len(answer) > 20:
             print("\n✅ Verification Passed! Answer looks valid.")
        else:
             print("\n❌ Verification Failed: Answer too short.")
             
    except Exception as e:
        print(f"\n❌ API Verification Failed: {e}")
        print("Note: This failure is expected if the Backend Server is not running locally on port 8000.")

if __name__ == "__main__":
    verify_chat_api()

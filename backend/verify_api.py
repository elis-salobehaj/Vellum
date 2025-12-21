import requests
import json

try:
    response = requests.post(
        "http://localhost:8000/api/v1/chat",
        json={"message": "Test message for session check", "model_id": "llama3"},
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer mock-token"
        }
    )
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

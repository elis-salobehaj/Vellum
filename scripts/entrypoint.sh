#!/bin/bash

# Start Ollama service in the background
/bin/ollama serve &
pid=$!

echo "🔴 [INIT] Waiting for Ollama API to be ready..."
# Wait up to 30 seconds for the server to start
count=0
while [ $count -lt 30 ]; do
    if ollama list > /dev/null 2>&1; then
        echo "🟢 [INIT] Ollama is up and running!"
        break
    fi
    sleep 1
    count=$((count+1))
done

# Pull models from config
echo "⚙️ [INIT] Pulling models (this may take time on first run)..."
# List matching backend/app/api/endpoints/admin.py
models=(
    "mistral" 
    "llama3" 
    "gemma2" 
    "gemma3:4b" 
    "llama3.2" 
    "gemma:2b"
)

for model in "${models[@]}"; do
    echo "⬇️  Pulling $model..."
    ollama pull "$model"
done

echo "🟢 [INIT] All models provisioned."

# Keep the container running by waiting for the background process
wait $pid

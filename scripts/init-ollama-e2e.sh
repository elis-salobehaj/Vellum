#!/bin/bash
# Script to initialize Ollama with a small model for E2E testing

set -e

echo "Waiting for Ollama to be ready..."
sleep 5

# Pull the smallest model for testing (gemma:2b is ~1.6GB)
echo "Pulling gemma:2b model for E2E tests..."
ollama pull gemma:2b

echo "Ollama initialization complete!"

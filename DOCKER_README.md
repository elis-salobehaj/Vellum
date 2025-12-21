# Docker Setup for kbase-ai

This project supports running the entire stack (Frontend + Backend + Vector DB Persistence) using Docker Compose.

## Prerequisites

- Docker Desktop installed
- Git

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and fill in your API keys (OpenAI, Google) and Azure Entra ID credentials.

## Running the App

### Windows
Run the provided PowerShell script:
```powershell
.\launch-docker.ps1
```

### macOS / Linux
Run the shell script:
```bash
chmod +x launch-docker.sh
./launch-docker.sh
```

### Manual Method
```bash
docker-compose up --build
```

## Accessing the App

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Troubleshooting

- **Container Conflicts**: If ports 3000 or 8000 are in use, edit `docker-compose.yml` to map to different ports.
- **Environment Variables**: Ensure `.env` is at the root of the project.

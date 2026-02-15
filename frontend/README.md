# Vellum Frontend

React 19 chat interface with Entra ID SSO, real-time streaming, and Tailwind CSS.

## Quick Start

```bash
pnpm install
pnpm dev
```

> **Note**: The frontend expects the backend API at `/api/v1`. Run `../scripts/connect.sh` to establish port-forwards.

## Configuration

| Variable | Description | Default |
| :--- | :--- | :--- |
| `VITE_API_URL` | Backend API URL | `/api/v1` |
| `VITE_BYPASS_AUTH` | Disable login for local dev | `false` |

## Full Documentation

- [Getting Started](../docs/guides/GETTING_STARTED.md)
- [Development Guide](../docs/guides/DEVELOPMENT.md)
- [Architecture & Conventions](../docs/context/ARCHITECTURE.md)
- [Authentication Guide](../docs/guides/AUTHENTICATION.md)

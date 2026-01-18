# Vellum Frontend

Modern Chat Interface built with React 19, Vite, and Tailwind CSS v4.

## Features

-   **Streaming Chat**: Real-time token streaming.
-   **Citations**: Displays source documents (PDFs) with accuracy scores.
-   **Markdown Support**: Renders tables, code blocks, and lists.
-   **Dark/Light Mode**: System-aware theming.

## Development

The frontend expects the backend to be available at `/api/v1`.

1.  **Install**:
    ```bash
    npm install
    ```

2.  **Run (Local)**:
    ```bash
    npm run dev
    # Runs on http://localhost:5173 (proxies to backend:8000)
    ```

3.  **Run (Production)**:
    In Kubernetes, this is served via Nginx on port **9090**.

## Configuration

| Variable | Description |
| :--- | :--- |
| `VITE_API_URL` | Backend API URL (default: `/api/v1`) |
| `VITE_BYPASS_AUTH` | Disable login for dev |

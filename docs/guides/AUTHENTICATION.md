# Authentication Guide

This guide explains how authentication works in the completed Phase 1 local stack, which runs on `Kind` but still keeps the Kubeflow-era Dex and Istio security model.

## 1. Vellum Application
The Vellum application is hosted either through the local frontend dev server or through the cluster frontend port-forward.
It uses **Microsoft Entra ID (Azure AD)** for primary user authentication.

- **Hybrid URL**: [http://localhost:5173](http://localhost:5173)
- **Cluster URL**: [http://localhost:9090](http://localhost:9090)
- **Login Method**: Click the "Sign in with Entra ID" button.
- **Redirection**: You will be redirected to `login.microsoftonline.com` to enter your enterprise credentials.
- **Session Management**: MSAL (Microsoft Authentication Library) manages the token lifecycle in the browser.

### Troubleshooting Vellum Auth
- Ensure the **Redirect URI** in your Azure App Registration matches `http://localhost:8086/`.
- Verify your `.env` file contains the correct `AZURE_CLIENT_ID` and `AZURE_TENANT_ID`.

---

## 2. Kubeflow Dashboard & Dex
The Kubeflow Central Dashboard and internal services are protected by **Dex** and **oauth2-proxy**.

- **URL**: [http://localhost:8086/](http://localhost:8086/)
- **Default User**: `vellum@example.com`
- **Default Password**: `12341234`

### Why Two Logins?
Vellum maintains its own identity provider (Entra ID) separate from Kubeflow's internal authentication (Dex). This ensures Vellum's security remains consistent across different environments (Dev, Staging, Prod), even if Kubeflow's auth configuration changes.

In completed Phase 1, moving from Minikube to `Kind` does **not** change this split yet. Dex remains part of the slim local platform until later migration phases remove Kubeflow-auth dependencies.

---

## 3. Developer Shortcuts
To bypass all authentication checks during local development:

Update your `.env` file:
```bash
BYPASS_AUTH=True
VITE_BYPASS_AUTH=true
```

---

## 4. Security Architecture

```
User Request
    ↓
Istio Ingress Gateway (initial routing)
    ↓
Request Authentication (JWT signature verification for /api/v1/*)
    ↓
Authorization Policies (deny-by-default in `kubeflow-vellum` namespace)
    ↓
FastAPI Backend (secondary signature check — defense-in-depth)
```

- **Inbound Gateway**: Istio Ingress Gateway handles initial routing on the local `Kind` cluster.
- **Request Authentication**: Istio verifies the JWT signature for API traffic that reaches the mesh-protected backend.
- **Authorization Policies**: Deny-by-default logic is applied to the `kubeflow-vellum` namespace, only allowing traffic from validated gateway principals.
- **Backend Enforcement**: FastAPI performs a secondary token check for defense-in-depth.
- **Kubeflow Internal Auth**: Dex and oauth2-proxy still protect the dashboard and the multi-user Kubeflow services that remain in the completed Phase 1 stack.

# Vellum Authentication Guide

This guide explains how authentication is handled in the Vellum application and how it integrates with the Kubeflow cluster-wide security.

## 1. Vellum Application (Port 8080)
The Vellum application is hosted at `http://localhost:8080/vellum/`. 
It use **Microsoft Entra ID (Azure AD)** for primary user authentication.

- **URL**: [http://localhost:8080/vellum/](http://localhost:8080/vellum/)
- **Login Method**: Click the "Sign in with Entra ID" button.
- **Redirection**: You will be redirected to `login.microsoftonline.com` to enter your enterprise credentials.
- **Session Management**: MSAL (Microsoft Authentication Library) manages the token life cycle in the browser.

### Troubleshooting Vellum Auth:
- Ensure the **Redirect URI** in your Azure App Registration matches `` or `http://localhost:8080/`.
- Verify your `.env` file contains the correct `AZURE_CLIENT_ID` and `AZURE_TENANT_ID`.
- Run `./scripts/deploy-local.sh` to sync environment changes to the cluster.

---

## 2. Kubeflow Dashboard & Dex (Port 8080)
The main Kubeflow Central Dashboard and other internal services are protected by **Dex** and **oauth2-proxy**. 

- **URL**: [http://localhost:8080/](http://localhost:8080/)
- **Default User**: `vellum@example.com`
- **Default Password**: `12341234`

### Why two logins?
Vellum is designed as a standalone application that can be embedded in Kubeflow or run independently. It maintains its own identity provider (Entra ID) to ensure that even if Kubeflow's internal authentication (Dex) changes, Vellum's security remains consistent across different environments (Dev, Staging, Prod).

---

## 3. Developer Shortcuts
If you are developing locally and want to bypass all authentication checks:
1. Update your `.env` file:
   ```bash
   BYPASS_AUTH=True
   VITE_BYPASS_AUTH=true
   ```
2. Redeploy:
   ```bash
   ./scripts/deploy-local.sh
   ```

## 4. Security Architecture
- **Inbound Gateway**: Istio Ingress Gateway handles initial routing.
- **Request Authentication**: Istio verifies the JWT signature for all API calls to `/api/v1/*`.
- **Authorization Policies**: Deny-by-default logic is applied to the `kubeflow-vellum` namespace, only allowing traffic from validated gateway principals.
- **Backend Enforcement**: The FastAPI backend performs a secondary signature check on every request for defense-in-depth.

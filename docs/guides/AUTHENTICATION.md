# Authentication Guide

> **Phase 4:** Dex and oauth2-proxy are fully removed.
> The only authentication path is **Microsoft Entra ID (Azure AD)** JWT.
> Istio Ambient mesh enforces the JWT at L7 (waypoint proxy) before requests reach the backend.
> The backend performs a secondary verification as defense-in-depth.

---

## 1. Vellum Application Authentication

### How it works (prod / staging)

```
Browser
  │  HTTPS + Authorization: Bearer <JWT>
  ▼
Istio Ingress Gateway
  │
  ▼
ztunnel (L4 mTLS — automatic, zero-trust between all pods)
  │
  ▼
Waypoint Proxy (L7)
  │  RequestAuthentication: verifies Entra ID JWT signature
  │  AuthorizationPolicy: allows only validated principals
  ▼
FastAPI Backend
  │  Secondary JWT signature check (defense-in-depth)
  ▼
Business logic
```

### Entra ID Setup

1. Register an App in your Azure tenant at [portal.azure.com](https://portal.azure.com).
2. Under **Authentication**, add a Redirect URI:
   - Local: `http://localhost:8086/` (Istio ingress)
   - Hybrid dev: `http://localhost:5173/`
3. Copy **Application (client) ID** and **Directory (tenant) ID** into `.env`:
   ```env
   AZURE_CLIENT_ID=<your-client-id>
   AZURE_TENANT_ID=<your-tenant-id>
   ```
4. The frontend uses `@azure/msal-react` (MSAL) — login via the **Sign in with Entra ID** button.

### Token flow

- Frontend acquires an Entra ID access token via MSAL interactive flow.
- Token is sent as `Authorization: Bearer <token>` on every API call.
- **Istio waypoint** checks the signature against the Entra ID JWKS endpoint first.
- **Backend** (`auth.py`) re-validates the token independently for defense-in-depth.

---

## 2. Local Development

### Full bypass (fastest)

Set in `.env`:
```env
BYPASS_AUTH=true
VITE_BYPASS_AUTH=true
```

All endpoints return a dummy `bypassed-user` principal. No Azure AD required.

### Hybrid dev with real auth

Run `./scripts/connect.sh` first (port-forwards the Istio ingress). Then run the frontend and backend locally. The frontend sends the JWT to `http://localhost:8086` (Istio ingress port-forward) which then proxies to the backend in the cluster.

For pure local backend (no cluster), the Istio mesh layer is bypassed — the backend's secondary JWT check is the only guard. Ensure `BYPASS_AUTH=false` and your Entra ID config is correct.

---

## 3. Istio Ambient Mesh

Vellum uses Istio Ambient mode (Phase 4). Key objects:

| Resource | Kind | Purpose |
|---|---|---|
| `vellum-waypoint` | Gateway | L7 waypoint proxy for `kubeflow-vellum` ns |
| `vellum-jwt` | RequestAuthentication | Entra ID JWT signature validation |
| `vellum-ns-auth` | AuthorizationPolicy | Allow only authenticated traffic + internal services |

The namespace is labelled `istio.io/dataplane-mode: ambient` — no sidecar injection required.

To enroll the waypoint after installation:
```bash
istioctl x waypoint apply --namespace kubeflow-vellum --enroll-namespace
```

---

## 4. What Is Gone (Phase 4)

| Component | Was used for | Replaced by |
|---|---|---|
| **Dex** | OIDC for Kubeflow Dashboard | Not needed — dashboard removed |
| **oauth2-proxy** | Auth middleware for KFP/Dashboard | Not needed |
| **kubeflow-userid header** | Dex → Istio header passthrough | Removed — was spoofable |
| **Cert-Manager** | TLS certs for Dex, webhooks | Removed with Kubeflow stack |
| **KFP OIDC callback** | Multi-user KFP auth | KFP removed in Phase 4 |

---

## 5. Security Notes

- **Never set `BYPASS_AUTH=true` in staging or production.** It is a local dev shortcut only.
- The `AZURE_CLIENT_ID` must appear in the token's `aud` claim. The backend checks both `<client-id>` and `api://<client-id>`.
- JWKS are cached in `auth.py` via `@lru_cache`. Clear the cache by restarting the backend in cases of key rotation.
- The Istio `RequestAuthentication` forwards the original token to the backend (`forwardOriginalToken: true`), enabling the backend's secondary check.
- Internal service-to-service traffic (Dagster → Qdrant, Backend → TEI, etc.) is mutually authenticated via ztunnel mTLS automatically — no application-level creds required for intra-cluster calls.

# Analysis: Infrastructure Code Location

The question of "Where does the infra code live?" is critical for scaling.

## Option 1: Monorepo (Current Approach)
Everything lives in the `Vellum` repository.
*   `Vellum/crossplane/` (Platform Definitions)
*   `Vellum/src/` (App Code)
*   `Vellum/claim.yaml` (Infrastructure Request)

### ✅ Pros
*   **Velocity**: "Atomic Commits". You can add a new Qdrant feature in the code and update the storage requirement in the Infrastructure in a single Pull Request.
*   **Simplicity**: One repo to clone, one CI/CD pipeline to manage.
*   **Visibility**: Developers see exactly what infrastructure supports their code.

### ❌ Cons
*   **Access Control**: In a strict enterprise, you don't want App Developers modifying the `Composition` (the "How").
*   **Blast Radius**: A bad CI run could theoretically mess up both App and Infra.

---

## Option 2: Polyrepo (Platform vs. App Separation)
Two separate repositories.
1.  **`Vellum-Platform`**: Owned by "Platform Engineering". Contains `XRDs`, `Compositions`, `Functions`.
2.  **`Vellum-App`**: Owned by "Data Science". Contains Source Code and the `Claim.yaml`.

### ✅ Pros
*   **Role Separation**: Mimics a real Enterprise structure. The Platform Team defines "Standard MLOps Stacks", and the App Team just consumes them.
*   **Stability**: The Platform repo changes rarely and undergoes rigorous testing. The App repo changes fast.
*   **Scalability**: One Platform repo can serve 50 different App repos.

### ❌ Cons
*   **Friction**: If you need a new feature in the platform (e.g., "Add Redis"), you must PR the Platform repo, release it, upgrade the App repo. (The "Review Delay" problem).
*   **Complexity**: Two git workflows, two CI pipelines.

---

## 💡 The "Crossplane" Nuance
Crossplane is uniquely designed to support **Role Separation** even within a Monorepo, or easily split later.

*   **The Provider/Platform**: Defines the `XRD` and `Composition`. (The "Menu")
*   **The Consumer**: Defines the `Claim`. (The "Order")

### Recommendation for Vellum (Learning Phase)
**Stick to Monorepo for now, but logical separation.**
We are "simulating" the Enterprise. Splitting into two physical Git repos adds logistical overhead (managing two folders, two commits) that slows down *learning*.
However, we should treat the `crossplane/` folder as "Protected Platform Code" and the `claim.yaml` as "App Code".

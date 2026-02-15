# 🤖 Vellum App Agent Manual

## 🛠️ Core Tech Stack
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS (in `/webapp`).
- **Backend:** Python 3.12, FastAPI, Pydantic v2 (in `/api`).
- **AI Layer:** Vellum SDK (Python/TS), LangGraph for stateful loops.

## 📜 Dev Rules & Best Practices
- **React:** Use functional components; avoid `useEffect` for data fetching (use React Query).
- **Python:** Strict type hints required; use `BaseModel` for all API schemas.
- **RAG Logic:** When touching retrieval code, always consider **MMR (Maximal Marginal Relevance)** to avoid redundant context.

## 🛠️ Critical Commands
- **Backend Setup:** `uv sync && uv run dev`.
- **Frontend Setup:** `pnpm install && pnpm dev`.
- **Run Evals:** `pytest api/evals/` (DO NOT commit if evals fail).

## 🚫 Boundaries
- NEVER modify `.env` or AWS Secret keys directly.
- ALWAYS ask for confirmation before changing a Vellum workflow ID or prompt version.
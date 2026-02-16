---
title: "Plan: Frontend UI Overhaul"
status: active
priority: high
estimated_hours: 40-60
dependencies:
  - docs/plans/implemented/dependency-standardization.md
created: 2026-02-15
date_updated: 2026-02-16
related_files:
  - frontend/src/index.css
  - frontend/src/App.tsx
  - frontend/src/main.tsx
  - frontend/src/types.ts
  - frontend/src/pages/ChatPage.tsx
  - frontend/src/pages/LoginPage.tsx
  - frontend/src/pages/AdminPage.tsx
  - frontend/src/components/Layout.tsx
  - frontend/src/components/Chat/ChatInput.tsx
  - frontend/src/components/Chat/MessageBubble.tsx
  - frontend/src/components/Chat/SourcePanel.tsx
  - frontend/src/components/RequireAuth.tsx
  - frontend/package.json
tags:
  - frontend
  - shadcn
  - ui
  - tailwind4
  - oklch
  - dark-mode
  - react19
completion:
  - [x] Phase 1 — Design System Foundation
  - [x] Phase 2 — Core Layout & Navigation Overhaul
  - [x] Phase 3 — Chat Experience Redesign
  - [x] Phase 4 — State Management & API Layer
  - [x] Phase 5 — Theming & Dark Mode ✅
  - [ ] Phase 6 — Accessibility & Polish
  - [ ] Phase 7 — Documentation & Cleanup
---

# Plan: Frontend UI Overhaul

**Date**: February 15, 2026
**Status**: Active
**Goal**: Rebuild the Vellum frontend into a premium, production-grade enterprise chat UI using shadcn/ui components, OKLCH color theming, and modern React patterns.

## Motivation

The current frontend is functional but architecturally basic:
- **No design system** — hardcoded Tailwind utility classes scattered across components.
- **No theming** — light mode only, no CSS variables, no dark mode.
- **No streaming** — full JSON responses, no real-time UX.
- **Duplicated auth logic** — every component acquires tokens independently.
- **Unused features** — the right-side SourcePanel is not useful and wastes screen space.
- **Inconsistent branding** — LoginPage says "kbase-ai" instead of "Vellum".

## Strategy

Adopt **shadcn/ui** as the component foundation with **Tailwind CSS 4** and **OKLCH colors** for the design system. This gives us:
- Copy-paste components we fully own (no runtime dependency).
- Built-in dark/light mode via CSS variables.
- Radix UI accessibility primitives under the hood.
- Full alignment with our existing Tailwind 4 setup.

### Inspirations
- **[assistant-ui](https://github.com/assistant-ui/assistant-ui)**: Thread management UX, composable chat primitives, streaming patterns.
- **[shadcn-chatbot-kit](https://github.com/Blazity/shadcn-chatbot-kit)**: Auto-resize input, message actions, smart scrolling, prompt suggestions.
- **Previous project overhaul**: OKLCH `@theme` tokens, container queries, `data-theme` switching.

---

## Phase 1: Design System Foundation

**Goal**: Establish the OKLCH-based design token system and install shadcn/ui.

### 1.1 Install shadcn/ui
- [x] Install `shadcn` CLI and initialize with Tailwind CSS 4.
- [x] Configure `components.json` with project aliases (`@/components`, `@/lib`).
- [x] Install core primitives: `button`, `input`, `textarea`, `card`, `badge`, `avatar`, `tooltip`, `dropdown-menu`, `dialog`, `sheet`, `separator`, `scroll-area`, `skeleton`.

### 1.2 OKLCH Design Tokens
- [x] Rewrite `frontend/src/index.css` with OKLCH-based CSS custom properties via Tailwind 4 `@theme`.
- [x] Define semantic color tokens: `--color-background`, `--color-foreground`, `--color-primary`, `--color-muted`, `--color-accent`, `--color-destructive`, `--color-border`, `--color-ring`.
- [x] Define chart palette: 6 accent colors for data visualization.
- [x] Define typography scale: `--font-sans` (Inter/Geist), `--font-mono` (JetBrains Mono/Geist Mono).

### 1.3 Utility Setup
- [x] Create `frontend/src/lib/utils.ts` with `cn()` helper (clsx + tailwind-merge).
- [x] Configure path aliases in `tsconfig.json` and `vite.config.ts` for `@/` imports.

**Files created/modified**:
- `frontend/src/index.css` (rewritten)
- `frontend/src/lib/utils.ts` (new)
- `frontend/components.json` (new)
- `frontend/tsconfig.json` (aliases)
- `frontend/vite.config.ts` (aliases)

---

## Phase 2: Core Layout & Navigation Overhaul

**Goal**: Replace the monolithic `Layout.tsx` with a modern, collapsible sidebar layout.

### 2.1 Sidebar Redesign
- [x] Create `frontend/src/components/layout/AppSidebar.tsx` — collapsible sidebar using shadcn `Sheet` (mobile) and CSS transitions (desktop).
- [x] Implement thread/history list with shadcn `ScrollArea` and `Button` primitives.
- [x] Add "New Chat" button with `+` icon and keyboard shortcut (`Ctrl+N`).
- [x] Show app branding: Vellum logo + version badge.
- [x] Add user profile section at bottom (avatar, name from MSAL, sign-out button).

### 2.2 App Shell
- [x] Create `frontend/src/components/layout/AppLayout.tsx` — replaces `Layout.tsx`.
- [x] Implement responsive breakpoints: collapsed sidebar on mobile, expanded on desktop.
- [x] Add top-level command bar / model selector in the header area.

### 2.3 Remove Unused Components
- [x] **Delete** `frontend/src/components/Chat/SourcePanel.tsx` — the right-side panel is not useful (confirmed by user).
- [x] Remove all `SourcePanel` references from `ChatPage.tsx` (the `selectedSource` state, the `onCitationClick` callback, and the panel rendering).
- [x] Simplify citation rendering in `MessageBubble.tsx` — citations become inline download links only.

### 2.4 Login Page Update
- [x] Update branding from "kbase-ai" to "Vellum".
- [x] Style with shadcn `Card` + `Button` components.
- [x] Add subtle background gradient or pattern.

**Files created/modified**:
- `frontend/src/components/layout/AppSidebar.tsx` (new)
- `frontend/src/components/layout/AppLayout.tsx` (new)
- `frontend/src/components/Chat/SourcePanel.tsx` (deleted)
- `frontend/src/components/Layout.tsx` (deleted, replaced by AppLayout)
- `frontend/src/pages/ChatPage.tsx` (remove SourcePanel)
- `frontend/src/pages/LoginPage.tsx` (rebrand)
- `frontend/src/App.tsx` (use new AppLayout)

---

## Phase 3: Chat Experience Redesign

**Goal**: Build a premium chat interface inspired by ChatGPT / assistant-ui.

### 3.1 Message Components
- [x] Create `frontend/src/components/chat/MessageList.tsx` — virtualized/windowed message list with smart auto-scroll (scroll-to-bottom button appears when scrolled up).
- [x] Create `frontend/src/components/chat/UserMessage.tsx` — clean user bubble with avatar.
- [x] Create `frontend/src/components/chat/AssistantMessage.tsx` — AI response with:
  - Markdown rendering (react-markdown + remark-gfm).
  - Code block syntax highlighting (rehype-highlight or shiki).
  - Copy-to-clipboard button on code blocks.
  - Message actions toolbar (copy full response, regenerate).
  - Inline citation badges (download links, no right panel).
- [x] Create `frontend/src/components/chat/ThinkingIndicator.tsx` — animated thinking/typing indicator (replace the plain "Thinking..." text).

### 3.2 Input Redesign
- [x] Rebuild `ChatInput.tsx` using shadcn `Textarea` with auto-resize.
- [x] Add prompt suggestions / quick actions above the input for empty conversations.
- [x] Implement `Shift+Enter` for newline, `Enter` to send.
- [x] Add file attachment button (UI only initially, wired in a future phase).
- [x] Add stop/cancel button when a response is being generated.

### 3.3 Empty State
- [x] Create `frontend/src/components/chat/EmptyState.tsx` — welcoming screen shown when no messages exist:
  - Vellum logo + tagline.
  - 3-4 prompt suggestion cards (e.g., "Summarize my documents", "Find information about...").

### 3.4 Model Selector
- [x] Move model selector into a shadcn `DropdownMenu` in the chat header (replace the plain `<select>`).
- [x] Show model provider icon + name.
- [x] Indicate active model with a checkmark.

**Files created/modified**:
- `frontend/src/components/chat/MessageList.tsx` (new)
- `frontend/src/components/chat/UserMessage.tsx` (new)
- `frontend/src/components/chat/AssistantMessage.tsx` (new)
- `frontend/src/components/chat/ThinkingIndicator.tsx` (new)
- `frontend/src/components/chat/EmptyState.tsx` (new)
- `frontend/src/components/Chat/ChatInput.tsx` (rewritten)
- `frontend/src/components/Chat/MessageBubble.tsx` (deleted, replaced)
- `frontend/src/pages/ChatPage.tsx` (rewritten)

---

## Phase 4: State Management & API Layer

**Goal**: Eliminate duplicated logic and introduce a proper data layer.

### 4.1 Shared Auth Hook
- [x] Create `frontend/src/hooks/useAuth.ts` — wraps MSAL token acquisition.
  - `getToken()`: Returns token or "mock-token" if bypass is enabled.
  - `user`: Current user profile (name, email).
  - `isAuthenticated`: Boolean.
- [x] Refactor all components to use `useAuth()` instead of inline `acquireTokenSilent` calls.

### 4.2 API Client
- [x] Create `frontend/src/lib/api.ts` — centralized API client using `fetch` with automatic token injection.
  - `api.get(path)`, `api.post(path, body)`, `api.stream(path, body)`.
  - Automatic `Authorization: Bearer <token>` header.
  - Centralized error handling and logging.

### 4.3 React Query Integration
- [x] Install `@tanstack/react-query`.
- [x] Create query hooks:
  - `useModels()` — fetches available models.
  - `useChatHistory()` — fetches sidebar history.
  - `useSessionMessages(sessionId)` — fetches messages for a session.
- [x] Replace all `useEffect` + `fetch` patterns with React Query hooks.

### 4.4 Chat Mutation
- [x] Create `useSendMessage()` mutation hook that handles:
  - Optimistic updates (show user message immediately).
  - Backend POST request.
  - Appending AI response.
  - Error handling with rollback.

**Files created/modified**:
- `frontend/src/hooks/useAuth.ts` (new)
- `frontend/src/lib/api.ts` (new)
- `frontend/src/hooks/useModels.ts` (new)
- `frontend/src/hooks/useChatHistory.ts` (new)
- `frontend/src/hooks/useSessionMessages.ts` (new)
- `frontend/src/hooks/useSendMessage.ts` (new)
- All page/component files refactored to use hooks.

---

## Phase 5: Theming & Dark Mode

**Goal**: Implement a complete dark mode and theme switching system.

### 5.1 Theme Provider
- [x] Create `frontend/src/components/theme/ThemeProvider.tsx` — manages `data-theme` attribute on `<html>`.
- [x] Support three modes: `light`, `dark`, `system` (follows OS preference).
- [x] Persist user preference in `localStorage`.

### 5.2 Theme Selection in User Menu
- [x] Integrate theme selection as a `DropdownMenuSub` under "Appearance" in the user profile menu.
- [x] Support three modes: `light`, `dark`, `system` (follows OS preference).
- [x] Place in user profile dropdown for a cleaner, unified preferences experience.

### 5.3 Dark Mode Tokens
- [x] Define `[data-theme="dark"]` CSS custom properties in `index.css`.
- [x] Ensure all shadcn components respect the CSS variable system.
- [x] Audit all custom components for hardcoded colors (`bg-white`, `text-gray-800`, etc.) and replace with semantic tokens.

### 5.4 Transition Polish
- [x] Add `transition-colors` to key elements for smooth theme switching.
- [x] Target: Theme switch INP < 50ms, CLS = 0.

**Files created/modified**:
- `frontend/src/components/theme/ThemeProvider.tsx` (new)
- `frontend/src/components/layout/AppSidebar.tsx` (Integrated collapse logic & appearance menu)
- `frontend/src/index.css` (dark mode tokens added)

---

## Phase 6: Accessibility & Polish

**Goal**: Ensure the application meets WCAG 2.1 AA and feels premium.

### 6.1 Keyboard Navigation
- [ ] `Ctrl+N` / `Cmd+N`: New chat.
- [ ] `Ctrl+K` / `Cmd+K`: Focus search/command bar (future).
- [ ] `Escape`: Close modals, dialogs, expanded input.
- [ ] `Tab` / `Shift+Tab`: Navigate between sidebar items and chat.

### 6.2 ARIA & Screen Reader
- [ ] Add `role="log"` to the message list container.
- [ ] Add `aria-live="polite"` for new assistant messages.
- [ ] Ensure all buttons have `aria-label` attributes.
- [ ] Add skip-to-content link.

### 6.3 Micro-Animations
- [ ] Message entry animation (fade-in + slide-up).
- [ ] Sidebar expand/collapse transition.
- [ ] Button hover states with subtle scale transforms.
- [ ] Loading skeleton animations for history and messages.

### 6.4 Performance Audit
- [ ] Target bundle CSS < 15KB.
- [ ] Lazy-load admin page (`React.lazy`).
- [ ] Ensure no layout shifts on theme toggle (CLS = 0).

---

## Phase 7: Documentation & Cleanup

**Goal**: Update all documentation and remove legacy files.

### 7.1 Code Cleanup
- [ ] Remove all deleted component files.
- [ ] Remove unused dependencies from `package.json`.
- [ ] Run `pnpm lint` and fix all warnings.
- [ ] Run Playwright tests to verify nothing broke.

### 7.2 Documentation Updates
- [ ] Update `docs/context/ARCHITECTURE.md` — Frontend section to reflect new component tree.
- [ ] Update `docs/guides/DEVELOPMENT.md` — Frontend commands section.
- [ ] Update `docs/README.md` — Active Plans table.
- [ ] Update root `README.md` if needed.

### 7.3 Commit & Ship
- [ ] Commit with `feat: frontend ui overhaul with shadcn, oklch theming, and dark mode`.
- [ ] Push and verify CI passes.
- [ ] Move this plan to `docs/plans/implemented/`.

---

## Architecture Standards

| Principle | Implementation |
|---|---|
| **CSS-First Theming** | OKLCH design tokens in `@theme`, no JS runtime for colors |
| **Component Ownership** | shadcn components copied into `src/components/ui/` — we own the code |
| **Composable Primitives** | Small, focused components. No monolithic page files > 150 lines |
| **Data Layer** | React Query for all server state. No `useEffect` + `fetch` |
| **Auth Abstraction** | Single `useAuth()` hook. No inline token logic |
| **Semantic Colors** | Use `bg-background`, `text-foreground`, etc. Never hardcode hex/rgb |

## Performance Targets

| Metric | Target |
|---|---|
| Bundle CSS | < 15KB |
| Theme Switch INP | < 50ms |
| CLS on Toggle | 0 |
| Largest Contentful Paint | < 1.5s |
| First Input Delay | < 100ms |

## New Dependency List

| Package | Purpose |
|---|---|
| `@radix-ui/*` | Accessible UI primitives (via shadcn) |
| `@tanstack/react-query` | Server state management |
| `class-variance-authority` | Component variant styling |
| `rehype-highlight` or `shiki` | Code syntax highlighting |
| `cmdk` | Command palette (future, Phase 6) |

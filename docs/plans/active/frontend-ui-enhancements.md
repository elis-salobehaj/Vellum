---
description: Enhance Frontend UI with improved sidebar, context menus, and code organization
---

# Frontend UI Enhancements

## 1. Sidebar UX Improvements
- [ ] **Hide Recent Chats when Collapsed**: Update `AppSidebar.tsx` to conditionally render the history list only when `!isCollapsed`.
- [ ] **Refactored Sidebar Items**:
  - [ ] Create a new `SidebarItem` component to handle individual chat history items.
  - [ ] Implement the "Google Gemini" style:
    - [ ] Rounded borders (`rounded-lg` or `rounded-xl`).
    - [ ] Encapsulated text with truncation.
    - [ ] Hover effect showing the 3-dots menu trigger.
  - [ ] Show 3-dots menu button **only on parent hover**.
- [ ] **Context Menu Functionality**:
  - [ ] Implement a `DropdownMenu` triggered by the 3-dots button.
  - [ ] Add options:
    - [ ] **Pin**: API call to pin/unpin chat. (May need backend support or mock for now).
    - [ ] **Rename**: Inline editing or modal to rename chat title.
    - [ ] **Delete**: Delete chat session with confirmation.
  - [ ] *Note*: Ensure the menu click doesn't trigger navigation (use `e.stopPropagation()`).

## 2. Code Quality & Best Practices
- [ ] **Deprecation Fix**: Replace usages of `ElementRef` with `ComponentRef<T>` in `frontend/src/App.tsx` or wherever used (though `ElementRef` comes from React types, standardized usage avoids confusion).
- [x] **Type Centralization**:
  - [x] Move `ChatSession` interface from `useChatHistory.ts` to `frontend/src/types/index.ts`.
  - [x] Move `Model` interface from `useModels.ts` to `frontend/src/types/index.ts`.
  - [x] Update imports across the codebase.
- [x] **Configuration Consolidation**:
  - [x] Merge `config.ts` and `authConfig.ts` into a single `config/` directory or unified file.
  - [x] Create `frontend/src/config/index.ts` (or keep `config.ts`) and include auth configuration there.
  - [x] Remove `authConfig.ts` and update imports in `useAuth.ts` and `main.tsx`.

## 3. Architecture & Restructuring
Structure the `frontend/src` directory for better scalability:

```
src/
├── components/
│   ├── common/        # Generic UI components (shadcn/ui)
│   ├── features/      # Business logic components (Chat, Admin)
│   ├── layout/        # App shell (Sidebar, Header)
│   └── providers/     # Context providers (Theme, Auth)
├── hooks/             # Custom React hooks
├── lib/               # Utilities and API clients
├── pages/             # Route pages
├── types/             # Shared TypeScript definitions
└── config/            # Configuration files
```

- [x] Move `components/ui` to `components/common/ui`.
- [x] Move `components/Chat` to `components/features/chat`.
- [x] Move `components/theme` to `components/providers` (or keep in `features` if it has UI).
- [x] Update all imports paths.

## 4. Implementation Steps

1.  [x] **Refactor Directory Structure** (Do this first to establish the new pattern).
2.  [x] **Consolidate Config & Types** (Clean up dependencies).
3.  **Implement Sidebar Enhancements** (UI/UX work).
    - Modify `AppSidebar.tsx`.
    - Create `ChatHistoryItem.tsx` (new component).
    - Integrate `DropdownMenu`.
4.  **Verify & Test**: Run `pnpm dev` and check behavior.

## 5. Dependencies
- No new packages needed.
- Uses existing `lucide-react` icons and `shadcn/ui` components.

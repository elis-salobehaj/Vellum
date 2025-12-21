# Vellum Frontend

The modern React-based frontend for the Vellum Chatbot.

## Technology Stack
- **Framework**: React 19 + Vite
- **Styling**: Tailwind CSS v4
- **Formatting**: `@tailwindcss/typography` (prose), `react-markdown`
- **Animation**: Framer Motion
- **Auth**: `@azure/msal-react`
- **Routing**: React Router v7

## Key Features
- **Responsive Chat Interface**: Animated input, auto-scrolling message list.
- **Markdown Rendering**: Supports bold, italics, lists, code blocks, and tables.
- **Admin Dashboard**: (`/admin`) for model configuration.
- **SSO Integration**: Microsoft Entra ID login flow.

## Local Development

```bash
# Install dependencies
npm install

# Run dev server
npm run dev
```

## Environment Variables
Create `.env` based on `.env.example`:
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_AZURE_CLIENT_ID=...
VITE_AZURE_AUTHORITY=...
VITE_BYPASS_AUTH=true  # For dev testing
```

import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { PublicClientApplication } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';
import { msalConfig } from './authConfig';
import { logger } from './lib/logger';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const msalInstance = new PublicClientApplication(msalConfig);
const queryClient = new QueryClient();

// Initialize MSAL and handle any redirect callbacks
msalInstance.initialize().then(async () => {
  // ... (existing code for MSAL)

  createRoot(document.getElementById('root')!).render(
    <MsalProvider instance={msalInstance}>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </MsalProvider>,
  )
  // ...
}).catch(err => {
  logger.error("msal_init_failed", { error: err });
});

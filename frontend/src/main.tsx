import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { PublicClientApplication, EventType, type AuthenticationResult } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';
import { msalConfig } from './authConfig';
import { logger } from './lib/logger';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './components/theme/ThemeProvider';

const msalInstance = new PublicClientApplication(msalConfig);
const queryClient = new QueryClient();

// Initialize MSAL and handle any redirect callbacks
msalInstance.initialize().then(async () => {
  // Default to the first account if no active account is set
  if (!msalInstance.getActiveAccount() && msalInstance.getAllAccounts().length > 0) {
    msalInstance.setActiveAccount(msalInstance.getAllAccounts()[0]);
  }

  // Handle redirect promises
  const result = await msalInstance.handleRedirectPromise();
  if (result) {
    msalInstance.setActiveAccount(result.account);
    logger.info("auth_redirect_success", { account: result.account.username });
  }

  // Optional: Listening for login events
  msalInstance.addEventCallback((event) => {
    if (event.eventType === EventType.LOGIN_SUCCESS && event.payload) {
      const payload = event.payload as AuthenticationResult;
      msalInstance.setActiveAccount(payload.account);
    }
  });

  createRoot(document.getElementById('root')!).render(
    <MsalProvider instance={msalInstance}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider defaultTheme="system" storageKey="vellum-theme">
          <App />
        </ThemeProvider>
      </QueryClientProvider>
    </MsalProvider>,
  )
}).catch(err => {
  logger.error("msal_init_failed", { error: err });
});

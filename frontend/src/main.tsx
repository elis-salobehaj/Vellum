import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { PublicClientApplication } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';
import { msalConfig } from './authConfig';
import { logger } from './lib/logger';

const msalInstance = new PublicClientApplication(msalConfig);

// Initialize MSAL and handle any redirect callbacks
msalInstance.initialize().then(async () => {
  logger.info("msal_initialized");

  // Check if we are returning from a redirect
  try {
    const result = await msalInstance.handleRedirectPromise();
    if (result) {
      logger.info("msal_redirect_success", { user: result.account?.username });
      msalInstance.setActiveAccount(result.account);
    } else {
      const accounts = msalInstance.getAllAccounts();
      if (accounts.length > 0) {
        logger.debug("msal_account_restored", { user: accounts[0].username });
        msalInstance.setActiveAccount(accounts[0]);
      }
    }
  } catch (err) {
    logger.error("msal_redirect_failed", { error: err });
  }

  createRoot(document.getElementById('root')!).render(
    <MsalProvider instance={msalInstance}>
      <App />
    </MsalProvider>,
  )
}).catch(err => {
  logger.error("msal_init_failed", { error: err });
});

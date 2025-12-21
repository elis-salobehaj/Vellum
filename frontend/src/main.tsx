import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { PublicClientApplication } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';
import { msalConfig } from './authConfig';

const msalInstance = new PublicClientApplication(msalConfig);

// Initialize MSAL and handle any redirect callbacks
msalInstance.initialize().then(async () => {
  // Check if we are returning from a redirect
  const result = await msalInstance.handleRedirectPromise().catch(err => console.error(err));

  // Set the active account if we have a result, otherwise try to load from cache
  if (result && result.account) {
    msalInstance.setActiveAccount(result.account);
  } else {
    const accounts = msalInstance.getAllAccounts();
    if (accounts.length > 0) {
      msalInstance.setActiveAccount(accounts[0]);
    }
  }

  createRoot(document.getElementById('root')!).render(
    <MsalProvider instance={msalInstance}>
      <App />
    </MsalProvider>,
  )
});

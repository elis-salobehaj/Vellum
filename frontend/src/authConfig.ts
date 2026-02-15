import { LogLevel } from "@azure/msal-browser";
import type { Configuration, PopupRequest } from "@azure/msal-browser";
import { logger } from './lib/logger';

export const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_AZURE_CLIENT_ID || "no-client-id-provided",
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_AZURE_TENANT_ID || "common"}/v2.0`,
    redirectUri: window.location.origin + "/",
    postLogoutRedirectUri: window.location.origin + "/",
  },
  cache: {
    cacheLocation: "localStorage", // Changed to localStorage for better persistence
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) {
          return;
        }
        switch (level) {
          case LogLevel.Error:
            logger.error("msal_error", { message });
            return;
          case LogLevel.Info:
            logger.info("msal_info", { message });
            return;
          case LogLevel.Verbose:
            logger.debug("msal_verbose", { message });
            return;
          case LogLevel.Warning:
            logger.warn("msal_warning", { message });
            return;
        }
      },
      logLevel: LogLevel.Warning // Reduce verbosity for MSAL
    }
  }
};

export const loginRequest: PopupRequest = {
  scopes: ["openid", "profile", "User.Read"]
};

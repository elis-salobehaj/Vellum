import { useMsal } from "@azure/msal-react";
import { loginRequest } from "@/config/authConfig";
import { logger } from "@/lib/logger";
import { config } from "@/config/index";

interface UseAuthReturn {
  getToken: () => Promise<string>;
  user: {
    name?: string;
    username?: string;
    email?: string;
  } | null;
  isAuthenticated: boolean;
  logout: () => Promise<void>;
}

/**
 * Shared authentication hook that wraps MSAL token acquisition.
 * Provides a consistent interface for getting tokens and user info across the app.
 */
export const useAuth = (): UseAuthReturn => {
  const { instance, accounts } = useMsal();
  const account = accounts[0];


  const getToken = async (): Promise<string> => {
    // If bypass auth is enabled, return mock token
    if (config.auth.bypassAuth) {
      return "mock-token";
    }

    // If no account, return empty string (unauthenticated)
    if (!account) {
      logger.warn("auth_no_account", { message: "No account found" });
      return "";
    }

    try {
      const response = await instance.acquireTokenSilent({
        ...loginRequest,
        account: account
      });
      logger.debug("auth_token_acquired", { hasToken: !!response.idToken });
      return response.idToken;
    } catch (error) {
      logger.error("auth_token_acquisition_failed", error);
      // Return empty string on error so API fails cleanly with 401
      return "";
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await instance.logoutPopup();
      logger.info("auth_logout_success");
    } catch (error) {
      logger.error("auth_logout_failed", error);
      throw error;
    }
  };

  const user = config.auth.bypassAuth ? {
    name: "Test User",
    username: "test@example.com",
    email: "test@example.com"
  } : (account ? {
    name: account.name,
    username: account.username,
    email: account.username // MSAL typically uses username as email
  } : null);

  const isAuthenticated = config.auth.bypassAuth || !!account;

  return {
    getToken,
    user,
    isAuthenticated,
    logout
  };
};

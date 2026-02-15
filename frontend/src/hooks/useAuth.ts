import { useMsal } from "@azure/msal-react";
import { loginRequest } from "@/authConfig";
import { logger } from "@/lib/logger";

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
  const isAuthenticated = !!account;

  const getToken = async (): Promise<string> => {
    // If no account, return mock token (for development/bypass mode)
    if (!account) {
      logger.warn("auth_no_account", { message: "No account found, using mock token" });
      return "mock-token";
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
      // Fallback to mock token on error
      return "mock-token";
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

  const user = account ? {
    name: account.name,
    username: account.username,
    email: account.username // MSAL typically uses username as email
  } : null;

  return {
    getToken,
    user,
    isAuthenticated,
    logout
  };
};

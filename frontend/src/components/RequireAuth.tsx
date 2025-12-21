import React from 'react';
import { useMsal } from "@azure/msal-react";
import { Navigate, useLocation } from "react-router-dom";

import { InteractionStatus } from "@azure/msal-browser";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { accounts, inProgress } = useMsal();
  const location = useLocation();

  if (import.meta.env.VITE_BYPASS_AUTH === 'true') {
    return children;
  }

  if (accounts.length > 0) {
    return children;
  }

  if (inProgress !== InteractionStatus.None) {
    return <div className="flex items-center justify-center h-screen">Loading authentication...</div>;
  }

  return <Navigate to="/login" state={{ from: location }} replace />;
}

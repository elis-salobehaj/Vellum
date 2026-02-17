import React from 'react';
import { useIsAuthenticated } from "@azure/msal-react";
import { Navigate, useLocation } from 'react-router-dom';
import { config } from '@/config/index';

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useIsAuthenticated();
  const location = useLocation();

  if (config.auth.bypassAuth) {
    return <>{children}</>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

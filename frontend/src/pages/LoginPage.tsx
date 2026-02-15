import { useState, useEffect } from 'react';
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { useNavigate } from 'react-router-dom';
import { loginRequest } from '../authConfig';
import { config } from '../config';
import { logger } from '../lib/logger';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const LoginPage = () => {
  const { instance } = useMsal();
  const isAuthenticated = useIsAuthenticated();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated || config.auth.bypassAuth) {
      logger.info("login_redirect_to_home", { bypassed: config.auth.bypassAuth });
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleLogin = async () => {
    logger.info("login_started");
    setIsLoading(true);
    try {
      await instance.loginRedirect(loginRequest);
    } catch (e) {
      logger.error("login_redirect_failed", { error: e });
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen flex items-center justify-center bg-muted/50">
      <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/5 via-background to-background" />

      <Card className="w-full max-w-md z-10 shadow-xl border-border/50">
        <CardHeader className="text-center space-y-4">
          <div className="w-16 h-16 bg-primary rounded-2xl flex items-center justify-center text-primary-foreground mx-auto shadow-lg shadow-primary/20 text-3xl font-bold">
            V
          </div>
          <div className="space-y-2">
            <CardTitle className="text-3xl font-bold tracking-tight">Vellum</CardTitle>
            <CardDescription className="text-base">
              Sign in with your enterprise account to access AI-powered document analysis.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <Button
            onClick={handleLogin}
            disabled={isLoading}
            size="lg"
            className="w-full h-12 text-base font-medium transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            {isLoading ? 'Signing in...' : 'Sign in with Entra ID'}
          </Button>
          <p className="mt-6 text-center text-xs text-muted-foreground uppercase tracking-widest font-semibold">
            Enterprise Secure
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage;

import { useState, useEffect } from 'react';
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { loginRequest } from '../authConfig';
import { useNavigate } from 'react-router-dom';

const LoginPage = () => {
  const { instance } = useMsal();
  const isAuthenticated = useIsAuthenticated();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleLogin = async () => {
    setIsLoading(true);
    try {
      await instance.loginRedirect(loginRequest);
    } catch (e) {
      console.error(e);
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center text-white mx-auto mb-4 text-2xl font-bold">k</div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome to kbase-ai</h1>
          <p className="text-gray-500 mt-2">Sign in with your enterprise account</p>
        </div>

        <button
          onClick={handleLogin}
          disabled={isLoading}
          className="w-full bg-black text-white py-3 px-4 rounded-xl font-medium hover:bg-gray-800 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {isLoading ? 'Signing in...' : 'Sign in with Entra ID'}
        </button>
      </div>
    </div>
  );
};

export default LoginPage;

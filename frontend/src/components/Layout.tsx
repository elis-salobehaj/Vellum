import React, { useCallback } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { MessageSquare, Settings, LogOut, Plus } from 'lucide-react';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from '../authConfig';

const Sidebar = () => {
  const [history, setHistory] = React.useState<Array<{ id: string; title?: string }>>([]);
  const navigate = useNavigate();
  const location = useLocation();
  const { instance, accounts } = useMsal();

  const fetchHistory = useCallback(async () => {
    try {
      const account = accounts[0];
      let token = "mock-token";

      if (account) {
        const response = await instance.acquireTokenSilent({
          ...loginRequest,
          account: account
        });
        token = response.accessToken;
      }

      // NOTE: Trailing slash is CRITICAL here. 
      // Without it, FastAPI returns 307 Redirect, which causes CORS/Fetch errors (ERR_EMPTY_RESPONSE).
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/history/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!res.ok) {
        console.warn(`History fetch failed: ${res.status}`);
        setHistory([]);
        return;
      }

      const text = await res.text();
      // Handle empty body
      if (!text) {
        setHistory([]);
        return;
      }

      const data = JSON.parse(text);
      if (Array.isArray(data)) setHistory(data);
    } catch (err) {
      console.error("Failed to load history", err);
    }
  }, [instance, accounts]);

  React.useEffect(() => {
    fetchHistory();
  }, [location.pathname, fetchHistory]);

  const handleLogout = () => {
    instance.logoutRedirect({
      postLogoutRedirectUri: "/",
    });
  };

  return (
    <div className="w-64 h-screen bg-gray-50 border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2 mb-4">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white">V</div>
          Vellum
        </h1>
        <button
          onClick={() => navigate('/')}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 px-3 text-sm font-medium flex items-center justify-center gap-2 transition-colors"
        >
          <Plus size={16} />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Recent Chats</div>
        {history.length === 0 && (
          <p className="text-xs text-gray-400 px-3">No recent history</p>
        )}
        {history.map((item) => (
          <button
            key={item.id}
            onClick={() => navigate(`/chat/${item.id}`)}
            className="w-full text-left px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
          >
            <MessageSquare size={16} />
            <span className="truncate">{item.title || item.id}</span>
          </button>
        ))}
      </div>

      <div className="p-4 border-t border-gray-200 space-y-1">
        <Link to="/admin" className="w-full text-left px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2">
          <Settings size={16} />
          Admin Settings
        </Link>
        <button
          onClick={handleLogout}
          className="w-full text-left px-3 py-2 rounded-md text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
        >
          <LogOut size={16} />
          Sign Out
        </button>
      </div>
    </div>
  );
};

const Layout = () => {
  return (
    <div className="flex h-screen bg-white">
      <Sidebar />
      <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;

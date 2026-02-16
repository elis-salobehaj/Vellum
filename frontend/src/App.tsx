import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { lazy, Suspense, useEffect } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { logger } from './lib/logger';
import { RequireAuth } from './components/RequireAuth';

const ChatPage = lazy(() => import('./pages/ChatPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const AdminPage = lazy(() => import('./pages/AdminPage'));

const PageLoader = () => (
  <div className="h-screen w-full flex items-center justify-center bg-background">
    <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
  </div>
);

function App() {
  const basename = import.meta.env.BASE_URL ? import.meta.env.BASE_URL.replace(/\/$/, "") : "";

  useEffect(() => {
    logger.info("app_initialized");
  }, []);

  return (
    <Router basename={basename}>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }>
            <Route path="/" element={<ChatPage />} />
            <Route path="/chat/:sessionId" element={<ChatPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Route>
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;

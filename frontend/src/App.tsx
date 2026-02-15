import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import Layout from './components/Layout';
import ChatPage from './pages/ChatPage';
import LoginPage from './pages/LoginPage';
import AdminPage from './pages/AdminPage';
import { logger } from './lib/logger';
import { RequireAuth } from './components/RequireAuth';

function App() {
  const basename = import.meta.env.BASE_URL ? import.meta.env.BASE_URL.replace(/\/$/, "") : "";

  useEffect(() => {
    logger.info("app_initialized");
  }, []);

  return (
    <Router basename={basename}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }>
          <Route path="/" element={<ChatPage />} />
          <Route path="/chat/:sessionId" element={<ChatPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;

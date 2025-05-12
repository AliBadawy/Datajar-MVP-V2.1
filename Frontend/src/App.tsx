import { useEffect, useState } from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import ChatInterface from './components/ChatInterface';
import { ProjectsPage } from './pages/projects-page';
import { SetupProjectPage } from './pages/setup-project-page';
import SallaCallback from './components/auth/SallaCallback';
import SignupPage from './pages/signup-page';
import LoginPage from './pages/login-page';
import { useAppStore } from './lib/store';

const App = () => {
  const [isInitializing, setIsInitializing] = useState(true);
  const checkAuth = useAppStore(state => state.checkAuth);
  const user = useAppStore(state => state.user);

  // Check authentication on app start
  useEffect(() => {
    const initAuth = async () => {
      try {
        await checkAuth();
      } catch (error) {
        console.error('Error checking authentication:', error);
      } finally {
        setIsInitializing(false);
      }
    };
    
    initAuth();
  }, [checkAuth]);

  // Show loading while checking authentication
  if (isInitializing) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
        <p className="ml-2">Initializing...</p>
      </div>
    );
  }
  return (
    <Router>
      <Header />
      <main className="pt-16">
        <Routes>
        {/* Public routes - accessible whether authenticated or not */}
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/salla-callback" element={<SallaCallback />} />
        
        {/* Protected routes - require authentication */}
        <Route path="/" element={user ? <Navigate to="/projects" replace /> : <Navigate to="/signup" replace />} />
        <Route path="/projects" element={user ? <ProjectsPage /> : <Navigate to="/signup" replace />} />
        <Route path="/chat" element={user ? <ChatInterface /> : <Navigate to="/signup" replace />} />
        <Route path="/chat/:projectId" element={user ? <ChatInterface /> : <Navigate to="/signup" replace />} />
        <Route path="/setup-project" element={user ? <SetupProjectPage /> : <Navigate to="/signup" replace />} />
      </Routes>
      </main>
    </Router>
  );
};

export default App;

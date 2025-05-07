import React from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ChatInterface from './components/ChatInterface';
import { ProjectsPage } from './pages/projects-page';
import { SetupProjectPage } from './pages/setup-project-page';
import SallaCallback from './components/auth/SallaCallback';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/chat" element={<ChatInterface />} />
        <Route path="/chat/:projectId" element={<ChatInterface />} />
        <Route path="/setup-project" element={<SetupProjectPage />} />
        <Route path="/salla-callback" element={<SallaCallback />} />
      </Routes>
    </Router>
  );
};

export default App;

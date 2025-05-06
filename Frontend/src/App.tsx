import React from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ChatInterface from './components/ChatInterface';
import { ProjectsPage } from './pages/projects-page';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/chat" element={<ChatInterface />} />
        {/* Will be implemented in the next step */}
        <Route path="/setup-project" element={<div className="p-8">Project Setup Coming Soon</div>} />
      </Routes>
    </Router>
  );
};

export default App;

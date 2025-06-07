import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import WorkflowBuilder from './pages/WorkflowBuilder';
import MarketData from './pages/MarketData';
import Projects from './pages/Projects';
import Team from './pages/Team';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (renamed from cacheTime in v5)
    },
  },
});

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="app-container">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/workflow-builder" element={<WorkflowBuilder />} />
            <Route path="/market-data" element={<MarketData />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/team" element={<Team />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
};

export default App; 
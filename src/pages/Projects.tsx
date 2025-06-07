import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { VscHome, VscArchive, VscCode, VscGraph, VscPlay, VscTrash, VscEdit } from 'react-icons/vsc';
import { FiSun, FiMoon, FiUsers } from 'react-icons/fi';
import Dock from '../components/Dock';
import type { DockItemData } from '../components/Dock';
import { useTheme } from '../hooks/useTheme';
import './Projects.css';

interface SavedProject {
  id: string;
  name: string;
  description?: string;
  nodes: any[];
  edges: any[];
  createdAt: string;
  updatedAt: string;
  thumbnail?: string;
}

const Projects: React.FC = () => {
  const [projects, setProjects] = useState<SavedProject[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { isDarkMode, toggleTheme } = useTheme();

  const dockItems: DockItemData[] = [
    { 
      icon: <VscHome size={18} />, 
      label: 'Home', 
      onClick: () => navigate('/') 
    },
    { 
      icon: <VscCode size={18} />, 
      label: 'Workflow Builder', 
      onClick: () => navigate('/workflow-builder') 
    },
    { 
      icon: <VscGraph size={18} />, 
      label: 'Market Data', 
      onClick: () => navigate('/market-data') 
    },
    { 
      icon: <VscArchive size={18} />, 
      label: 'Projects', 
      onClick: () => navigate('/projects') 
    },
    { 
      icon: <FiUsers size={18} />, 
      label: 'Team', 
      onClick: () => navigate('/team') 
    },
    // Separator
    { 
      icon: null, 
      label: '', 
      onClick: () => {},
      isSeparator: true
    },
    { 
      icon: isDarkMode ? <FiMoon size={18} /> : <FiSun size={18} />, 
      label: isDarkMode ? 'Light Mode' : 'Dark Mode', 
      onClick: toggleTheme 
    },
  ];

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = () => {
    try {
      const savedProjects = localStorage.getItem('xrpl-workflows');
      if (savedProjects) {
        setProjects(JSON.parse(savedProjects));
      }
    } catch (error) {
      console.error('Error loading projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteProject = (projectId: string) => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      const updatedProjects = projects.filter(p => p.id !== projectId);
      setProjects(updatedProjects);
      localStorage.setItem('xrpl-workflows', JSON.stringify(updatedProjects));
    }
  };

  const loadProject = (project: SavedProject) => {
    // Store the project to load in sessionStorage so WorkflowBuilder can pick it up
    sessionStorage.setItem('loadProject', JSON.stringify(project));
    navigate('/workflow-builder');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="projects-page">
        <div className="projects-header">
          <h1>My Projects</h1>
          <p>Loading your saved workflows...</p>
        </div>
        <Dock 
          items={dockItems}
          panelHeight={68}
          baseItemSize={50}
          magnification={70}
        />
      </div>
    );
  }

  return (
    <div className="projects-page">
      <div className="projects-header">
        <h1>My Projects</h1>
        <p>Manage your saved XRPL workflows</p>
        <button 
          className="btn-primary"
          onClick={() => navigate('/workflow-builder')}
        >
          <VscEdit size={16} />
          Create New Workflow
        </button>
      </div>

      <div className="projects-content">
        {projects.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📁</div>
            <h3>No projects yet</h3>
            <p>Start building your first XRPL workflow to see it here.</p>
            <button 
              className="btn-primary"
              onClick={() => navigate('/workflow-builder')}
            >
              Create Your First Workflow
            </button>
          </div>
        ) : (
          <div className="projects-grid">
            {projects.map((project) => (
              <div key={project.id} className="project-card">
                <div className="project-card-header">
                  <h3>{project.name}</h3>
                  <div className="project-actions">
                    <button
                      className="action-btn load-btn"
                      onClick={() => loadProject(project)}
                      title="Load project"
                    >
                      <VscPlay size={16} />
                    </button>
                    <button
                      className="action-btn delete-btn"
                      onClick={() => deleteProject(project.id)}
                      title="Delete project"
                    >
                      <VscTrash size={16} />
                    </button>
                  </div>
                </div>
                
                <div className="project-card-body">
                  {project.description && (
                    <p className="project-description">{project.description}</p>
                  )}
                  
                  <div className="project-stats">
                    <div className="stat">
                      <span className="stat-label">Nodes:</span>
                      <span className="stat-value">{project.nodes.length}</span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Connections:</span>
                      <span className="stat-value">{project.edges.length}</span>
                    </div>
                  </div>
                </div>
                
                <div className="project-card-footer">
                  <div className="project-dates">
                    <small>Created: {formatDate(project.createdAt)}</small>
                    <small>Updated: {formatDate(project.updatedAt)}</small>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Dock positioned at bottom */}
      <div className="floating-dock">
        <Dock 
          items={dockItems}
          panelHeight={68}
          baseItemSize={50}
          magnification={70}
        />
      </div>
    </div>
  );
};

export default Projects; 
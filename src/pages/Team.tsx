import React from 'react';
import { useNavigate } from 'react-router-dom';
import { VscHome, VscArchive, VscCode, VscGraph } from 'react-icons/vsc';
import { FiSun, FiMoon, FiUsers } from 'react-icons/fi';
import Dock from '../components/Dock';
import UtkarshCard from '../components/UtkarshCard';
import BishmithCard from '../components/BishmithCard';
import YuvCard from '../components/YuvCard';
import Modal from '../components/Modal';
import type { DockItemData } from '../components/Dock';
import { useTheme } from '../hooks/useTheme';
import { useModal } from '../hooks/useModal';
import './Team.css';

const Team: React.FC = () => {
  const navigate = useNavigate();
  const { isDarkMode, toggleTheme } = useTheme();
  const { modal, showModal, hideModal } = useModal();

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

  // Individual card components with custom positioning

  return (
    <div className="team-page">
      {/* Header with glassmorphism */}
      <div className="team-header">
        <button onClick={() => navigate('/')} className="back-button">
          ← Back to Home
        </button>
        <div className="team-header-content">
          <h1>Meet Our Team</h1>
          <p>The passionate minds behind Agentflow XRPL</p>
        </div>
      </div>

      {/* Team cards container */}
      <div className="team-content">
        <div className="team-cards-container">
          <div className="team-card-wrapper">
            <UtkarshCard
              onContactClick={() => {
                console.log(`Contact clicked for Utkarsh`);
                showModal(`Contact feature coming soon for Utkarsh!`, 'Coming Soon', 'info');
              }}
            />
          </div>
          <div className="team-card-wrapper">
            <BishmithCard
              onContactClick={() => {
                console.log(`Contact clicked for Bishmith`);
                showModal(`Contact feature coming soon for Bishmith!`, 'Coming Soon', 'info');
              }}
            />
          </div>
          <div className="team-card-wrapper">
            <YuvCard
              onContactClick={() => {
                console.log(`Contact clicked for Yuv`);
                showModal(`Contact feature coming soon for Yuv!`, 'Coming Soon', 'info');
              }}
            />
          </div>
        </div>
      </div>

      {/* Floating Dock */}
      <div className="floating-dock">
        <Dock 
          items={dockItems}
          panelHeight={68}
          baseItemSize={50}
          magnification={70}
        />
      </div>
      
      {/* Modal */}
      <Modal
        isOpen={modal.isOpen}
        onClose={hideModal}
        title={modal.title}
        type={modal.type}
      >
        {modal.message}
      </Modal>
    </div>
  );
};

export default Team; 
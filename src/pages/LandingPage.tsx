import React from 'react';
import { useNavigate } from 'react-router-dom';
import { VscHome, VscArchive, VscCode, VscCloud, VscGraph } from 'react-icons/vsc';
import { FiSun, FiMoon, FiUsers } from 'react-icons/fi';
import Dock from '../components/Dock';
import Header from '../components/Header';
import CardSwap, { Card } from '../components/CardSwap';
import Modal from '../components/Modal';
import type { DockItemData } from '../components/Dock';
import { useTheme } from '../hooks/useTheme';
import { useModal } from '../hooks/useModal';
import './LandingPage.css';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { isDarkMode, toggleTheme } = useTheme();
  const { modal, showModal, hideModal } = useModal();

  const handleWalletConnect = () => {
    // Handle wallet connection logic here
    showModal('Wallet connection feature coming soon!', 'Info', 'info');
  };

  const dockItems: DockItemData[] = [
    { 
      icon: <VscHome size={18} />, 
      label: 'Home', 
      onClick: () => {} 
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

  return (
    <div className="landing-page">
      {/* Header */}
      <Header onWalletConnect={handleWalletConnect} />
      
      <div className="landing-content">
        {/* Hero section on the left */}
        <div className="hero-section">
          <div className="hero-brand">Agentflow XRPL</div>
          <div className="hero-title">
            POWERING THE AUTONOMOUS AI ECONOMY
          </div>
          <button className="cta-button" onClick={() => navigate('/workflow-builder')}>
            Build your AI
          </button>
        </div>
        
        {/* Card Swap Component - positioned on the right side */}
        <div className="card-swap-wrapper">
          <CardSwap
            cardDistance={80}
            verticalDistance={90}
            delay={5000}
            pauseOnHover={true}
          >
            <Card>
              <h3>🔗 Visual Workflows</h3>
              <p>Drag-and-drop interface to build complex XRPL automations without coding. Connect nodes to create powerful workflows.</p>
            </Card>
            <Card>
              <h3>💰 DeFi Integration</h3>
              <p>Seamlessly integrate with XRPL's native DeFi features including escrow accounts, multi-signature transactions, and automated payments.</p>
            </Card>
            <Card>
              <h3>🔐 Identity Verification</h3>
              <p>Built-in DID verification system for secure user authentication and wallet ownership validation on XRPL network.</p>
            </Card>
            <Card>
              <h3>📊 Smart Analytics</h3>
              <p>Real-time transaction monitoring with AI-powered insights using advanced LLM providers for intelligent reporting.</p>
            </Card>
          </CardSwap>
        </div>
      </div>
      
      {/* Dock positioned at bottom */}
      <Dock 
        items={dockItems}
        panelHeight={68}
        baseItemSize={50}
        magnification={70}
      />
      
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

export default LandingPage; 
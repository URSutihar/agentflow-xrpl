import React from 'react';
import { useNavigate } from 'react-router-dom';
import { VscHome, VscArchive, VscCode, VscGraph } from 'react-icons/vsc';
import { FiSun, FiMoon, FiUsers } from 'react-icons/fi';
import Header from '../components/Header';
import CardSwap, { Card } from '../components/CardSwap';
import Modal from '../components/Modal';
import Dock from '../components/Dock';
import type { DockItemData } from '../components/Dock';
import { useModal } from '../hooks/useModal';
import { useTheme } from '../hooks/useTheme';
import './LandingPage.css';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { modal, showModal, hideModal } = useModal();
  const { isDarkMode, toggleTheme } = useTheme();

  const handleWalletConnect = () => {
    // Handle wallet connection logic here
    showModal('Wallet connection feature coming soon!', 'Info', 'info');
  };

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

  return (
    <div className="landing-page">
      {/* Header */}
      <Header onWalletConnect={handleWalletConnect} />
      
      <div className="landing-content">
        {/* Hero section - moved to left */}
        <div className="hero-section">
          <div className="hero-title">
            DEMOCRATIZING THE AUTONOMOUS AI ECONOMY
          </div>
          <div className="hero-subtitle">
            The <strong>visual workflow builder</strong> where XRPL automations become <strong>accessible financial services</strong> for everyone
          </div>
          <div className="hero-description">
            Build autonomous AI agents that deliver impact solutions like microfinancing, crypto lending, and payment solutions for underserved communities. 
            Our platform makes complex XRPL workflows accessible to anyone—creating <strong>financial inclusion through technology</strong>.
          </div>
          <div className="hero-actions">
            <button className="cta-button primary" onClick={() => navigate('/workflow-builder')}>
              Build Financial Solutions
            </button>
            <button className="cta-button secondary" onClick={() => navigate('/projects')}>
              See Impact Examples
            </button>
          </div>
        </div>
        
        {/* Card Swap Component - repositioned */}
        <div className="card-swap-wrapper">
          <CardSwap
            cardDistance={60}
            verticalDistance={70}
            delay={2500}
            pauseOnHover={true}
          >
            <Card>
              <h3>🌍 Financial Inclusion</h3>
              <p>Deploy microfinance and payment solutions that reach the 1.4 billion unbanked worldwide using XRPL's low-cost infrastructure.</p>
            </Card>
            <Card>
              <h3>💡 AI-Powered Access</h3>
              <p>Intelligent workflows that adapt to local needs, from micro-lending algorithms to automated savings programs for emerging markets.</p>
            </Card>
            <Card>
              <h3>⚡ Instant Deployment</h3>
              <p>Launch financial services in minutes, not months. Our visual builder makes complex XRPL automations accessible to anyone.</p>
            </Card>
            <Card>
              <h3>🤝 Community Impact</h3>
              <p>Create transparent, traceable financial solutions that build trust and deliver measurable social impact in underserved communities.</p>
            </Card>
          </CardSwap>
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

export default LandingPage; 
import React from 'react';
import { VscAccount } from 'react-icons/vsc';
import Modal from './Modal';
import { useModal } from '../hooks/useModal';
import './Header.css';

interface HeaderProps {
  onWalletConnect?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onWalletConnect }) => {
  const { modal, showModal, hideModal } = useModal();
  
  const handleWalletConnect = () => {
    if (onWalletConnect) {
      onWalletConnect();
    } else {
      // Default wallet connection logic
      showModal('Connect your crypto wallet to continue', 'Wallet Connection', 'info');
    }
  };

  return (
    <header className="app-header">
      <div className="header-content">
        {/* Left side - Hero icon and brand */}
        <div className="header-left">
          <div className="hero-icon">
            <img src="/icon.png" alt="XRPL Icon" className="icon-image" />
          </div>
          <div className="brand-text">
            <span className="brand-name">AgentFlow</span>
            <span className="brand-tech">XRPL</span>
          </div>
        </div>

        {/* Right side - Wallet login button */}
        <div className="header-right">
          <button className="wallet-login-btn" onClick={handleWalletConnect}>
            <VscAccount className="wallet-icon" />
            <span>Connect Wallet</span>
          </button>
        </div>
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
    </header>
  );
};

export default Header; 
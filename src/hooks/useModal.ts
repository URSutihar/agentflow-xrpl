import { useState } from 'react';

interface ModalState {
  isOpen: boolean;
  title?: string;
  message: React.ReactNode;
  type?: 'info' | 'success' | 'warning' | 'error';
}

export const useModal = () => {
  const [modal, setModal] = useState<ModalState>({
    isOpen: false,
    title: '',
    message: '',
    type: 'info'
  });

  const showModal = (
    message: React.ReactNode, 
    title?: string, 
    type: 'info' | 'success' | 'warning' | 'error' = 'info'
  ) => {
    setModal({
      isOpen: true,
      title,
      message,
      type
    });
  };

  const hideModal = () => {
    setModal(prev => ({ ...prev, isOpen: false }));
  };

  return {
    modal,
    showModal,
    hideModal
  };
}; 
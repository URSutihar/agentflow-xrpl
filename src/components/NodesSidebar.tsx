import React, { useState } from 'react';
import { VscChevronDown, VscChevronRight, VscClose } from 'react-icons/vsc';
import { FiPlay, FiDatabase, FiSend, FiCheck, FiBell, FiSettings, FiSlack, FiFileText, FiUserCheck, FiTrello, FiDollarSign } from 'react-icons/fi';
import './NodesSidebar.css';

interface NodesSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onAddNode: (nodeItem: NodeItem) => void;
}

interface NodeCategory {
  id: string;
  title: string;
  icon: React.ReactNode;
  nodes: NodeItem[];
}

interface NodeItem {
  id: string;
  type: string;
  label: string;
  icon: React.ReactNode;
  description: string;
  color: string;
}

const nodeCategories: NodeCategory[] = [
  {
    id: 'samples',
    title: 'NGO Example',
    icon: <FiSlack size={16} />,
    nodes: [
      {
        id: 'ui-form',
        type: 'form',
        label: 'UI Form',
        icon: <FiFileText size={14} />,
        description: 'A form for collecting user input',
        color: '#93d6a7'
      },
      {
        id: 'identity-verification', 
        type: 'verify',
        label: 'Identity Verification (DID)',
        icon: <FiUserCheck size={14} />,
        description: 'User identity verification',
        color: '#93d6a7'
      },
      {
        id: 'escrow-account', 
        type: 'account',
        label: 'Escrow Account',
        icon: <FiTrello size={14} />,
        description: 'Escrow account creation and release',
        color: '#93d6a7'
      },
      {
        id: 'transaction-monitoring', 
        type: 'transaction',
        label: 'Transaction Monitoring',
        icon: <FiDollarSign size={14} />,
        description: 'Transaction monitoring and summary',
        color: '#93d6a7'
      }
    ]
  },
  {
    id: 'triggers',
    title: 'Triggers',
    icon: <FiPlay size={16} />,
    nodes: [
      {
        id: 'xrpl-payment-trigger',
        type: 'trigger',
        label: 'XRPL Payment',
        icon: <FiPlay size={14} />,
        description: 'Trigger when XRPL payment is received',
        color: '#2c3e50'
      },
      {
        id: 'xrpl-account-trigger', 
        type: 'trigger',
        label: 'Account Monitor',
        icon: <FiPlay size={14} />,
        description: 'Monitor XRPL account for changes',
        color: '#2c3e50'
      }
    ]
  },
  {
    id: 'xrpl',
    title: 'XRPL Operations',
    icon: <FiDatabase size={16} />,
    nodes: [
      {
        id: 'xrpl-send-payment',
        type: 'action',
        label: 'Send Payment',
        icon: <FiSend size={14} />,
        description: 'Send XRP or token payment',
        color: 'var(--accent-purple)'
      },
      {
        id: 'xrpl-get-balance',
        type: 'action', 
        label: 'Get Balance',
        icon: <FiDatabase size={14} />,
        description: 'Retrieve account balance',
        color: 'var(--accent-purple)'
      },
      {
        id: 'xrpl-validate-tx',
        type: 'action',
        label: 'Validate Transaction',
        icon: <FiCheck size={14} />,
        description: 'Validate transaction details',
        color: 'var(--accent-purple)'
      }
    ]
  },
  {
    id: 'utilities',
    title: 'Utilities',
    icon: <FiSettings size={16} />,
    nodes: [
      {
        id: 'notification',
        type: 'action',
        label: 'Send Notification',
        icon: <FiBell size={14} />,
        description: 'Send email/webhook notification',
        color: '#ef4444'
      },
      {
        id: 'condition',
        type: 'logic',
        label: 'Condition',
        icon: <FiCheck size={14} />,
        description: 'Conditional logic flow',
        color: '#f59e0b'
      }
    ]
  }
];

const NodesSidebar: React.FC<NodesSidebarProps> = ({ isOpen, onClose, onAddNode }) => {
  const [expandedCategories, setExpandedCategories] = useState<string[]>(['samples']);

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories(prev => 
      prev.includes(categoryId) 
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const onDragStart = (event: React.DragEvent, nodeItem: NodeItem) => {
    console.log('Drag started for:', nodeItem.label); // Debug log
    
    const nodeData = {
      type: nodeItem.type,
      data: { 
        label: nodeItem.label,
        description: nodeItem.description
      },
      style: {
        background: nodeItem.color,
        color: 'white',
        border: `1px solid ${nodeItem.color}`,
        borderRadius: '8px',
        fontSize: '12px',
        fontWeight: '500',
        padding: '8px 12px',
        minWidth: '120px',
        textAlign: 'center'
      }
    };
    
    event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeData));
    event.dataTransfer.effectAllowed = 'move';
    
    // Improved drag image
    try {
      const dragImage = document.createElement('div');
      dragImage.innerHTML = nodeItem.label;
      dragImage.style.cssText = `
        position: absolute;
        top: -1000px;
        left: -1000px;
        background: ${nodeItem.color};
        color: white;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
        min-width: 120px;
        text-align: center;
        transform: rotate(5deg);
        opacity: 0.8;
        pointer-events: none;
        z-index: 9999;
      `;
      
      document.body.appendChild(dragImage);
      event.dataTransfer.setDragImage(dragImage, 60, 20);
      
      // Clean up
      setTimeout(() => {
        if (document.body.contains(dragImage)) {
          document.body.removeChild(dragImage);
        }
      }, 0);
    } catch (error) {
      console.warn('Failed to set custom drag image:', error);
    }
  };

  const onNodeClick = (nodeItem: NodeItem) => {
    console.log('Node clicked:', nodeItem.label);
    onAddNode(nodeItem);
  };

  if (!isOpen) return null;

  return (
    <div className="nodes-sidebar">
        {/* Header */}
        <div className="sidebar-header">
          <h3>Nodes</h3>
          <button className="sidebar-close" onClick={onClose}>
            <VscClose size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="sidebar-content">
          {nodeCategories.map(category => (
            <div key={category.id} className="node-category">
              {/* Category Header */}
              <button 
                className="category-header"
                onClick={() => toggleCategory(category.id)}
              >
                {category.icon}
                <span>{category.title}</span>
                {expandedCategories.includes(category.id) ? 
                  <VscChevronDown size={16} /> : 
                  <VscChevronRight size={16} />
                }
              </button>

              {/* Category Nodes */}
              {expandedCategories.includes(category.id) && (
                <div className="category-nodes">
                  {category.nodes.map(node => (
                    <div
                      key={node.id}
                      className="draggable-node"
                      draggable
                      onDragStart={(e) => onDragStart(e, node)}
                      onClick={() => onNodeClick(node)}
                    >
                      <div className="node-icon" style={{ color: node.color }}>
                        {node.icon}
                      </div>
                      <div className="node-info">
                        <div className="node-label">{node.label}</div>
                        <div className="node-description">{node.description}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
  );
};

export default NodesSidebar; 
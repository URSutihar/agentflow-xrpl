import React, { useCallback, useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { VscHome, VscArchive, VscCode, VscGraph, VscMenu, VscEdit } from 'react-icons/vsc';
import { FiSun, FiMoon, FiUsers } from 'react-icons/fi';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Connection,
  EdgeChange,
  NodeChange,
  BackgroundVariant,
  ReactFlowInstance,
  SelectionMode,
} from 'reactflow';
import 'reactflow/dist/style.css';
import Dock from '../components/Dock';
import type { DockItemData } from '../components/Dock';
import NodesSidebar from '../components/NodesSidebar';
import Modal from '../components/Modal';

import { useTheme } from '../hooks/useTheme';
import { useModal } from '../hooks/useModal';
import './WorkflowBuilder.css';

// Start with empty canvas
const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

const WorkflowBuilder: React.FC = () => {
  const [nodes, setNodes, onNodesChangeBase] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const [isInteractive, setIsInteractive] = useState(true);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [showNewProjectDialog, setShowNewProjectDialog] = useState(false);
  const [saveProjectName, setSaveProjectName] = useState('');
  const [saveProjectDescription, setSaveProjectDescription] = useState('');
  const [hasAutoSave, setHasAutoSave] = useState(false);
  const [lastAutoSave, setLastAutoSave] = useState<string | null>(null);
  const [currentProjectName, setCurrentProjectName] = useState('Build-0');
  const [isEditingProjectName, setIsEditingProjectName] = useState(false);
  const [tempProjectName, setTempProjectName] = useState('Build-0');
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { isDarkMode, toggleTheme } = useTheme();
  const { modal, showModal, hideModal } = useModal();

  // Undo/Redo state management
  const [undoStack, setUndoStack] = useState<Array<{nodes: Node[], edges: Edge[]}>>([]);
  const [redoStack, setRedoStack] = useState<Array<{nodes: Node[], edges: Edge[]}>>([]);
  const [isUndoRedoing, setIsUndoRedoing] = useState(false);

  // Save current state to undo stack
  const saveStateToHistory = useCallback(() => {
    if (isUndoRedoing) return; // Don't save state during undo/redo operations
    
    setUndoStack(prev => {
      const newStack = [...prev, { nodes: [...nodes], edges: [...edges] }];
      // Limit undo stack to 50 items to prevent memory issues
      return newStack.length > 50 ? newStack.slice(1) : newStack;
    });
    // Clear redo stack when new action is performed
    setRedoStack([]);
  }, [nodes, edges, isUndoRedoing]);

  // Undo function
  const handleUndo = useCallback(() => {
    if (undoStack.length === 0) return;
    
    setIsUndoRedoing(true);
    const lastState = undoStack[undoStack.length - 1];
    
    // Save current state to redo stack
    setRedoStack(prev => [...prev, { nodes: [...nodes], edges: [...edges] }]);
    
    // Remove last state from undo stack
    setUndoStack(prev => prev.slice(0, -1));
    
    // Restore previous state
    setNodes(lastState.nodes);
    setEdges(lastState.edges);
    
    // Clear selection if the selected node no longer exists
    if (selectedNode && !lastState.nodes.some(node => node.id === selectedNode.id)) {
      setSelectedNode(null);
    }
    
    setTimeout(() => setIsUndoRedoing(false), 0);
  }, [undoStack, nodes, edges, selectedNode, setNodes, setEdges]);

  // Redo function
  const handleRedo = useCallback(() => {
    if (redoStack.length === 0) return;
    
    setIsUndoRedoing(true);
    const nextState = redoStack[redoStack.length - 1];
    
    // Save current state to undo stack
    setUndoStack(prev => [...prev, { nodes: [...nodes], edges: [...edges] }]);
    
    // Remove last state from redo stack
    setRedoStack(prev => prev.slice(0, -1));
    
    // Restore next state
    setNodes(nextState.nodes);
    setEdges(nextState.edges);
    
    // Clear selection if the selected node no longer exists
    if (selectedNode && !nextState.nodes.some(node => node.id === selectedNode.id)) {
      setSelectedNode(null);
    }
    
    setTimeout(() => setIsUndoRedoing(false), 0);
  }, [redoStack, nodes, edges, selectedNode, setNodes, setEdges]);

  // Default fields for UI Form
  const getFormFields = (node: Node) => {
    // If formFields has been set (even if empty), use it as-is
    if (node.data.hasOwnProperty('formFields')) {
      return node.data.formFields || [];
    }
    // Only provide defaults for brand new nodes that haven't been configured yet
    return [
      { label: 'First Name' },
      { label: 'Last Name' },
      { label: 'Wallet Address' }
    ];
  };



  // Keyboard shortcuts for node selection and undo/redo
  // Auto-save functionality
  const autoSave = useCallback(() => {
    if (nodes.length > 0 || edges.length > 0) {
      const autoSaveData = {
        nodes,
        edges,
        timestamp: new Date().toISOString()
      };
      localStorage.setItem('xrpl-workflow-autosave', JSON.stringify(autoSaveData));
      setHasAutoSave(true);
      setLastAutoSave(new Date().toLocaleTimeString());
      console.log('Auto-saved workspace with', nodes.length, 'nodes and', edges.length, 'edges');
    }
  }, [nodes, edges]);

  // Load project or auto-save on component mount
  useEffect(() => {
    console.log('WorkflowBuilder mounted, checking for project/auto-save to load...');
    
    const loadProject = sessionStorage.getItem('loadProject');
    if (loadProject) {
      try {
        const project = JSON.parse(loadProject);
        console.log('Loading specific project:', project.name);
        setNodes(project.nodes || []);
        setEdges(project.edges || []);
        sessionStorage.removeItem('loadProject');
        // Clear auto-save when loading a specific project
        localStorage.removeItem('xrpl-workflow-autosave');
        setHasAutoSave(false);
        setLastAutoSave(null);
        return;
      } catch (error) {
        console.error('Error loading project:', error);
      }
    }

    // If no specific project to load, check for auto-save
    const autoSaveData = localStorage.getItem('xrpl-workflow-autosave');
    if (autoSaveData) {
      try {
        const saved = JSON.parse(autoSaveData);
        console.log('Loading auto-saved data:', saved);
        setNodes(saved.nodes || []);
        setEdges(saved.edges || []);
        setHasAutoSave(true);
        setLastAutoSave(new Date(saved.timestamp).toLocaleTimeString());
        console.log('Auto-save loaded successfully');
      } catch (error) {
        console.error('Error loading auto-save:', error);
        localStorage.removeItem('xrpl-workflow-autosave');
      }
    } else {
      console.log('No auto-save data found');
    }
  }, [setNodes, setEdges]);

  // Auto-save when nodes or edges change (debounced)
  useEffect(() => {
    // Skip auto-save if we just loaded the component (first render)
    const timer = setTimeout(() => {
      if (nodes.length > 0 || edges.length > 0) {
        autoSave();
      }
    }, 2000); // Auto-save after 2 seconds of inactivity

    return () => clearTimeout(timer);
  }, [nodes, edges, autoSave]);

  // Auto-save on page unload and navigation
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (nodes.length > 0 || edges.length > 0) {
        const autoSaveData = {
          nodes,
          edges,
          timestamp: new Date().toISOString()
        };
        localStorage.setItem('xrpl-workflow-autosave', JSON.stringify(autoSaveData));
      }
    };

    // Save on page unload
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    // Save immediately when component unmounts (page navigation)
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      handleBeforeUnload(); // Save when component unmounts
    };
  }, [nodes, edges]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for Cmd+Z (Mac) or Ctrl+Z (Windows) - Undo
      if ((event.metaKey || event.ctrlKey) && event.key === 'z' && !event.shiftKey) {
        event.preventDefault();
        handleUndo();
        return;
      }

      // Check for Cmd+Y (Mac) or Ctrl+Y (Windows) - Redo
      // Also handle Cmd+Shift+Z (Mac) as alternative redo
      if ((event.metaKey || event.ctrlKey) && (event.key === 'y' || (event.key === 'z' && event.shiftKey))) {
        event.preventDefault();
        handleRedo();
        return;
      }

      // Check for Cmd+A (Mac) or Ctrl+A (Windows) - Select All
      if ((event.metaKey || event.ctrlKey) && event.key === 'a') {
        event.preventDefault();
        console.log('Select all nodes triggered');
        
        // Select all nodes
        const updatedNodes = nodes.map(node => ({
          ...node,
          selected: true
        }));
        setNodes(updatedNodes);
        return;
      }

      // Escape key - Deselect all nodes
      if (event.key === 'Escape') {
        event.preventDefault();
        console.log('Deselect all nodes triggered');
        
        // Deselect all nodes
        const updatedNodes = nodes.map(node => ({
          ...node,
          selected: false
        }));
        setNodes(updatedNodes);
        setSelectedNode(null); // Also clear configuration panel
        return;
      }
    };

    // Add event listener
    document.addEventListener('keydown', handleKeyDown);

    // Cleanup
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [nodes, setNodes, handleUndo, handleRedo]);

  const onConnect = useCallback(
    (params: Connection) => {
      saveStateToHistory();
      setEdges((eds) => addEdge(params, eds));
    },
    [setEdges, saveStateToHistory]
  );

  // Custom onEdgesChange to track edge deletions
  const onEdgesChangeCustom = useCallback((changes: EdgeChange[]) => {
    // Only track edge removals for undo/redo
    const significantChanges = changes.filter(change => change.type === 'remove');
    
    if (significantChanges.length > 0) {
      saveStateToHistory();
    }
    
    // Apply the changes
    onEdgesChange(changes);
  }, [onEdgesChange, saveStateToHistory]);

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    
    // Close sidebar when clicking on canvas
    if (sidebarOpen) {
      setSidebarOpen(false);
    }
    
    // Deselect all nodes when clicking on empty canvas
    const updatedNodes = nodes.map(node => ({
      ...node,
      selected: false
    }));
    setNodes(updatedNodes);
  }, [nodes, setNodes, sidebarOpen]);

  // Smart positioning function to find closest empty area
  const findEmptyPosition = useCallback((preferredX: number = 400, preferredY: number = 300) => {
    const nodeWidth = 150; // Approximate node width
    // const nodeHeight = 50; // Approximate node height
    const spacing = 20; // Minimum spacing between nodes
    
    // Check if a position overlaps with existing nodes
    const isPositionOccupied = (x: number, y: number) => {
      return nodes.some(node => {
        const distance = Math.sqrt(
          Math.pow(node.position.x - x, 2) + Math.pow(node.position.y - y, 2)
        );
        return distance < (nodeWidth + spacing);
      });
    };
    
    // Start from preferred position and spiral outward to find empty space
    let searchRadius = 0;
    const maxRadius = 500; // Maximum search distance
    const step = 30; // Step size for search
    
    while (searchRadius <= maxRadius) {
      // Try positions in a circle around the preferred position
      for (let angle = 0; angle < 360; angle += 45) {
        const radian = (angle * Math.PI) / 180;
        const x = preferredX + searchRadius * Math.cos(radian);
        const y = preferredY + searchRadius * Math.sin(radian);
        
        if (!isPositionOccupied(x, y)) {
          return { x, y };
        }
      }
      searchRadius += step;
    }
    
    // If no empty space found, fall back to slight stacking
    const stackOffset = nodes.length * 15;
    return {
      x: preferredX + (stackOffset % 60),
      y: preferredY + Math.floor(stackOffset / 60) * 20
    };
  }, [nodes]);

  // Add node from sidebar click
  const onAddNodeFromSidebar = useCallback((nodeItem: any) => {
    console.log('Adding node from sidebar:', nodeItem.label);
    
    // Save state before adding new node
    saveStateToHistory();
    
    // Find the best empty position
    const position = findEmptyPosition();
    
    const newNode: Node = {
      id: `node_${Date.now()}`,
      type: nodeItem.type === 'trigger' ? 'input' : nodeItem.type === 'logic' ? 'default' : 'default',
      position: position,
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
        textAlign: 'center' as const
      }
    };
    
    setNodes((nds) => nds.concat(newNode));
  }, [findEmptyPosition, setNodes, saveStateToHistory]);

  // Custom onNodesChange that clears selection if selected node is deleted and saves state
  const onNodesChange = useCallback((changes: NodeChange[]) => {
    // Debug: Log change types to see what's being triggered
    if (changes.length > 0) {
      console.log('Node change types:', changes.map(c => c.type));
    }
    
    // Only track these significant changes for undo/redo:
    const significantChanges = changes.filter(change => 
      change.type === 'remove' || // Node deletion
      (change.type === 'position' && change.dragging === false && change.positionAbsolute) // Only save position when drag ends and position actually changed
      // Explicitly exclude: 'select', 'add' (handled separately), 'dimensions', and other minor changes
    );
    
    if (significantChanges.length > 0) {
      console.log('Saving to history for change types:', significantChanges.map(c => c.type));
      saveStateToHistory();
    }
    
    // Check if any node is being removed
    const removedNodes = changes.filter(change => change.type === 'remove');
    
    // If the currently selected node is being removed, clear the selection
    if (selectedNode && removedNodes.some(change => change.id === selectedNode.id)) {
      setSelectedNode(null);
    }
    
    // Apply the changes
    onNodesChangeBase(changes);
  }, [selectedNode, onNodesChangeBase, saveStateToHistory]);

    const addNewNode = useCallback(() => {
    const newNode: Node = {
      id: `${nodes.length + 1}`,
      data: { label: `New XRPL Node ${nodes.length + 1}` },
      position: { x: Math.random() * 400, y: Math.random() * 400 },
      style: {
        background: 'var(--accent-purple)',
        color: 'white',
        border: '1px solid var(--accent-purple)',
        borderRadius: '8px',
        fontSize: '12px',
        fontWeight: '500',
      },
    };
    setNodes((nds) => [...nds, newNode]);
  }, [nodes.length, setNodes]);

  // Deploy function to collect all node configurations and send workflow to API
  const handleDeploy = useCallback(async () => {
    const workflow: any[] = [];

    // Find and process UI Form nodes
    const uiFormNodes = nodes.filter(node => node.data.label === 'UI Form');
    if (uiFormNodes.length > 0) {
      const allFormFields: string[] = [];
      uiFormNodes.forEach(node => {
        const fields = getFormFields(node);
        const validFields = fields
          .filter((field: any) => field.label && field.label.trim() !== '')
          .map((field: any) => field.label.trim().toLowerCase().replace(/\s+/g, '_'));
        allFormFields.push(...validFields);
      });

      if (allFormFields.length > 0) {
        workflow.push({
          type: "ui_form",
          config: {
            fields: allFormFields
          },
          next: "did_verification"
        });
      }
    }

    // Find and process Identity Verification nodes
    const didNodes = nodes.filter(node => node.data.label === 'Identity Verification (DID)');
    if (didNodes.length > 0) {
      const didNode = didNodes[0]; // Take first one
      workflow.push({
        type: "did_verification",
        config: {
          provider: "XRPL",
          required_claims: ["wallet_ownership"],
          xrpl_network: didNode.data.networkOption?.toLowerCase() || "testnet",
          verification_method: "xrpl_did"
        },
        next: "escrow_accounts"
      });
    }

    // Find and process Escrow Account nodes
    const escrowNodes = nodes.filter(node => node.data.label === 'Escrow Account');
    if (escrowNodes.length > 0) {
      const escrowNode = escrowNodes[0]; // Take first one
      workflow.push({
        type: "escrow_accounts",
        config: {
          provider: "XRPL",
          auto_release: false,
          approval_required: true,
          release_condition: "email_verification",
          wallet_address: escrowNode.data.walletAddress || "",
          email_address: escrowNode.data.emailAddress || "",
          wallet_secret: escrowNode.data.walletSecret || "",
          currency_option: escrowNode.data.currencyOption || "XRP"
        },
        next: "summarization"
      });
    }

    // Find and process Transaction Monitoring nodes (maps to summarization)
    const transactionNodes = nodes.filter(node => node.data.label === 'Transaction Monitoring');
    if (transactionNodes.length > 0) {
      const transactionNode = transactionNodes[0]; // Take first one
      const llmProviderMap: { [key: string]: string } = {
        'Gemini': 'gemini',
        'GPT': 'openai',
        'Perplexity': 'perplexity'
      };
      
      workflow.push({
        type: "summarization",
        config: {
          generate_report: true,
          metrics_string: transactionNode.data.transactionMetric || "",
          llm_provider: llmProviderMap[transactionNode.data.llmProvider] || "openai",
          web_search: transactionNode.data.webSearch === 'Enable' || transactionNode.data.webSearch === undefined
        },
        next: "END"
      });
    }

    // Validate workflow
    if (workflow.length === 0) {
              showModal('No configured nodes found. Please add and configure nodes (UI Form, Identity Verification, Escrow Account, Transaction Monitoring) to deploy.', 'Deployment Error', 'warning');
      return;
    }

    try {
      console.log('Sending workflow deployment request:', workflow);
      
      const response = await fetch('http://localhost:8000/workflow', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(workflow)
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Workflow deployment successful:', result);
        showModal(`Workflow deployed successfully!\n\nDeployed ${workflow.length} node(s):\n${workflow.map((node, index) => `${index + 1}. ${node.type}`).join('\n')}`, 'Deployment Successful', 'success');
      } else {
        const errorText = await response.text();
        console.error('Workflow deployment failed:', response.status, errorText);
                  showModal(`Deployment failed: ${response.status} ${response.statusText}\n${errorText}`, 'Deployment Failed', 'error');
      }
    } catch (error) {
      console.error('Error during workflow deployment:', error);
              showModal(`Deployment error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'Deployment Error', 'error');
    }
  }, [nodes, getFormFields]);

  const handleSaveWorkflow = () => {
    if (nodes.length === 0) {
      showModal('Cannot save an empty workflow. Please add some nodes first.', 'Save Error', 'warning');
      return;
    }
    setSaveProjectName(currentProjectName);
    setShowSaveDialog(true);
  };

  const saveWorkflow = () => {
    if (!saveProjectName.trim()) {
      showModal('Please enter a project name.', 'Save Error', 'warning');
      return;
    }

    try {
      const existingProjects = localStorage.getItem('xrpl-workflows');
      const projects = existingProjects ? JSON.parse(existingProjects) : [];
      
      const newProject = {
        id: Date.now().toString(),
        name: saveProjectName.trim(),
        description: saveProjectDescription.trim(),
        nodes: [...nodes],
        edges: [...edges],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      projects.push(newProject);
      localStorage.setItem('xrpl-workflows', JSON.stringify(projects));
      
      setShowSaveDialog(false);
      setSaveProjectName('');
      setSaveProjectDescription('');
      
      // Clear auto-save since project is now explicitly saved
      localStorage.removeItem('xrpl-workflow-autosave');
      setHasAutoSave(false);
      setLastAutoSave(null);
      
              showModal('Workflow saved successfully!', 'Save Successful', 'success');
      
      // Check if we should start a new project after saving
      const shouldStartNew = sessionStorage.getItem('startNewAfterSave');
      if (shouldStartNew) {
        sessionStorage.removeItem('startNewAfterSave');
        setTimeout(() => {
          clearWorkspace();
        }, 100);
      }
    } catch (error) {
      console.error('Error saving workflow:', error);
              showModal('Failed to save workflow. Please try again.', 'Save Failed', 'error');
    }
  };

  const cancelSave = () => {
    setShowSaveDialog(false);
    setSaveProjectName('');
    setSaveProjectDescription('');
  };

  const startNewProject = () => {
    if (nodes.length > 0 || edges.length > 0) {
      setShowNewProjectDialog(true);
    } else {
      // If canvas is empty, just start fresh
      clearWorkspace();
    }
  };

  const clearWorkspace = () => {
    setNodes([]);
    setEdges([]);
    localStorage.removeItem('xrpl-workflow-autosave');
    setHasAutoSave(false);
    setLastAutoSave(null);
    setSelectedNode(null);
    setShowNewProjectDialog(false);
  };

  const saveCurrentAndStartNew = () => {
    setShowNewProjectDialog(false);
    setShowSaveDialog(true);
    // Set a flag to clear workspace after saving
    sessionStorage.setItem('startNewAfterSave', 'true');
  };

  const discardAndStartNew = () => {
    clearWorkspace();
  };

  const cancelNewProject = () => {
    setShowNewProjectDialog(false);
  };

  const startEditingProjectName = () => {
    setTempProjectName(currentProjectName);
    setIsEditingProjectName(true);
  };

  const saveEditedProjectName = () => {
    if (tempProjectName.trim()) {
      setCurrentProjectName(tempProjectName.trim());
    } else {
      setTempProjectName(currentProjectName);
    }
    setIsEditingProjectName(false);
  };

  const cancelEditingProjectName = () => {
    setTempProjectName(currentProjectName);
    setIsEditingProjectName(false);
  };

  const handleProjectNameKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      saveEditedProjectName();
    } else if (event.key === 'Escape') {
      cancelEditingProjectName();
    }
  };



  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      console.log('Drop event triggered at:', { x: event.clientX, y: event.clientY }); // Debug log

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      if (!reactFlowBounds || !reactFlowInstance) {
        console.log('Missing bounds or instance:', { reactFlowBounds, reactFlowInstance }); // Debug log
        return;
      }

      console.log('ReactFlow bounds:', reactFlowBounds); // Debug log

      const nodeData = event.dataTransfer.getData('application/reactflow');
      console.log('Retrieved node data:', nodeData); // Debug log
      if (!nodeData) {
        console.log('No node data found in dataTransfer'); // Debug log
        return;
      }

      try {
        const parsedNodeData = JSON.parse(nodeData);
        console.log('Parsed node data:', parsedNodeData); // Debug log
        
        // Save state before adding new node
        saveStateToHistory();
        
        // Calculate position relative to the ReactFlow canvas
        const position = reactFlowInstance.project({
          x: event.clientX - reactFlowBounds.left,
          y: event.clientY - reactFlowBounds.top,
        });

        console.log('Calculated position:', position); // Debug log

        const newNode: Node = {
          id: `node_${Date.now()}`, // Use timestamp for unique ID
          type: parsedNodeData.type === 'trigger' ? 'input' : parsedNodeData.type === 'logic' ? 'default' : 'default',
          position,
          data: parsedNodeData.data,
          style: parsedNodeData.style,
        };

        console.log('Adding new node:', newNode); // Debug log
        setNodes((nds) => nds.concat(newNode));
      } catch (error) {
        console.error('Error parsing dropped node data:', error);
      }
    },
    [reactFlowInstance, setNodes, saveStateToHistory]
  );

  const handleNavigation = (path: string) => {
    // Auto-save before navigation
    if (nodes.length > 0 || edges.length > 0) {
      const autoSaveData = {
        nodes,
        edges,
        timestamp: new Date().toISOString()
      };
      localStorage.setItem('xrpl-workflow-autosave', JSON.stringify(autoSaveData));
      setHasAutoSave(true);
      setLastAutoSave(new Date().toLocaleTimeString());
      console.log('Saved workspace before navigation to', path, 'with', nodes.length, 'nodes and', edges.length, 'edges');
    } else {
      console.log('No content to save before navigation to', path);
    }
    navigate(path);
  };

  const dockItems: DockItemData[] = [
    { 
      icon: <VscHome size={18} />, 
      label: 'Home', 
      onClick: () => handleNavigation('/') 
    },
    { 
      icon: <VscCode size={18} />, 
      label: 'Workflow Builder', 
      onClick: () => handleNavigation('/workflow-builder') 
    },
    { 
      icon: <VscGraph size={18} />, 
      label: 'Market Data', 
      onClick: () => handleNavigation('/market-data') 
    },
    { 
      icon: <VscArchive size={18} />, 
      label: 'Projects', 
      onClick: () => handleNavigation('/projects') 
    },
    { 
      icon: <FiUsers size={18} />, 
      label: 'Team', 
      onClick: () => handleNavigation('/team') 
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
    <div className="workflow-builder">
      {/* Header */}
      <div className="workflow-header">
        {/* Hamburger Menu */}
        <button 
          className="hamburger-menu"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          <VscMenu size={20} />
        </button>

        <div className="workflow-title">
          <h1>Agentflow XRPL - Builder</h1>
          <p>Build powerful XRPL automations with visual workflows</p>
          {hasAutoSave && lastAutoSave && (
            <div className="auto-save-indicator">
              <span className="auto-save-dot"></span>
              Auto-saved at {lastAutoSave}
            </div>
          )}
        </div>

        {/* Project Name Editor */}
        <div className="project-name-section">
          {isEditingProjectName ? (
            <div className="project-name-editor">
              <input
                type="text"
                value={tempProjectName}
                onChange={(e) => setTempProjectName(e.target.value)}
                onKeyDown={handleProjectNameKeyDown}
                onBlur={saveEditedProjectName}
                autoFocus
                className="project-name-input"
                placeholder="Project name..."
              />
              <div className="project-name-actions">
                <button onClick={saveEditedProjectName} className="save-name-btn">✓</button>
                <button onClick={cancelEditingProjectName} className="cancel-name-btn">✕</button>
              </div>
            </div>
          ) : (
            <div className="project-name-display" onClick={startEditingProjectName}>
              <h2 className="project-name">{currentProjectName}</h2>
              <VscEdit className="edit-icon" size={14} />
            </div>
          )}
        </div>


        <div className="workflow-controls">
          <button className="btn-secondary" onClick={handleSaveWorkflow}>
            Save Workflow
          </button>
          <button className="btn-new-project" onClick={startNewProject}>
            New Project
          </button>
          <button className="btn-deploy" onClick={handleDeploy}>
            Deploy
          </button>
        </div>
      </div>

      {/* Main content area - Canva-style layout */}
      <div className="workflow-main-content">
        {/* Nodes Sidebar */}
        <NodesSidebar 
          isOpen={sidebarOpen} 
          onClose={() => setSidebarOpen(false)} 
          onAddNode={onAddNodeFromSidebar}
        />

        {/* Main workflow canvas */}
        <div className="workflow-canvas" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChangeCustom}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            attributionPosition="bottom-left"
            // Interactive controls
            nodesDraggable={isInteractive}
            nodesConnectable={isInteractive}
            elementsSelectable={isInteractive}
            // Canva-style navigation
            panOnScroll={isInteractive}
            panOnScrollSpeed={0.5}
            zoomOnScroll={isInteractive}
            zoomOnPinch={isInteractive}
            zoomOnDoubleClick={isInteractive}
            selectionOnDrag={isInteractive}
            selectionMode={SelectionMode.Partial}
            multiSelectionKeyCode={["Meta", "Control"]}
            deleteKeyCode={["Delete", "Backspace"]}
            // Pan with mouse/trackpad
            panOnDrag={isInteractive ? [1, 2] : false}
            // Zoom settings
            minZoom={0.1}
            maxZoom={4}
          >
            <Background 
              variant={BackgroundVariant.Dots} 
              gap={20} 
              size={1}
              color="var(--text-secondary)"
            />
            <Controls 
              style={{
                background: 'rgba(6, 6, 6, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
              }}
              onInteractiveChange={(interactive) => setIsInteractive(interactive)}
              showInteractive={true}
            />
            <MiniMap 
              style={{
                background: 'rgba(6, 6, 6, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
              }}
              nodeColor="var(--accent-purple)"
              maskColor="rgba(0, 0, 0, 0.2)"
            />
          </ReactFlow>
        </div>

        {/* Configuration Panel */}
        {selectedNode && (
          <div className="node-properties">
            <h3>Configuration Panel</h3>
            
            <div className="node-properties-content">
              {/* Basic Information */}
              <div className="config-section">
              <h4>Basic Information</h4>
              <div className="property-group">
                <label>Node ID:</label>
                <span>{selectedNode.id}</span>
              </div>
              <div className="property-group">
                <label>Label:</label>
                <input 
                  type="text" 
                  value={selectedNode.data.label} 
                  onChange={(e) => {
                    setNodes((nds) =>
                      nds.map((node) =>
                        node.id === selectedNode.id
                          ? { ...node, data: { ...node.data, label: e.target.value } }
                          : node
                      )
                    );
                    setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, label: e.target.value } });
                  }}
                />
              </div>
              <div className="property-group">
                <label>Position:</label>
                <span>X: {Math.round(selectedNode.position.x)}, Y: {Math.round(selectedNode.position.y)}</span>
              </div>
            </div>

            {/* UI Form Configuration - Only show for UI Form nodes */}
            {selectedNode.data.label === 'UI Form' && (
              <div className="config-section">
                <h4>Form Fields</h4>
                <div className="form-fields-config">
                  {/* Current Fields */}
                  {getFormFields(selectedNode).map((field: any, index: number) => (
                    <div key={index} className="field-item">
                      <div className="property-group">
                        <label>Field {index + 1}:</label>
                        <div className="field-input-group">
                          <input
                            type="text"
                            placeholder="Enter form label"
                            value={field.label || ''}
                            onChange={(e) => {
                              const currentFields = getFormFields(selectedNode);
                              const newFields = [...currentFields];
                              newFields[index] = { ...newFields[index], label: e.target.value };
                              // Always set formFields property to indicate this node has been configured
                              const updatedData = { ...selectedNode.data, formFields: newFields };
                              
                              setNodes((nds) =>
                                nds.map((node) =>
                                  node.id === selectedNode.id
                                    ? { ...node, data: updatedData }
                                    : node
                                )
                              );
                              setSelectedNode({ ...selectedNode, data: updatedData });
                            }}
                          />
                          <button
                            className="delete-field-btn"
                            onClick={() => {
                              const currentFields = getFormFields(selectedNode);
                              const newFields = currentFields.filter((_: any, i: number) => i !== index);
                              // Always set formFields property to indicate this node has been configured
                              const updatedData = { ...selectedNode.data, formFields: newFields };
                              
                              setNodes((nds) =>
                                nds.map((node) =>
                                  node.id === selectedNode.id
                                    ? { ...node, data: updatedData }
                                    : node
                                )
                              );
                              setSelectedNode({ ...selectedNode, data: updatedData });
                            }}
                          >
                            ×
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* Add Field Button */}
                  <button
                    className="add-field-btn"
                    onClick={() => {
                      const currentFields = getFormFields(selectedNode);
                      if (currentFields.length >= 10) {
                        showModal('Maximum 10 fields allowed', 'Field Limit', 'warning');
                        return;
                      }
                      
                      const newField = { label: '' };
                      const newFields = [...currentFields, newField];
                      const updatedData = { ...selectedNode.data, formFields: newFields };
                      
                      setNodes((nds) =>
                        nds.map((node) =>
                          node.id === selectedNode.id
                            ? { ...node, data: updatedData }
                            : node
                        )
                      );
                      setSelectedNode({ ...selectedNode, data: updatedData });
                    }}
                    disabled={getFormFields(selectedNode).length >= 10}
                  >
                    + Add Field ({getFormFields(selectedNode).length}/10)
                  </button>
                </div>
              </div>
            )}

            {/* Identity Verification Configuration - Only show for Identity Verification nodes */}
            {selectedNode.data.label === 'Identity Verification (DID)' && (
              <div className="config-section">
                <h4>Verification Settings</h4>
                <div className="verification-config">
                  {/* Required Claims Option */}
                  <div className="property-group">
                    <label>Required Claims Option:</label>
                    <select
                      value={selectedNode.data.requiredClaims || 'select'}
                      onChange={(e) => {
                        const updatedData = { ...selectedNode.data, requiredClaims: e.target.value };
                        setNodes((nds) =>
                          nds.map((node) =>
                            node.id === selectedNode.id
                              ? { ...node, data: updatedData }
                              : node
                          )
                        );
                        setSelectedNode({ ...selectedNode, data: updatedData });
                      }}
                    >
                      <option value="select" disabled>Select an option</option>
                      <option value="Wallet Ownership">Wallet Ownership</option>
                    </select>
                  </div>

                  {/* Network Options Toggle */}
                  <div className="property-group">
                    <label>Network Options:</label>
                    <div className="toggle-switch" data-active={selectedNode.data.networkOption || 'Testnet'}>
                      <button
                        className={`toggle-option ${(selectedNode.data.networkOption || 'Testnet') === 'Testnet' ? 'active' : ''}`}
                        onClick={() => {
                          const updatedData = { ...selectedNode.data, networkOption: 'Testnet' };
                          setNodes((nds) =>
                            nds.map((node) =>
                              node.id === selectedNode.id
                                ? { ...node, data: updatedData }
                                : node
                            )
                          );
                          setSelectedNode({ ...selectedNode, data: updatedData });
                        }}
                      >
                        Testnet
                      </button>
                      <button
                        className={`toggle-option ${(selectedNode.data.networkOption || 'Testnet') === 'Mainnet' ? 'active' : ''}`}
                        onClick={() => {
                          const updatedData = { ...selectedNode.data, networkOption: 'Mainnet' };
                          setNodes((nds) =>
                            nds.map((node) =>
                              node.id === selectedNode.id
                                ? { ...node, data: updatedData }
                                : node
                            )
                          );
                          setSelectedNode({ ...selectedNode, data: updatedData });
                        }}
                      >
                        Mainnet
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Escrow Account Configuration - Only show for Escrow Account nodes */}
            {selectedNode.data.label === 'Escrow Account' && (
              <div className="config-section">
                <h4>Account Settings</h4>
                <div className="account-config">
                  {/* Wallet Address - Required */}
                  <div className="property-group">
                    <label>Wallet Address<span className="required">*</span>:</label>
                    <input
                      type="text"
                      placeholder="Enter wallet address"
                      value={selectedNode.data.walletAddress || ''}
                      onChange={(e) => {
                        const updatedData = { ...selectedNode.data, walletAddress: e.target.value };
                        setNodes((nds) =>
                          nds.map((node) =>
                            node.id === selectedNode.id
                              ? { ...node, data: updatedData }
                              : node
                          )
                        );
                        setSelectedNode({ ...selectedNode, data: updatedData });
                      }}
                      required
                    />
                  </div>

                  {/* Email Address - Required */}
                  <div className="property-group">
                    <label>Email Address<span className="required">*</span>:</label>
                    <input
                      type="email"
                      placeholder="Enter email address"
                      value={selectedNode.data.emailAddress || ''}
                      onChange={(e) => {
                        const updatedData = { ...selectedNode.data, emailAddress: e.target.value };
                        setNodes((nds) =>
                          nds.map((node) =>
                            node.id === selectedNode.id
                              ? { ...node, data: updatedData }
                              : node
                          )
                        );
                        setSelectedNode({ ...selectedNode, data: updatedData });
                      }}
                      required
                    />
                  </div>

                  {/* Max Balance - Required */}
                  <div className="property-group">
                    <label>Max Balance<span className="required">*</span>:</label>
                    <input
                      type="number"
                      placeholder="Enter maximum balance"
                      value={selectedNode.data.maxBalance || ''}
                      onChange={(e) => {
                        const updatedData = { ...selectedNode.data, maxBalance: e.target.value };
                        setNodes((nds) =>
                          nds.map((node) =>
                            node.id === selectedNode.id
                              ? { ...node, data: updatedData }
                              : node
                          )
                        );
                        setSelectedNode({ ...selectedNode, data: updatedData });
                      }}
                      required
                    />
                  </div>

                  {/* Wallet Secret - Required */}
                  <div className="property-group">
                    <label>Wallet Secret<span className="required">*</span>:</label>
                    <input
                      type="password"
                      placeholder="Enter wallet secret"
                      value={selectedNode.data.walletSecret || ''}
                      onChange={(e) => {
                        const updatedData = { ...selectedNode.data, walletSecret: e.target.value };
                        setNodes((nds) =>
                          nds.map((node) =>
                            node.id === selectedNode.id
                              ? { ...node, data: updatedData }
                              : node
                          )
                        );
                        setSelectedNode({ ...selectedNode, data: updatedData });
                      }}
                      required
                    />
                  </div>

                  {/* Release Condition Dropdown */}
                  <div className="property-group">
                    <label>Release Condition:</label>
                    <select
                      value={selectedNode.data.releaseCondition || 'select'}
                      onChange={(e) => {
                        const updatedData = { ...selectedNode.data, releaseCondition: e.target.value };
                        setNodes((nds) =>
                          nds.map((node) =>
                            node.id === selectedNode.id
                              ? { ...node, data: updatedData }
                              : node
                          )
                        );
                        setSelectedNode({ ...selectedNode, data: updatedData });
                      }}
                    >
                      <option value="select" disabled>Select an option</option>
                      <option value="Email">Email</option>
                    </select>
                  </div>

                  {/* Currency Options Toggle */}
                  <div className="property-group">
                    <label>Currency Options:</label>
                    <div className="toggle-switch" data-active={selectedNode.data.currencyOption || 'XRP'}>
                      <button
                        className={`toggle-option ${(selectedNode.data.currencyOption || 'XRP') === 'XRP' ? 'active' : ''}`}
                        onClick={() => {
                          const updatedData = { ...selectedNode.data, currencyOption: 'XRP' };
                          setNodes((nds) =>
                            nds.map((node) =>
                              node.id === selectedNode.id
                                ? { ...node, data: updatedData }
                                : node
                            )
                          );
                          setSelectedNode({ ...selectedNode, data: updatedData });
                        }}
                      >
                        XRP
                      </button>
                      <button
                        className={`toggle-option ${(selectedNode.data.currencyOption || 'XRP') === 'RLUSD' ? 'active' : ''}`}
                        onClick={() => {
                          const updatedData = { ...selectedNode.data, currencyOption: 'RLUSD' };
                          setNodes((nds) =>
                            nds.map((node) =>
                              node.id === selectedNode.id
                                ? { ...node, data: updatedData }
                                : node
                            )
                          );
                          setSelectedNode({ ...selectedNode, data: updatedData });
                        }}
                      >
                        RLUSD
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Transaction Monitoring Configuration - Only show for Transaction Monitoring nodes */}
            {selectedNode.data.label === 'Transaction Monitoring' && (
              <div className="config-section">
                <h4>Transaction Settings</h4>
                <div className="transaction-config">
                  {/* LLM Provider Dropdown */}
                  <div className="property-group">
                    <label>LLM Provider:</label>
                    <select
                      value={selectedNode.data.llmProvider || 'select'}
                      onChange={(e) => {
                        const updatedData = { ...selectedNode.data, llmProvider: e.target.value };
                        setNodes((nds) =>
                          nds.map((node) =>
                            node.id === selectedNode.id
                              ? { ...node, data: updatedData }
                              : node
                          )
                        );
                        setSelectedNode({ ...selectedNode, data: updatedData });
                      }}
                    >
                      <option value="select" disabled>Select an option</option>
                      <option value="Gemini">Gemini</option>
                      <option value="GPT">GPT</option>
                      <option value="Perplexity">Perplexity</option>
                    </select>
                  </div>

                  {/* Web Search Toggle */}
                  <div className="property-group">
                    <label>Web Search:</label>
                    <div className="toggle-switch" data-active={selectedNode.data.webSearch || 'Enable'}>
                      <button
                        className={`toggle-option ${(selectedNode.data.webSearch || 'Enable') === 'Enable' ? 'active' : ''}`}
                        onClick={() => {
                          const updatedData = { ...selectedNode.data, webSearch: 'Enable' };
                          setNodes((nds) =>
                            nds.map((node) =>
                              node.id === selectedNode.id
                                ? { ...node, data: updatedData }
                                : node
                            )
                          );
                          setSelectedNode({ ...selectedNode, data: updatedData });
                        }}
                      >
                        Enable
                      </button>
                      <button
                        className={`toggle-option ${(selectedNode.data.webSearch || 'Enable') === 'Disable' ? 'active' : ''}`}
                        onClick={() => {
                          const updatedData = { ...selectedNode.data, webSearch: 'Disable' };
                          setNodes((nds) =>
                            nds.map((node) =>
                              node.id === selectedNode.id
                                ? { ...node, data: updatedData }
                                : node
                            )
                          );
                          setSelectedNode({ ...selectedNode, data: updatedData });
                        }}
                      >
                        Disable
                      </button>
                    </div>
                  </div>

                  {/* Transaction Metric Text Field */}
                  <div className="property-group">
                    <label>Transaction Metric:</label>
                    <input
                      type="text"
                      placeholder="Enter transaction metric"
                      value={selectedNode.data.transactionMetric || ''}
                      onChange={(e) => {
                        const updatedData = { ...selectedNode.data, transactionMetric: e.target.value };
                        setNodes((nds) =>
                          nds.map((node) =>
                            node.id === selectedNode.id
                              ? { ...node, data: updatedData }
                              : node
                          )
                        );
                        setSelectedNode({ ...selectedNode, data: updatedData });
                      }}
                    />
                  </div>
                </div>
              </div>
            )}
            </div>

          </div>
        )}
      </div>

      {/* Save Dialog Modal */}
      {showSaveDialog && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Save Workflow</h3>
            <div className="save-form">
              <div className="form-group">
                <label>Project Name<span className="required">*</span>:</label>
                <input
                  type="text"
                  placeholder="Enter project name"
                  value={saveProjectName}
                  onChange={(e) => setSaveProjectName(e.target.value)}
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label>Description (optional):</label>
                <textarea
                  placeholder="Enter project description"
                  value={saveProjectDescription}
                  onChange={(e) => setSaveProjectDescription(e.target.value)}
                  rows={3}
                />
              </div>
              <div className="form-actions">
                <button className="btn-secondary" onClick={cancelSave}>
                  Cancel
                </button>
                <button className="btn-primary" onClick={saveWorkflow}>
                  Save Project
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Project Dialog Modal */}
      {showNewProjectDialog && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Start New Project</h3>
            <p>You have unsaved changes in your current workspace. What would you like to do?</p>
            <div className="new-project-actions">
              <button className="btn-save-and-new" onClick={saveCurrentAndStartNew}>
                Save Current Project
              </button>
              <button className="btn-discard-and-new" onClick={discardAndStartNew}>
                Discard Changes
              </button>
              <button className="btn-cancel-new" onClick={cancelNewProject}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Dock over canvas */}
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

export default WorkflowBuilder; 
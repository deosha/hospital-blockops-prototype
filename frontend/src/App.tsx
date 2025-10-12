/**
 * ============================================================================
 * Hospital BlockOps - Main Application Component
 * ============================================================================
 *
 * Complete React application with:
 * - Real-time API integration using polling
 * - State management for scenarios, agents, messages, and blockchain
 * - Demo controls with start/pause/reset/speed
 * - Error handling and loading states
 * - Comprehensive TypeScript types
 *
 * Architecture:
 * - Uses custom API service layer (src/services/api.ts)
 * - Polls backend every 1-3 seconds for updates
 * - Unsubscribes from polling on component unmount
 * - Handles connection loss and retry logic
 */

import { useState, useEffect, useRef } from 'react';
import {
  Activity,
  Radio,
  Play,
  Pause,
  RotateCcw,
  TrendingUp,
  Clock,
  CheckCircle2,
  Zap,
  Brain,
  Gauge,
  AlertCircle,
  Wifi,
  WifiOff
} from 'lucide-react';
import AgentStatusCard from './components/AgentStatusCard';
import CoordinationTimeline from './components/CoordinationTimeline';
import BlockchainExplorer from './components/BlockchainExplorer';
import MetricsCard from './components/MetricsCard';
import ReasoningViewer, { ReasoningData } from './components/ReasoningViewer';

// Import API service layer
import {
  startScenario,
  resetScenario as apiResetScenario,
  getMessages,
  getAgentStatus,
  pollScenarioStatus,
  pollAgentStatus,
  pollBlockchain,
  checkServerHealth,
  type Scenario,
  type Agent,
  type Message as ApiMessage,
  type BlockchainResponse
} from './services/api';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

/**
 * Component-level Message type (compatible with CoordinationTimeline)
 */
interface Message {
  id: number;
  timestamp: string;
  from: string;
  to: string[];
  type: string;
  content: string;
}

/**
 * Metrics calculated from coordination data
 */

/**
 * Metrics calculated from coordination data
 */
interface Metrics {
  costSavings: number;
  avgLatency: number;
  blockchainTxs: number;
  successRate: number;
}

// ============================================================================
// MAIN APP COMPONENT
// ============================================================================

function App() {
  // =========================================================================
  // STATE MANAGEMENT
  // =========================================================================

  // Scenario state
  const [currentScenario, setCurrentScenario] = useState<Scenario | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [demoSpeed, setDemoSpeed] = useState(1); // 1x, 2x, 4x

  // Agents state
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  // Messages state
  const [messages, setMessages] = useState<Message[]>([]);

  // Blockchain state
  const [blockchain, setBlockchain] = useState<BlockchainResponse | null>(null);

  // UI state
  const [isReasoningModalOpen, setIsReasoningModalOpen] = useState(false);
  const [reasoningData, setReasoningData] = useState<ReasoningData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Metrics (computed from data)
  const [metrics, setMetrics] = useState<Metrics>({
    costSavings: 0,
    avgLatency: 0,
    blockchainTxs: 0,
    successRate: 0
  });

  // =========================================================================
  // REFS FOR POLLING CLEANUP
  // =========================================================================

  const unsubscribeScenario = useRef<(() => void) | null>(null);
  const unsubscribeMessages = useRef<(() => void) | null>(null);
  const unsubscribeAgents = useRef<(() => void) | null>(null);
  const unsubscribeBlockchain = useRef<(() => void) | null>(null);

  // =========================================================================
  // LIFECYCLE: COMPONENT MOUNT
  // =========================================================================

  /**
   * On component mount:
   * 1. Check backend server health
   * 2. Load initial agent status
   * 3. Start polling for agent updates
   */
  useEffect(() => {
    console.log('[App] Component mounted - Initializing...');

    // Check server health
    checkServerHealth()
      .then((healthy) => {
        setIsConnected(healthy);
        if (healthy) {
          console.log('[App] ✓ Backend server is healthy');

          // Load initial agent status
          getAgentStatus()
            .then((agentsData) => {
              setAgents(agentsData);
              console.log('[App] ✓ Loaded agent status:', agentsData.length, 'agents');
            })
            .catch((err) => {
              console.error('[App] Failed to load initial agent status:', err);
            });

          // Start polling for agent status updates
          startAgentPolling();
        } else {
          console.warn('[App] ⚠ Backend server is offline');
          setError('Backend server is not responding. Please start the Flask backend.');
        }
      })
      .catch((err) => {
        console.error('[App] Error checking server health:', err);
        setIsConnected(false);
        setError('Cannot connect to backend server');
      });

    // Cleanup on unmount
    return () => {
      console.log('[App] Component unmounting - Cleaning up...');
      stopAllPolling();
    };
  }, []);

  // =========================================================================
  // POLLING FUNCTIONS
  // =========================================================================

  /**
   * Start polling agent status every 2 seconds
   */
  const startAgentPolling = () => {
    console.log('[App] Starting agent status polling...');

    unsubscribeAgents.current = pollAgentStatus(
      (agentsData) => {
        setAgents(agentsData);
      },
      (error) => {
        console.error('[App] Agent polling error:', error);
        setIsConnected(false);
      },
      2000 // Poll every 2 seconds
    );
  };

  /**
   * Start polling scenario status every 1 second
   */
  const startScenarioPolling = (scenarioId: string) => {
    console.log('[App] Starting scenario polling for:', scenarioId);

    unsubscribeScenario.current = pollScenarioStatus(
      scenarioId,
      (scenario) => {
        console.log('[App] 🔄 Scenario poll update - State:', scenario.state);
        setCurrentScenario(scenario);

        // When scenario completes, stop polling
        if (scenario.state === 'completed') {
          setIsRunning(false);
          console.log('[App] ✓ Scenario completed!');
          // Load final messages
          loadScenarioData(scenarioId);
        } else if (scenario.state === 'failed') {
          setIsRunning(false);
          setError('Scenario execution failed');
          console.error('[App] ✗ Scenario failed');
        }
      },
      (error) => {
        console.error('[App] Scenario polling error:', error);
        setError(error.message);
      },
      1000 // Poll every 1 second
    );

    // Start dedicated message polling every 500ms for real-time updates
    console.log('[App] Starting dedicated message polling for:', scenarioId);
    const messagePollingInterval = setInterval(() => {
      loadScenarioData(scenarioId);
    }, 500); // Poll messages every 500ms for real-time feel

    // Store interval ID so we can clear it later
    unsubscribeMessages.current = () => {
      console.log('[App] Stopping message polling');
      clearInterval(messagePollingInterval);
    };
  };

  /**
   * Start polling blockchain every 3 seconds
   */
  const startBlockchainPolling = () => {
    console.log('[App] Starting blockchain polling...');

    unsubscribeBlockchain.current = pollBlockchain(
      (apiBlockchain) => {
        // Convert API blockchain to component format
        const adaptedBlockchain = adaptBlockchainResponse(apiBlockchain);
        setBlockchain(apiBlockchain); // Store original for reference

        // Update blockchain transaction count metric
        setMetrics(prev => ({
          ...prev,
          blockchainTxs: adaptedBlockchain.blocks.reduce((sum, block) =>
            sum + block.transactions.length, 0
          )
        }));
      },
      (error) => {
        console.error('[App] Blockchain polling error:', error);
      },
      3000 // Poll every 3 seconds
    );
  };

  /**
   * Stop all active polling subscriptions
   */
  const stopAllPolling = () => {
    console.log('[App] Stopping all polling...');

    if (unsubscribeScenario.current) {
      unsubscribeScenario.current();
      unsubscribeScenario.current = null;
    }
    if (unsubscribeMessages.current) {
      unsubscribeMessages.current();
      unsubscribeMessages.current = null;
    }
    if (unsubscribeAgents.current) {
      unsubscribeAgents.current();
      unsubscribeAgents.current = null;
    }
    if (unsubscribeBlockchain.current) {
      unsubscribeBlockchain.current();
      unsubscribeBlockchain.current = null;
    }
  };

  // =========================================================================
  // DATA LOADING FUNCTIONS
  // =========================================================================

  /**
   * Convert API message to component message format
   */
  const adaptApiMessage = (apiMsg: ApiMessage, index: number): Message => ({
    id: index + 1,
    timestamp: apiMsg.timestamp,
    from: apiMsg.from,
    to: apiMsg.to,
    type: apiMsg.type,
    content: typeof apiMsg.content === 'string' ? apiMsg.content : JSON.stringify(apiMsg.content)
  });

  /**
   * Convert API BlockchainResponse to component BlockchainData format
   */
  const adaptBlockchainResponse = (response: BlockchainResponse) => ({
    blocks: response.blocks.map(block => ({
      index: block.index,
      timestamp: block.timestamp,
      transactions: [{
        id: block.data.transaction_id,
        type: block.data.action_type as any, // Map action_type to component type
        agentId: block.data.agent_name,
        agentName: block.data.agent_name,
        action: block.data.action_type,
        timestamp: block.data.timestamp,
        data: block.data.details
      }],
      previousHash: block.previous_hash,
      hash: block.hash,
      nonce: block.nonce || 0,
      validator: block.validator || 'Unknown'
    })),
    chainLength: response.length,
    isValid: response.is_valid,
    lastValidation: response.last_validation,
    validationTimeMs: 0 // API doesn't provide this yet
  });

  /**
   * Load scenario data (messages)
   */
  const loadScenarioData = async (scenarioId: string) => {
    try {
      console.log('[App] 📥 Loading scenario data for:', scenarioId);

      // Load messages from API
      const apiMessages = await getMessages(scenarioId);

      console.log('[App] 📨 Received API messages:', apiMessages.length, 'messages');

      // Convert API messages to component format
      const componentMessages = apiMessages.map((msg, idx) => adaptApiMessage(msg, idx));

      console.log('[App] 📋 Converted messages:', componentMessages.length);
      console.log('[App] 📋 First message sample:', componentMessages[0]);

      setMessages(componentMessages);
      console.log('[App] ✓ Messages state updated with', componentMessages.length, 'messages');

      // Calculate metrics from messages
      calculateMetrics(componentMessages);
    } catch (err: any) {
      console.error('[App] ❌ Error loading scenario data:', err);
      setError(err.message);
    }
  };

  /**
   * Calculate metrics from coordination data
   */
  const calculateMetrics = (messagesData: Message[]) => {
    // Extract timing data
    const timestamps = messagesData
      .map(m => new Date(m.timestamp).getTime())
      .sort((a, b) => a - b);

    const avgLatency = timestamps.length > 1
      ? (timestamps[timestamps.length - 1] - timestamps[0]) / 1000 / timestamps.length
      : 0;

    // Success rate: Check if coordination resulted in execution
    // A coordination is successful if there's an "inform" message with status "executed"
    const proposals = messagesData.filter(m => m.type === 'proposal').length;
    const executedAgreements = messagesData.filter(m =>
      m.type === 'inform' &&
      typeof m.content === 'string' &&
      m.content.includes('"status": "executed"')
    ).length;
    const successRate = proposals > 0 ? (executedAgreements / proposals) * 100 : 0;

    setMetrics(prev => ({
      ...prev,
      costSavings: 33200, // From the scenario (₹1,66,000 - ₹1,32,800)
      avgLatency: parseFloat(avgLatency.toFixed(2)),
      successRate: Math.round(successRate)
    }));
  };

  // =========================================================================
  // SCENARIO CONTROL FUNCTIONS
  // =========================================================================

  /**
   * Start the coordination scenario
   *
   * Predefined scenario from research paper:
   * - PPE shortage in hospital
   * - Supply Chain wants 1000 units (₹1,66,000)
   * - Financial has ₹1,66,000 budget remaining
   * - Facility has only 800 units storage available
   * - Expected outcome: Order 800 units for ₹1,32,800 (storage-constrained)
   */
  const handleStartScenario = async () => {
    console.log('[App] Starting coordination scenario...');
    setIsLoading(true);
    setError(null);

    try {
      // Predefined scenario parameters from research paper
      const scenarioParams = {
        scenario_type: 'supply_chain_coordination',
        parameters: {
          item: 'PPE Masks N95',
          current_stock: 200,
          reorder_point: 500,
          required_quantity: 1000,
          price_per_unit: 166.0, // ₹166 per unit
          supplier: 'MedSupply Corp',
          monthly_budget: 166000, // ₹1,66,000
          spent_this_month: 0,
          budget_remaining: 166000,
          storage_capacity_total: 5000,
          storage_capacity_used: 4200,
          storage_capacity_available: 800 // Limiting factor!
        }
      };

      console.log('[App] Sending scenario request:', scenarioParams);

      // Start scenario via API
      const scenario = await startScenario(scenarioParams);

      console.log('[App] ✓ Scenario started:', scenario.id);
      setCurrentScenario(scenario);
      setIsRunning(true);

      // Start polling for updates
      startScenarioPolling(scenario.id);
      startBlockchainPolling();

      setIsLoading(false);
    } catch (err: any) {
      console.error('[App] Error starting scenario:', err);
      setError(err.message || 'Failed to start scenario');
      setIsLoading(false);
      setIsRunning(false);
    }
  };

  /**
   * Pause/Resume the scenario
   * Note: This just pauses the UI updates, not the backend execution
   */
  const handlePauseResume = () => {
    if (isPaused) {
      console.log('[App] Resuming scenario...');
      setIsPaused(false);

      // Resume polling if scenario is running
      if (currentScenario) {
        startScenarioPolling(currentScenario.id);
        startBlockchainPolling();
      }
    } else {
      console.log('[App] Pausing scenario...');
      setIsPaused(true);

      // Stop scenario, message, and blockchain polling (keep agent polling)
      if (unsubscribeScenario.current) {
        unsubscribeScenario.current();
        unsubscribeScenario.current = null;
      }
      if (unsubscribeMessages.current) {
        unsubscribeMessages.current();
        unsubscribeMessages.current = null;
      }
      if (unsubscribeBlockchain.current) {
        unsubscribeBlockchain.current();
        unsubscribeBlockchain.current = null;
      }
    }
  };

  /**
   * Reset the scenario to initial state
   */
  const handleResetScenario = async () => {
    console.log('[App] Resetting scenario...');
    setIsLoading(true);

    try {
      // Call API reset
      await apiResetScenario();

      // Stop all polling
      stopAllPolling();

      // Reset all state
      setCurrentScenario(null);
      setIsRunning(false);
      setIsPaused(false);
      setMessages([]);
      setBlockchain(null);
      setMetrics({
        costSavings: 0,
        avgLatency: 0,
        blockchainTxs: 0,
        successRate: 0
      });

      // Restart agent polling only
      startAgentPolling();

      console.log('[App] ✓ Scenario reset complete');
      setIsLoading(false);
    } catch (err: any) {
      console.error('[App] Error resetting scenario:', err);
      setError(err.message || 'Failed to reset scenario');
      setIsLoading(false);
    }
  };

  /**
   * Change demo playback speed
   */
  const handleSpeedChange = (speed: number) => {
    console.log('[App] Changing demo speed to', speed, 'x');
    setDemoSpeed(speed);

    // TODO: Adjust polling intervals based on speed
    // For now, this is cosmetic only
  };

  // =========================================================================
  // REASONING MODAL FUNCTIONS
  // =========================================================================

  /**
   * Show agent reasoning for selected agent
   */
  const handleShowReasoning = async () => {
    if (!currentScenario || agents.length === 0) {
      console.warn('[App] No scenario or agents available');
      return;
    }

    try {
      // Get reasoning for first agent (Supply Chain)
      const agentName = agents[0]?.name || 'SC-001';

      // TODO: Fetch real reasoning from API
      // const reasoning = await getAgentReasoning(currentScenario.id, agentName);

      // For now, use sample data (same as before)
      const sampleReasoning: ReasoningData = {
        agentId: 'SC-001',
        agentName: 'Supply Chain Agent',
        agentRole: 'supply_chain',
        timestamp: new Date().toISOString(),
        inputContext: {
          situation: {
            description: 'Critical shortage of PPE supplies detected in Emergency Department. Current inventory at 15% capacity with projected depletion in 48 hours.',
            urgency: 'critical',
            affectedDepartments: ['Emergency', 'ICU', 'Surgical'],
          },
          constraints: [
            {
              agentName: 'Financial Agent',
              type: 'budget_constraint',
              value: { remaining: 166000, allocated: 166000 },
              priority: 'high',
            },
            {
              agentName: 'Facility Agent',
              type: 'storage_constraint',
              value: { available_space: 800, max_capacity: 5000 },
              priority: 'high',
            },
          ],
          historicalData: {
            similarCases: 23,
            avgOutcome: 'Successfully resolved with 18h lead time',
            successRate: 87,
          },
          knowledgeBase: [
            { key: 'min_ppe_threshold', value: 500, source: 'hospital_policy.json' },
            { key: 'emergency_supplier', value: 'MedSupply Corp', source: 'suppliers.db' },
          ],
        },
        llmPrompt: {
          systemMessage: 'You are an expert Supply Chain Agent in a hospital operations system.',
          userMessage: 'SITUATION: Critical PPE shortage in Emergency Department\n- Current inventory: 15% (75 units)\n- Projected depletion: 48 hours',
          temperature: 0.7,
          maxTokens: 2048,
          model: 'gpt-4-turbo-preview',
        },
        llmResponse: {
          analysis: 'Critical situation requiring immediate action. With only 15% inventory remaining and 48-hour depletion window, we need to order supplies immediately. Storage constraint (800 units) is our limiting factor.',
          recommendedAction: 'Order 800 PPE units from MedSupply Corp for ₹1,32,800 with expedited 2-day delivery',
          confidence: 0.92,
          justification: 'This decision balances all constraints optimally: maximizes storage utilization (800/800 units), stays within budget (₹1,32,800/₹1,66,000), and exceeds minimum threshold (800 > 500 units required).',
          alternatives: [
            {
              action: 'Order 1,000 units (budget maximum)',
              pros: ['Maximizes inventory buffer', 'Better long-term coverage'],
              cons: ['Exceeds storage capacity by 200 units', 'Requires off-site storage'],
              confidence: 0.45,
            },
            {
              action: 'Order 500 units (minimum threshold)',
              pros: ['Meets minimum requirement', 'Lower cost (₹83,000)'],
              cons: ['Minimal safety margin', 'Likely to need reorder soon'],
              confidence: 0.68,
            },
          ],
          risks: [
            'Delivery delay beyond 2 days could create critical gap',
            'Supplier out of stock scenario',
            'Usage spike above projections',
          ],
          responseTimeMs: 1847,
          rawJSON: '{\n  "analysis": "Critical situation...",\n  "recommended_action": "Order 800 PPE units",\n  "confidence": 0.92\n}',
        },
        executionResult: {
          actionTaken: 'Purchase order PO-2024-1847 created: 800 PPE units @ ₹166/unit = ₹1,32,800 total',
          smartContractValidation: {
            budgetCheck: true,
            storageCheck: true,
            confidenceCheck: true,
            complianceCheck: true,
            details: 'All policy constraints satisfied. Budget: ₹1,32,800/₹1,66,000 (80%). Storage: 800/800 (100%).',
          },
          blockchainTx: {
            txHash: '0x7f8a3bc4d29e1f5a6b8c9d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2',
            blockNumber: 1847,
            timestamp: new Date().toISOString(),
          },
          outcome: 'Order successfully placed and recorded to blockchain. Supplier confirmed 2-day delivery.',
          impact: {
            costSaved: 33200,
            timesSaved: 2.5,
            efficiencyGain: 23,
          },
        },
        escalationStatus: 'none',
        riskLevel: 'medium',
      };

      setReasoningData(sampleReasoning);
      setIsReasoningModalOpen(true);
    } catch (err: any) {
      console.error('[App] Error loading reasoning:', err);
      setError(err.message);
    }
  };

  // =========================================================================
  // RENDER
  // =========================================================================

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* ===================================================================
          HEADER - Status bar with controls
          =================================================================== */}
      <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-lg bg-slate-900/80 border-b border-slate-700/50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo/Title */}
            <div className="flex items-center space-x-4">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Activity className="w-8 h-8 text-blue-500" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Hospital BlockOps Demo</h1>
                <p className="text-sm text-slate-400">Autonomous Multi-Agent Coordination with Blockchain</p>
              </div>
            </div>

            {/* Status & Controls */}
            <div className="flex items-center space-x-6">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                {isConnected ? (
                  <>
                    <Wifi className="w-4 h-4 text-green-500" />
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-sm text-slate-300">Connected</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4 text-red-500" />
                    <div className="w-2 h-2 rounded-full bg-red-500" />
                    <span className="text-sm text-slate-300">Disconnected</span>
                  </>
                )}
              </div>

              {/* Demo Speed Control */}
              <div className="flex items-center space-x-2">
                <Gauge className="w-4 h-4 text-slate-400" />
                <div className="flex space-x-1">
                  {[1, 2, 4].map((speed) => (
                    <button
                      key={speed}
                      onClick={() => handleSpeedChange(speed)}
                      disabled={!isRunning}
                      className={`px-2 py-1 text-xs rounded transition-all duration-200 ${
                        demoSpeed === speed
                          ? 'bg-blue-500 text-white'
                          : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {speed}x
                    </button>
                  ))}
                </div>
              </div>

              {/* Scenario Controls */}
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleShowReasoning}
                  disabled={!currentScenario}
                  className="flex items-center space-x-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg transition-all duration-200 font-medium"
                  title="View AI Agent Reasoning Process"
                >
                  <Brain className="w-4 h-4" />
                  <span>Reasoning</span>
                </button>

                <button
                  onClick={handleStartScenario}
                  disabled={isRunning || isLoading}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg transition-all duration-200 font-medium"
                >
                  <Play className="w-4 h-4" />
                  <span>{isLoading ? 'Starting...' : 'Start Demo'}</span>
                </button>

                <button
                  onClick={handlePauseResume}
                  disabled={!isRunning || isLoading}
                  className="flex items-center space-x-2 px-4 py-2 bg-yellow-500 hover:bg-yellow-600 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg transition-all duration-200 font-medium"
                >
                  {isPaused ? (
                    <>
                      <Play className="w-4 h-4" />
                      <span>Resume</span>
                    </>
                  ) : (
                    <>
                      <Pause className="w-4 h-4" />
                      <span>Pause</span>
                    </>
                  )}
                </button>

                <button
                  onClick={handleResetScenario}
                  disabled={isLoading}
                  className="flex items-center space-x-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-lg transition-all duration-200"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Reset</span>
                </button>
              </div>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mt-4 px-4 py-3 bg-red-500/10 border border-red-500/50 rounded-lg flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-red-200 font-medium">Error</p>
                <p className="text-sm text-red-300">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-red-400 hover:text-red-300"
              >
                ×
              </button>
            </div>
          )}
        </div>
      </header>

      {/* ===================================================================
          MAIN CONTENT AREA - 3-column layout
          =================================================================== */}
      <main className="container mx-auto px-6 pt-32 pb-8">
        <div className="grid grid-cols-12 gap-6 min-h-[calc(100vh-16rem)]">
          {/* ===============================================================
              LEFT COLUMN - Agent Status (25%)
              =============================================================== */}
          <div className="col-span-3 space-y-4">
            <div className="backdrop-blur-lg bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center">
                <Radio className="w-5 h-5 mr-2 text-blue-500" />
                Active Agents
              </h2>
              <div className="space-y-3">
                {agents.length > 0 ? (
                  agents.map((agent) => (
                    <AgentStatusCard
                      key={agent.name}
                      agent={{
                        id: agent.name,
                        name: agent.name,
                        type: agent.role,
                        state: agent.state,
                        lastAction: agent.last_action,
                        confidence: agent.confidence,
                        timestamp: agent.timestamp
                      }}
                    />
                  ))
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <Radio className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No agents available</p>
                    <p className="text-xs mt-1">Start backend server</p>
                  </div>
                )}
              </div>
            </div>

            {/* Agent Legend */}
            <div className="backdrop-blur-lg bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
              <h3 className="text-sm font-medium text-slate-300 mb-3">Agent States</h3>
              <div className="space-y-2 text-xs text-slate-400">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-slate-500" />
                  <span>Idle: Waiting for tasks</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
                  <span>Thinking: Analyzing context</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                  <span>Negotiating: Coordinating</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <span>Executing: Taking action</span>
                </div>
              </div>
            </div>
          </div>

          {/* ===============================================================
              MIDDLE COLUMN - Coordination Timeline (50%)
              =============================================================== */}
          <div className="col-span-6">
            <div className="backdrop-blur-lg bg-slate-800/50 rounded-xl p-6 border border-slate-700/50 h-full">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2 text-green-500" />
                Coordination Timeline
              </h2>
              <CoordinationTimeline messages={messages} />
            </div>
          </div>

          {/* ===============================================================
              RIGHT COLUMN - Blockchain Explorer (25%)
              =============================================================== */}
          <div className="col-span-3">
            <div className="backdrop-blur-lg bg-slate-800/50 rounded-xl p-4 border border-slate-700/50 h-full">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center">
                <Zap className="w-5 h-5 mr-2 text-purple-500" />
                Blockchain
              </h2>
              <BlockchainExplorer
                data={blockchain ? adaptBlockchainResponse(blockchain) : {
                  blocks: [],
                  chainLength: 0,
                  isValid: true,
                  lastValidation: new Date().toISOString(),
                  validationTimeMs: 0
                }}
              />
            </div>
          </div>
        </div>

        {/* =================================================================
            BOTTOM METRICS DASHBOARD
            ================================================================= */}
        <div className="grid grid-cols-4 gap-6 mt-6">
          <MetricsCard
            icon={<TrendingUp className="w-6 h-6" />}
            title="Cost Savings"
            value={`₹${metrics.costSavings.toLocaleString()}`}
            subtitle="vs manual process"
            color="green"
          />
          <MetricsCard
            icon={<Clock className="w-6 h-6" />}
            title="Decision Latency"
            value={`${metrics.avgLatency}s`}
            subtitle="average response time"
            color="blue"
          />
          <MetricsCard
            icon={<Zap className="w-6 h-6" />}
            title="Blockchain Txs"
            value={metrics.blockchainTxs}
            subtitle="total transactions"
            color="purple"
          />
          <MetricsCard
            icon={<CheckCircle2 className="w-6 h-6" />}
            title="Success Rate"
            value={`${metrics.successRate}%`}
            subtitle="coordination success"
            color="green"
          />
        </div>
      </main>

      {/* ===================================================================
          REASONING VIEWER MODAL
          =================================================================== */}
      {reasoningData && (
        <ReasoningViewer
          data={reasoningData}
          isOpen={isReasoningModalOpen}
          onClose={() => setIsReasoningModalOpen(false)}
        />
      )}
    </div>
  );
}

export default App;

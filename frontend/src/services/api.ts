/**
 * API Service Layer for Hospital BlockOps Frontend
 *
 * Handles all HTTP communication with Flask backend at http://localhost:5000
 * Includes automatic retries, error handling, and request/response logging
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// =============================================================================
// TypeScript Interfaces
// =============================================================================

export type ScenarioState = 'pending' | 'running' | 'completed' | 'failed';
export type MessageType = 'intent' | 'constraint' | 'proposal' | 'critique' | 'accept' | 'reject' | 'inform';
export type AgentState = 'idle' | 'thinking' | 'negotiating' | 'executing';

export interface Scenario {
  id: string;
  type: string;
  state: ScenarioState;
  parameters: Record<string, any>;
  started_at: string;
  completed_at?: string;
}

export interface Message {
  id: string;
  timestamp: string;
  from: string;
  to: string[];
  type: MessageType;
  content: any;
  scenario_id?: string;
}

export interface Agent {
  name: string;
  role: string;
  state: AgentState;
  confidence: number;
  last_action: string;
  timestamp: string;
}

export interface Transaction {
  transaction_id: string;
  agent_name: string;
  action_type: string;
  details: Record<string, any>;
  validation_status: boolean;
  timestamp: string;
}

export interface Block {
  index: number;
  timestamp: string;
  data: Transaction;
  hash: string;
  previous_hash: string;
  nonce?: number;
  validator?: string;
}

export interface BlockchainResponse {
  blocks: Block[];
  length: number;
  is_valid: boolean;
  last_validation: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface ReasoningTrace {
  agent_name: string;
  scenario_id: string;
  input_context: Record<string, any>;
  llm_prompt: {
    system_message: string;
    user_message: string;
    temperature: number;
    max_tokens: number;
    model: string;
  };
  llm_response: {
    analysis: string;
    recommended_action: string;
    confidence: number;
    justification: string;
    alternatives: any[];
    risks: string[];
    response_time_ms: number;
  };
  execution_result: Record<string, any>;
}

// =============================================================================
// API Configuration
// =============================================================================

// Use environment variable for API URL, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';
const DEFAULT_TIMEOUT = 10000; // 10 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

/**
 * Create axios instance with default configuration
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: DEFAULT_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor - Log all outgoing requests
  client.interceptors.request.use(
    (config) => {
      const timestamp = new Date().toISOString();
      console.log(`[API Request] ${timestamp} ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
      });
      return config;
    },
    (error) => {
      console.error('[API Request Error]', error);
      return Promise.reject(error);
    }
  );

  // Response interceptor - Log all responses and transform errors
  client.interceptors.response.use(
    (response) => {
      const timestamp = new Date().toISOString();
      console.log(`[API Response] ${timestamp} ${response.config.method?.toUpperCase()} ${response.config.url}`, {
        status: response.status,
        data: response.data,
      });
      return response;
    },
    (error: AxiosError) => {
      const timestamp = new Date().toISOString();
      console.error(`[API Error] ${timestamp}`, {
        url: error.config?.url,
        status: error.response?.status,
        message: error.message,
        data: error.response?.data,
      });
      return Promise.reject(transformError(error));
    }
  );

  return client;
};

const apiClient = createApiClient();

/**
 * Transform axios error into user-friendly error object
 */
const transformError = (error: AxiosError): Error => {
  if (error.code === 'ECONNABORTED') {
    return new Error('Request timeout - Server is not responding');
  }
  if (error.code === 'ERR_NETWORK') {
    return new Error('Network error - Unable to connect to server');
  }
  if (error.response) {
    const data: any = error.response.data;
    return new Error(data?.error || data?.message || `Server error: ${error.response.status}`);
  }
  return new Error(error.message || 'Unknown error occurred');
};

/**
 * Retry function with exponential backoff
 */
const retryRequest = async <T>(
  requestFn: () => Promise<T>,
  retries: number = MAX_RETRIES,
  delay: number = RETRY_DELAY
): Promise<T> => {
  try {
    return await requestFn();
  } catch (error) {
    if (retries === 0) {
      throw error;
    }
    console.log(`[Retry] Retrying request... (${MAX_RETRIES - retries + 1}/${MAX_RETRIES})`);
    await new Promise((resolve) => setTimeout(resolve, delay));
    return retryRequest(requestFn, retries - 1, delay * 2);
  }
};

// =============================================================================
// 1. Scenario Management API
// =============================================================================

/**
 * Start a new coordination scenario
 *
 * @param params - Scenario parameters including type, agents, and constraints
 * @returns Scenario object with unique ID
 * @throws Error if scenario creation fails
 *
 * @example
 * const scenario = await startScenario({
 *   type: 'ppe_shortage',
 *   agents: ['SC-001', 'FIN-001', 'FAC-001'],
 *   required_quantity: 1000,
 *   budget_limit: 166000
 * });
 */
export const startScenario = async (params: Record<string, any>): Promise<Scenario> => {
  return retryRequest(async () => {
    const response = await apiClient.post<ApiResponse<Scenario>>('/api/scenarios/start', params);
    if (!response.data.success || !response.data.data) {
      throw new Error(response.data.error || 'Failed to start scenario');
    }
    return response.data.data;
  });
};

/**
 * Get current status of a running scenario
 *
 * @param scenarioId - Unique scenario identifier
 * @returns Current scenario state and progress
 * @throws Error if scenario not found
 *
 * @example
 * const status = await getScenarioStatus('scenario-123');
 * console.log(status.state); // 'running' | 'completed' | 'failed'
 */
export const getScenarioStatus = async (scenarioId: string): Promise<Scenario> => {
  return retryRequest(async () => {
    const response = await apiClient.get<ApiResponse<Scenario>>(`/api/scenarios/${scenarioId}/status`);
    if (!response.data.success || !response.data.data) {
      throw new Error(response.data.error || 'Failed to get scenario status');
    }
    return response.data.data;
  });
};

/**
 * Reset/clear the current scenario
 *
 * @returns Success confirmation
 * @throws Error if reset fails
 *
 * @example
 * await resetScenario();
 * console.log('Scenario reset successfully');
 */
export const resetScenario = async (): Promise<{ success: boolean }> => {
  return retryRequest(async () => {
    const response = await apiClient.post<ApiResponse<{ success: boolean }>>('/api/scenarios/reset');
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to reset scenario');
    }
    return { success: true };
  });
};

// =============================================================================
// 2. Coordination Data API
// =============================================================================

/**
 * Get all negotiation messages for a scenario
 *
 * @param scenarioId - Unique scenario identifier
 * @returns Array of messages exchanged between agents
 * @throws Error if scenario not found
 *
 * @example
 * const messages = await getMessages('scenario-123');
 * messages.forEach(msg => console.log(`${msg.from} → ${msg.to}: ${msg.content}`));
 */
export const getMessages = async (scenarioId: string): Promise<Message[]> => {
  return retryRequest(async () => {
    const response = await apiClient.get<ApiResponse<Message[]>>(`/api/scenarios/${scenarioId}/messages`);
    if (!response.data.success || !response.data.data) {
      throw new Error(response.data.error || 'Failed to get messages');
    }
    return response.data.data;
  });
};

/**
 * Get detailed reasoning trace for a specific agent decision
 *
 * @param scenarioId - Unique scenario identifier
 * @param agentName - Agent name (e.g., 'SC-001')
 * @returns Complete reasoning trace including LLM prompts and responses
 * @throws Error if agent or scenario not found
 *
 * @example
 * const reasoning = await getAgentReasoning('scenario-123', 'SC-001');
 * console.log(reasoning.llm_response.analysis);
 * console.log('Confidence:', reasoning.llm_response.confidence);
 */
export const getAgentReasoning = async (scenarioId: string, agentName: string): Promise<ReasoningTrace> => {
  return retryRequest(async () => {
    const response = await apiClient.get<ApiResponse<ReasoningTrace>>(
      `/api/scenarios/${scenarioId}/agents/${agentName}/reasoning`
    );
    if (!response.data.success || !response.data.data) {
      throw new Error(response.data.error || 'Failed to get agent reasoning');
    }
    return response.data.data;
  });
};

/**
 * Get current status of all agents in the system
 *
 * @returns Array of agent objects with current states
 * @throws Error if request fails
 *
 * @example
 * const agents = await getAgentStatus();
 * agents.forEach(agent => {
 *   console.log(`${agent.name}: ${agent.state} (confidence: ${agent.confidence})`);
 * });
 */
export const getAgentStatus = async (): Promise<Agent[]> => {
  return retryRequest(async () => {
    const response = await apiClient.get<ApiResponse<Agent[]>>('/api/agents/status');
    if (!response.data.success || !response.data.data) {
      throw new Error(response.data.error || 'Failed to get agent status');
    }
    return response.data.data;
  });
};

// =============================================================================
// 3. Blockchain Data API
// =============================================================================

/**
 * Get complete blockchain with all blocks and transactions
 *
 * @returns Blockchain object with blocks array and validation status
 * @throws Error if blockchain unavailable
 *
 * @example
 * const blockchain = await getBlockchain();
 * console.log(`Chain length: ${blockchain.length}`);
 * console.log(`Valid: ${blockchain.is_valid}`);
 * blockchain.blocks.forEach(block => console.log(`Block ${block.index}: ${block.hash}`));
 */
export const getBlockchain = async (): Promise<BlockchainResponse> => {
  return retryRequest(async () => {
    const response = await apiClient.get<ApiResponse<BlockchainResponse>>('/api/blockchain');
    if (!response.data.success || !response.data.data) {
      throw new Error(response.data.error || 'Failed to get blockchain');
    }
    return response.data.data;
  });
};

/**
 * Get a specific block by index
 *
 * @param index - Block index (0 for genesis block)
 * @returns Block object with transactions and hash
 * @throws Error if block not found
 *
 * @example
 * const genesisBlock = await getBlock(0);
 * console.log('Genesis hash:', genesisBlock.hash);
 *
 * const latestBlock = await getBlock(-1); // Get latest block
 */
export const getBlock = async (index: number): Promise<Block> => {
  return retryRequest(async () => {
    const response = await apiClient.get<ApiResponse<Block>>(`/api/blockchain/blocks/${index}`);
    if (!response.data.success || !response.data.data) {
      throw new Error(response.data.error || 'Failed to get block');
    }
    return response.data.data;
  });
};

/**
 * Validate blockchain integrity
 *
 * @returns Validation result with detailed information
 * @throws Error if validation fails
 *
 * @example
 * const validation = await validateChain();
 * if (validation.is_valid) {
 *   console.log('✓ Blockchain is valid');
 * } else {
 *   console.error('✗ Blockchain compromised:', validation.errors);
 * }
 */
export const validateChain = async (): Promise<{
  is_valid: boolean;
  validation_time_ms: number;
  errors?: string[];
}> => {
  return retryRequest(async () => {
    const response = await apiClient.post<
      ApiResponse<{
        is_valid: boolean;
        validation_time_ms: number;
        errors?: string[];
      }>
    >('/api/blockchain/validate');
    if (!response.data.success || !response.data.data) {
      throw new Error(response.data.error || 'Failed to validate chain');
    }
    return response.data.data;
  });
};

// =============================================================================
// 4. Real-time Updates (Polling)
// =============================================================================

/**
 * Poll scenario status at regular intervals
 *
 * Automatically calls the provided callback function whenever scenario state changes
 * Returns an unsubscribe function to stop polling
 *
 * @param scenarioId - Unique scenario identifier
 * @param onUpdate - Callback function called with updated scenario
 * @param onError - Optional callback for error handling
 * @param interval - Polling interval in milliseconds (default: 1000)
 * @returns Unsubscribe function to stop polling
 *
 * @example
 * const unsubscribe = pollScenarioStatus(
 *   'scenario-123',
 *   (scenario) => {
 *     console.log('Status updated:', scenario.state);
 *     if (scenario.state === 'completed') {
 *       unsubscribe(); // Stop polling when done
 *     }
 *   },
 *   (error) => console.error('Polling error:', error),
 *   1000 // Poll every second
 * );
 *
 * // Later: unsubscribe() to stop polling
 */
export const pollScenarioStatus = (
  scenarioId: string,
  onUpdate: (scenario: Scenario) => void,
  onError?: (error: Error) => void,
  interval: number = 1000
): (() => void) => {
  let previousState: ScenarioState | null = null;
  let isPolling = true;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  const poll = async () => {
    if (!isPolling) return;

    try {
      const scenario = await getScenarioStatus(scenarioId);

      // Only trigger callback if state changed
      if (scenario.state !== previousState) {
        previousState = scenario.state;
        onUpdate(scenario);
      }

      // Continue polling if scenario is still running
      if (scenario.state === 'running' || scenario.state === 'pending') {
        timeoutId = setTimeout(poll, interval);
      } else {
        console.log('[Polling] Scenario completed, stopping poll');
        isPolling = false;
      }
    } catch (error) {
      if (onError) {
        onError(error as Error);
      } else {
        console.error('[Polling Error]', error);
      }

      // Continue polling even on error (server might be temporarily down)
      if (isPolling) {
        timeoutId = setTimeout(poll, interval * 2); // Back off on error
      }
    }
  };

  // Start polling
  poll();

  // Return unsubscribe function
  return () => {
    console.log('[Polling] Unsubscribed from scenario updates');
    isPolling = false;
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  };
};

/**
 * Poll agent status at regular intervals
 *
 * @param onUpdate - Callback function called with updated agents
 * @param onError - Optional callback for error handling
 * @param interval - Polling interval in milliseconds (default: 2000)
 * @returns Unsubscribe function to stop polling
 *
 * @example
 * const unsubscribe = pollAgentStatus(
 *   (agents) => {
 *     agents.forEach(agent => {
 *       console.log(`${agent.name}: ${agent.state}`);
 *     });
 *   },
 *   undefined,
 *   2000 // Poll every 2 seconds
 * );
 */
export const pollAgentStatus = (
  onUpdate: (agents: Agent[]) => void,
  onError?: (error: Error) => void,
  interval: number = 2000
): (() => void) => {
  let isPolling = true;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  const poll = async () => {
    if (!isPolling) return;

    try {
      const agents = await getAgentStatus();
      onUpdate(agents);

      if (isPolling) {
        timeoutId = setTimeout(poll, interval);
      }
    } catch (error) {
      if (onError) {
        onError(error as Error);
      }

      if (isPolling) {
        timeoutId = setTimeout(poll, interval * 2);
      }
    }
  };

  poll();

  return () => {
    isPolling = false;
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  };
};

/**
 * Poll blockchain for new blocks
 *
 * @param onUpdate - Callback function called with updated blockchain
 * @param onError - Optional callback for error handling
 * @param interval - Polling interval in milliseconds (default: 3000)
 * @returns Unsubscribe function to stop polling
 *
 * @example
 * const unsubscribe = pollBlockchain(
 *   (blockchain) => {
 *     console.log(`New block added! Chain length: ${blockchain.length}`);
 *   }
 * );
 */
export const pollBlockchain = (
  onUpdate: (blockchain: BlockchainResponse) => void,
  onError?: (error: Error) => void,
  interval: number = 3000
): (() => void) => {
  let isPolling = true;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let previousLength = 0;

  const poll = async () => {
    if (!isPolling) return;

    try {
      const blockchain = await getBlockchain();

      // Only trigger callback if new blocks were added
      if (blockchain.length !== previousLength) {
        previousLength = blockchain.length;
        onUpdate(blockchain);
      }

      if (isPolling) {
        timeoutId = setTimeout(poll, interval);
      }
    } catch (error) {
      if (onError) {
        onError(error as Error);
      }

      if (isPolling) {
        timeoutId = setTimeout(poll, interval * 2);
      }
    }
  };

  poll();

  return () => {
    isPolling = false;
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  };
};

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Check if backend server is reachable
 *
 * @returns True if server is online, false otherwise
 *
 * @example
 * const isOnline = await checkServerHealth();
 * if (!isOnline) {
 *   alert('Backend server is offline');
 * }
 */
export const checkServerHealth = async (): Promise<boolean> => {
  try {
    const response = await apiClient.get('/api/health', { timeout: 3000 });
    return response.status === 200;
  } catch (error) {
    return false;
  }
};

/**
 * Get API statistics and metrics
 *
 * @returns Server statistics including uptime, request count, etc.
 */
export const getServerStats = async (): Promise<Record<string, any>> => {
  const response = await apiClient.get<ApiResponse<Record<string, any>>>('/api/stats');
  if (!response.data.success || !response.data.data) {
    throw new Error('Failed to get server stats');
  }
  return response.data.data;
};

// =============================================================================
// Export API Client (for advanced usage)
// =============================================================================

export { apiClient };

/**
 * Default export with all API functions
 */
export default {
  // Scenario Management
  startScenario,
  getScenarioStatus,
  resetScenario,

  // Coordination Data
  getMessages,
  getAgentReasoning,
  getAgentStatus,

  // Blockchain Data
  getBlockchain,
  getBlock,
  validateChain,

  // Real-time Updates
  pollScenarioStatus,
  pollAgentStatus,
  pollBlockchain,

  // Utilities
  checkServerHealth,
  getServerStats,
};

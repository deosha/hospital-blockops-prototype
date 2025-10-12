export interface Agent {
  id: string;
  name: string;
  type: 'supply_chain' | 'energy' | 'scheduling' | 'maintenance' | 'decision_support';
  status: 'active' | 'idle' | 'processing' | 'error';
  lastAction?: string;
  timestamp?: string;
  confidence?: number;
}

export interface Decision {
  id: string;
  agentId: string;
  agentName: string;
  type: string;
  description: string;
  reasoning: string;
  confidence: number;
  autonomyLevel: 1 | 2 | 3;
  status: 'pending' | 'approved' | 'rejected' | 'executed';
  timestamp: string;
  riskScore: number;
}

export interface Coordination {
  id: string;
  initiatorAgent: string;
  participatingAgents: string[];
  type: 'negotiation' | 'auction' | 'escalation';
  description: string;
  status: 'initiated' | 'negotiating' | 'resolved' | 'failed';
  messages: CoordinationMessage[];
  outcome?: string;
  timestamp: string;
}

export interface CoordinationMessage {
  from: string;
  to: string;
  type: 'intent' | 'proposal' | 'accept' | 'reject' | 'query' | 'inform';
  content: string;
  timestamp: string;
}

export interface SystemStats {
  totalDecisions: number;
  autonomousDecisions: number;
  approvalRequired: number;
  humanLed: number;
  averageConfidence: number;
  energySavings: number;
  costReduction: number;
  complianceRate: number;
}

export interface BlockchainRecord {
  id: string;
  decisionId: string;
  hash: string;
  previousHash: string;
  timestamp: string;
  data: any;
  validated: boolean;
}

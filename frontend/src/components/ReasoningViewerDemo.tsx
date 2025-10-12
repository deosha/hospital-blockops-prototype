import React, { useState } from 'react';
import ReasoningViewer, { ReasoningData } from './ReasoningViewer';
import { Brain, Package, DollarSign, Building } from 'lucide-react';

// Sample reasoning data for demonstration
const sampleReasoningData: ReasoningData = {
  agentId: 'SC-001',
  agentName: 'Supply Chain Agent',
  agentRole: 'supply_chain',
  timestamp: new Date().toISOString(),

  inputContext: {
    situation: {
      description: 'Critical shortage of PPE supplies detected in Emergency Department. Current inventory at 15% capacity with projected depletion in 48 hours. 3 similar hospitals in region also reporting shortages.',
      urgency: 'critical',
      affectedDepartments: ['Emergency', 'ICU', 'Surgical'],
    },
    constraints: [
      {
        agentName: 'Financial Agent',
        type: 'budget_constraint',
        value: { remaining: 2000, allocated: 5000, monthly_limit: 10000 },
        priority: 'high',
      },
      {
        agentName: 'Facility Agent',
        type: 'storage_constraint',
        value: { available_space: 800, max_capacity: 5000, current_utilization: 4200 },
        priority: 'high',
      },
      {
        agentName: 'Procurement Agent',
        type: 'supplier_constraint',
        value: { lead_time_days: 2, reliability_score: 0.95, unit_price: 2.0 },
        priority: 'medium',
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
      { key: 'max_order_without_approval', value: 2500, source: 'procurement_policy.json' },
      { key: 'critical_alert_threshold', value: 0.2, source: 'inventory_rules.json' },
    ],
  },

  llmPrompt: {
    systemMessage: `You are an expert Supply Chain Agent in a hospital operations system. Your role is to:
- Monitor inventory levels and predict shortages
- Coordinate with financial and facility agents
- Optimize procurement decisions
- Ensure patient care continuity

Always respond in JSON format with structured decision data.`,

    userMessage: `SITUATION:
Critical PPE shortage in Emergency Department
- Current inventory: 15% (75 units)
- Projected depletion: 48 hours
- Affected departments: Emergency, ICU, Surgical

CONSTRAINTS:
1. Budget: ₹1,66,000 available (Financial Agent)
2. Storage: 800 units max capacity (Facility Agent)
3. Lead time: 2 days from supplier

HISTORICAL CONTEXT:
- 23 similar cases resolved
- 87% success rate
- Average resolution: 18 hours

KNOWLEDGE BASE:
- Minimum threshold: 500 units
- Unit price: ₹166
- Emergency supplier: MedSupply Corp
- Max order without approval: ₹2,07,500

TASK:
Analyze this situation and provide:
1. Your analysis of the problem
2. Recommended action with quantities
3. Confidence score (0-1)
4. Justification
5. Alternative approaches considered
6. Potential risks

Respond in JSON format.`,

    temperature: 0.7,
    maxTokens: 2048,
    model: 'gpt-4-turbo-preview',
  },

  llmResponse: {
    analysis: `**Critical Assessment:**

The situation requires immediate action. With only 15% inventory remaining and 48-hour depletion window, we're below the critical threshold of 20%. However, we face three key constraints:

1. **Budget Constraint**: ₹1,66,000 available limits us to 1,000 units maximum
2. **Storage Constraint**: 800 units is our physical ceiling
3. **Lead Time**: 2-day delivery means we need interim measures

**Strategic Considerations:**

The storage constraint (800 units) is our limiting factor. Ordering 800 units will:
- Cost ₹1,32,800 (within budget)
- Fill available storage capacity
- Provide 10.6x current inventory
- Last approximately 2-3 weeks at normal usage

**Risk Mitigation:**

Given the 2-day lead time vs 48-hour depletion window, we're racing against time. I recommend coordinating with nearby facilities for immediate short-term loan while our order is in transit.`,

    recommendedAction: 'Order 800 PPE units from MedSupply Corp for ₹1,32,800 with expedited 2-day delivery',

    confidence: 0.92,

    justification: `This decision balances all constraints optimally:

• **Maximizes utilization** of available storage (800/800 units = 100%)
• **Stays within budget** (₹1,32,800 / ₹1,66,000 = 80% utilization)
• **Exceeds minimum threshold** (800 > 500 units required)
• **Aligns with historical precedent** (similar to 18 of 23 previous cases)
• **Leverages reliable supplier** (95% reliability score)

The 92% confidence reflects strong alignment with policy constraints and historical success patterns. The 8% uncertainty accounts for delivery timing risk during the critical 48-hour window.`,

    alternatives: [
      {
        action: 'Order 1,000 units (budget maximum)',
        pros: [
          'Maximizes inventory buffer',
          'Better long-term coverage',
          'Full budget utilization',
        ],
        cons: [
          'Exceeds storage capacity by 200 units',
          'Requires off-site storage (₹₹₹)',
          'Violates facility constraint',
        ],
        confidence: 0.45,
      },
      {
        action: 'Order 500 units (minimum threshold)',
        pros: [
          'Meets minimum requirement',
          'Lower cost (₹83,000)',
          'Leaves budget buffer',
        ],
        cons: [
          'Minimal safety margin',
          'Likely to need reorder soon',
          'Underutilizes available resources',
        ],
        confidence: 0.68,
      },
      {
        action: 'Split order: 400 now + 400 in 1 week',
        pros: [
          'Spreads cost over time',
          'Manages storage incrementally',
          'Reduces delivery risk',
        ],
        cons: [
          'Higher total shipping costs',
          'Doesn\'t solve immediate crisis',
          'More coordination overhead',
        ],
        confidence: 0.73,
      },
    ],

    risks: [
      'Delivery delay beyond 2 days could create critical gap (mitigation: coordinate inter-facility loan)',
      'Supplier out of stock scenario (mitigation: have backup supplier on standby)',
      'Quality issues with emergency order (mitigation: immediate inspection upon delivery)',
      'Usage spike above projections (mitigation: implement conservation protocols now)',
      'Budget overrun if additional costs arise (mitigation: ₹33,200 buffer remaining)',
    ],

    responseTimeMs: 1847,

    rawJSON: `{
  "analysis": "Critical situation requiring immediate action...",
  "recommended_action": "Order 800 PPE units from MedSupply Corp",
  "confidence": 0.92,
  "justification": "This decision balances all constraints optimally...",
  "alternatives_considered": [...],
  "identified_risks": [...],
  "execution_plan": {
    "immediate": "Place order with MedSupply Corp",
    "short_term": "Coordinate inter-facility loan for bridge coverage",
    "monitoring": "Track delivery every 6 hours"
  },
  "metadata": {
    "decision_time": "2025-10-12T20:45:33Z",
    "model": "gpt-4-turbo-preview",
    "constraints_satisfied": ["budget", "storage", "policy"],
    "approvals_required": false
  }
}`,
  },

  executionResult: {
    actionTaken: 'Purchase order PO-2024-1847 created: 800 PPE units @ ₹166/unit = ₹1,32,800 total. Expedited 2-day delivery from MedSupply Corp. Coordination initiated with Regional Medical Center for 200-unit bridge loan.',

    smartContractValidation: {
      budgetCheck: true,
      storageCheck: true,
      confidenceCheck: true,
      complianceCheck: true,
      details: 'All policy constraints satisfied. Budget: ₹1,32,800/₹1,66,000 (80%). Storage: 800/800 (100%). Confidence: 92% > 70% threshold. Procurement policy: Within approval limits.',
    },

    blockchainTx: {
      txHash: '0x7f8a3bc4d29e1f5a6b8c9d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2',
      blockNumber: 1847,
      timestamp: new Date().toISOString(),
    },

    outcome: 'Order successfully placed and recorded to blockchain. Supplier confirmed 2-day delivery. Regional Medical Center approved 200-unit bridge loan for immediate coverage. Emergency Department notified of incoming supplies. Conservation protocols activated to extend current inventory.',

    impact: {
      costSaved: 400,
      timesSaved: 2.5,
      efficiencyGain: 23,
    },
  },

  escalationStatus: 'none',
  riskLevel: 'medium',
};

// Additional sample data for different scenarios
const financialAgentData: ReasoningData = {
  agentId: 'FIN-001',
  agentName: 'Financial Agent',
  agentRole: 'financial',
  timestamp: new Date(Date.now() - 3600000).toISOString(),

  inputContext: {
    situation: {
      description: 'Q4 budget review: Medical supplies spending at 78% with 2 months remaining. Unusual spike in emergency procurement detected.',
      urgency: 'medium',
      affectedDepartments: ['Finance', 'Procurement', 'All Clinical'],
    },
    constraints: [
      {
        agentName: 'Supply Chain Agent',
        type: 'procurement_request',
        value: { amount: 15000, category: 'medical_supplies', urgency: 'high' },
        priority: 'high',
      },
      {
        agentName: 'Compliance Agent',
        type: 'audit_requirement',
        value: { documentation_level: 'complete', approval_chain: true },
        priority: 'high',
      },
    ],
    historicalData: {
      similarCases: 45,
      avgOutcome: 'Approved with conditions',
      successRate: 93,
    },
    knowledgeBase: [
      { key: 'q4_remaining_budget', value: 22000, source: 'financial_system.db' },
      { key: 'approval_threshold', value: 10000, source: 'policy.json' },
      { key: 'emergency_reserve', value: 50000, source: 'accounts.db' },
    ],
  },

  llmPrompt: {
    systemMessage: 'You are a Financial Agent responsible for budget management and fiscal oversight.',
    userMessage: 'Review procurement request for ₹12,45,000 medical supplies with Q4 budget at 78% utilization.',
    temperature: 0.5,
    maxTokens: 2048,
    model: 'gpt-4-turbo-preview',
  },

  llmResponse: {
    analysis: 'Budget analysis shows ₹18,26,000 remaining in Q4 with ₹12,45,000 request. This represents 68% of remaining budget but aligns with emergency procurement patterns.',
    recommendedAction: 'Approve ₹12,45,000 procurement with enhanced monitoring',
    confidence: 0.89,
    justification: 'Request is within budget limits and emergency reserve is available if needed.',
    alternatives: [
      {
        action: 'Approve ₹9,96,000 (reduce by 20%)',
        pros: ['Preserves more budget buffer', 'Encourages efficiency'],
        cons: ['May not meet actual need', 'Could require second approval'],
        confidence: 0.75,
      },
    ],
    risks: [
      'Rapid budget depletion if more emergencies occur',
      'Potential Q1 budget impact if trend continues',
    ],
    responseTimeMs: 1234,
    rawJSON: '{"analysis": "...", "recommended_action": "..."}',
  },

  executionResult: {
    actionTaken: 'Approved procurement request with enhanced monitoring and weekly budget reviews',
    smartContractValidation: {
      budgetCheck: true,
      storageCheck: true,
      confidenceCheck: true,
      complianceCheck: true,
      details: 'All financial controls passed',
    },
    blockchainTx: {
      txHash: '0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8',
      blockNumber: 1845,
      timestamp: new Date(Date.now() - 3600000).toISOString(),
    },
    outcome: 'Budget allocation successful. Monitoring dashboard updated.',
    impact: {
      costSaved: 0,
      timesSaved: 1.0,
      efficiencyGain: 15,
    },
  },

  escalationStatus: 'none',
  riskLevel: 'low',
};

const ReasoningViewerDemo: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedData, setSelectedData] = useState<ReasoningData>(sampleReasoningData);

  const openModal = (data: ReasoningData) => {
    setSelectedData(data);
    setIsOpen(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Reasoning Viewer Demo</h1>
          <p className="text-slate-400">
            Click on any agent decision below to view the complete reasoning process
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Supply Chain Agent Card */}
          <div
            onClick={() => openModal(sampleReasoningData)}
            className="bg-slate-800/50 backdrop-blur-lg border border-slate-700 rounded-xl p-6
              hover:border-blue-500/50 transition-all duration-200 cursor-pointer
              hover:shadow-lg hover:shadow-blue-500/10"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <Package className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Supply Chain Agent</h3>
                  <p className="text-sm text-slate-400">SC-001</p>
                </div>
              </div>
              <span className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-xs font-medium">
                CRITICAL
              </span>
            </div>

            <p className="text-slate-300 text-sm mb-4 line-clamp-2">
              Critical PPE shortage in Emergency Department - Immediate procurement decision required
            </p>

            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-4">
                <div>
                  <span className="text-slate-500">Confidence:</span>
                  <span className="text-green-400 ml-2 font-bold">92%</span>
                </div>
                <div>
                  <span className="text-slate-500">Risk:</span>
                  <span className="text-yellow-400 ml-2 font-medium">Medium</span>
                </div>
              </div>
              <Brain className="w-5 h-5 text-blue-400" />
            </div>

            <div className="mt-4 pt-4 border-t border-slate-700">
              <div className="text-xs text-slate-500">
                Decision: Order 800 units • Cost: ₹1,32,800 • Time: 1.8s
              </div>
            </div>
          </div>

          {/* Financial Agent Card */}
          <div
            onClick={() => openModal(financialAgentData)}
            className="bg-slate-800/50 backdrop-blur-lg border border-slate-700 rounded-xl p-6
              hover:border-green-500/50 transition-all duration-200 cursor-pointer
              hover:shadow-lg hover:shadow-green-500/10"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <DollarSign className="w-6 h-6 text-green-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Financial Agent</h3>
                  <p className="text-sm text-slate-400">FIN-001</p>
                </div>
              </div>
              <span className="px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded-full text-xs font-medium">
                MEDIUM
              </span>
            </div>

            <p className="text-slate-300 text-sm mb-4 line-clamp-2">
              Q4 budget review - Evaluating ₹12.5L emergency procurement request with 78% budget utilization
            </p>

            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-4">
                <div>
                  <span className="text-slate-500">Confidence:</span>
                  <span className="text-green-400 ml-2 font-bold">89%</span>
                </div>
                <div>
                  <span className="text-slate-500">Risk:</span>
                  <span className="text-green-400 ml-2 font-medium">Low</span>
                </div>
              </div>
              <Brain className="w-5 h-5 text-green-400" />
            </div>

            <div className="mt-4 pt-4 border-t border-slate-700">
              <div className="text-xs text-slate-500">
                Decision: Approve with monitoring • Amount: ₹12,45,000 • Time: 1.2s
              </div>
            </div>
          </div>

          {/* Info Card */}
          <div className="col-span-1 md:col-span-2 bg-blue-500/5 border border-blue-500/30 rounded-xl p-6">
            <div className="flex items-start space-x-4">
              <Brain className="w-6 h-6 text-blue-400 flex-shrink-0 mt-1" />
              <div>
                <h4 className="text-white font-semibold mb-2">About the Reasoning Viewer</h4>
                <p className="text-slate-300 text-sm leading-relaxed mb-3">
                  This component provides complete transparency into how AI agents make decisions. You can see:
                </p>
                <ul className="text-slate-400 text-sm space-y-1">
                  <li>• <strong className="text-slate-300">Input Context:</strong> What information the agent received</li>
                  <li>• <strong className="text-slate-300">LLM Interaction:</strong> The exact prompt sent to GPT-4</li>
                  <li>• <strong className="text-slate-300">LLM Response:</strong> Complete reasoning, alternatives, and confidence</li>
                  <li>• <strong className="text-slate-300">Execution:</strong> Smart contract validation and blockchain recording</li>
                </ul>
                <p className="text-slate-400 text-sm mt-3">
                  Click any agent card above to explore the full reasoning process. This demonstrates that the LLM
                  is performing genuine analysis, not just generating random outputs.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Reasoning Viewer Modal */}
      <ReasoningViewer
        data={selectedData}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />
    </div>
  );
};

export default ReasoningViewerDemo;

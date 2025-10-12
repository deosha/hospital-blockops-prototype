import React, { useState } from 'react';
import {
  X,
  Download,
  Copy,
  Check,
  Brain,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Search,
  ChevronDown,
  ChevronRight,
  Package,
  DollarSign,
  Building,
  Zap,
  Shield,
  TrendingUp,
  Users,
} from 'lucide-react';

// TypeScript Interfaces
export interface KnowledgeBaseEntry {
  key: string;
  value: string | number;
  source: string;
}

export interface Constraint {
  agentName: string;
  type: string;
  value: any;
  priority: 'high' | 'medium' | 'low';
}

export interface InputContext {
  situation: {
    description: string;
    urgency: 'critical' | 'high' | 'medium' | 'low';
    affectedDepartments: string[];
  };
  constraints: Constraint[];
  historicalData: {
    similarCases: number;
    avgOutcome: string;
    successRate: number;
  };
  knowledgeBase: KnowledgeBaseEntry[];
}

export interface LLMPrompt {
  systemMessage: string;
  userMessage: string;
  temperature: number;
  maxTokens: number;
  model: string;
}

export interface Alternative {
  action: string;
  pros: string[];
  cons: string[];
  confidence: number;
}

export interface LLMResponse {
  analysis: string;
  recommendedAction: string;
  confidence: number;
  justification: string;
  alternatives: Alternative[];
  risks: string[];
  responseTimeMs: number;
  rawJSON: string;
}

export interface SmartContractValidation {
  budgetCheck: boolean;
  storageCheck: boolean;
  confidenceCheck: boolean;
  complianceCheck: boolean;
  details: string;
}

export interface ExecutionResult {
  actionTaken: string;
  smartContractValidation: SmartContractValidation;
  blockchainTx: {
    txHash: string;
    blockNumber: number;
    timestamp: string;
  };
  outcome: string;
  impact: {
    costSaved: number;
    timesSaved: number;
    efficiencyGain: number;
  };
}

export interface ReasoningData {
  agentId: string;
  agentName: string;
  agentRole: 'supply_chain' | 'financial' | 'facility' | 'decision_support';
  timestamp: string;
  inputContext: InputContext;
  llmPrompt: LLMPrompt;
  llmResponse: LLMResponse;
  executionResult: ExecutionResult;
  escalationStatus: 'none' | 'human_review' | 'escalated';
  riskLevel: 'low' | 'medium' | 'high';
}

export interface ReasoningViewerProps {
  data: ReasoningData;
  isOpen: boolean;
  onClose: () => void;
}

// Agent icons
const agentIcons: Record<string, React.ComponentType<any>> = {
  supply_chain: Package,
  financial: DollarSign,
  facility: Building,
  decision_support: Brain,
};

// Copy to clipboard hook
const useCopyToClipboard = () => {
  const [copied, setCopied] = useState<string | null>(null);

  const copy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  return { copied, copy };
};

const ReasoningViewer: React.FC<ReasoningViewerProps> = ({ data, isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'context' | 'prompt' | 'response' | 'execution'>('context');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['all']));
  const { copied, copy } = useCopyToClipboard();

  if (!isOpen) return null;

  const AgentIcon = agentIcons[data.agentRole] || Brain;

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const exportAsJSON = () => {
    const dataStr = JSON.stringify(data, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `reasoning-${data.agentId}-${new Date().getTime()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const tabs = [
    { id: 'context', label: 'Input Context', icon: TrendingUp },
    { id: 'prompt', label: 'LLM Interaction', icon: Brain },
    { id: 'response', label: 'LLM Response', icon: Zap },
    { id: 'execution', label: 'Execution', icon: CheckCircle2 },
  ];

  // Risk color mapping
  const riskColors = {
    low: 'text-green-400 bg-green-500/10 border-green-500/30',
    medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
    high: 'text-red-400 bg-red-500/10 border-red-500/30',
  };

  const escalationColors = {
    none: 'text-green-400',
    human_review: 'text-yellow-400',
    escalated: 'text-red-400',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      {/* Modal Container */}
      <div className="w-full h-full max-w-7xl max-h-[95vh] bg-slate-900 border border-slate-700 rounded-xl shadow-2xl flex flex-col m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <AgentIcon className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{data.agentName} - Reasoning Process</h2>
              <p className="text-sm text-slate-400">
                {new Date(data.timestamp).toLocaleString()} • {data.agentRole.replace('_', ' ')}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search reasoning..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 bg-slate-800 border border-slate-600 rounded-lg
                  text-sm text-slate-200 placeholder-slate-500 focus:outline-none
                  focus:ring-2 focus:ring-blue-500/50 w-64"
              />
            </div>

            {/* Export Button */}
            <button
              onClick={exportAsJSON}
              className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700
                border border-slate-600 rounded-lg text-sm text-slate-300 transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center space-x-1 px-6 pt-4 border-b border-slate-700">
          {tabs.map((tab) => {
            const TabIcon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 px-4 py-3 rounded-t-lg font-medium
                  text-sm transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-slate-800 text-white border-t border-x border-slate-700'
                      : 'text-slate-400 hover:text-slate-300 hover:bg-slate-800/50'
                  }`}
              >
                <TabIcon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Tab 1: Input Context */}
          {activeTab === 'context' && (
            <div className="space-y-4">
              {/* Situation */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
                <button
                  onClick={() => toggleSection('situation')}
                  className="w-full flex items-center justify-between p-4 hover:bg-slate-700/30 transition-colors"
                >
                  <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-400" />
                    <span>Current Situation</span>
                  </h3>
                  {expandedSections.has('situation') ? (
                    <ChevronDown className="w-5 h-5 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-slate-400" />
                  )}
                </button>
                {expandedSections.has('situation') && (
                  <div className="p-4 border-t border-slate-700 space-y-3">
                    <p className="text-slate-300 leading-relaxed">{data.inputContext.situation.description}</p>
                    <div className="flex items-center space-x-4">
                      <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                        data.inputContext.situation.urgency === 'critical' ? 'bg-red-500/20 text-red-400' :
                        data.inputContext.situation.urgency === 'high' ? 'bg-orange-500/20 text-orange-400' :
                        'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        Urgency: {data.inputContext.situation.urgency.toUpperCase()}
                      </div>
                      <div className="flex items-center space-x-2 text-sm text-slate-400">
                        <Users className="w-4 h-4" />
                        <span>Affects: {data.inputContext.situation.affectedDepartments.join(', ')}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Constraints */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
                <button
                  onClick={() => toggleSection('constraints')}
                  className="w-full flex items-center justify-between p-4 hover:bg-slate-700/30 transition-colors"
                >
                  <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                    <Shield className="w-5 h-5 text-blue-400" />
                    <span>Constraints from Other Agents ({data.inputContext.constraints.length})</span>
                  </h3>
                  {expandedSections.has('constraints') ? (
                    <ChevronDown className="w-5 h-5 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-slate-400" />
                  )}
                </button>
                {expandedSections.has('constraints') && (
                  <div className="p-4 border-t border-slate-700 space-y-2">
                    {data.inputContext.constraints.map((constraint, i) => (
                      <div key={i} className="bg-slate-900/50 rounded-lg p-3 flex items-start justify-between">
                        <div>
                          <p className="text-sm font-medium text-white">{constraint.agentName}</p>
                          <p className="text-xs text-slate-400 mt-1">{constraint.type}: {JSON.stringify(constraint.value)}</p>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${
                          constraint.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                          constraint.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-green-500/20 text-green-400'
                        }`}>
                          {constraint.priority}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Historical Data */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center space-x-2">
                  <Clock className="w-5 h-5 text-purple-400" />
                  <span>Historical Context</span>
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-slate-900/50 rounded-lg p-3">
                    <p className="text-xs text-slate-500 mb-1">Similar Cases</p>
                    <p className="text-2xl font-bold text-white">{data.inputContext.historicalData.similarCases}</p>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-3">
                    <p className="text-xs text-slate-500 mb-1">Success Rate</p>
                    <p className="text-2xl font-bold text-green-400">{data.inputContext.historicalData.successRate}%</p>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-3">
                    <p className="text-xs text-slate-500 mb-1">Avg Outcome</p>
                    <p className="text-sm font-medium text-white">{data.inputContext.historicalData.avgOutcome}</p>
                  </div>
                </div>
              </div>

              {/* Knowledge Base */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
                <button
                  onClick={() => toggleSection('kb')}
                  className="w-full flex items-center justify-between p-4 hover:bg-slate-700/30 transition-colors"
                >
                  <h3 className="text-lg font-semibold text-white">Knowledge Base Entries Retrieved</h3>
                  {expandedSections.has('kb') ? (
                    <ChevronDown className="w-5 h-5 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-slate-400" />
                  )}
                </button>
                {expandedSections.has('kb') && (
                  <div className="p-4 border-t border-slate-700">
                    <div className="space-y-2">
                      {data.inputContext.knowledgeBase.map((entry, i) => (
                        <div key={i} className="bg-slate-900/50 rounded p-2 font-mono text-xs">
                          <span className="text-blue-400">{entry.key}</span>
                          <span className="text-slate-500">: </span>
                          <span className="text-green-400">{JSON.stringify(entry.value)}</span>
                          <span className="text-slate-600 ml-2">// {entry.source}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tab 2: LLM Prompt */}
          {activeTab === 'prompt' && (
            <div className="space-y-4">
              {/* Model Info */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white">LLM Configuration</h3>
                  <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs font-medium">
                    {data.llmPrompt.model}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">Temperature:</span>
                    <span className="text-white ml-2 font-mono">{data.llmPrompt.temperature}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Max Tokens:</span>
                    <span className="text-white ml-2 font-mono">{data.llmPrompt.maxTokens}</span>
                  </div>
                </div>
              </div>

              {/* System Message */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
                <div className="flex items-center justify-between p-4 bg-purple-500/5 border-b border-slate-700">
                  <h3 className="text-sm font-semibold text-purple-400">System Message</h3>
                  <button
                    onClick={() => copy(data.llmPrompt.systemMessage, 'system')}
                    className="p-1.5 hover:bg-slate-700 rounded transition-colors"
                  >
                    {copied === 'system' ? (
                      <Check className="w-4 h-4 text-green-400" />
                    ) : (
                      <Copy className="w-4 h-4 text-slate-400" />
                    )}
                  </button>
                </div>
                <pre className="p-4 text-sm text-slate-300 overflow-x-auto font-mono leading-relaxed">
                  {data.llmPrompt.systemMessage}
                </pre>
              </div>

              {/* User Message */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
                <div className="flex items-center justify-between p-4 bg-blue-500/5 border-b border-slate-700">
                  <h3 className="text-sm font-semibold text-blue-400">User Message (Context)</h3>
                  <button
                    onClick={() => copy(data.llmPrompt.userMessage, 'user')}
                    className="p-1.5 hover:bg-slate-700 rounded transition-colors"
                  >
                    {copied === 'user' ? (
                      <Check className="w-4 h-4 text-green-400" />
                    ) : (
                      <Copy className="w-4 h-4 text-slate-400" />
                    )}
                  </button>
                </div>
                <pre className="p-4 text-sm text-slate-300 overflow-x-auto font-mono leading-relaxed whitespace-pre-wrap">
                  {data.llmPrompt.userMessage}
                </pre>
              </div>
            </div>
          )}

          {/* Tab 3: LLM Response */}
          {activeTab === 'response' && (
            <div className="space-y-4">
              {/* Response Time */}
              <div className="flex items-center justify-between bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                <div className="flex items-center space-x-2">
                  <Clock className="w-5 h-5 text-blue-400" />
                  <span className="text-slate-300">Response Time:</span>
                </div>
                <span className="text-2xl font-bold text-white">{data.llmResponse.responseTimeMs}ms</span>
              </div>

              {/* Analysis */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                <h3 className="text-lg font-semibold text-white mb-3">Analysis</h3>
                <div className="prose prose-invert max-w-none text-slate-300 leading-relaxed">
                  {data.llmResponse.analysis}
                </div>
              </div>

              {/* Recommended Action */}
              <div className="bg-green-500/5 rounded-lg border border-green-500/30 p-4">
                <h3 className="text-lg font-semibold text-green-400 mb-2 flex items-center space-x-2">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Recommended Action</span>
                </h3>
                <p className="text-slate-200 font-medium">{data.llmResponse.recommendedAction}</p>
              </div>

              {/* Confidence */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white">Confidence Score</h3>
                  <span className="text-2xl font-bold text-blue-400">{(data.llmResponse.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all duration-500 ${
                      data.llmResponse.confidence >= 0.7 ? 'bg-green-500' :
                      data.llmResponse.confidence >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${data.llmResponse.confidence * 100}%` }}
                  />
                </div>
              </div>

              {/* Justification */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                <h3 className="text-lg font-semibold text-white mb-3">Justification</h3>
                <p className="text-slate-300 leading-relaxed">{data.llmResponse.justification}</p>
              </div>

              {/* Alternatives */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                <h3 className="text-lg font-semibold text-white mb-4">Alternatives Considered</h3>
                <div className="space-y-3">
                  {data.llmResponse.alternatives.map((alt, i) => (
                    <div key={i} className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-white">{alt.action}</h4>
                        <span className="text-sm text-slate-400">{(alt.confidence * 100).toFixed(0)}% confidence</span>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <p className="text-green-400 font-medium mb-1">Pros:</p>
                          <ul className="space-y-1 text-slate-300">
                            {alt.pros.map((pro, j) => (
                              <li key={j}>• {pro}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="text-red-400 font-medium mb-1">Cons:</p>
                          <ul className="space-y-1 text-slate-300">
                            {alt.cons.map((con, j) => (
                              <li key={j}>• {con}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Risks */}
              <div className="bg-yellow-500/5 rounded-lg border border-yellow-500/30 p-4">
                <h3 className="text-lg font-semibold text-yellow-400 mb-3 flex items-center space-x-2">
                  <AlertTriangle className="w-5 h-5" />
                  <span>Identified Risks</span>
                </h3>
                <ul className="space-y-2 text-slate-300">
                  {data.llmResponse.risks.map((risk, i) => (
                    <li key={i} className="flex items-start space-x-2">
                      <span className="text-yellow-400 mt-1">•</span>
                      <span>{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Raw JSON */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
                <div className="flex items-center justify-between p-4 border-b border-slate-700">
                  <h3 className="text-sm font-semibold text-slate-300">Raw JSON Response</h3>
                  <button
                    onClick={() => copy(data.llmResponse.rawJSON, 'raw')}
                    className="p-1.5 hover:bg-slate-700 rounded transition-colors"
                  >
                    {copied === 'raw' ? (
                      <Check className="w-4 h-4 text-green-400" />
                    ) : (
                      <Copy className="w-4 h-4 text-slate-400" />
                    )}
                  </button>
                </div>
                <pre className="p-4 text-xs text-slate-300 overflow-x-auto font-mono leading-relaxed">
                  {data.llmResponse.rawJSON}
                </pre>
              </div>
            </div>
          )}

          {/* Tab 4: Execution */}
          {activeTab === 'execution' && (
            <div className="space-y-4">
              {/* Action Taken */}
              <div className="bg-green-500/5 rounded-lg border border-green-500/30 p-4">
                <h3 className="text-lg font-semibold text-green-400 mb-2 flex items-center space-x-2">
                  <Zap className="w-5 h-5" />
                  <span>Action Taken</span>
                </h3>
                <p className="text-slate-200 text-lg font-medium">{data.executionResult.actionTaken}</p>
              </div>

              {/* Smart Contract Validation */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                  <Shield className="w-5 h-5 text-indigo-400" />
                  <span>Smart Contract Validation</span>
                </h3>
                <div className="grid grid-cols-2 gap-3 mb-4">
                  {Object.entries(data.executionResult.smartContractValidation).map(([key, value]) => {
                    if (key === 'details') return null;
                    return (
                      <div key={key} className="flex items-center space-x-3 bg-slate-900/50 rounded-lg p-3">
                        {value ? (
                          <CheckCircle2 className="w-5 h-5 text-green-400" />
                        ) : (
                          <X className="w-5 h-5 text-red-400" />
                        )}
                        <span className="text-slate-300 capitalize">
                          {key.replace(/([A-Z])/g, ' $1').replace('Check', '')}
                        </span>
                      </div>
                    );
                  })}
                </div>
                <p className="text-sm text-slate-400 bg-slate-900/50 rounded-lg p-3">
                  {data.executionResult.smartContractValidation.details}
                </p>
              </div>

              {/* Blockchain Transaction */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                  <Shield className="w-5 h-5 text-purple-400" />
                  <span>Blockchain Transaction</span>
                </h3>
                <div className="space-y-3 font-mono text-sm">
                  <div className="flex justify-between bg-slate-900/50 rounded p-3">
                    <span className="text-slate-500">Tx Hash:</span>
                    <span className="text-purple-400">{data.executionResult.blockchainTx.txHash}</span>
                  </div>
                  <div className="flex justify-between bg-slate-900/50 rounded p-3">
                    <span className="text-slate-500">Block:</span>
                    <span className="text-white">#{data.executionResult.blockchainTx.blockNumber}</span>
                  </div>
                  <div className="flex justify-between bg-slate-900/50 rounded p-3">
                    <span className="text-slate-500">Timestamp:</span>
                    <span className="text-slate-300">{new Date(data.executionResult.blockchainTx.timestamp).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Outcome */}
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                <h3 className="text-lg font-semibold text-white mb-3">Outcome</h3>
                <p className="text-slate-300 leading-relaxed mb-4">{data.executionResult.outcome}</p>

                <h4 className="text-sm font-semibold text-slate-400 mb-3">Impact Metrics</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-green-500/10 rounded-lg p-4 border border-green-500/30">
                    <p className="text-xs text-green-400 mb-1">Cost Saved</p>
                    <p className="text-2xl font-bold text-white">${data.executionResult.impact.costSaved}</p>
                  </div>
                  <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/30">
                    <p className="text-xs text-blue-400 mb-1">Time Saved</p>
                    <p className="text-2xl font-bold text-white">{data.executionResult.impact.timesSaved}h</p>
                  </div>
                  <div className="bg-purple-500/10 rounded-lg p-4 border border-purple-500/30">
                    <p className="text-xs text-purple-400 mb-1">Efficiency Gain</p>
                    <p className="text-2xl font-bold text-white">{data.executionResult.impact.efficiencyGain}%</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-slate-700 bg-slate-800/50">
          <div className="flex items-center space-x-6">
            {/* Confidence */}
            <div className="flex items-center space-x-3">
              <div className="text-right">
                <p className="text-xs text-slate-500">Overall Confidence</p>
                <p className="text-2xl font-bold text-white">{(data.llmResponse.confidence * 100).toFixed(0)}%</p>
              </div>
              <div className="w-16 h-16 rounded-full border-4 flex items-center justify-center" style={{
                borderColor: data.llmResponse.confidence >= 0.7 ? '#22c55e' :
                             data.llmResponse.confidence >= 0.4 ? '#eab308' : '#ef4444'
              }}>
                <Brain className="w-6 h-6" style={{
                  color: data.llmResponse.confidence >= 0.7 ? '#22c55e' :
                         data.llmResponse.confidence >= 0.4 ? '#eab308' : '#ef4444'
                }} />
              </div>
            </div>

            {/* Risk Level */}
            <div className={`px-4 py-2 rounded-lg border ${riskColors[data.riskLevel]}`}>
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4" />
                <span className="font-medium text-sm">Risk: {data.riskLevel.toUpperCase()}</span>
              </div>
            </div>

            {/* Escalation Status */}
            <div className="flex items-center space-x-2">
              <Users className={`w-4 h-4 ${escalationColors[data.escalationStatus]}`} />
              <span className={`text-sm font-medium ${escalationColors[data.escalationStatus]}`}>
                {data.escalationStatus === 'none' ? 'Autonomous' :
                 data.escalationStatus === 'human_review' ? 'Pending Review' : 'Escalated'}
              </span>
            </div>
          </div>

          <div className="text-xs text-slate-500">
            Agent ID: {data.agentId} • {data.agentRole}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReasoningViewer;

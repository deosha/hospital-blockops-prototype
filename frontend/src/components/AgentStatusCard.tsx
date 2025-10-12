import { ShoppingCart, DollarSign, Building2, Brain } from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  type: string;
  state: 'idle' | 'thinking' | 'negotiating' | 'executing' | 'coordinating';
  lastAction: string | null;
  confidence: number;
  timestamp?: string;
}

interface AgentStatusCardProps {
  agent: Agent;
}

const stateConfig = {
  idle: {
    color: 'slate',
    bgColor: 'bg-slate-500/10',
    textColor: 'text-slate-400',
    dotColor: 'bg-slate-500',
    label: 'Idle'
  },
  thinking: {
    color: 'yellow',
    bgColor: 'bg-yellow-500/10',
    textColor: 'text-yellow-400',
    dotColor: 'bg-yellow-500',
    label: 'Thinking'
  },
  negotiating: {
    color: 'blue',
    bgColor: 'bg-blue-500/10',
    textColor: 'text-blue-400',
    dotColor: 'bg-blue-500',
    label: 'Negotiating'
  },
  coordinating: {
    color: 'purple',
    bgColor: 'bg-purple-500/10',
    textColor: 'text-purple-400',
    dotColor: 'bg-purple-500',
    label: 'Coordinating'
  },
  executing: {
    color: 'green',
    bgColor: 'bg-green-500/10',
    textColor: 'text-green-400',
    dotColor: 'bg-green-500',
    label: 'Executing'
  }
};

const getAgentIcon = (type: string) => {
  switch (type) {
    case 'supply_chain':
      return <ShoppingCart className="w-5 h-5" />;
    case 'financial':
      return <DollarSign className="w-5 h-5" />;
    case 'facility':
      return <Building2 className="w-5 h-5" />;
    default:
      return <Brain className="w-5 h-5" />;
  }
};

const AgentStatusCard = ({ agent }: AgentStatusCardProps) => {
  const config = stateConfig[agent.state] || stateConfig.idle; // Fallback to idle if state not found
  const isActive = agent.state !== 'idle';

  return (
    <div className={`
      backdrop-blur-sm bg-slate-700/30 rounded-lg p-3 border border-slate-600/50
      transition-all duration-300
      ${isActive ? 'ring-2 ring-blue-500/50 shadow-lg shadow-blue-500/10' : ''}
    `}>
      {/* Agent Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className={`p-2 rounded-lg ${config.bgColor}`}>
            {getAgentIcon(agent.type)}
          </div>
          <div>
            <h3 className="text-sm font-medium text-white">{agent.name}</h3>
            <p className="text-xs text-slate-400">{agent.id.toUpperCase()}</p>
          </div>
        </div>
        <div className={`flex items-center space-x-1 text-xs ${config.textColor}`}>
          <div className={`w-2 h-2 rounded-full ${config.dotColor} ${isActive ? 'animate-pulse' : ''}`} />
          <span>{config.label}</span>
        </div>
      </div>

      {/* Confidence Meter */}
      {agent.confidence > 0 && (
        <div className="mb-2">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-slate-400">Confidence</span>
            <span className="text-white font-medium">{(agent.confidence * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-1.5">
            <div
              className="bg-gradient-to-r from-blue-500 to-green-500 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${agent.confidence * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Last Action */}
      {agent.timestamp && (
        <div className="text-xs text-slate-400 mt-2">
          Last active: {new Date(agent.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

export default AgentStatusCard;

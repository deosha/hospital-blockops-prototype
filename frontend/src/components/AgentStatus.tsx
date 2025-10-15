import React, { useState } from 'react';
import { Package, DollarSign, Building, Wrench, Brain, ChevronDown, ChevronUp, Activity, Clock } from 'lucide-react';

// TypeScript types
export interface AgentStatusProps {
  agent: {
    name: string;
    role: string;
    state: 'idle' | 'thinking' | 'negotiating' | 'executing';
    confidence: number;
    lastAction: string;
    timestamp: string;
  };
}

// Agent role to icon mapping
const roleIcons: Record<string, React.ComponentType<any>> = {
  'supply_chain': Package,
  'financial': DollarSign,
  'facility': Building,
  'maintenance': Wrench,
  'decision_support': Brain,
};

// State configuration with colors and animations
const stateConfig = {
  idle: {
    bg: 'bg-slate-700/50',
    border: 'border-slate-600/50',
    badge: 'bg-slate-600',
    badgeText: 'text-slate-300',
    label: 'Idle',
    pulse: false,
    gradient: false,
    checkmark: false,
  },
  thinking: {
    bg: 'bg-gradient-to-br from-blue-600/20 to-blue-800/20',
    border: 'border-blue-500/50',
    badge: 'bg-blue-500',
    badgeText: 'text-white',
    label: 'Thinking',
    pulse: true,
    gradient: true,
    checkmark: false,
  },
  negotiating: {
    bg: 'bg-gradient-to-br from-purple-600/20 to-purple-800/20',
    border: 'border-purple-500/50',
    badge: 'bg-purple-500',
    badgeText: 'text-white',
    label: 'Negotiating',
    pulse: true,
    gradient: false,
    checkmark: false,
  },
  executing: {
    bg: 'bg-gradient-to-br from-green-600/20 to-green-800/20',
    border: 'border-green-500/50',
    badge: 'bg-green-500',
    badgeText: 'text-white',
    label: 'Executing',
    pulse: true,
    gradient: false,
    checkmark: true,
  },
};

// Confidence level configuration
const getConfidenceConfig = (confidence: number) => {
  if (confidence < 0.3) {
    return {
      color: 'bg-red-500',
      label: 'Low Confidence',
      textColor: 'text-red-400',
    };
  } else if (confidence < 0.7) {
    return {
      color: 'bg-yellow-500',
      label: 'Medium Confidence',
      textColor: 'text-yellow-400',
    };
  } else {
    return {
      color: 'bg-green-500',
      label: 'High Confidence',
      textColor: 'text-green-400',
    };
  }
};

// Relative time formatter
const getRelativeTime = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 10) return 'just now';
    if (diffSec < 60) return `${diffSec} seconds ago`;
    if (diffMin === 1) return '1 minute ago';
    if (diffMin < 60) return `${diffMin} minutes ago`;
    if (diffHour === 1) return '1 hour ago';
    if (diffHour < 24) return `${diffHour} hours ago`;
    if (diffDay === 1) return '1 day ago';
    return `${diffDay} days ago`;
  } catch {
    return timestamp;
  }
};

const AgentStatus: React.FC<AgentStatusProps> = ({ agent }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const config = stateConfig[agent.state];
  const confidenceConfig = getConfidenceConfig(agent.confidence);

  // Determine icon based on role
  const roleKey = agent.role.toLowerCase().replace(/\s+/g, '_');
  const IconComponent = roleIcons[roleKey] || Activity;

  const relativeTime = getRelativeTime(agent.timestamp);

  return (
    <div
      className="relative group"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute z-50 -top-2 left-1/2 -translate-x-1/2 -translate-y-full
          bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 min-w-[300px]
          shadow-2xl transition-all duration-200 opacity-0 group-hover:opacity-100">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Agent Name:</span>
              <span className="text-white font-medium">{agent.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Role:</span>
              <span className="text-white font-medium">{agent.role}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Current State:</span>
              <span className={`font-medium ${config.badgeText}`}>{config.label}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Confidence:</span>
              <span className={`font-medium ${confidenceConfig.textColor}`}>
                {(agent.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="border-t border-slate-700 pt-2">
              <span className="text-slate-400">Last Action:</span>
              <p className="text-white text-xs mt-1">{agent.lastAction}</p>
            </div>
          </div>
          {/* Tooltip arrow */}
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-full
            w-0 h-0 border-l-8 border-r-8 border-t-8 border-transparent border-t-slate-700" />
        </div>
      )}

      {/* Main Card */}
      <div
        className={`
          backdrop-blur-lg ${config.bg}
          border ${config.border}
          rounded-xl p-5
          transition-all duration-300 ease-in-out
          hover:scale-[1.02] hover:shadow-2xl
          ${config.pulse ? 'animate-pulse-slow' : ''}
        `}
      >
        {/* Animated gradient overlay for thinking state */}
        {config.gradient && (
          <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-blue-500/10 to-transparent
            animate-shimmer bg-[length:200%_100%]" />
        )}

        {/* Header Section */}
        <div className="flex items-start justify-between mb-4 relative z-10">
          {/* Icon and Name */}
          <div className="flex items-center space-x-3">
            {/* Agent Icon */}
            <div className={`
              p-3 rounded-lg
              ${config.badge}/20
              border border-${config.badge}
              transition-all duration-300
            `}>
              <IconComponent
                className={`w-6 h-6 ${config.badgeText}`}
                strokeWidth={2}
              />
            </div>

            {/* Name and Role */}
            <div>
              <h3 className="text-xl font-bold text-white mb-0.5">
                {agent.name}
              </h3>
              <p className="text-sm text-slate-400">
                {agent.role}
              </p>
            </div>
          </div>

          {/* Status Badge */}
          <div className="relative">
            <div className={`
              ${config.badge} ${config.badgeText}
              px-3 py-1.5 rounded-full text-xs font-semibold
              flex items-center space-x-2
              transition-all duration-300
              ${config.pulse ? 'animate-pulse' : ''}
            `}>
              {config.checkmark && (
                <svg className="w-3 h-3 animate-bounce" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
              <span>{config.label}</span>
            </div>
            {/* Pulse ring for active states */}
            {config.pulse && (
              <div className={`
                absolute inset-0 rounded-full ${config.badge}
                animate-ping opacity-20
              `} />
            )}
          </div>
        </div>

        {/* Confidence Meter */}
        <div className="mb-4 relative z-10">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-slate-400 font-medium">Confidence</span>
            <span className={`text-xs font-bold ${confidenceConfig.textColor}`}>
              {(agent.confidence * 100).toFixed(0)}% • {confidenceConfig.label}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-700/50 rounded-full h-2.5 overflow-hidden">
            <div
              className={`
                ${confidenceConfig.color} h-2.5 rounded-full
                transition-all duration-700 ease-out
                animate-fill
              `}
              style={{ width: `${agent.confidence * 100}%` }}
            >
              {/* Shimmer effect on progress bar */}
              <div className="w-full h-full bg-gradient-to-r from-transparent via-white/30 to-transparent
                animate-shimmer bg-[length:200%_100%]" />
            </div>
          </div>
        </div>

        {/* Last Action */}
        <div className="mb-3 relative z-10">
          <div className="flex items-center space-x-2 mb-1.5">
            <Activity className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs text-slate-400 font-medium">Last Action</span>
          </div>
          <p className="text-sm text-slate-200 leading-relaxed pl-5">
            {agent.lastAction}
          </p>
        </div>

        {/* Timestamp */}
        <div className="flex items-center space-x-2 text-xs text-slate-500 mb-3 pl-5 relative z-10">
          <Clock className="w-3 h-3" />
          <span>{relativeTime}</span>
        </div>

        {/* Expand Button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-center space-x-2
            py-2 px-3 rounded-lg
            bg-slate-700/30 hover:bg-slate-700/50
            border border-slate-600/30 hover:border-slate-600/50
            text-slate-400 hover:text-slate-300
            transition-all duration-300
            text-xs font-medium
            relative z-10"
        >
          <span>{isExpanded ? 'Hide' : 'Show'} Reasoning Trace</span>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {/* Expanded Reasoning Trace */}
        {isExpanded && (
          <div className="mt-3 pt-3 border-t border-slate-600/30 relative z-10
            animate-slideDown">
            <div className="bg-slate-800/50 rounded-lg p-3 space-y-2">
              <div className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5" />
                <div className="flex-1">
                  <p className="text-xs text-slate-400 mb-1">Step 1: Analysis</p>
                  <p className="text-xs text-slate-300">
                    Evaluated current scenario constraints and requirements
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-500 mt-1.5" />
                <div className="flex-1">
                  <p className="text-xs text-slate-400 mb-1">Step 2: Decision</p>
                  <p className="text-xs text-slate-300">
                    Generated proposal based on available resources and constraints
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-green-500 mt-1.5" />
                <div className="flex-1">
                  <p className="text-xs text-slate-400 mb-1">Step 3: Validation</p>
                  <p className="text-xs text-slate-300">
                    Validated proposal against constraints with {(agent.confidence * 100).toFixed(0)}% confidence
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Custom animations */}
      <style>{`
        @keyframes pulse-slow {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.8; }
        }
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        @keyframes fill {
          0% { width: 0; }
        }
        @keyframes slideDown {
          0% {
            opacity: 0;
            transform: translateY(-10px);
          }
          100% {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-pulse-slow {
          animation: pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        .animate-shimmer {
          animation: shimmer 2s linear infinite;
        }
        .animate-fill {
          animation: fill 0.7s ease-out;
        }
        .animate-slideDown {
          animation: slideDown 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default AgentStatus;

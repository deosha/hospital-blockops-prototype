import { useState, useEffect } from 'react';
import {
  MessageSquare,
  AlertCircle,
  FileText,
  MessageCircle,
  CheckCircle,
  XCircle,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface Message {
  id: number;
  timestamp: string;
  from: string;
  to: string[];
  type: string;
  content: string;
}

interface CoordinationTimelineProps {
  messages: Message[];
}

const messageTypeConfig: Record<string, {
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  label: string;
}> = {
  intent: {
    icon: <MessageSquare className="w-4 h-4" />,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    label: 'Intent'
  },
  constraint: {
    icon: <AlertCircle className="w-4 h-4" />,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10',
    label: 'Constraint'
  },
  proposal: {
    icon: <FileText className="w-4 h-4" />,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    label: 'Proposal'
  },
  critique: {
    icon: <MessageCircle className="w-4 h-4" />,
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/10',
    label: 'Critique'
  },
  accept: {
    icon: <CheckCircle className="w-4 h-4" />,
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    label: 'Accept'
  },
  reject: {
    icon: <XCircle className="w-4 h-4" />,
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    label: 'Reject'
  },
  inform: {
    icon: <Info className="w-4 h-4" />,
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    label: 'Info'
  }
};

const CoordinationTimeline = ({ messages }: CoordinationTimelineProps) => {
  const [expandedMessages, setExpandedMessages] = useState<Set<number>>(new Set());

  // Debug logging
  useEffect(() => {
    console.log('[CoordinationTimeline] 📬 Messages prop updated:', messages.length, 'messages');
    if (messages.length > 0) {
      console.log('[CoordinationTimeline] 📬 First message:', messages[0]);
    }
  }, [messages]);

  const toggleExpand = (id: number) => {
    const newExpanded = new Set(expandedMessages);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedMessages(newExpanded);
  };

  /**
   * Recursively render nested objects in a user-friendly format
   */
  const renderValue = (value: any, level: number = 0): JSX.Element => {
    if (value === null || value === undefined) {
      return <span className="text-slate-500">null</span>;
    }

    if (typeof value === 'boolean') {
      return <span className={value ? 'text-green-400' : 'text-red-400'}>{String(value)}</span>;
    }

    if (typeof value === 'number') {
      return <span className="text-blue-400">{value.toLocaleString()}</span>;
    }

    if (Array.isArray(value)) {
      return (
        <div className={`space-y-1 ${level > 0 ? 'ml-4' : ''}`}>
          {value.map((item, idx) => (
            <div key={idx} className="flex gap-2">
              <span className="text-slate-500">•</span>
              {renderValue(item, level + 1)}
            </div>
          ))}
        </div>
      );
    }

    if (typeof value === 'object') {
      return (
        <div className={`space-y-1 ${level > 0 ? 'ml-4 border-l border-slate-700 pl-3' : ''}`}>
          {Object.entries(value).map(([key, val]) => (
            <div key={key} className="flex flex-col">
              <span className="text-slate-400 font-medium capitalize">
                {key.replace(/_/g, ' ')}:
              </span>
              <div className="ml-2">{renderValue(val, level + 1)}</div>
            </div>
          ))}
        </div>
      );
    }

    return <span className="text-slate-300">{String(value)}</span>;
  };

  /**
   * Format message content to be user-friendly
   */
  const formatContent = (content: string, type: string): JSX.Element => {
    // Safety check
    if (!content) {
      return <p className="text-slate-300">No content</p>;
    }

    try {
      // Try to parse as Python dict string (e.g., "{'key': 'value'}")
      const jsonStr = content.replace(/'/g, '"').replace(/True/g, 'true').replace(/False/g, 'false').replace(/None/g, 'null');
      const parsed = JSON.parse(jsonStr);

      // Format based on message type
      if (type === 'intent') {
        return (
          <div className="space-y-1">
            <p className="font-medium text-blue-300">{parsed.intent}</p>
            {parsed.context && (
              <div className="text-xs text-slate-400 space-y-0.5 mt-2">
                <div>Item: {parsed.context.item}</div>
                <div>Quantity: {parsed.context.required_quantity} units</div>
                <div>Budget: ₹{parsed.context.budget_remaining?.toLocaleString()}</div>
              </div>
            )}
          </div>
        );
      }

      if (type === 'constraint') {
        // Handle nested constraints object
        const constraints = parsed.constraints || parsed;
        return (
          <div className="space-y-2 text-sm">
            {parsed.type && <p className="text-yellow-300 capitalize font-semibold">{parsed.type} Constraints</p>}
            <div className="text-xs">
              {renderValue(constraints)}
            </div>
          </div>
        );
      }

      if (type === 'proposal') {
        return (
          <div className="space-y-2">
            <p className="font-semibold text-purple-300">
              {parsed.item_name || 'Item'}: {parsed.proposed_quantity?.toLocaleString()} units @ ₹{parsed.price_per_unit?.toLocaleString()}
            </p>
            <div className="text-xs space-y-1">
              <div className="text-blue-400">Total Cost: ₹{parsed.proposed_cost?.toLocaleString()}</div>
              {parsed.reasoning && (
                <div className="text-slate-300 mt-2 italic border-l-2 border-purple-500/30 pl-2">
                  {parsed.reasoning}
                </div>
              )}
              {parsed.constraints_satisfied && (
                <div className="mt-2">
                  <span className="text-slate-400 font-medium">Constraints Satisfied:</span>
                  {renderValue(parsed.constraints_satisfied)}
                </div>
              )}
            </div>
          </div>
        );
      }

      if (type === 'accept' || type === 'reject') {
        const decision = parsed.decision || type;
        const isAccept = decision.toLowerCase() === 'accept';
        return (
          <div className="space-y-2">
            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded ${
              isAccept ? 'bg-green-500/20 border border-green-500/30' : 'bg-red-500/20 border border-red-500/30'
            }`}>
              <span className={`text-lg ${isAccept ? 'text-green-400' : 'text-red-400'}`}>
                {isAccept ? '✓' : '✗'}
              </span>
              <span className={`font-semibold ${isAccept ? 'text-green-300' : 'text-red-300'}`}>
                {decision.toUpperCase()}
              </span>
            </div>
            {parsed.agent && (
              <p className="text-xs text-slate-400">
                by {parsed.agent}
              </p>
            )}
            {parsed.reasoning && (
              <p className="text-xs text-slate-300 mt-2 border-l-2 border-slate-600 pl-3 italic">
                {parsed.reasoning}
              </p>
            )}
            {parsed.confidence !== undefined && (
              <div className="flex items-center gap-2 text-xs text-slate-400 mt-2">
                <span>Confidence:</span>
                <div className="flex-1 max-w-xs bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-full rounded-full ${isAccept ? 'bg-green-500' : 'bg-red-500'}`}
                    style={{ width: `${parsed.confidence * 100}%` }}
                  />
                </div>
                <span className="font-medium">{(parsed.confidence * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>
        );
      }

      if (type === 'inform' || type === 'query') {
        if (parsed.announcement) {
          return <p className="text-slate-300">{parsed.announcement}</p>;
        }
        if (parsed.query) {
          return <p className="text-slate-300 italic">{parsed.query}</p>;
        }

        // Handle execution status
        if (parsed.status === 'executed' && parsed.agreement) {
          const proposal = parsed.agreement.proposal;
          return (
            <div className="space-y-3 text-xs">
              <div className="bg-green-500/10 border border-green-500/30 rounded px-3 py-2">
                <p className="text-green-400 font-semibold mb-1">✓ Agreement Executed</p>
                <p className="text-slate-300">
                  {proposal.item_name}: {proposal.proposed_quantity?.toLocaleString()} units @ ₹{proposal.price_per_unit?.toLocaleString()}
                </p>
                <p className="text-blue-400 mt-1">Total: ₹{proposal.proposed_cost?.toLocaleString()}</p>
              </div>

              {parsed.blockchain && (
                <div className="bg-purple-500/10 border border-purple-500/30 rounded px-3 py-2">
                  <p className="text-purple-400 font-semibold">⛓️ Recorded to Blockchain</p>
                  <div className="text-slate-400 mt-1 space-y-0.5">
                    <div>Block #{parsed.blockchain.block_index}</div>
                    <div className="text-xs text-slate-500 break-all">TX: {parsed.blockchain.transaction_id}</div>
                  </div>
                </div>
              )}

              {parsed.agreement.participants && (
                <div>
                  <p className="text-slate-400 font-medium mb-1">Participants:</p>
                  <div className="flex flex-wrap gap-2">
                    {parsed.agreement.participants.map((p: string) => (
                      <span key={p} className="px-2 py-1 bg-slate-700/50 rounded text-slate-300 text-xs">
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        }

        // Fallback: show key-value pairs using renderValue
        return (
          <div className="text-xs">
            {renderValue(parsed)}
          </div>
        );
      }

      // Default: use renderValue for any nested structure
      return (
        <div className="text-xs">
          {renderValue(parsed)}
        </div>
      );
    } catch {
      // If parsing fails, return plain text
      return <p className="text-slate-300">{content}</p>;
    }
  };

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <MessageSquare className="w-16 h-16 text-slate-600 mb-4" />
        <p className="text-slate-400 text-lg mb-2">No coordination active</p>
        <p className="text-slate-500 text-sm">Click "Start Demo" to begin</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-h-[calc(100vh-20rem)] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent">
      {messages.map((message, index) => {
        try {
          const config = messageTypeConfig[message.type] || messageTypeConfig.inform;
          const isExpanded = expandedMessages.has(message.id);
          const isLast = index === messages.length - 1;

          return (
            <div
              key={message.id}
              className={`
                relative backdrop-blur-sm bg-slate-700/30 rounded-lg border border-slate-600/50
                transition-all duration-300 hover:border-slate-500
                ${isLast ? 'ring-2 ring-blue-500/30 animate-pulse-slow' : ''}
              `}
            >
              {/* Timeline Connector */}
              {index < messages.length - 1 && (
                <div className="absolute left-6 top-full h-4 w-0.5 bg-slate-600" />
              )}

              <div className="p-4">
                {/* Message Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${config.bgColor}`}>
                      <div className={config.color}>
                        {config.icon}
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className={`text-sm font-medium ${config.color}`}>
                          {config.label}
                        </span>
                        <span className="text-xs text-slate-500">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        <span className="font-medium text-white">{message.from}</span>
                        <span className="mx-1">→</span>
                        <span>{Array.isArray(message.to) ? message.to.join(', ') : message.to}</span>
                      </div>
                    </div>
                  </div>

                  {/* Expand Button */}
                  <button
                    onClick={() => toggleExpand(message.id)}
                    className="p-1 hover:bg-slate-600/50 rounded transition-colors"
                  >
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </button>
                </div>

                {/* Message Content */}
                <div className={`ml-11 ${isExpanded ? '' : 'line-clamp-2'}`}>
                  {formatContent(message.content, message.type)}
                </div>
              </div>
            </div>
          );
        } catch (error) {
          console.error('[CoordinationTimeline] Error rendering message:', error, message);
          return (
            <div key={message.id || index} className="p-4 bg-red-900/20 border border-red-500/50 rounded-lg">
              <p className="text-red-400 text-sm">Error rendering message {message.id}</p>
            </div>
          );
        }
      })}
    </div>
  );
};

export default CoordinationTimeline;

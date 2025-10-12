import React, { useState, useEffect } from 'react';
import {
  Blocks,
  CheckCircle2,
  XCircle,
  Clock,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  Shield,
  Search,
  Filter,
  Download,
  Info,
  ArrowRight,
  Eye,
  Zap,
} from 'lucide-react';

// TypeScript Interfaces
export interface Transaction {
  id: string;
  type: 'coordination' | 'decision' | 'validation' | 'execution';
  agentId: string;
  agentName: string;
  action: string;
  timestamp: string;
  data: Record<string, any>;
}

export interface Block {
  index: number;
  timestamp: string;
  transactions: Transaction[];
  previousHash: string;
  hash: string;
  nonce: number;
  validator: string;
}

export interface BlockchainData {
  blocks: Block[];
  chainLength: number;
  isValid: boolean;
  lastValidation: string;
  validationTimeMs: number;
}

export interface BlockchainExplorerProps {
  data: BlockchainData;
  onValidateChain?: () => void;
  onBlockClick?: (blockIndex: number) => void;
}

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

// Transaction type configuration
const transactionTypeConfig: Record<string, { color: string; icon: React.ComponentType<any>; label: string }> = {
  coordination: { color: 'text-blue-400', icon: Zap, label: 'Coordination' },
  decision: { color: 'text-purple-400', icon: Shield, label: 'Decision' },
  validation: { color: 'text-green-400', icon: CheckCircle2, label: 'Validation' },
  execution: { color: 'text-orange-400', icon: Zap, label: 'Execution' },
};

const BlockchainExplorer: React.FC<BlockchainExplorerProps> = ({
  data,
  onValidateChain,
  onBlockClick,
}) => {
  const [expandedBlock, setExpandedBlock] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string | null>(null);
  const [showValidationAnimation, setShowValidationAnimation] = useState(false);
  const [newBlockIndex, setNewBlockIndex] = useState<number | null>(null);
  const { copied, copy } = useCopyToClipboard();

  // Detect new blocks and animate
  useEffect(() => {
    if (data.blocks.length > 0) {
      const latestBlock = data.blocks[data.blocks.length - 1];
      setNewBlockIndex(latestBlock.index);
      setTimeout(() => setNewBlockIndex(null), 1000);
    }
  }, [data.blocks.length]);

  const handleValidateChain = () => {
    setShowValidationAnimation(true);
    setTimeout(() => setShowValidationAnimation(false), 2000);
    onValidateChain?.();
  };

  const toggleBlockExpand = (index: number) => {
    setExpandedBlock(expandedBlock === index ? null : index);
  };

  const truncateHash = (hash: string, chars: number = 8): string => {
    return `${hash.substring(0, chars)}...${hash.substring(hash.length - chars)}`;
  };

  const exportBlockchain = () => {
    const dataStr = JSON.stringify(data, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `blockchain-export-${new Date().getTime()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Filter blocks by search and transaction type
  const filteredBlocks = data.blocks.filter((block) => {
    const matchesSearch =
      searchQuery === '' ||
      block.hash.toLowerCase().includes(searchQuery.toLowerCase()) ||
      block.transactions.some((tx) =>
        tx.agentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tx.action.toLowerCase().includes(searchQuery.toLowerCase())
      );

    const matchesFilter =
      filterType === null ||
      block.transactions.some((tx) => tx.type === filterType);

    return matchesSearch && matchesFilter;
  });

  if (data.blocks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
        <Blocks className="w-16 h-16 text-slate-600 mb-4" />
        <p className="text-slate-400 text-lg mb-2 font-semibold">No blockchain activity</p>
        <p className="text-slate-500 text-sm">Blocks will appear here as decisions are recorded</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Header Section */}
      <div className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-4 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-500/10 rounded-lg">
              <Blocks className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Blockchain Ledger</h3>
              <p className="text-xs text-slate-400">Immutable Audit Trail</p>
            </div>
          </div>

          {/* Validation Status */}
          <div className="flex items-center space-x-2">
            {data.isValid ? (
              <div className="flex items-center space-x-2 px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-lg">
                {showValidationAnimation ? (
                  <div className="w-4 h-4 border-2 border-green-400 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                )}
                <span className="text-sm font-medium text-green-400">Valid Chain</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2 px-3 py-1.5 bg-red-500/10 border border-red-500/30 rounded-lg">
                <XCircle className="w-4 h-4 text-red-400" />
                <span className="text-sm font-medium text-red-400">Invalid Chain</span>
              </div>
            )}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-slate-900/50 rounded-lg p-3">
            <p className="text-xs text-slate-500 mb-1">Chain Length</p>
            <p className="text-2xl font-bold text-white">{data.chainLength}</p>
          </div>
          <div className="bg-slate-900/50 rounded-lg p-3">
            <p className="text-xs text-slate-500 mb-1">Last Block</p>
            <p className="text-sm font-medium text-white">
              {data.blocks.length > 0
                ? new Date(data.blocks[data.blocks.length - 1].timestamp).toLocaleTimeString()
                : 'N/A'}
            </p>
          </div>
          <div className="bg-slate-900/50 rounded-lg p-3">
            <p className="text-xs text-slate-500 mb-1">Validation Time</p>
            <p className="text-sm font-medium text-white">{data.validationTimeMs}ms</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2 mt-4">
          <button
            onClick={handleValidateChain}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-500 hover:bg-blue-600
              text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Shield className="w-4 h-4" />
            <span>Validate Chain</span>
          </button>

          <button
            onClick={exportBlockchain}
            className="flex items-center space-x-2 px-3 py-2 bg-slate-700 hover:bg-slate-600
              text-slate-300 rounded-lg text-sm font-medium transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="flex items-center space-x-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by hash, agent, or action..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-600 rounded-lg
              text-sm text-slate-200 placeholder-slate-500 focus:outline-none
              focus:ring-2 focus:ring-purple-500/50"
          />
        </div>

        <div className="relative">
          <button
            onClick={() => setFilterType(filterType ? null : 'coordination')}
            className="flex items-center space-x-2 px-3 py-2 bg-slate-800/50 border border-slate-600
              rounded-lg text-sm text-slate-300 hover:bg-slate-700 transition-colors"
          >
            <Filter className="w-4 h-4" />
            <span>{filterType ? `Filter: ${filterType}` : 'All Types'}</span>
          </button>
        </div>
      </div>

      {/* Chain Integrity Indicator */}
      <div
        className={`p-3 rounded-lg border flex items-start space-x-3 ${
          data.isValid
            ? 'bg-green-500/5 border-green-500/30'
            : 'bg-red-500/5 border-red-500/30'
        }`}
      >
        {data.isValid ? (
          <>
            <Shield className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-green-400">Chain Integrity: Valid</p>
              <p className="text-xs text-slate-400 mt-1">
                All blocks verified. Hash chain intact. Last validated{' '}
                {new Date(data.lastValidation).toLocaleString()}.
              </p>
            </div>
          </>
        ) : (
          <>
            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-400">Chain Integrity: Compromised</p>
              <p className="text-xs text-slate-400 mt-1">
                Hash mismatch detected. Data may have been tampered with.
              </p>
            </div>
          </>
        )}
      </div>

      {/* Visual Chain Representation */}
      <div className="bg-slate-800/50 backdrop-blur-lg rounded-xl p-4 border border-slate-700">
        <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
          <ArrowRight className="w-4 h-4 mr-2 text-purple-400" />
          Chain Structure
        </h4>
        <div className="flex items-center space-x-2 overflow-x-auto pb-2">
          {data.blocks.map((block, index) => (
            <div key={block.index} className="flex items-center">
              {/* Block Node */}
              <div
                className={`relative group cursor-pointer ${
                  block.index === 0 ? 'w-16' : 'w-12'
                }`}
                onClick={() => toggleBlockExpand(block.index)}
                title={`Block #${block.index}\nHash: ${block.hash}`}
              >
                <div
                  className={`
                    ${block.index === 0 ? 'w-16 h-16' : 'w-12 h-12'}
                    rounded-lg flex items-center justify-center font-bold text-white
                    transition-all duration-200 hover:scale-110
                    ${
                      block.index === 0
                        ? 'bg-gradient-to-br from-yellow-500 to-orange-500 border-2 border-yellow-400'
                        : 'bg-gradient-to-br from-purple-500 to-blue-500'
                    }
                    ${newBlockIndex === block.index ? 'animate-slideIn' : ''}
                  `}
                >
                  {block.index === 0 ? (
                    <span className="text-sm">Genesis</span>
                  ) : (
                    <span>{block.index}</span>
                  )}
                </div>

                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0
                  group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                  <div className="bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs
                    whitespace-nowrap shadow-xl">
                    <p className="text-white font-medium">Block #{block.index}</p>
                    <p className="text-slate-400">
                      Hash: <code className="text-purple-400">{truncateHash(block.hash, 6)}</code>
                    </p>
                    <p className="text-slate-400">{block.transactions.length} tx</p>
                  </div>
                </div>
              </div>

              {/* Arrow Connection */}
              {index < data.blocks.length - 1 && (
                <div className="flex items-center">
                  <div className="w-8 h-0.5 bg-gradient-to-r from-purple-500 to-blue-500" />
                  <ArrowRight className="w-4 h-4 text-purple-400" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Block List */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-slate-600">
        {filteredBlocks.map((block, blockIndex) => {
          const isExpanded = expandedBlock === block.index;
          const isGenesis = block.index === 0;
          const isNew = newBlockIndex === block.index;

          return (
            <div
              key={block.index}
              className={`
                bg-slate-800/50 backdrop-blur-lg rounded-xl border overflow-hidden
                transition-all duration-300
                ${isGenesis ? 'border-yellow-500/50 bg-gradient-to-br from-yellow-500/5 to-orange-500/5' : 'border-slate-700'}
                ${isNew ? 'animate-slideIn ring-2 ring-purple-500/30' : ''}
                hover:border-purple-500/50
              `}
            >
              {/* Block Header */}
              <div
                className="p-4 cursor-pointer"
                onClick={() => toggleBlockExpand(block.index)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold
                        ${isGenesis ? 'bg-gradient-to-br from-yellow-500 to-orange-500' : 'bg-gradient-to-br from-purple-500 to-blue-500'}`}
                    >
                      <span className="text-white text-sm">
                        {isGenesis ? 'G' : block.index}
                      </span>
                    </div>
                    <div>
                      <h4 className="text-base font-semibold text-white">
                        {isGenesis ? 'Genesis Block' : `Block #${block.index}`}
                      </h4>
                      <p className="text-xs text-slate-400">
                        {block.transactions.length} transaction{block.transactions.length !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {data.isValid && (
                      <div className="flex items-center space-x-1 text-green-400 animate-checkmark">
                        <CheckCircle2 className="w-4 h-4" />
                      </div>
                    )}
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-slate-400" />
                    )}
                  </div>
                </div>

                {/* Compact Info */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Timestamp:</span>
                    <span className="text-slate-300">
                      {new Date(block.timestamp).toLocaleString()}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Hash:</span>
                    <div className="flex items-center space-x-2">
                      <code className="text-purple-400 font-mono">
                        {truncateHash(block.hash)}
                      </code>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          copy(block.hash, `hash-${block.index}`);
                        }}
                        className="p-1 hover:bg-slate-700 rounded transition-colors"
                      >
                        {copied === `hash-${block.index}` ? (
                          <Check className="w-3 h-3 text-green-400" />
                        ) : (
                          <Copy className="w-3 h-3 text-slate-400" />
                        )}
                      </button>
                    </div>
                  </div>

                  {!isGenesis && (
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Previous:</span>
                      <div className="flex items-center space-x-2">
                        <code className="text-blue-400 font-mono">
                          {truncateHash(block.previousHash)}
                        </code>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            copy(block.previousHash, `prev-${block.index}`);
                          }}
                          className="p-1 hover:bg-slate-700 rounded transition-colors"
                        >
                          {copied === `prev-${block.index}` ? (
                            <Check className="w-3 h-3 text-green-400" />
                          ) : (
                            <Copy className="w-3 h-3 text-slate-400" />
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Transaction Summary (collapsed) */}
                {!isExpanded && block.transactions.length > 0 && (
                  <div className="mt-3 p-2 bg-slate-900/50 rounded text-xs text-slate-300">
                    {block.transactions[0].agentName}: {block.transactions[0].action}
                    {block.transactions.length > 1 && (
                      <span className="text-slate-500"> +{block.transactions.length - 1} more</span>
                    )}
                  </div>
                )}
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="border-t border-slate-700 p-4 space-y-4 animate-slideDown">
                  {/* Full Hash Details */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-400">Complete Hash</span>
                      <button
                        onClick={() => copy(block.hash, `full-hash-${block.index}`)}
                        className="text-xs text-purple-400 hover:text-purple-300 flex items-center space-x-1"
                      >
                        {copied === `full-hash-${block.index}` ? (
                          <>
                            <Check className="w-3 h-3" />
                            <span>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                    <code className="block bg-slate-900/50 rounded p-2 text-xs text-purple-400 font-mono break-all">
                      {block.hash}
                    </code>
                  </div>

                  {!isGenesis && (
                    <div className="space-y-2">
                      <span className="text-xs font-medium text-slate-400">Previous Block Hash</span>
                      <code className="block bg-slate-900/50 rounded p-2 text-xs text-blue-400 font-mono break-all">
                        {block.previousHash}
                      </code>
                    </div>
                  )}

                  {/* Validator Info */}
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Validator:</span>
                    <span className="text-slate-200 font-medium">{block.validator}</span>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Nonce:</span>
                    <span className="text-slate-200 font-mono">{block.nonce}</span>
                  </div>

                  {/* Transactions */}
                  <div>
                    <h5 className="text-xs font-semibold text-slate-300 mb-2">
                      Transactions ({block.transactions.length})
                    </h5>
                    <div className="space-y-2">
                      {block.transactions.map((tx, txIndex) => {
                        const txConfig = transactionTypeConfig[tx.type] || transactionTypeConfig.coordination;
                        const TxIcon = txConfig.icon;

                        return (
                          <div
                            key={tx.id}
                            className="bg-slate-900/50 rounded-lg p-3 border border-slate-700/50"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center space-x-2">
                                <TxIcon className={`w-4 h-4 ${txConfig.color}`} />
                                <span className={`text-xs font-medium ${txConfig.color}`}>
                                  {txConfig.label}
                                </span>
                              </div>
                              <span className="text-xs text-slate-500">
                                {new Date(tx.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 mb-1">
                              <span className="text-white font-medium">{tx.agentName}</span> ({tx.agentId})
                            </p>
                            <p className="text-xs text-slate-300">{tx.action}</p>

                            {/* Transaction Data */}
                            <details className="mt-2">
                              <summary className="text-xs text-purple-400 cursor-pointer hover:text-purple-300">
                                View Data
                              </summary>
                              <pre className="mt-2 bg-slate-950 rounded p-2 text-xs text-slate-300 overflow-x-auto">
                                {JSON.stringify(tx.data, null, 2)}
                              </pre>
                            </details>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Data Integrity Visualization */}
                  <div className="p-3 bg-green-500/5 border border-green-500/30 rounded-lg">
                    <div className="flex items-center space-x-2 mb-2">
                      <Shield className="w-4 h-4 text-green-400" />
                      <span className="text-xs font-medium text-green-400">Data Integrity</span>
                    </div>
                    <p className="text-xs text-slate-400">
                      This block is cryptographically linked to the previous block. Any modification
                      to the data would change the hash and break the chain.
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Educational Tooltip Section */}
      <div className="bg-blue-500/5 border border-blue-500/30 rounded-lg p-3 flex items-start space-x-3">
        <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300">
          <p className="font-medium text-blue-400 mb-1">Why Blockchain?</p>
          <p>
            Each block contains a hash of the previous block, creating an immutable chain. Changing any
            historical data would require recalculating all subsequent hashes, making tampering evident.
          </p>
        </div>
      </div>

      {/* Custom Animations */}
      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes slideDown {
          from {
            opacity: 0;
            max-height: 0;
          }
          to {
            opacity: 1;
            max-height: 2000px;
          }
        }
        @keyframes checkmark {
          0%, 100% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.2);
          }
        }
        .animate-slideIn {
          animation: slideIn 0.5s ease-out;
        }
        .animate-slideDown {
          animation: slideDown 0.3s ease-out;
        }
        .animate-checkmark {
          animation: checkmark 0.6s ease-in-out;
        }
      `}</style>
    </div>
  );
};

export default BlockchainExplorer;

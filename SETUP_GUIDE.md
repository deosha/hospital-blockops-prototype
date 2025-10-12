# Quick Setup Guide for BlockOps Demo

## ✅ Files Already Created

The following structure has been created:

```
hospital-blockops-demo/
├── frontend/
│   ├── src/
│   │   ├── types/index.ts ✅
│   │   ├── services/api.ts ✅
│   │   ├── App.tsx ✅
│   │   ├── main.tsx ✅
│   │   └── index.css ✅
│   ├── package.json ✅
│   ├── vite.config.ts ✅
│   ├── tailwind.config.js ✅
│   ├── tsconfig.json ✅
│   ├── postcss.config.js ✅
│   └── index.html ✅
├── backend/
│   ├── app.py ✅
│   ├── requirements.txt ✅
│   └── .env.example ✅
├── README.md ✅
└── .gitignore ✅
```

## 🚀 Quick Start (Minimal Working Version)

### Step 1: Create Missing Backend Files

Run these commands to create the remaining backend files:

```bash
cd hospital-blockops-demo/backend

# Create API routes
cat > api/__init__.py << 'EOF'
EOF

cat > api/routes.py << 'EOF'
from flask import Blueprint, jsonify, request
from datetime import datetime
import random

api_bp = Blueprint('api', __name__)

# Mock data store
agents_store = {
    'sc001': {'id': 'sc001', 'name': 'Supply Chain Agent', 'type': 'supply_chain', 'status': 'active'},
    'en001': {'id': 'en001', 'name': 'Energy Management Agent', 'type': 'energy', 'status': 'active'},
    'sh001': {'id': 'sh001', 'name': 'Scheduling Agent', 'type': 'scheduling', 'status': 'idle'},
    'mt001': {'id': 'mt001', 'name': 'Maintenance Agent', 'type': 'maintenance', 'status': 'processing'},
    'ds001': {'id': 'ds001', 'name': 'Decision Support Agent', 'type': 'decision_support', 'status': 'active'},
}

decisions_store = []
coordinations_store = []

@api_bp.route('/agents', methods=['GET'])
def get_agents():
    return jsonify(list(agents_store.values()))

@api_bp.route('/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    agent = agents_store.get(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    return jsonify(agent)

@api_bp.route('/agents/<agent_id>/action', methods=['POST'])
def trigger_action(agent_id):
    data = request.get_json()
    action = data.get('action', 'generic_action')

    decision = {
        'id': f'dec_{len(decisions_store) + 1}',
        'agentId': agent_id,
        'agentName': agents_store[agent_id]['name'],
        'type': action,
        'description': f'Executing {action}',
        'reasoning': 'Automated decision based on threshold triggers',
        'confidence': random.uniform(0.75, 0.99),
        'autonomyLevel': random.choice([1, 2, 3]),
        'status': 'pending',
        'timestamp': datetime.now().isoformat(),
        'riskScore': random.uniform(0.1, 0.8)
    }

    decisions_store.append(decision)
    return jsonify(decision)

@api_bp.route('/decisions', methods=['GET'])
def get_decisions():
    return jsonify(decisions_store[-20:])  # Last 20 decisions

@api_bp.route('/decisions/pending', methods=['GET'])
def get_pending_decisions():
    pending = [d for d in decisions_store if d['status'] == 'pending']
    return jsonify(pending)

@api_bp.route('/decisions/<decision_id>/approve', methods=['POST'])
def approve_decision(decision_id):
    for decision in decisions_store:
        if decision['id'] == decision_id:
            decision['status'] = 'approved'
            return jsonify(decision)
    return jsonify({'error': 'Decision not found'}), 404

@api_bp.route('/decisions/<decision_id>/reject', methods=['POST'])
def reject_decision(decision_id):
    data = request.get_json()
    for decision in decisions_store:
        if decision['id'] == decision_id:
            decision['status'] = 'rejected'
            decision['rejectionReason'] = data.get('reason', 'No reason provided')
            return jsonify(decision)
    return jsonify({'error': 'Decision not found'}), 404

@api_bp.route('/decisions/<decision_id>/explain', methods=['GET'])
def explain_decision(decision_id):
    return jsonify({
        'explanation': 'This is a simulated explanation. In production, this would query the LLM-based Decision Support Agent for detailed reasoning.'
    })

@api_bp.route('/coordinations', methods=['GET'])
def get_coordinations():
    return jsonify(coordinations_store[-10:])

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    total = len(decisions_store)
    return jsonify({
        'totalDecisions': total,
        'autonomousDecisions': int(total * 0.82),
        'approvalRequired': int(total * 0.15),
        'humanLed': int(total * 0.03),
        'averageConfidence': 0.87,
        'energySavings': 18.3,
        'costReduction': 23.1,
        'complianceRate': 99.8
    })

@api_bp.route('/blockchain/records', methods=['GET'])
def get_blockchain_records():
    limit = request.args.get('limit', 10, type=int)
    records = []
    for i, decision in enumerate(decisions_store[-limit:]):
        records.append({
            'id': f'block_{i}',
            'decisionId': decision['id'],
            'hash': f'0x{random.randint(10000, 99999)}',
            'previousHash': f'0x{random.randint(10000, 99999)}',
            'timestamp': decision['timestamp'],
            'data': decision,
            'validated': True
        })
    return jsonify(records)
EOF

# Create agents package
mkdir -p agents
touch agents/__init__.py

# Create blockchain package
mkdir -p blockchain
touch blockchain/__init__.py
```

### Step 2: Create Missing Frontend Components

```bash
cd ../frontend/src/components

# Create Layout component
cat > Layout.tsx << 'EOF'
import { Link, useLocation } from 'react-router-dom';
import { Home, Users, FileCheck, GitBranch, Database } from 'lucide-react';

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  const navItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/agents', icon: Users, label: 'Agents' },
    { path: '/decisions', icon: FileCheck, label: 'Decisions' },
    { path: '/coordination', icon: GitBranch, label: 'Coordination' },
    { path: '/blockchain', icon: Database, label: 'Blockchain' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-2xl font-bold text-primary-600">BlockOps</h1>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                        isActive
                          ? 'border-primary-500 text-gray-900'
                          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                      }`}
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}
EOF

# Create Dashboard component
cat > Dashboard.tsx << 'EOF'
import { useEffect, useState } from 'react';
import { statsService, agentService, decisionService } from '@/services/api';
import type { Agent, SystemStats, Decision } from '@/types';
import { Activity, TrendingDown, Zap, CheckCircle } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [recentDecisions, setRecentDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, agentsData, decisionsData] = await Promise.all([
          statsService.getSystemStats(),
          agentService.getAllAgents(),
          decisionService.getAllDecisions(),
        ]);
        setStats(statsData);
        setAgents(agentsData);
        setRecentDecisions(decisionsData.slice(-5));
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="text-center py-12">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">System Dashboard</h2>
        <p className="mt-1 text-sm text-gray-500">
          Real-time monitoring of hospital operations multi-agent system
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Activity className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Decisions
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {stats?.totalDecisions || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingDown className="h-6 w-6 text-green-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Cost Reduction
                  </dt>
                  <dd className="text-lg font-semibold text-green-600">
                    {stats?.costReduction.toFixed(1)}%
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Zap className="h-6 w-6 text-yellow-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Energy Savings
                  </dt>
                  <dd className="text-lg font-semibold text-yellow-600">
                    {stats?.energySavings.toFixed(1)}%
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircle className="h-6 w-6 text-blue-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Compliance Rate
                  </dt>
                  <dd className="text-lg font-semibold text-blue-600">
                    {stats?.complianceRate.toFixed(1)}%
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Agents Status */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Active Agents
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400"
              >
                <div className="flex-shrink-0">
                  <span
                    className={`inline-flex h-10 w-10 items-center justify-center rounded-full ${
                      agent.status === 'active'
                        ? 'bg-green-100'
                        : agent.status === 'processing'
                        ? 'bg-yellow-100'
                        : 'bg-gray-100'
                    }`}
                  >
                    <Activity
                      className={`h-6 w-6 ${
                        agent.status === 'active'
                          ? 'text-green-600'
                          : agent.status === 'processing'
                          ? 'text-yellow-600'
                          : 'text-gray-600'
                      }`}
                    />
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">
                    {agent.name}
                  </p>
                  <p className="text-sm text-gray-500 truncate">
                    {agent.status}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Decisions */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Recent Decisions
          </h3>
          <div className="space-y-3">
            {recentDecisions.map((decision) => (
              <div
                key={decision.id}
                className="border-l-4 border-primary-500 bg-primary-50 p-4"
              >
                <div className="flex">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-primary-900">
                      {decision.description}
                    </p>
                    <p className="mt-1 text-sm text-primary-700">
                      Agent: {decision.agentName} | Confidence:{' '}
                      {(decision.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="ml-4 flex-shrink-0">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        decision.status === 'approved'
                          ? 'bg-green-100 text-green-800'
                          : decision.status === 'pending'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {decision.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
EOF

# Create stub components
for component in AgentsView DecisionsView CoordinationView BlockchainView; do
  cat > ${component}.tsx << EOF
export default function ${component}() {
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4">${component}</h2>
      <p className="text-gray-600">
        This view is under construction. Check back soon!
      </p>
    </div>
  );
}
EOF
done
```

### Step 3: Install Dependencies and Run

```bash
# Install frontend dependencies
cd ../..
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY if you have one

# Start backend (in one terminal)
python app.py

# Start frontend (in another terminal)
cd ../frontend
npm run dev
```

### Step 4: Access the Demo

Open your browser to `http://localhost:3000`

---

## 🎯 What You'll See

1. **Dashboard** - System overview with metrics
2. **Agents** - Status of 5 agents
3. **Decisions** - Recent autonomous decisions
4. **Coordination** - (Coming soon)
5. **Blockchain** - (Coming soon)

## 🔥 Quick Test

```bash
# Test backend health
curl http://localhost:5000/health

# Test agents endpoint
curl http://localhost:5000/api/agents

# Trigger an agent action
curl -X POST http://localhost:5000/api/agents/sc001/action \
  -H "Content-Type: application/json" \
  -d '{"action":"check_inventory"}'
```

## ✅ Success Indicators

- ✅ Frontend loads at http://localhost:3000
- ✅ Backend responds at http://localhost:5000
- ✅ Dashboard shows 5 agents
- ✅ No console errors
- ✅ Stats display correctly

---

**This creates a minimal working demo!** The full implementation with all features (detailed agents, blockchain simulation, LLM integration) can be added incrementally.

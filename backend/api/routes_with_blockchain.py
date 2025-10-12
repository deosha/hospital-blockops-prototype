"""
Flask API Routes with Blockchain Integration

This file replaces the simple routes.py with full blockchain support.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import random

# Import blockchain manager
from blockchain.manager import (
    get_blockchain,
    record_agent_decision,
    get_recent_blocks,
    verify_block,
    get_blockchain_stats,
    get_transaction_history,
    validate_constraints_preview,
    get_smart_contract_constraints,
    format_block_summary,
    reset_blockchain
)

# Import real coordination engine
from api.real_coordination import get_coordination_engine

api_bp = Blueprint('api', __name__)

# Mock data store (for agents and coordinations not yet on blockchain)
agents_store = {
    'sc001': {'id': 'sc001', 'name': 'Supply Chain Agent', 'type': 'supply_chain', 'status': 'active'},
    'en001': {'id': 'en001', 'name': 'Energy Management Agent', 'type': 'energy', 'status': 'active'},
    'sh001': {'id': 'sh001', 'name': 'Scheduling Agent', 'type': 'scheduling', 'status': 'idle'},
    'mt001': {'id': 'mt001', 'name': 'Maintenance Agent', 'type': 'maintenance', 'status': 'processing'},
    'ds001': {'id': 'ds001', 'name': 'Decision Support Agent', 'type': 'decision_support', 'status': 'active'},
}

coordinations_store = []


# ============================================================================
# AGENT ENDPOINTS
# ============================================================================

@api_bp.route('/agents', methods=['GET'])
def get_agents():
    """Get all agents"""
    return jsonify(list(agents_store.values()))


@api_bp.route('/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get specific agent"""
    agent = agents_store.get(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    return jsonify(agent)


@api_bp.route('/agents/<agent_id>/action', methods=['POST'])
def trigger_action(agent_id):
    """
    Trigger agent action and record to blockchain.

    This endpoint now:
    1. Creates agent decision
    2. Records to blockchain with smart contract validation
    3. Returns decision with blockchain confirmation
    """
    data = request.get_json()
    action = data.get('action', 'generic_action')

    agent = agents_store.get(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404

    # Generate decision details based on agent type
    decision_details = _generate_decision_details(agent['type'], action)

    # Record to blockchain
    blockchain_result = record_agent_decision(
        agent_id=agent_id,
        agent_name=agent['name'],
        action_type=action.upper().replace(' ', '_'),
        decision_details=decision_details
    )

    # Create decision response
    decision = {
        'id': blockchain_result['transaction_id'],
        'agentId': agent_id,
        'agentName': agent['name'],
        'type': action,
        'description': f'Executing {action}',
        'reasoning': decision_details.get('reasoning', 'Automated decision based on threshold triggers'),
        'confidence': decision_details.get('confidence', random.uniform(0.75, 0.99)),
        'autonomyLevel': _determine_autonomy_level(decision_details),
        'status': 'approved' if blockchain_result['success'] else 'rejected',
        'timestamp': blockchain_result['timestamp'],
        'riskScore': decision_details.get('risk_score', random.uniform(0.1, 0.8)),
        'blockchain': {
            'recorded': blockchain_result['success'],
            'block_index': blockchain_result['block_index'],
            'block_hash': blockchain_result['block_hash'][:16] + '...' if blockchain_result['block_hash'] else None,
            'validation': blockchain_result['validation']
        }
    }

    return jsonify(decision)


def _generate_decision_details(agent_type: str, action: str) -> dict:
    """Generate realistic decision details based on agent type"""

    if agent_type == 'supply_chain':
        return {
            'item': 'Medical Supplies',
            'quantity': random.randint(100, 1000),
            'amount': random.uniform(500, 5000),
            'vendor': random.choice(['MedSupply Corp', 'Healthcare Plus', 'MediPro Inc']),
            'confidence': random.uniform(0.75, 0.98),
            'available_budget': 10000.00,
            'available_storage': 2000,
            'reasoning': f'Inventory below safety threshold. Forecasted demand requires immediate reorder.'
        }

    elif agent_type == 'energy':
        return {
            'zone': f'Zone {random.randint(1, 10)}',
            'action': random.choice(['HVAC_ADJUST', 'LIGHTING_DIM', 'TEMP_OPTIMIZE']),
            'temperature_delta': random.uniform(-3, 3),
            'estimated_savings_kwh': random.uniform(20, 100),
            'confidence': random.uniform(0.80, 0.95),
            'reasoning': f'Occupancy forecast predicts low utilization. Adjusting climate control to reduce energy consumption.'
        }

    elif agent_type == 'scheduling':
        return {
            'resource': f'Operating Room {random.randint(1, 20)}',
            'time_slot': f'{random.randint(8, 18)}:00',
            'staff_assigned': random.randint(3, 8),
            'confidence': random.uniform(0.70, 0.92),
            'reasoning': f'Optimal scheduling based on staff availability and equipment usage patterns.'
        }

    elif agent_type == 'maintenance':
        return {
            'equipment': f'MRI-{random.randint(1, 5)}',
            'maintenance_type': random.choice(['PREVENTIVE', 'PREDICTIVE', 'CORRECTIVE']),
            'estimated_downtime_hours': random.uniform(1, 6),
            'confidence': random.uniform(0.75, 0.95),
            'reasoning': f'Equipment failure probability exceeds threshold. Scheduling preventive maintenance to avoid unplanned downtime.'
        }

    else:  # decision_support
        return {
            'decision_type': 'ANALYSIS',
            'recommendation': 'Optimize resource allocation',
            'confidence': random.uniform(0.85, 0.98),
            'reasoning': f'Analysis of operational data suggests optimization opportunity.'
        }


def _determine_autonomy_level(details: dict) -> int:
    """Determine autonomy level based on decision details"""
    confidence = details.get('confidence', 0.5)
    amount = details.get('amount', 0)

    if confidence < 0.7 or amount > 10000:
        return 3  # Human-led
    elif confidence < 0.85 or amount > 5000:
        return 2  # Approval required
    else:
        return 1  # Autonomous


# ============================================================================
# DECISION ENDPOINTS
# ============================================================================

@api_bp.route('/decisions', methods=['GET'])
def get_decisions():
    """Get all decisions from blockchain"""
    transactions = get_transaction_history()
    decisions = []

    for tx in transactions[-20:]:  # Last 20 decisions
        decisions.append({
            'id': tx['transaction_id'],
            'agentId': tx.get('agent_name', 'Unknown'),
            'agentName': tx['agent_name'],
            'type': tx['action_type'],
            'description': f"{tx['action_type']} by {tx['agent_name']}",
            'reasoning': tx['details'].get('reasoning', 'No reasoning provided'),
            'confidence': tx['details'].get('confidence', 0.0),
            'autonomyLevel': 1,  # Could derive from details
            'status': tx['validation_status'],
            'timestamp': tx['timestamp'],
            'riskScore': tx['details'].get('risk_score', 0.0),
            'blockIndex': tx['block_index'],
            'blockHash': tx['block_hash'][:16] + '...'
        })

    return jsonify(decisions)


@api_bp.route('/decisions/pending', methods=['GET'])
def get_pending_decisions():
    """Get pending decisions (Level 2 autonomy)"""
    # In a real system, these would be filtered from blockchain
    all_decisions = get_decisions().get_json()
    pending = [d for d in all_decisions if d.get('autonomyLevel') == 2 and d['status'] == 'pending']
    return jsonify(pending)


@api_bp.route('/decisions/<decision_id>/approve', methods=['POST'])
def approve_decision(decision_id):
    """Approve a decision and record approval to blockchain"""
    # Record approval to blockchain
    result = record_agent_decision(
        agent_id="human_operator",
        agent_name="Human Operator",
        action_type="DECISION_APPROVAL",
        decision_details={
            'original_decision_id': decision_id,
            'action': 'APPROVED',
            'timestamp': datetime.now().isoformat()
        }
    )

    return jsonify({
        'decision_id': decision_id,
        'status': 'approved',
        'blockchain_recorded': result['success'],
        'block_index': result['block_index']
    })


@api_bp.route('/decisions/<decision_id>/reject', methods=['POST'])
def reject_decision(decision_id):
    """Reject a decision and record rejection to blockchain"""
    data = request.get_json()
    reason = data.get('reason', 'No reason provided')

    result = record_agent_decision(
        agent_id="human_operator",
        agent_name="Human Operator",
        action_type="DECISION_REJECTION",
        decision_details={
            'original_decision_id': decision_id,
            'action': 'REJECTED',
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
    )

    return jsonify({
        'decision_id': decision_id,
        'status': 'rejected',
        'reason': reason,
        'blockchain_recorded': result['success'],
        'block_index': result['block_index']
    })


@api_bp.route('/decisions/<decision_id>/explain', methods=['GET'])
def explain_decision(decision_id):
    """Get LLM explanation for decision (simulated)"""
    return jsonify({
        'explanation': f'Decision {decision_id}: This action was taken based on operational thresholds and historical patterns. '
                      f'The agent analyzed current state, retrieved relevant policies from the knowledge base, '
                      f'and determined this action optimizes operational efficiency while maintaining safety constraints. '
                      f'All constraints were validated via smart contracts before blockchain recording.'
    })


# ============================================================================
# BLOCKCHAIN ENDPOINTS
# ============================================================================

@api_bp.route('/blockchain/blocks', methods=['GET'])
def get_blocks():
    """Get recent blocks from blockchain"""
    limit = request.args.get('limit', 10, type=int)
    blocks = get_recent_blocks(limit=limit)

    # Format for API response
    formatted_blocks = [format_block_summary(block) for block in blocks]

    return jsonify(formatted_blocks)


@api_bp.route('/blockchain/blocks/<int:block_index>', methods=['GET'])
def get_block(block_index):
    """Get specific block"""
    blockchain = get_blockchain()
    block = blockchain.get_block(block_index)

    if not block:
        return jsonify({'error': f'Block {block_index} not found'}), 404

    return jsonify(block.to_dict())


@api_bp.route('/blockchain/verify/<int:block_index>', methods=['GET'])
def verify_blockchain_block(block_index):
    """Verify specific block integrity"""
    result = verify_block(block_index)
    return jsonify(result)


@api_bp.route('/blockchain/validate', methods=['GET'])
def validate_blockchain():
    """Validate entire blockchain"""
    blockchain = get_blockchain()
    validation = blockchain.validate_chain()
    return jsonify(validation)


@api_bp.route('/blockchain/stats', methods=['GET'])
def blockchain_stats():
    """Get blockchain statistics"""
    stats = get_blockchain_stats()
    return jsonify(stats)


@api_bp.route('/blockchain/transactions', methods=['GET'])
def get_blockchain_transactions():
    """Get transaction history"""
    agent_name = request.args.get('agent', None)
    transactions = get_transaction_history(agent_name=agent_name)
    return jsonify(transactions)


@api_bp.route('/blockchain/constraints', methods=['GET'])
def get_constraints():
    """Get smart contract constraints"""
    constraints = get_smart_contract_constraints()
    return jsonify(constraints)


@api_bp.route('/blockchain/constraints/validate', methods=['POST'])
def validate_constraints():
    """Preview constraint validation"""
    data = request.get_json()

    result = validate_constraints_preview(
        amount=data.get('amount'),
        quantity=data.get('quantity'),
        confidence=data.get('confidence')
    )

    return jsonify(result)


@api_bp.route('/blockchain/reset', methods=['POST'])
def reset_blockchain_endpoint():
    """Reset blockchain (demo/testing only)"""
    blockchain = reset_blockchain()
    return jsonify({
        'message': 'Blockchain reset successfully',
        'blocks': len(blockchain.chain),
        'genesis_hash': blockchain.chain[0].hash
    })


# ============================================================================
# COORDINATION ENDPOINTS (Placeholder)
# ============================================================================

@api_bp.route('/coordinations', methods=['GET'])
def get_coordinations():
    """Get active coordinations"""
    return jsonify(coordinations_store[-10:])


@api_bp.route('/coordinations/initiate', methods=['POST'])
def initiate_coordination():
    """Initiate new coordination"""
    data = request.get_json()

    coordination = {
        'id': f'coord_{len(coordinations_store) + 1}',
        'initiatorAgent': data.get('agentId', 'unknown'),
        'type': data.get('type', 'negotiation'),
        'description': data.get('description', ''),
        'status': 'initiated',
        'timestamp': datetime.now().isoformat()
    }

    coordinations_store.append(coordination)
    return jsonify(coordination)


# ============================================================================
# SYSTEM STATS
# ============================================================================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'data': {'status': 'healthy', 'message': 'BlockOps backend is running'},
        'timestamp': datetime.now().isoformat()
    })


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get system-wide statistics"""
    blockchain_stats = get_blockchain_stats()

    return jsonify({
        'success': True,
        'data': {
            'totalDecisions': blockchain_stats['total_transactions'],
            'autonomousDecisions': int(blockchain_stats['total_transactions'] * 0.82),
            'approvalRequired': int(blockchain_stats['total_transactions'] * 0.15),
            'humanLed': int(blockchain_stats['total_transactions'] * 0.03),
            'averageConfidence': 0.87,
            'energySavings': 18.3,
            'costReduction': 23.1,
            'complianceRate': 99.8,
            'blockchainStats': blockchain_stats
        },
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# SCENARIO ENDPOINTS (for frontend demo)
# ============================================================================

# Store for active scenarios
scenarios_store = {}

@api_bp.route('/scenarios/start', methods=['POST'])
def start_scenario():
    """
    Start a new coordination scenario

    Uses REAL LLM agents if available, falls back to demo simulation
    """
    data = request.get_json()
    scenario_id = f"scenario-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Get coordination engine
    engine = get_coordination_engine()

    # Start coordination (real LLM or demo mode)
    result = engine.start_coordination(
        scenario_id=scenario_id,
        scenario_type=data.get('scenario_type', 'supply_chain_coordination'),
        parameters=data.get('parameters', {})
    )

    # Create scenario object for response
    scenario = {
        'id': scenario_id,
        'type': data.get('scenario_type', 'supply_chain_coordination'),
        'state': result['status'],
        'parameters': data.get('parameters', {}),
        'started_at': datetime.now().isoformat(),
        'using_real_llm': result['using_real_llm'],
        'agents_involved': ['Supply Chain Agent', 'Financial Agent', 'Facility Agent']
    }

    # Store scenario
    scenarios_store[scenario_id] = scenario

    return jsonify({
        'success': True,
        'data': scenario,
        'timestamp': datetime.now().isoformat(),
        'info': result.get('info', '')
    })


@api_bp.route('/scenarios/<scenario_id>/status', methods=['GET'])
def get_scenario_status(scenario_id):
    """Get scenario status"""
    scenario = scenarios_store.get(scenario_id)
    if not scenario:
        return jsonify({
            'success': False,
            'error': 'Scenario not found',
            'timestamp': datetime.now().isoformat()
        }), 404

    return jsonify({
        'success': True,
        'data': scenario,
        'timestamp': datetime.now().isoformat()
    })


@api_bp.route('/scenarios/<scenario_id>/messages', methods=['GET'])
def get_scenario_messages(scenario_id):
    """Get messages for a scenario"""
    # Try to get messages from coordination engine first (real LLM)
    engine = get_coordination_engine()
    messages = engine.get_session_messages(scenario_id)

    if messages:
        return jsonify({
            'success': True,
            'data': messages,
            'timestamp': datetime.now().isoformat()
        })

    # Fall back to scenarios_store (demo mode)
    scenario = scenarios_store.get(scenario_id)
    if not scenario:
        return jsonify({
            'success': False,
            'error': 'Scenario not found',
            'timestamp': datetime.now().isoformat()
        }), 404

    return jsonify({
        'success': True,
        'data': scenario.get('messages', []),
        'timestamp': datetime.now().isoformat()
    })


@api_bp.route('/scenarios/reset', methods=['POST'])
def reset_scenario():
    """Reset all scenarios"""
    global scenarios_store
    scenarios_store = {}

    return jsonify({
        'success': True,
        'data': {'success': True},
        'timestamp': datetime.now().isoformat()
    })


@api_bp.route('/agents/status', methods=['GET'])
def get_agents_status():
    """Get agent status in format expected by frontend"""
    # Get coordination engine to check for active sessions
    engine = get_coordination_engine()

    # Check if any sessions are running
    active_session = None
    for session_id, session_info in engine.active_sessions.items():
        if session_info['status'] == 'running':
            active_session = session_info
            break

    # Get agent states from active session or default to idle
    agent_states = {}
    if active_session and 'agent_states' in active_session:
        agent_states = active_session['agent_states']

    agents = []
    for agent_name, role in [
        ('Supply Chain Agent', 'supply_chain'),
        ('Financial Agent', 'financial'),
        ('Facility Agent', 'facility')
    ]:
        state = agent_states.get(agent_name, 'idle')

        # Determine last action and confidence based on state
        if state == 'thinking':
            last_action = f"Analyzing request..."
            confidence = 0.5
        elif state == 'negotiating':
            last_action = f"Negotiating proposal"
            confidence = 0.75
        elif state == 'executing':
            last_action = f"Executing agreement"
            confidence = 0.95
        else:  # idle
            last_action = 'Ready for coordination'
            confidence = 0.0

        agents.append({
            'name': agent_name,
            'role': role,
            'state': state,
            'confidence': confidence,
            'last_action': last_action,
            'timestamp': datetime.now().isoformat()
        })

    return jsonify({
        'success': True,
        'data': agents,
        'timestamp': datetime.now().isoformat()
    })


def _simulate_coordination(scenario_id: str, parameters: dict):
    """Simulate coordination messages between agents"""
    scenario = scenarios_store[scenario_id]
    messages = []

    # Message 1: Supply Chain Agent intent
    messages.append({
        'id': f'{scenario_id}-msg-1',
        'timestamp': datetime.now().isoformat(),
        'from': 'Supply Chain Agent',
        'to': ['Financial Agent', 'Facility Agent'],
        'type': 'intent',
        'content': f"Need to order {parameters.get('required_quantity', 1000)} units of {parameters.get('item', 'PPE')} - current stock critical"
    })

    # Message 2: Financial Agent constraint
    messages.append({
        'id': f'{scenario_id}-msg-2',
        'timestamp': datetime.now().isoformat(),
        'from': 'Financial Agent',
        'to': ['Coordinator'],
        'type': 'constraint',
        'content': f"Budget remaining: ₹{parameters.get('budget_remaining', 166000):,} (can afford {parameters.get('required_quantity', 1000)} units)"
    })

    # Message 3: Facility Agent constraint
    messages.append({
        'id': f'{scenario_id}-msg-3',
        'timestamp': datetime.now().isoformat(),
        'from': 'Facility Agent',
        'to': ['Coordinator'],
        'type': 'constraint',
        'content': f"Storage available: {parameters.get('storage_capacity_available', 800)} units (limiting factor)"
    })

    # Message 4: Supply Chain proposal
    storage_limit = parameters.get('storage_capacity_available', 800)
    price_per_unit = parameters.get('price_per_unit', 166.0)
    total_cost = storage_limit * price_per_unit

    messages.append({
        'id': f'{scenario_id}-msg-4',
        'timestamp': datetime.now().isoformat(),
        'from': 'Supply Chain Agent',
        'to': ['Financial Agent', 'Facility Agent'],
        'type': 'proposal',
        'content': f"Propose ordering {storage_limit} units for ₹{total_cost:,} (constrained by storage)"
    })

    # Message 5: Financial acceptance
    messages.append({
        'id': f'{scenario_id}-msg-5',
        'timestamp': datetime.now().isoformat(),
        'from': 'Financial Agent',
        'to': ['Coordinator'],
        'type': 'accept',
        'content': f"Approved: ₹{total_cost:,} within budget"
    })

    # Message 6: Facility acceptance
    messages.append({
        'id': f'{scenario_id}-msg-6',
        'timestamp': datetime.now().isoformat(),
        'from': 'Facility Agent',
        'to': ['Coordinator'],
        'type': 'accept',
        'content': f"Approved: {storage_limit} units fits storage capacity"
    })

    # Message 7: Execution complete
    messages.append({
        'id': f'{scenario_id}-msg-7',
        'timestamp': datetime.now().isoformat(),
        'from': 'Coordinator',
        'to': ['All Agents'],
        'type': 'inform',
        'content': 'Agreement reached and recorded to blockchain ✓'
    })

    scenario['messages'] = messages
    scenario['state'] = 'completed'
    scenario['completed_at'] = datetime.now().isoformat()

    # Record final decision to blockchain
    record_agent_decision(
        agent_id='SC-001',
        agent_name='Supply Chain Agent',
        action_type='PURCHASE_ORDER',
        decision_details={
            'item': parameters.get('item', 'PPE'),
            'quantity': storage_limit,
            'unit_price': price_per_unit,
            'total_cost': total_cost,
            'supplier': parameters.get('supplier', 'MedSupply Corp'),
            'approved_by': ['Financial Agent', 'Facility Agent']
        }
    )


# ============================================================================
# BLOCKCHAIN ENDPOINT ADDITIONS
# ============================================================================

@api_bp.route('/blockchain', methods=['GET'])
def get_blockchain_endpoint():
    """Get complete blockchain"""
    blockchain = get_blockchain()
    transactions = get_transaction_history()

    blocks = []
    for i, block in enumerate(blockchain.chain):
        blocks.append({
            'index': i,
            'timestamp': block.timestamp,
            'data': block.data,
            'hash': block.hash,
            'previous_hash': block.previous_hash,
            'nonce': block.nonce,
            'validator': 'Coordinator-001'
        })

    # Validate chain (returns {"valid": bool, "errors": [...], "blocks_checked": int})
    validation = blockchain.validate_chain()

    return jsonify({
        'success': True,
        'data': {
            'blocks': blocks,
            'length': len(blocks),
            'is_valid': validation.get('valid', True),  # Use 'valid' not 'is_valid'
            'last_validation': datetime.now().isoformat()
        },
        'timestamp': datetime.now().isoformat()
    })

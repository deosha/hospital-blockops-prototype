"""
Real LLM-Powered Coordination Integration

This module integrates the actual multi-agent system with LLM reasoning
into the Flask API, with graceful fallback to demo simulation mode.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Thread

# Import real agents
try:
    from agents.coordinator import AgentCoordinator
    from agents.supply_chain_agent import SupplyChainAgent
    from agents.financial_agent import FinancialAgent
    from agents.facility_agent import FacilityAgent
    from blockchain.manager import record_agent_decision

    REAL_AGENTS_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✓ Real LLM agents loaded successfully")
except Exception as e:
    REAL_AGENTS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠ Real agents not available: {e}. Will use demo mode.")


class CoordinationEngine:
    """
    Manages real LLM coordination with fallback to demo mode
    """

    def __init__(self):
        self.coordinator = None
        self.use_real_agents = False
        self.active_sessions = {}

        # Try to initialize real agents
        if REAL_AGENTS_AVAILABLE:
            try:
                self._initialize_real_agents()
                self.use_real_agents = True
                logger.info("✓ Coordination engine using REAL LLM agents")
            except Exception as e:
                logger.error(f"✗ Failed to initialize real agents: {e}")
                logger.info("→ Falling back to demo simulation mode")
                self.use_real_agents = False
        else:
            logger.info("→ Using demo simulation mode")

    def _initialize_real_agents(self):
        """Initialize the real multi-agent system"""
        # Check for OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")

        # Create coordinator
        self.coordinator = AgentCoordinator(
            timeout_seconds=60,  # 1 minute timeout
            max_negotiation_rounds=3
        )

        # Create agents (they will use OPENAI_API_KEY from environment)
        supply_agent = SupplyChainAgent(
            name="Supply Chain Agent"
        )

        financial_agent = FinancialAgent(
            name="Financial Agent"
        )

        facility_agent = FacilityAgent(
            name="Facility Agent"
        )

        # Register agents with coordinator
        self.coordinator.register_agent(supply_agent)
        self.coordinator.register_agent(financial_agent)
        self.coordinator.register_agent(facility_agent)

        logger.info("✓ All agents registered with coordinator")

    def start_coordination(
        self,
        scenario_id: str,
        scenario_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Start a coordination scenario

        Returns:
            {
                'session_id': str,
                'using_real_llm': bool,
                'status': 'running' | 'completed' | 'failed',
                'messages': List[Dict],
                'error': Optional[str]
            }
        """

        if self.use_real_agents and self.coordinator:
            return self._run_real_coordination(scenario_id, scenario_type, parameters)
        else:
            return self._run_demo_coordination(scenario_id, scenario_type, parameters)

    def _run_real_coordination(
        self,
        scenario_id: str,
        scenario_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run actual LLM-powered coordination"""
        logger.info(f"[Real LLM] Starting coordination for scenario {scenario_id}")

        # Convert API parameters to coordinator scenario format
        scenario = {
            'initiator': 'Supply Chain Agent',
            'intent': f"Order {parameters.get('required_quantity', 1000)} units of {parameters.get('item', 'PPE')}",
            'participants': ['Supply Chain Agent', 'Financial Agent', 'Facility Agent'],
            'context': {
                'item': parameters.get('item', 'PPE Masks N95'),
                'current_stock': parameters.get('current_stock', 200),
                'required_quantity': parameters.get('required_quantity', 1000),
                'price_per_unit': parameters.get('price_per_unit', 166.0),
                'budget_remaining': parameters.get('budget_remaining', 166000),
                'storage_available': parameters.get('storage_capacity_available', 800),
                'supplier': parameters.get('supplier', 'MedSupply Corp')
            }
        }

        # Store session info
        session_info = {
            'scenario_id': scenario_id,
            'status': 'running',
            'using_real_llm': True,
            'started_at': datetime.now().isoformat(),
            'messages': [],
            'error': None,
            'agent_states': {
                'Supply Chain Agent': 'idle',
                'Financial Agent': 'idle',
                'Facility Agent': 'idle'
            },
            'current_step': 'Starting...'
        }
        self.active_sessions[scenario_id] = session_info

        # Run coordination in background thread
        def run_async():
            try:
                logger.info("[Real LLM] Executing coordination protocol...")

                # Create a callback to update messages in real-time
                def message_callback(msg):
                    """Called by coordinator when a new message is created"""
                    try:
                        formatted_msg = {
                            'id': msg.message_id,
                            'timestamp': msg.timestamp,
                            'from': msg.sender,
                            'to': msg.recipients,
                            'type': msg.message_type.value,
                            'content': self._format_message_content(msg.content)
                        }
                        session_info['messages'].append(formatted_msg)
                        logger.info(f"[Real LLM] 📬 Message added: {msg.message_type.value} from {msg.sender}")

                        # Update agent states based on message type
                        if msg.message_type.value == 'query' and msg.recipients:
                            # Agent is being queried - set to thinking
                            for agent_name in msg.recipients:
                                if agent_name in session_info['agent_states']:
                                    session_info['agent_states'][agent_name] = 'thinking'
                        elif msg.message_type.value in ['constraint', 'proposal', 'accept', 'reject', 'critique']:
                            # Agent responded - set to negotiating
                            if msg.sender in session_info['agent_states']:
                                session_info['agent_states'][msg.sender] = 'negotiating'
                        elif msg.message_type.value == 'inform' and msg.sender == 'COORDINATOR':
                            # Check if this is execution phase
                            if 'executed' in msg.content or 'Agreement reached' in self._format_message_content(msg.content):
                                # Set all agents to executing
                                for agent_name in session_info['agent_states']:
                                    session_info['agent_states'][agent_name] = 'executing'
                    except Exception as e:
                        logger.error(f"[Real LLM] ✗ Failed to add message: {e}")

                # Run coordination with callback
                session = self.coordinator.run_coordination(scenario, message_callback=message_callback)

                logger.info(f"[Real LLM] ✓ Coordination completed with {len(session_info['messages'])} messages")

                # Update session - KEEP IN ACTIVE_SESSIONS so messages persist
                # Messages are already added via callback, no need to convert again
                session_info['status'] = 'completed' if session.state.value == 'completed' else 'failed'
                session_info['completed_at'] = datetime.now().isoformat()
                session_info['final_proposal'] = session.final_proposal
                session_info['agreement'] = session.agreement
                session_info['blockchain_record'] = session.blockchain_record

                # Set all agents back to idle after coordination
                for agent_name in session_info['agent_states']:
                    session_info['agent_states'][agent_name] = 'idle'

                logger.info(f"[Real LLM] ✓ Session updated with {len(session_info['messages'])} messages - session will persist for API access")

                # Record to blockchain if successful
                if session.state.value == 'completed' and session.final_proposal:
                    self._record_to_blockchain(session, parameters)

                logger.info(f"[Real LLM] ✓ Coordination completed: {session.state.value}")

            except Exception as e:
                logger.error(f"[Real LLM] ✗ Coordination failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
                session_info['status'] = 'failed'
                session_info['error'] = str(e)
                session_info['completed_at'] = datetime.now().isoformat()

        # Start async execution
        thread = Thread(target=run_async, daemon=True)
        thread.start()

        return {
            'session_id': scenario_id,
            'using_real_llm': True,
            'status': 'running',
            'messages': [],
            'info': 'Real LLM coordination in progress. Poll for updates.'
        }

    def _run_demo_coordination(
        self,
        scenario_id: str,
        scenario_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run fast demo simulation (fallback mode)"""
        logger.info(f"[Demo Mode] Starting simulation for scenario {scenario_id}")

        messages = []

        # Generate demo messages
        messages.append({
            'id': f'{scenario_id}-msg-1',
            'timestamp': datetime.now().isoformat(),
            'from': 'Supply Chain Agent',
            'to': ['Financial Agent', 'Facility Agent'],
            'type': 'intent',
            'content': f"Need to order {parameters.get('required_quantity', 1000)} units of {parameters.get('item', 'PPE')} - current stock critical"
        })

        messages.append({
            'id': f'{scenario_id}-msg-2',
            'timestamp': datetime.now().isoformat(),
            'from': 'Financial Agent',
            'to': ['Coordinator'],
            'type': 'constraint',
            'content': f"Budget remaining: ₹{parameters.get('budget_remaining', 166000):,} (can afford {parameters.get('required_quantity', 1000)} units)"
        })

        messages.append({
            'id': f'{scenario_id}-msg-3',
            'timestamp': datetime.now().isoformat(),
            'from': 'Facility Agent',
            'to': ['Coordinator'],
            'type': 'constraint',
            'content': f"Storage available: {parameters.get('storage_capacity_available', 800)} units (limiting factor)"
        })

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

        messages.append({
            'id': f'{scenario_id}-msg-5',
            'timestamp': datetime.now().isoformat(),
            'from': 'Financial Agent',
            'to': ['Coordinator'],
            'type': 'accept',
            'content': f"Approved: ₹{total_cost:,} within budget"
        })

        messages.append({
            'id': f'{scenario_id}-msg-6',
            'timestamp': datetime.now().isoformat(),
            'from': 'Facility Agent',
            'to': ['Coordinator'],
            'type': 'accept',
            'content': f"Approved: {storage_limit} units fits storage capacity"
        })

        messages.append({
            'id': f'{scenario_id}-msg-7',
            'timestamp': datetime.now().isoformat(),
            'from': 'Coordinator',
            'to': ['All Agents'],
            'type': 'inform',
            'content': 'Agreement reached and recorded to blockchain ✓'
        })

        # Store session
        session_info = {
            'scenario_id': scenario_id,
            'status': 'completed',
            'using_real_llm': False,
            'started_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat(),
            'messages': messages,
            'error': None
        }
        self.active_sessions[scenario_id] = session_info

        # Record to blockchain
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
                'approved_by': ['Financial Agent', 'Facility Agent'],
                'mode': 'demo_simulation'
            }
        )

        logger.info(f"[Demo Mode] ✓ Simulation completed instantly")

        return {
            'session_id': scenario_id,
            'using_real_llm': False,
            'status': 'completed',
            'messages': messages,
            'info': 'Demo simulation mode (instant results)'
        }

    def get_session_status(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a coordination session"""
        return self.active_sessions.get(scenario_id)

    def get_session_messages(self, scenario_id: str) -> list:
        """Get messages from a coordination session"""
        session = self.active_sessions.get(scenario_id)
        if session:
            return session.get('messages', [])
        return []

    def _format_message_content(self, content: Dict[str, Any]) -> str:
        """Format message content for display"""
        import json

        # Extract the most relevant information from content dict
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            # Try to extract a human-readable summary
            if 'description' in content:
                return content['description']
            elif 'text' in content:
                return content['text']
            elif 'message' in content:
                return content['message']
            else:
                # Format as pretty JSON for better display
                try:
                    return json.dumps(content, indent=2)
                except:
                    return str(content)
        return str(content)

    def _record_to_blockchain(self, session, parameters):
        """Record successful coordination to blockchain"""
        try:
            if session.final_proposal:
                record_agent_decision(
                    agent_id='COORD-001',
                    agent_name='Coordinator',
                    action_type='COORDINATED_DECISION',
                    decision_details={
                        'session_id': session.session_id,
                        'proposal': session.final_proposal,
                        'agreement': session.agreement,
                        'participants': session.participants,
                        'rounds': len(session.negotiation_rounds),
                        'mode': 'real_llm_coordination'
                    }
                )
                logger.info("✓ Coordination recorded to blockchain")
        except Exception as e:
            logger.error(f"✗ Failed to record to blockchain: {e}")


# Global coordination engine instance
_coordination_engine = None

def get_coordination_engine() -> CoordinationEngine:
    """Get or create the global coordination engine"""
    global _coordination_engine
    if _coordination_engine is None:
        _coordination_engine = CoordinationEngine()
    return _coordination_engine

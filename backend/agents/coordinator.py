"""
Multi-Agent Coordination System for Hospital BlockOps

Orchestrates negotiation between agents using FIPA-ACL inspired message passing
and an 8-step negotiation protocol based on the research paper.
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
from threading import Lock


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class MessageType(Enum):
    """FIPA-ACL inspired message types for agent communication"""
    INTENT = "intent"  # "I need to order supplies"
    CONSTRAINT = "constraint"  # "Budget limit is $X"
    PROPOSAL = "proposal"  # "I propose ordering Y units at $Z"
    CRITIQUE = "critique"  # "Proposal exceeds budget by $W"
    ACCEPT = "accept"  # "Proposal approved"
    REJECT = "reject"  # "Proposal rejected because..."
    QUERY = "query"  # "What is your constraint?"
    INFORM = "inform"  # "My constraint is X"


class CoordinationState(Enum):
    """State machine for coordination process"""
    INITIATED = "initiated"
    COLLECTING_CONSTRAINTS = "collecting_constraints"
    GENERATING_PROPOSALS = "generating_proposals"
    NEGOTIATING = "negotiating"
    VALIDATING = "validating"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class Message:
    """Agent communication message"""
    message_id: str
    timestamp: str
    sender: str
    recipients: List[str]
    message_type: MessageType
    content: Dict[str, Any]
    in_reply_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            **asdict(self),
            'message_type': self.message_type.value
        }


@dataclass
class NegotiationRound:
    """Single round of negotiation"""
    round_number: int
    proposal: Dict[str, Any]
    critiques: List[Dict[str, Any]]
    timestamp: str
    duration_seconds: float


@dataclass
class CoordinationSession:
    """Complete coordination session with full history"""
    session_id: str
    scenario: Dict[str, Any]
    initiator: str
    participants: List[str]
    state: CoordinationState
    started_at: str
    completed_at: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    negotiation_rounds: List[NegotiationRound] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    final_proposal: Optional[Dict[str, Any]] = None
    agreement: Optional[Dict[str, Any]] = None
    blockchain_record: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'session_id': self.session_id,
            'scenario': self.scenario,
            'initiator': self.initiator,
            'participants': self.participants,
            'state': self.state.value,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'messages': [msg.to_dict() for msg in self.messages],
            'negotiation_rounds': [asdict(round) for round in self.negotiation_rounds],
            'constraints': self.constraints,
            'final_proposal': self.final_proposal,
            'agreement': self.agreement,
            'blockchain_record': self.blockchain_record,
            'error': self.error
        }


class AgentCoordinator:
    """
    Multi-agent coordination system implementing 8-step negotiation protocol.

    The coordination process follows these steps:
    1. Initiate negotiation (initiator declares intent)
    2. Broadcast intent (inform relevant agents)
    3. Collect constraints (gather limitations from all agents)
    4. Generate proposals (initiator creates proposals)
    5. Evaluate proposals (agents critique and provide feedback)
    6. Refine proposals (iterative improvement, max 3 rounds)
    7. Validate agreement (smart contract validation)
    8. Execute coordinated action (blockchain recording)
    """

    def __init__(self, timeout_seconds: int = 30, max_negotiation_rounds: int = 3):
        """
        Initialize coordinator.

        Args:
            timeout_seconds: Maximum time for coordination (default: 30s)
            max_negotiation_rounds: Maximum negotiation rounds (default: 3)
        """
        self.agents: Dict[str, Any] = {}
        self.sessions: Dict[str, CoordinationSession] = {}
        self.timeout_seconds = timeout_seconds
        self.max_negotiation_rounds = max_negotiation_rounds
        self.message_counter = 0
        self.session_counter = 0
        self._lock = Lock()

        self.logger = logging.getLogger("AgentCoordinator")
        self.logger.info(
            f"Coordinator initialized (timeout: {timeout_seconds}s, "
            f"max rounds: {max_negotiation_rounds})"
        )

    # =========================================================================
    # Agent Management
    # =========================================================================

    def register_agent(self, agent: Any) -> None:
        """
        Register an agent with the coordinator.

        Args:
            agent: Agent instance (must have .name and .role attributes)
        """
        with self._lock:
            self.agents[agent.name] = agent
            self.logger.info(f"Registered agent: {agent.name} ({agent.role})")

    def get_agent(self, name: str) -> Optional[Any]:
        """Get agent by name"""
        return self.agents.get(name)

    def list_agents(self) -> List[Dict[str, str]]:
        """List all registered agents"""
        return [
            {"name": name, "role": agent.role}
            for name, agent in self.agents.items()
        ]

    # =========================================================================
    # Message Passing
    # =========================================================================

    def _create_message(
        self,
        sender: str,
        recipients: List[str],
        message_type: MessageType,
        content: Dict[str, Any],
        in_reply_to: Optional[str] = None
    ) -> Message:
        """Create a new message with auto-incrementing ID"""
        with self._lock:
            self.message_counter += 1
            message_id = f"MSG-{self.message_counter:05d}"

        return Message(
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            sender=sender,
            recipients=recipients,
            message_type=message_type,
            content=content,
            in_reply_to=in_reply_to
        )

    def broadcast_message(
        self,
        session: CoordinationSession,
        sender: str,
        recipients: List[str],
        message_type: MessageType,
        content: Dict[str, Any],
        in_reply_to: Optional[str] = None
    ) -> Message:
        """
        Broadcast message to agents and log in session.

        Args:
            session: Current coordination session
            sender: Sender agent name
            recipients: List of recipient agent names
            message_type: Type of message
            content: Message content
            in_reply_to: ID of message being replied to

        Returns:
            Created message
        """
        message = self._create_message(
            sender=sender,
            recipients=recipients,
            message_type=message_type,
            content=content,
            in_reply_to=in_reply_to
        )

        session.messages.append(message)

        # Call the callback if provided (for real-time message updates)
        if hasattr(self, 'message_callback') and self.message_callback:
            try:
                self.message_callback(message)
            except Exception as e:
                self.logger.error(f"Message callback error: {e}")

        self.logger.info(
            f"[{session.session_id}] {message_type.value.upper()}: "
            f"{sender} → {', '.join(recipients)}"
        )
        self.logger.debug(f"  Content: {content}")

        return message

    # =========================================================================
    # 8-Step Negotiation Protocol
    # =========================================================================

    def run_coordination(self, scenario: Dict[str, Any], message_callback=None) -> CoordinationSession:
        """
        Execute full coordination process for a scenario.

        Args:
            scenario: Dict with keys:
                - initiator: Agent name that starts negotiation
                - intent: What the initiator wants to do
                - participants: List of agent names to involve
                - context: Additional scenario context
            message_callback: Optional callback function(message) called when messages are created

        Returns:
            Completed coordination session
        """
        # Store callback for broadcast_message to use
        self.message_callback = message_callback

        # Create session
        with self._lock:
            self.session_counter += 1
            session_id = f"COORD-{self.session_counter:05d}"

        session = CoordinationSession(
            session_id=session_id,
            scenario=scenario,
            initiator=scenario['initiator'],
            participants=scenario['participants'],
            state=CoordinationState.INITIATED,
            started_at=datetime.now().isoformat()
        )

        self.sessions[session_id] = session
        start_time = time.time()

        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"Starting Coordination Session: {session_id}")
        self.logger.info(f"Scenario: {scenario.get('intent', 'Unknown')}")
        self.logger.info(f"{'='*80}\n")

        try:
            # Step 1: Initiate negotiation
            self._step1_initiate_negotiation(session, scenario)

            # Check timeout
            if self._check_timeout(session, start_time):
                return session

            # Step 2: Broadcast intent
            self._step2_broadcast_intent(session, scenario)

            if self._check_timeout(session, start_time):
                return session

            # Step 3: Collect constraints
            self._step3_collect_constraints(session)

            if self._check_timeout(session, start_time):
                return session

            # Step 4: Generate proposals
            proposals = self._step4_generate_proposals(session, scenario)

            if self._check_timeout(session, start_time):
                return session

            # Steps 5-6: Evaluate and refine (iterative negotiation)
            final_proposal = self._step5_6_negotiate(session, proposals)

            if self._check_timeout(session, start_time):
                return session

            # Step 7: Validate agreement
            validation_result = self._step7_validate_agreement(session, final_proposal)

            if self._check_timeout(session, start_time):
                return session

            # Step 8: Execute coordinated action
            if validation_result['valid']:
                self._step8_execute_action(session, final_proposal)
            else:
                session.state = CoordinationState.FAILED
                session.error = f"Validation failed: {validation_result['reason']}"

            # Mark as completed
            session.completed_at = datetime.now().isoformat()
            duration = time.time() - start_time

            if session.state != CoordinationState.FAILED:
                session.state = CoordinationState.COMPLETED
                self.logger.info(f"\n{'='*80}")
                self.logger.info(f"✅ Coordination Completed: {session_id}")
                self.logger.info(f"Duration: {duration:.2f}s")
                self.logger.info(f"{'='*80}\n")
            else:
                self.logger.error(f"\n{'='*80}")
                self.logger.error(f"❌ Coordination Failed: {session_id}")
                self.logger.error(f"Error: {session.error}")
                self.logger.error(f"{'='*80}\n")

        except Exception as e:
            session.state = CoordinationState.FAILED
            session.error = str(e)
            session.completed_at = datetime.now().isoformat()
            self.logger.error(f"Coordination error: {e}", exc_info=True)

        return session

    def _check_timeout(self, session: CoordinationSession, start_time: float) -> bool:
        """Check if coordination has timed out"""
        elapsed = time.time() - start_time
        if elapsed > self.timeout_seconds:
            session.state = CoordinationState.TIMEOUT
            session.error = f"Coordination timed out after {elapsed:.1f}s"
            session.completed_at = datetime.now().isoformat()
            self.logger.warning(f"⏰ Timeout: {session.session_id}")
            return True
        return False

    def _step1_initiate_negotiation(
        self,
        session: CoordinationSession,
        scenario: Dict[str, Any]
    ) -> None:
        """Step 1: Initiator declares intent to coordinate"""
        self.logger.info(f"[{session.session_id}] STEP 1: Initiate Negotiation")

        session.state = CoordinationState.INITIATED

        # Initiator sends INTENT message
        self.broadcast_message(
            session=session,
            sender=session.initiator,
            recipients=session.participants,
            message_type=MessageType.INTENT,
            content={
                "intent": scenario['intent'],
                "context": scenario.get('context', {}),
                "requires_coordination": True,
                "timestamp": datetime.now().isoformat()
            }
        )

    def _step2_broadcast_intent(
        self,
        session: CoordinationSession,
        scenario: Dict[str, Any]
    ) -> None:
        """Step 2: Broadcast intent to all relevant agents"""
        self.logger.info(f"[{session.session_id}] STEP 2: Broadcast Intent")

        # Coordinator acknowledges and broadcasts
        self.broadcast_message(
            session=session,
            sender="COORDINATOR",
            recipients=session.participants,
            message_type=MessageType.INFORM,
            content={
                "announcement": f"Coordination session {session.session_id} initiated",
                "initiator": session.initiator,
                "intent": scenario['intent'],
                "please_provide": "constraints"
            }
        )

    def _step3_collect_constraints(self, session: CoordinationSession) -> None:
        """Step 3: Collect constraints from all participating agents"""
        self.logger.info(f"[{session.session_id}] STEP 3: Collect Constraints")

        session.state = CoordinationState.COLLECTING_CONSTRAINTS
        constraints = {}

        for agent_name in session.participants:
            agent = self.get_agent(agent_name)
            if not agent:
                self.logger.warning(f"Agent not found: {agent_name}")
                continue

            # Query agent for constraints
            self.broadcast_message(
                session=session,
                sender="COORDINATOR",
                recipients=[agent_name],
                message_type=MessageType.QUERY,
                content={"query": "What are your constraints for this coordination?"}
            )

            # Get constraints based on agent type
            agent_constraints = self._get_agent_constraints(agent, session.scenario)

            # Agent responds with constraints
            self.broadcast_message(
                session=session,
                sender=agent_name,
                recipients=["COORDINATOR"],
                message_type=MessageType.CONSTRAINT,
                content=agent_constraints
            )

            constraints[agent_name] = agent_constraints

        session.constraints = constraints
        self.logger.info(f"Collected constraints from {len(constraints)} agents")

    def _get_agent_constraints(
        self,
        agent: Any,
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract constraints from an agent using LLM reasoning"""
        context = scenario.get('context', {})

        # Use agent's LLM reasoning to get constraints
        try:
            perception = agent.perceive(context)

            prompt = f"""As a {agent.role} agent, analyze the following scenario and provide your constraints.

Scenario: {scenario.get('intent', 'Unknown scenario')}
Context: {perception}

Provide your constraints as a JSON object. Include relevant limits, policies, and requirements.
Return ONLY valid JSON, no markdown or explanation."""

            constraints = agent.reason(
                context=perception,
                prompt_template=prompt,
                temperature=0.3,  # Lower temperature for more consistent constraints
                max_tokens=500
            )

            self.logger.info(f"[LLM] {agent.name} provided constraints via GPT")
            return constraints

        except Exception as e:
            self.logger.warning(f"[LLM] Failed to get constraints from {agent.name}: {e}, using fallback")

            # Fallback to knowledge base
            if "supply" in agent.role.lower():
                return {
                    "type": "supply_chain",
                    "reorder_point": context.get('reorder_point', 500),
                    "min_order_quantity": agent.knowledge_base['reorder_policies']['min_order_quantity'],
                    "max_order_quantity": agent.knowledge_base['reorder_policies']['max_order_quantity'],
                    "current_stock": context.get('current_stock', 0),
                    "urgency": context.get('urgency', 'medium')
                }
            elif "financial" in agent.role.lower():
                return {
                    "type": "financial",
                    "budget_remaining": context.get('budget_remaining', 100000),
                    "autonomous_limit": agent.knowledge_base['budget_policies']['autonomous_approval_limit'],
                    "emergency_reserve": agent.knowledge_base['budget_policies']['emergency_reserve'],
                    "risk_tolerance": "medium"
                }
            elif "facility" in agent.role.lower():
                return {
                    "type": "facility",
                    "storage_available": context.get('storage_available', 1000),
                    "max_storage": 5000,
                    "current_utilization": 0.65
                }
            else:
                return {"type": "unknown", "available": True}

    def _step4_generate_proposals(
        self,
        session: CoordinationSession,
        scenario: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Step 4: Initiator generates proposals based on constraints"""
        self.logger.info(f"[{session.session_id}] STEP 4: Generate Proposals")

        session.state = CoordinationState.GENERATING_PROPOSALS

        initiator_agent = self.get_agent(session.initiator)
        if not initiator_agent:
            raise ValueError(f"Initiator agent not found: {session.initiator}")

        # Get constraints to consider
        constraints = session.constraints
        context = scenario.get('context', {})

        # Generate proposal using initiator agent's decision-making
        # (In this case, Supply Chain Agent)
        proposal = self._generate_coordinated_proposal(
            initiator_agent,
            context,
            constraints
        )

        proposals = [proposal]

        # Broadcast proposal
        self.broadcast_message(
            session=session,
            sender=session.initiator,
            recipients=[a for a in session.participants if a != session.initiator],
            message_type=MessageType.PROPOSAL,
            content=proposal
        )

        return proposals

    def _generate_coordinated_proposal(
        self,
        initiator: Any,
        context: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate proposal using LLM reasoning"""
        try:
            # Use LLM to generate coordinated proposal
            prompt = f"""As a {initiator.role} agent, generate a procurement proposal that satisfies all agent constraints.

Context:
{context}

Constraints from all agents:
{constraints}

Generate a proposal as JSON with these fields:
- item_name: the item being ordered
- proposed_quantity: how many units to order
- proposed_cost: total cost
- price_per_unit: unit price
- reasoning: explanation of the proposal
- constraints_satisfied: dict with budget and storage booleans

Ensure the proposal respects all constraints. Return ONLY valid JSON."""

            perception = initiator.perceive(context)
            proposal = initiator.reason(
                context=perception,
                prompt_template=prompt,
                temperature=0.5,
                max_tokens=800
            )

            self.logger.info(f"[LLM] {initiator.name} generated proposal via GPT")
            return proposal

        except Exception as e:
            self.logger.warning(f"[LLM] Failed to generate proposal from {initiator.name}: {e}, using fallback")

            # Fallback to rule-based logic
            financial_constraints = next(
                (c for c in constraints.values() if c.get('type') == 'financial'),
                {}
            )
            facility_constraints = next(
                (c for c in constraints.values() if c.get('type') == 'facility'),
                {}
            )

            budget_remaining = financial_constraints.get('budget_remaining', 100000)
            storage_available = facility_constraints.get('storage_available', 1000)
            price_per_unit = context.get('price_per_unit', 2.00)

            required_quantity = context.get('required_quantity', 1000)
            budget_limit_qty = int(budget_remaining / price_per_unit)
            storage_limit_qty = storage_available

            proposed_quantity = min(required_quantity, budget_limit_qty, storage_limit_qty)
            proposed_cost = proposed_quantity * price_per_unit

            return {
                "item_name": context.get('item_name', 'Unknown Item'),
                "proposed_quantity": proposed_quantity,
                "proposed_cost": proposed_cost,
                "price_per_unit": price_per_unit,
                "reasoning": (
                    f"Proposed {proposed_quantity} units (original: {required_quantity}) "
                    f"constrained by budget (max: {budget_limit_qty}) "
                    f"and storage (max: {storage_limit_qty})"
                ),
                "constraints_satisfied": {
                    "budget": proposed_cost <= budget_remaining,
                    "storage": proposed_quantity <= storage_available
                }
            }

    def _step5_6_negotiate(
        self,
        session: CoordinationSession,
        proposals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Steps 5-6: Evaluate proposals and refine iteratively"""
        self.logger.info(f"[{session.session_id}] STEPS 5-6: Negotiate")

        session.state = CoordinationState.NEGOTIATING

        current_proposal = proposals[0]
        round_num = 0

        for round_num in range(1, self.max_negotiation_rounds + 1):
            round_start = time.time()

            self.logger.info(f"  Negotiation Round {round_num}/{self.max_negotiation_rounds}")

            # Step 5: Evaluate proposal
            critiques = self._step5_evaluate_proposal(session, current_proposal)

            # Check if everyone accepts
            all_accept = all(c['decision'] == 'accept' for c in critiques)

            if all_accept:
                self.logger.info(f"  ✅ Proposal accepted in round {round_num}")
                round_duration = time.time() - round_start

                session.negotiation_rounds.append(NegotiationRound(
                    round_number=round_num,
                    proposal=current_proposal,
                    critiques=critiques,
                    timestamp=datetime.now().isoformat(),
                    duration_seconds=round_duration
                ))

                session.final_proposal = current_proposal
                return current_proposal

            # Step 6: Refine proposal based on critiques
            if round_num < self.max_negotiation_rounds:
                self.logger.info(f"  🔄 Refining proposal based on {len(critiques)} critiques")
                current_proposal = self._step6_refine_proposal(
                    session,
                    current_proposal,
                    critiques
                )

            round_duration = time.time() - round_start
            session.negotiation_rounds.append(NegotiationRound(
                round_number=round_num,
                proposal=current_proposal,
                critiques=critiques,
                timestamp=datetime.now().isoformat(),
                duration_seconds=round_duration
            ))

        # Max rounds reached - use best proposal
        self.logger.warning(
            f"  ⚠️ Max negotiation rounds reached. Using current proposal."
        )
        session.final_proposal = current_proposal
        return current_proposal

    def _step5_evaluate_proposal(
        self,
        session: CoordinationSession,
        proposal: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Step 5: Agents evaluate and critique the proposal"""
        critiques = []

        for agent_name in session.participants:
            if agent_name == session.initiator:
                continue  # Skip initiator

            agent = self.get_agent(agent_name)
            if not agent:
                continue

            # Get agent's critique
            critique = self._agent_critique_proposal(agent, proposal, session)

            # Send critique message
            message_type = MessageType.ACCEPT if critique['decision'] == 'accept' else MessageType.CRITIQUE

            self.broadcast_message(
                session=session,
                sender=agent_name,
                recipients=[session.initiator, "COORDINATOR"],
                message_type=message_type,
                content=critique
            )

            critiques.append(critique)

        return critiques

    def _agent_critique_proposal(
        self,
        agent: Any,
        proposal: Dict[str, Any],
        session: CoordinationSession
    ) -> Dict[str, Any]:
        """Agent evaluates a proposal using LLM reasoning"""
        agent_name = agent.name
        constraints = session.constraints.get(agent_name, {})

        try:
            # Use LLM to evaluate proposal
            prompt = f"""As a {agent.role} agent, evaluate the following procurement proposal against your constraints.

Proposal:
{proposal}

Your Constraints:
{constraints}

Decide whether to accept or reject this proposal. Return JSON with:
- agent: your agent name
- decision: "accept" or "reject"
- reasoning: explanation for your decision
- confidence: number between 0 and 1
- suggested_adjustment: (optional) if rejecting, suggest changes

Return ONLY valid JSON."""

            perception = agent.perceive({"proposal": proposal, "constraints": constraints})
            critique = agent.reason(
                context=perception,
                prompt_template=prompt,
                temperature=0.3,  # Lower for more consistent evaluation
                max_tokens=600
            )

            # Ensure agent field is set
            if 'agent' not in critique:
                critique['agent'] = agent_name

            self.logger.info(f"[LLM] {agent_name} evaluated proposal via GPT: {critique.get('decision')}")
            return critique

        except Exception as e:
            self.logger.warning(f"[LLM] Failed to get critique from {agent_name}: {e}, using fallback")

            # Fallback to rule-based logic
            if constraints.get('type') == 'financial':
                proposed_cost = proposal.get('proposed_cost', 0)
                budget_remaining = constraints.get('budget_remaining', 100000)

                if proposed_cost <= budget_remaining:
                    return {
                        "agent": agent_name,
                        "decision": "accept",
                        "reasoning": f"Cost ${proposed_cost:.2f} within budget ${budget_remaining:.2f}",
                        "confidence": 0.95
                    }
                else:
                    return {
                        "agent": agent_name,
                        "decision": "reject",
                        "reasoning": f"Cost ${proposed_cost:.2f} exceeds budget ${budget_remaining:.2f}",
                        "suggested_adjustment": {
                            "max_cost": budget_remaining,
                            "max_quantity": int(budget_remaining / proposal.get('price_per_unit', 1))
                        },
                        "confidence": 0.90
                    }

            elif constraints.get('type') == 'facility':
                proposed_quantity = proposal.get('proposed_quantity', 0)
                storage_available = constraints.get('storage_available', 1000)

                if proposed_quantity <= storage_available:
                    return {
                        "agent": agent_name,
                        "decision": "accept",
                        "reasoning": f"Quantity {proposed_quantity} fits in storage {storage_available}",
                        "confidence": 0.93
                    }
                else:
                    return {
                        "agent": agent_name,
                        "decision": "reject",
                        "reasoning": f"Quantity {proposed_quantity} exceeds storage {storage_available}",
                        "suggested_adjustment": {
                            "max_quantity": storage_available
                        },
                        "confidence": 0.92
                    }

            # Default: accept
            else:
                return {
                    "agent": agent_name,
                    "decision": "accept",
                    "reasoning": "No constraints violated",
                    "confidence": 0.85
                }

    def _step6_refine_proposal(
        self,
        session: CoordinationSession,
        current_proposal: Dict[str, Any],
        critiques: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Step 6: Refine proposal based on critiques"""
        # Find the most restrictive constraint
        max_quantity = current_proposal['proposed_quantity']
        max_cost = current_proposal['proposed_cost']

        for critique in critiques:
            if critique['decision'] == 'reject' and 'suggested_adjustment' in critique:
                adjustment = critique['suggested_adjustment']

                if 'max_quantity' in adjustment:
                    max_quantity = min(max_quantity, adjustment['max_quantity'])

                if 'max_cost' in adjustment:
                    max_cost = min(max_cost, adjustment['max_cost'])

        # Recalculate based on constraints
        price_per_unit = current_proposal['price_per_unit']
        quantity_from_cost = int(max_cost / price_per_unit)
        refined_quantity = min(max_quantity, quantity_from_cost)
        refined_cost = refined_quantity * price_per_unit

        refined_proposal = {
            **current_proposal,
            "proposed_quantity": refined_quantity,
            "proposed_cost": refined_cost,
            "reasoning": f"Refined to {refined_quantity} units based on agent feedback"
        }

        # Broadcast refined proposal
        self.broadcast_message(
            session=session,
            sender=session.initiator,
            recipients=[a for a in session.participants if a != session.initiator],
            message_type=MessageType.PROPOSAL,
            content=refined_proposal
        )

        return refined_proposal

    def _step7_validate_agreement(
        self,
        session: CoordinationSession,
        proposal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 7: Validate agreement via smart contract"""
        self.logger.info(f"[{session.session_id}] STEP 7: Validate Agreement")

        session.state = CoordinationState.VALIDATING

        # Simulate smart contract validation
        # In real system, this would call blockchain smart contract
        validation_result = {
            "valid": True,
            "checks": {},
            "timestamp": datetime.now().isoformat()
        }

        # Budget check
        financial_constraint = next(
            (c for c in session.constraints.values() if c.get('type') == 'financial'),
            {}
        )
        if financial_constraint:
            budget_ok = proposal['proposed_cost'] <= financial_constraint['budget_remaining']
            validation_result['checks']['budget'] = {
                "valid": budget_ok,
                "reason": f"Cost ${proposal['proposed_cost']:.2f} vs Budget ${financial_constraint['budget_remaining']:.2f}"
            }
            if not budget_ok:
                validation_result['valid'] = False
                validation_result['reason'] = "Budget constraint violated"

        # Storage check
        facility_constraint = next(
            (c for c in session.constraints.values() if c.get('type') == 'facility'),
            {}
        )
        if facility_constraint:
            storage_ok = proposal['proposed_quantity'] <= facility_constraint['storage_available']
            validation_result['checks']['storage'] = {
                "valid": storage_ok,
                "reason": f"Quantity {proposal['proposed_quantity']} vs Storage {facility_constraint['storage_available']}"
            }
            if not storage_ok:
                validation_result['valid'] = False
                validation_result['reason'] = "Storage constraint violated"

        # Broadcast validation result
        message_type = MessageType.ACCEPT if validation_result['valid'] else MessageType.REJECT

        self.broadcast_message(
            session=session,
            sender="SMART_CONTRACT",
            recipients=session.participants,
            message_type=message_type,
            content=validation_result
        )

        return validation_result

    def _step8_execute_action(
        self,
        session: CoordinationSession,
        proposal: Dict[str, Any]
    ) -> None:
        """Step 8: Execute coordinated action and record to blockchain"""
        self.logger.info(f"[{session.session_id}] STEP 8: Execute Action")

        session.state = CoordinationState.EXECUTING

        # Create agreement
        agreement = {
            "session_id": session.session_id,
            "proposal": proposal,
            "participants": session.participants,
            "constraints_satisfied": session.constraints,
            "timestamp": datetime.now().isoformat(),
            "execution_status": "pending"
        }

        session.agreement = agreement

        # Simulate blockchain recording
        # In real system, this would call blockchain.manager.record_agent_decision
        blockchain_record = {
            "transaction_id": f"TX-{session.session_id}",
            "block_index": len(self.sessions),  # Simulated
            "block_hash": f"hash_{session.session_id}",
            "timestamp": datetime.now().isoformat(),
            "agreement": agreement,
            "recorded": True
        }

        session.blockchain_record = blockchain_record
        agreement['execution_status'] = "completed"

        # Broadcast execution confirmation
        self.broadcast_message(
            session=session,
            sender="COORDINATOR",
            recipients=session.participants,
            message_type=MessageType.INFORM,
            content={
                "status": "executed",
                "agreement": agreement,
                "blockchain": blockchain_record
            }
        )

        self.logger.info(f"✅ Action executed and recorded to blockchain")

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get_session(self, session_id: str) -> Optional[CoordinationSession]:
        """Get coordination session by ID"""
        return self.sessions.get(session_id)

    def get_negotiation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get full message history for a session"""
        session = self.get_session(session_id)
        if not session:
            return []

        return [msg.to_dict() for msg in session.messages]

    def get_current_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of coordination session"""
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "state": session.state.value,
            "participants": session.participants,
            "message_count": len(session.messages),
            "negotiation_rounds": len(session.negotiation_rounds),
            "final_proposal": session.final_proposal,
            "completed": session.completed_at is not None
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all coordination sessions"""
        return [
            {
                "session_id": sid,
                "state": session.state.value,
                "initiator": session.initiator,
                "started_at": session.started_at,
                "completed_at": session.completed_at
            }
            for sid, session in self.sessions.items()
        ]

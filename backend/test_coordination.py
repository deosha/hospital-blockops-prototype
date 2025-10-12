"""
Comprehensive Test Suite for Multi-Agent Coordination System

Tests the 8-step negotiation protocol with realistic scenarios.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add agents to path
sys.path.insert(0, os.path.dirname(__file__))

from agents import (
    SupplyChainAgent,
    FinancialAgent,
    FacilityAgent,
    AgentCoordinator,
    CoordinationState
)


def print_header(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}".center(80))
    print("=" * 80 + "\n")


def print_session_summary(session):
    """Pretty print coordination session summary"""
    print(f"\n{'─' * 80}")
    print(f"📋 Session Summary: {session.session_id}")
    print(f"{'─' * 80}")
    print(f"  State: {session.state.value.upper()}")
    print(f"  Initiator: {session.initiator}")
    print(f"  Participants: {', '.join(session.participants)}")
    print(f"  Started: {session.started_at}")
    print(f"  Completed: {session.completed_at or 'In progress'}")
    print(f"  Messages: {len(session.messages)}")
    print(f"  Negotiation Rounds: {len(session.negotiation_rounds)}")

    if session.final_proposal:
        print(f"\n  Final Proposal:")
        print(f"    Item: {session.final_proposal.get('item_name', 'N/A')}")
        print(f"    Quantity: {session.final_proposal.get('proposed_quantity', 0)} units")
        print(f"    Cost: ${session.final_proposal.get('proposed_cost', 0):,.2f}")

    if session.agreement:
        print(f"\n  ✅ Agreement Reached")
        print(f"    Status: {session.agreement.get('execution_status', 'unknown')}")

    if session.blockchain_record:
        print(f"\n  🔗 Blockchain Record:")
        print(f"    TX ID: {session.blockchain_record.get('transaction_id', 'N/A')}")
        print(f"    Block: #{session.blockchain_record.get('block_index', 'N/A')}")

    if session.error:
        print(f"\n  ❌ Error: {session.error}")

    print(f"{'─' * 80}\n")


def print_negotiation_details(session):
    """Print detailed negotiation history"""
    print(f"\n{'─' * 80}")
    print(f"🔄 Negotiation Details: {session.session_id}")
    print(f"{'─' * 80}\n")

    for round in session.negotiation_rounds:
        print(f"  Round {round.round_number} ({round.duration_seconds:.2f}s):")
        print(f"    Proposal: {round.proposal.get('proposed_quantity', 0)} units "
              f"@ ${round.proposal.get('proposed_cost', 0):,.2f}")

        for critique in round.critiques:
            decision = critique.get('decision', 'unknown')
            agent = critique.get('agent', 'unknown')
            reasoning = critique.get('reasoning', 'N/A')
            symbol = "✅" if decision == "accept" else "❌"
            print(f"      {symbol} {agent}: {reasoning}")

        print()


def print_message_log(session):
    """Print message passing log"""
    print(f"\n{'─' * 80}")
    print(f"💬 Message Log: {session.session_id}")
    print(f"{'─' * 80}\n")

    for msg in session.messages:
        msg_type = msg.message_type.value.upper()
        sender = msg.sender
        recipients = ', '.join(msg.recipients)
        print(f"  [{msg_type}] {sender} → {recipients}")

        # Print key content
        if msg.message_type.value in ['proposal', 'constraint']:
            content_str = json.dumps(msg.content, indent=2)
            # Truncate if too long
            if len(content_str) > 200:
                content_str = content_str[:200] + "..."
            print(f"    {content_str}")

        print()


def test_scenario_1_successful_coordination():
    """
    Test Scenario 1: Successful Coordination

    Supply Chain needs 1000 PPE units
    Financial has $2000 budget remaining
    Facility has storage for 800 units
    Expected: Order 800 units for $1600 (constrained by storage)
    """
    print_header("TEST SCENARIO 1: Successful Coordination")

    print("📋 Scenario Setup:")
    print("  Supply Chain Agent needs to order PPE equipment")
    print("  - Required: 1000 units")
    print("  - Price: $2.00/unit")
    print("  - Current stock: 50 units")
    print("  - Reorder point: 500 units")
    print()
    print("  Financial Agent constraints:")
    print("  - Budget remaining: $2000")
    print("  - Can afford: 1000 units")
    print()
    print("  Facility Agent constraints:")
    print("  - Storage available: 800 units")
    print("  - LIMITING FACTOR")
    print()
    print("  Expected Outcome: Order 800 units for $1600")
    print("  (Constrained by storage capacity)")

    # Initialize coordinator
    coordinator = AgentCoordinator(timeout_seconds=60, max_negotiation_rounds=3)

    # Create and register agents
    sc_agent = SupplyChainAgent(name="SC-001")
    fin_agent = FinancialAgent(name="FIN-001")
    fac_agent = FacilityAgent(name="FAC-001")

    coordinator.register_agent(sc_agent)
    coordinator.register_agent(fin_agent)
    coordinator.register_agent(fac_agent)

    print(f"\n✅ Agents registered: {len(coordinator.list_agents())}")
    for agent_info in coordinator.list_agents():
        print(f"  - {agent_info['name']}: {agent_info['role']}")

    # Define scenario
    scenario = {
        "initiator": "SC-001",
        "intent": "Order PPE equipment to replenish low inventory",
        "participants": ["SC-001", "FIN-001", "FAC-001"],
        "context": {
            "item_name": "PPE Equipment (N95 Masks)",
            "current_stock": 50,
            "reorder_point": 500,
            "required_quantity": 1000,
            "price_per_unit": 2.00,
            "budget_remaining": 2000.00,
            "storage_available": 800,
            "urgency": "high"
        }
    }

    # Run coordination
    print(f"\n🚀 Starting coordination...")
    session = coordinator.run_coordination(scenario)

    # Print results
    print_session_summary(session)
    print_negotiation_details(session)
    print_message_log(session)

    # Validate results
    assert session.state == CoordinationState.COMPLETED, "Should complete successfully"
    assert session.final_proposal is not None, "Should have final proposal"
    assert session.final_proposal['proposed_quantity'] == 800, "Should order 800 units (storage limit)"
    assert session.final_proposal['proposed_cost'] == 1600.00, "Should cost $1600"
    assert session.agreement is not None, "Should have agreement"
    assert session.blockchain_record is not None, "Should record to blockchain"

    print("✅ TEST SCENARIO 1 PASSED\n")
    return session


def test_scenario_2_budget_constraint():
    """
    Test Scenario 2: Budget Constraint

    Supply Chain needs 1000 units
    Financial has $1200 budget remaining
    Facility has storage for 1000 units
    Expected: Order 600 units for $1200 (constrained by budget)
    """
    print_header("TEST SCENARIO 2: Budget Constraint")

    print("📋 Scenario Setup:")
    print("  Supply Chain Agent needs medical supplies")
    print("  - Required: 1000 units")
    print("  - Price: $2.00/unit")
    print()
    print("  Financial Agent constraints:")
    print("  - Budget remaining: $1200")
    print("  - Can afford: 600 units")
    print("  - LIMITING FACTOR")
    print()
    print("  Facility Agent constraints:")
    print("  - Storage available: 1000 units")
    print()
    print("  Expected Outcome: Order 600 units for $1200")
    print("  (Constrained by budget)")

    # Initialize coordinator
    coordinator = AgentCoordinator(timeout_seconds=60, max_negotiation_rounds=3)

    # Create and register agents
    sc_agent = SupplyChainAgent(name="SC-002")
    fin_agent = FinancialAgent(name="FIN-002")
    fac_agent = FacilityAgent(name="FAC-002")

    coordinator.register_agent(sc_agent)
    coordinator.register_agent(fin_agent)
    coordinator.register_agent(fac_agent)

    # Define scenario with tight budget
    scenario = {
        "initiator": "SC-002",
        "intent": "Order medical supplies",
        "participants": ["SC-002", "FIN-002", "FAC-002"],
        "context": {
            "item_name": "Medical Gloves (Boxes)",
            "current_stock": 100,
            "reorder_point": 500,
            "required_quantity": 1000,
            "price_per_unit": 2.00,
            "budget_remaining": 1200.00,  # Budget constraint
            "storage_available": 1000,
            "urgency": "medium"
        }
    }

    # Run coordination
    print(f"\n🚀 Starting coordination...")
    session = coordinator.run_coordination(scenario)

    # Print results
    print_session_summary(session)
    print_negotiation_details(session)

    # Validate results
    assert session.state == CoordinationState.COMPLETED, "Should complete successfully"
    assert session.final_proposal['proposed_quantity'] == 600, "Should order 600 units (budget limit)"
    assert session.final_proposal['proposed_cost'] == 1200.00, "Should cost $1200"

    print("✅ TEST SCENARIO 2 PASSED\n")
    return session


def test_scenario_3_multiple_constraints():
    """
    Test Scenario 3: Multiple Tight Constraints

    Supply Chain needs 2000 units
    Financial has $1500 budget (can afford 750 units)
    Facility has storage for 700 units
    Expected: Order 700 units for $1400 (storage is tightest)
    """
    print_header("TEST SCENARIO 3: Multiple Tight Constraints")

    print("📋 Scenario Setup:")
    print("  Supply Chain Agent needs large order")
    print("  - Required: 2000 units")
    print("  - Price: $2.00/unit")
    print()
    print("  Financial Agent constraints:")
    print("  - Budget remaining: $1500")
    print("  - Can afford: 750 units")
    print()
    print("  Facility Agent constraints:")
    print("  - Storage available: 700 units")
    print("  - TIGHTEST CONSTRAINT")
    print()
    print("  Expected Outcome: Order 700 units for $1400")
    print("  (Constrained by storage, which is tightest)")

    # Initialize coordinator
    coordinator = AgentCoordinator(timeout_seconds=60, max_negotiation_rounds=3)

    # Create and register agents
    sc_agent = SupplyChainAgent(name="SC-003")
    fin_agent = FinancialAgent(name="FIN-003")
    fac_agent = FacilityAgent(name="FAC-003")

    coordinator.register_agent(sc_agent)
    coordinator.register_agent(fin_agent)
    coordinator.register_agent(fac_agent)

    # Define scenario with multiple constraints
    scenario = {
        "initiator": "SC-003",
        "intent": "Order large shipment of supplies",
        "participants": ["SC-003", "FIN-003", "FAC-003"],
        "context": {
            "item_name": "IV Fluid Bags",
            "current_stock": 200,
            "reorder_point": 800,
            "required_quantity": 2000,
            "price_per_unit": 2.00,
            "budget_remaining": 1500.00,  # Can afford 750
            "storage_available": 700,  # Tightest constraint
            "urgency": "high"
        }
    }

    # Run coordination
    print(f"\n🚀 Starting coordination...")
    session = coordinator.run_coordination(scenario)

    # Print results
    print_session_summary(session)
    print_negotiation_details(session)

    # Validate results
    assert session.state == CoordinationState.COMPLETED, "Should complete successfully"
    assert session.final_proposal['proposed_quantity'] == 700, "Should order 700 units (storage limit)"
    assert session.final_proposal['proposed_cost'] == 1400.00, "Should cost $1400"

    print("✅ TEST SCENARIO 3 PASSED\n")
    return session


def test_visualization_data():
    """Test that coordination generates data suitable for frontend visualization"""
    print_header("TEST: Visualization Data")

    print("Testing that coordination session produces JSON-serializable data")
    print("suitable for frontend visualization...")

    coordinator = AgentCoordinator()

    # Create agents
    sc_agent = SupplyChainAgent(name="SC-VIZ")
    fin_agent = FinancialAgent(name="FIN-VIZ")
    fac_agent = FacilityAgent(name="FAC-VIZ")

    coordinator.register_agent(sc_agent)
    coordinator.register_agent(fin_agent)
    coordinator.register_agent(fac_agent)

    # Run simple scenario
    scenario = {
        "initiator": "SC-VIZ",
        "intent": "Test visualization data",
        "participants": ["SC-VIZ", "FIN-VIZ", "FAC-VIZ"],
        "context": {
            "item_name": "Test Item",
            "current_stock": 100,
            "reorder_point": 500,
            "required_quantity": 500,
            "price_per_unit": 1.00,
            "budget_remaining": 1000.00,
            "storage_available": 800,
            "urgency": "low"
        }
    }

    session = coordinator.run_coordination(scenario)

    # Convert to dict (as would be sent to frontend)
    session_dict = session.to_dict()

    # Validate structure
    print("\n✅ Session data structure:")
    print(f"  - session_id: {session_dict['session_id']}")
    print(f"  - state: {session_dict['state']}")
    print(f"  - messages: {len(session_dict['messages'])} messages")
    print(f"  - negotiation_rounds: {len(session_dict['negotiation_rounds'])} rounds")
    print(f"  - constraints: {len(session_dict['constraints'])} agents")

    # Try to serialize to JSON (this would fail if not JSON-serializable)
    json_str = json.dumps(session_dict, indent=2)
    print(f"\n✅ Successfully serialized to JSON ({len(json_str)} characters)")

    # Validate key fields exist
    assert 'session_id' in session_dict
    assert 'state' in session_dict
    assert 'messages' in session_dict
    assert 'negotiation_rounds' in session_dict
    assert 'final_proposal' in session_dict
    assert 'agreement' in session_dict
    assert 'blockchain_record' in session_dict

    print("\n✅ All required fields present for visualization")
    print("✅ TEST VISUALIZATION DATA PASSED\n")


def main():
    """Run all coordination tests"""
    print("\n" + "🏥" * 40)
    print(" " * 10 + "HOSPITAL BLOCKOPS - COORDINATION TEST SUITE")
    print("🏥" * 40)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠️  WARNING: ANTHROPIC_API_KEY not found")
        print("   Coordination tests will work but agent decision-making")
        print("   uses simulated proposals without Claude API")
        print("   (This is OK for testing the coordination protocol)")

    print(f"\n📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Testing: 8-step negotiation protocol")

    try:
        # Test 1: Successful coordination
        session1 = test_scenario_1_successful_coordination()

        # Test 2: Budget constraint
        session2 = test_scenario_2_budget_constraint()

        # Test 3: Multiple constraints
        session3 = test_scenario_3_multiple_constraints()

        # Test 4: Visualization data
        test_visualization_data()

        # Final summary
        print_header("TEST SUMMARY")
        print("✅ All coordination tests passed!\n")

        print("Test Results:")
        print(f"  Scenario 1 (Storage Constraint): {session1.state.value}")
        print(f"    - Final: {session1.final_proposal['proposed_quantity']} units @ ${session1.final_proposal['proposed_cost']:.2f}")
        print(f"    - Rounds: {len(session1.negotiation_rounds)}")
        print(f"    - Messages: {len(session1.messages)}")

        print(f"\n  Scenario 2 (Budget Constraint): {session2.state.value}")
        print(f"    - Final: {session2.final_proposal['proposed_quantity']} units @ ${session2.final_proposal['proposed_cost']:.2f}")
        print(f"    - Rounds: {len(session2.negotiation_rounds)}")
        print(f"    - Messages: {len(session2.messages)}")

        print(f"\n  Scenario 3 (Multiple Constraints): {session3.state.value}")
        print(f"    - Final: {session3.final_proposal['proposed_quantity']} units @ ${session3.final_proposal['proposed_cost']:.2f}")
        print(f"    - Rounds: {len(session3.negotiation_rounds)}")
        print(f"    - Messages: {len(session3.messages)}")

        print("\n" + "=" * 80)
        print("🎉 Coordination system fully functional!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

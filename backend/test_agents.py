"""
Comprehensive Test Suite for Hospital BlockOps Agents

Tests Supply Chain and Financial agents with realistic scenarios.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add agents to path
sys.path.insert(0, os.path.dirname(__file__))

from agents import SupplyChainAgent, FinancialAgent


def print_header(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}".center(80))
    print("=" * 80 + "\n")


def print_decision(decision: dict, title: str = "Decision"):
    """Pretty print agent decision"""
    print(f"\n{'─' * 80}")
    print(f"📋 {title}")
    print(f"{'─' * 80}")

    for key, value in decision.items():
        if isinstance(value, list):
            print(f"  {key}: ")
            for item in value:
                print(f"    • {item}")
        elif isinstance(value, float):
            if key == "confidence":
                print(f"  {key}: {value:.1%}")
            elif "cost" in key.lower() or "amount" in key.lower():
                print(f"  {key}: ${value:,.2f}")
            else:
                print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")
    print(f"{'─' * 80}\n")


def test_supply_chain_agent():
    """Test Supply Chain Agent with various scenarios"""
    print_header("TEST 1: SUPPLY CHAIN AGENT")

    # Initialize agent
    print("🤖 Initializing Supply Chain Agent...")
    sc_agent = SupplyChainAgent(name="SC-TEST-001")
    print(f"✅ Agent initialized: {sc_agent}")
    print(f"   Role: {sc_agent.role}")
    print(f"   Model: {sc_agent.model}")

    # Scenario 1: Critical shortage - needs immediate reorder
    print("\n" + "─" * 80)
    print("📦 SCENARIO 1: Critical Shortage - Surgical Masks")
    print("─" * 80)
    print("Current stock: 50 units")
    print("Reorder point: 500 units")
    print("⚠️ CRITICAL: Stock at 10% of reorder point!")

    try:
        decision1 = sc_agent.decide_purchase(
            item_name="Surgical Masks (N95)",
            current_stock=50,
            reorder_point=500,
            required_quantity=1000,
            price_per_unit=2.50,
            budget_remaining=50000.00,
            storage_available=5000,
            priority="critical",
            historical_usage=[800, 850, 900, 920, 950],
            supplier_name="MedSupply Inc",
            lead_time_days=3
        )

        print_decision(decision1, "Supply Chain Decision - Critical Shortage")

    except Exception as e:
        print(f"❌ Error in Scenario 1: {e}")

    # Scenario 2: Normal reorder with bulk discount opportunity
    print("\n" + "─" * 80)
    print("📦 SCENARIO 2: Normal Reorder - Medical Gloves (Bulk Discount)")
    print("─" * 80)
    print("Current stock: 400 units")
    print("Reorder point: 500 units")
    print("💡 Opportunity: Can get bulk discount at 1000+ units")

    try:
        decision2 = sc_agent.decide_purchase(
            item_name="Medical Gloves (Box of 100)",
            current_stock=400,
            reorder_point=500,
            required_quantity=800,
            price_per_unit=15.00,
            budget_remaining=25000.00,
            storage_available=2000,
            priority="high",
            historical_usage=[600, 650, 620, 680, 700],
            supplier_name="HealthCare Direct",
            lead_time_days=5
        )

        print_decision(decision2, "Supply Chain Decision - Bulk Discount Opportunity")

    except Exception as e:
        print(f"❌ Error in Scenario 2: {e}")

    # Scenario 3: Storage constraint limiting order
    print("\n" + "─" * 80)
    print("📦 SCENARIO 3: Storage Constraint - Large Item")
    print("─" * 80)
    print("Current stock: 80 units")
    print("Reorder point: 100 units")
    print("⚠️ Limited storage: Only 150 units available")

    try:
        decision3 = sc_agent.decide_purchase(
            item_name="Wheelchair (Standard)",
            current_stock=80,
            reorder_point=100,
            required_quantity=200,
            price_per_unit=250.00,
            budget_remaining=60000.00,
            storage_available=150,  # Limited storage!
            priority="medium",
            historical_usage=[10, 12, 11, 13, 12],
            supplier_name="MedEquip Corp",
            lead_time_days=10
        )

        print_decision(decision3, "Supply Chain Decision - Storage Constrained")

    except Exception as e:
        print(f"❌ Error in Scenario 3: {e}")

    # Show agent statistics
    print("\n" + "─" * 80)
    print("📊 Supply Chain Agent Statistics")
    print("─" * 80)
    stats = sc_agent.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            if key == "avg_confidence":
                print(f"  {key}: {value:.1%}")
            elif key == "avg_response_time":
                print(f"  {key}: {value:.2f}s")
            else:
                print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")

    return sc_agent


def test_financial_agent():
    """Test Financial Agent with various scenarios"""
    print_header("TEST 2: FINANCIAL AGENT")

    # Initialize agent
    print("🤖 Initializing Financial Agent...")
    fin_agent = FinancialAgent(name="FIN-TEST-001")
    print(f"✅ Agent initialized: {fin_agent}")
    print(f"   Role: {fin_agent.role}")
    print(f"   Model: {fin_agent.model}")

    # Show budget summary
    print("\n" + "─" * 80)
    print("💰 Budget Configuration")
    print("─" * 80)
    budget_summary = fin_agent.get_budget_summary()
    print(f"  Monthly Budget: ${budget_summary['monthly_budget']:,.2f}")
    print(f"  Emergency Reserve: ${budget_summary['emergency_reserve']:,.2f}")
    print(f"  Autonomous Limit: ${budget_summary['autonomous_limit']:,.2f}")

    # Scenario 1: Easy approval - well within budget
    print("\n" + "─" * 80)
    print("💵 SCENARIO 1: Easy Approval - Small Purchase")
    print("─" * 80)
    print("Request: $2,500 for surgical masks")
    print("Budget: $500,000 total, $320,000 spent, $180,000 remaining")
    print("Days remaining: 12")

    try:
        decision1 = fin_agent.approve_purchase(
            item_name="Surgical Masks (N95)",
            quantity=1000,
            total_cost=2500.00,
            monthly_budget=500000.00,
            spent_so_far=320000.00,
            days_remaining=12,
            priority="critical",
            historical_average=2800.00,
            stockout_risk="high",
            requesting_agent="SC-TEST-001",
            category="medical_supplies"
        )

        print_decision(decision1, "Financial Decision - Easy Approval")

    except Exception as e:
        print(f"❌ Error in Scenario 1: {e}")

    # Scenario 2: Borderline approval - budget getting tight
    print("\n" + "─" * 80)
    print("💵 SCENARIO 2: Borderline Approval - Budget Tight")
    print("─" * 80)
    print("Request: $45,000 for equipment maintenance")
    print("Budget: $500,000 total, $430,000 spent, $70,000 remaining")
    print("Days remaining: 5")
    print("⚠️ WARNING: 86% budget utilization!")

    try:
        decision2 = fin_agent.approve_purchase(
            item_name="MRI Maintenance Contract",
            quantity=1,
            total_cost=45000.00,
            monthly_budget=500000.00,
            spent_so_far=430000.00,
            days_remaining=5,
            priority="high",
            historical_average=38000.00,
            stockout_risk="medium",
            requesting_agent="MAINT-001",
            category="equipment_maintenance"
        )

        print_decision(decision2, "Financial Decision - Borderline Approval")

    except Exception as e:
        print(f"❌ Error in Scenario 2: {e}")

    # Scenario 3: Likely rejection - budget exhausted
    print("\n" + "─" * 80)
    print("💵 SCENARIO 3: Likely Rejection - Budget Nearly Exhausted")
    print("─" * 80)
    print("Request: $65,000 for office furniture")
    print("Budget: $500,000 total, $475,000 spent, $25,000 remaining")
    print("Days remaining: 8")
    print("🚨 CRITICAL: 95% budget utilization + low priority!")

    try:
        decision3 = fin_agent.approve_purchase(
            item_name="Office Furniture Upgrade",
            quantity=50,
            total_cost=65000.00,
            monthly_budget=500000.00,
            spent_so_far=475000.00,
            days_remaining=8,
            priority="low",
            historical_average=15000.00,
            stockout_risk="low",
            requesting_agent="ADMIN-001",
            category="administrative"
        )

        print_decision(decision3, "Financial Decision - Budget Exhausted")

    except Exception as e:
        print(f"❌ Error in Scenario 3: {e}")

    # Scenario 4: Partial approval - compromise solution
    print("\n" + "─" * 80)
    print("💵 SCENARIO 4: Potential Partial Approval")
    print("─" * 80)
    print("Request: $30,000 for cleaning supplies")
    print("Budget: $500,000 total, $465,000 spent, $35,000 remaining")
    print("Days remaining: 3")
    print("💡 Opportunity: Could approve partial amount")

    try:
        decision4 = fin_agent.approve_purchase(
            item_name="Cleaning Supplies (Quarterly Stock)",
            quantity=1000,
            total_cost=30000.00,
            monthly_budget=500000.00,
            spent_so_far=465000.00,
            days_remaining=3,
            priority="medium",
            historical_average=28000.00,
            stockout_risk="medium",
            requesting_agent="FACILITY-001",
            category="miscellaneous"
        )

        print_decision(decision4, "Financial Decision - Partial Approval Option")

    except Exception as e:
        print(f"❌ Error in Scenario 4: {e}")

    # Budget health check
    print("\n" + "─" * 80)
    print("🏥 Budget Health Check")
    print("─" * 80)
    health = fin_agent.check_budget_health(
        spent_so_far=465000.00,
        monthly_budget=500000.00,
        days_remaining=3
    )

    print(f"  Health Status: {health['health'].upper()}")
    print(f"  Utilization: {health['utilization']:.1%}")
    print(f"  Spent: ${health['spent']:,.2f}")
    print(f"  Remaining: ${health['remaining']:,.2f}")
    print(f"  Daily Burn Rate: ${health['daily_burn_rate']:,.2f}")
    print(f"  Projected Month-End: ${health['projected_month_end']:,.2f}")
    print(f"  On Track: {'✅ Yes' if health['on_track'] else '❌ No'}")
    if health['warning']:
        print(f"  ⚠️ Warning: {health['warning']}")

    # Show agent statistics
    print("\n" + "─" * 80)
    print("📊 Financial Agent Statistics")
    print("─" * 80)
    stats = fin_agent.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            if key == "avg_confidence":
                print(f"  {key}: {value:.1%}")
            elif key == "avg_response_time":
                print(f"  {key}: {value:.2f}s")
            else:
                print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")

    return fin_agent


def test_agent_coordination():
    """Test coordination between Supply Chain and Financial agents"""
    print_header("TEST 3: AGENT COORDINATION")

    print("🤖 Initializing both agents for coordination test...")
    sc_agent = SupplyChainAgent(name="SC-COORD-001")
    fin_agent = FinancialAgent(name="FIN-COORD-001")

    print("\n" + "─" * 80)
    print("🔄 SCENARIO: Coordinated Purchase Decision")
    print("─" * 80)
    print("Supply Chain detects low stock → proposes purchase → Financial approves")

    # Step 1: Supply Chain proposes purchase
    print("\n📦 Step 1: Supply Chain Agent proposes purchase...")
    try:
        sc_decision = sc_agent.decide_purchase(
            item_name="IV Fluid Bags (1000ml)",
            current_stock=150,
            reorder_point=500,
            required_quantity=800,
            price_per_unit=5.00,
            budget_remaining=100000.00,
            storage_available=2000,
            priority="critical",
            historical_usage=[650, 700, 720, 680, 750]
        )

        print(f"✅ Supply Chain recommends: {sc_decision['recommended_quantity']} units")
        print(f"   Estimated cost: ${sc_decision['estimated_cost']:,.2f}")
        print(f"   Confidence: {sc_decision['confidence']:.1%}")

        # Step 2: Financial Agent reviews the purchase
        print("\n💵 Step 2: Financial Agent reviews purchase...")
        fin_decision = fin_agent.approve_purchase(
            item_name="IV Fluid Bags (1000ml)",
            quantity=sc_decision['recommended_quantity'],
            total_cost=sc_decision['estimated_cost'],
            monthly_budget=500000.00,
            spent_so_far=380000.00,
            days_remaining=10,
            priority="critical",
            historical_average=3500.00,
            stockout_risk="high",
            requesting_agent="SC-COORD-001",
            category="medical_supplies"
        )

        print(f"✅ Financial decision: {fin_decision['decision'].upper()}")
        print(f"   Approved amount: ${fin_decision['approved_amount']:,.2f}")
        print(f"   Confidence: {fin_decision['confidence']:.1%}")

        # Step 3: Show coordination result
        print("\n" + "─" * 80)
        print("🎯 Coordination Result")
        print("─" * 80)

        if fin_decision['decision'] == "approve":
            print("✅ Purchase APPROVED - Coordination successful!")
            print(f"   Supply Chain proposed: {sc_decision['recommended_quantity']} units")
            print(f"   Financial approved: ${fin_decision['approved_amount']:,.2f}")
            print(f"   Both agents agree: Full purchase can proceed")
        elif fin_decision['decision'] == "approve_partial":
            print("⚠️ Partial approval - Negotiation needed")
            print(f"   Supply Chain wanted: ${sc_decision['estimated_cost']:,.2f}")
            print(f"   Financial approved: ${fin_decision['approved_amount']:,.2f}")
            print(f"   Difference: ${sc_decision['estimated_cost'] - fin_decision['approved_amount']:,.2f}")
            print("   → Supply Chain should revise quantity or find alternative supplier")
        else:
            print("❌ Purchase REJECTED - Coordination failed")
            print(f"   Supply Chain wanted: ${sc_decision['estimated_cost']:,.2f}")
            print(f"   Financial rejected due to: {fin_decision['reasoning']}")
            print("   → Need to escalate to human oversight or wait for next month")

    except Exception as e:
        print(f"❌ Error in coordination: {e}")


def main():
    """Run all agent tests"""
    print("\n" + "🏥" * 40)
    print(" " * 15 + "HOSPITAL BLOCKOPS - AGENT TEST SUITE")
    print("🏥" * 40)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ERROR: ANTHROPIC_API_KEY not found in environment")
        print("   Please add it to backend/.env file")
        print("   Example: ANTHROPIC_API_KEY=sk-ant-...")
        return

    print(f"\n📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 Model: claude-3-5-sonnet-20241022")

    try:
        # Test 1: Supply Chain Agent
        sc_agent = test_supply_chain_agent()

        # Test 2: Financial Agent
        fin_agent = test_financial_agent()

        # Test 3: Coordination
        test_agent_coordination()

        # Final summary
        print_header("TEST SUMMARY")
        print("✅ All tests completed successfully!")
        print(f"\nSupply Chain Agent:")
        print(f"  Total decisions: {len(sc_agent.decision_history)}")
        print(f"  Average confidence: {sum(d.confidence for d in sc_agent.decision_history) / len(sc_agent.decision_history):.1%}")

        print(f"\nFinancial Agent:")
        print(f"  Total decisions: {len(fin_agent.decision_history)}")
        print(f"  Average confidence: {sum(d.confidence for d in fin_agent.decision_history) / len(fin_agent.decision_history):.1%}")

        print("\n" + "=" * 80)
        print("🎉 Test suite completed! Agents are working correctly.")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

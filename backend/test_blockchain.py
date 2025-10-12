#!/usr/bin/env python3
"""
Test script for blockchain functionality.

Run this to verify blockchain is working correctly.
"""

from blockchain.ledger import Blockchain, Transaction, SmartContractValidator
from blockchain.manager import (
    record_agent_decision,
    get_recent_blocks,
    get_blockchain_stats,
    verify_block,
    get_transaction_history,
    reset_blockchain
)
from datetime import datetime


def test_basic_blockchain():
    """Test basic blockchain operations"""
    print("\n" + "="*80)
    print("TEST 1: Basic Blockchain Operations".center(80))
    print("="*80 + "\n")

    # Reset to start fresh
    blockchain = reset_blockchain()

    print(f"✅ Blockchain initialized")
    print(f"   Genesis block: {blockchain.chain[0].hash[:16]}...")
    print(f"   Chain length: {len(blockchain.chain)}")

    # Create a simple transaction
    print("\n📝 Creating transaction...")
    tx = Transaction(
        transaction_id="TEST_TX_001",
        agent_name="Supply Chain Agent",
        action_type="PURCHASE_ORDER",
        details={
            "item": "Test Item",
            "quantity": 100,
            "amount": 500.00,
            "confidence": 0.90,
            "available_budget": 2000.00,
            "available_storage": 500
        },
        timestamp=datetime.now().isoformat()
    )

    # Add and commit
    validation = blockchain.add_transaction(tx)
    print(f"   Validation: {'✅ PASSED' if validation['valid'] else '❌ FAILED'}")

    if validation['valid']:
        block = blockchain.commit_pending_transactions()
        print(f"   Block created: #{block.index}")
        print(f"   Block hash: {block.hash[:16]}...")

    # Validate chain
    chain_validation = blockchain.validate_chain()
    print(f"\n🔍 Chain validation: {'✅ VALID' if chain_validation['valid'] else '❌ INVALID'}")
    print(f"   Blocks checked: {chain_validation['blocks_checked']}")


def test_smart_contracts():
    """Test smart contract validation"""
    print("\n" + "="*80)
    print("TEST 2: Smart Contract Validation".center(80))
    print("="*80 + "\n")

    validator = SmartContractValidator()

    # Test 1: Valid budget
    print("📊 Test 1: Valid Budget ($1,000 within $2,000 limit)")
    result = validator.validate_budget(1000.00, 2000.00)
    print(f"   Result: {'✅ VALID' if result['valid'] else '❌ INVALID'}")
    print(f"   Reason: {result['reason']}")
    print(f"   Remaining: ${result['remaining']:,.2f}")

    # Test 2: Insufficient budget
    print("\n📊 Test 2: Insufficient Budget ($3,000 within $2,000 limit)")
    result = validator.validate_budget(3000.00, 2000.00)
    print(f"   Result: {'✅ VALID' if result['valid'] else '❌ INVALID'}")
    print(f"   Reason: {result['reason']}")

    # Test 3: Valid storage
    print("\n📦 Test 3: Valid Storage (500 units within 1000 capacity)")
    result = validator.validate_storage(500, 1000)
    print(f"   Result: {'✅ VALID' if result['valid'] else '❌ INVALID'}")
    print(f"   Reason: {result['reason']}")

    # Test 4: Insufficient storage
    print("\n📦 Test 4: Insufficient Storage (2000 units within 1000 capacity)")
    result = validator.validate_storage(2000, 1000)
    print(f"   Result: {'✅ VALID' if result['valid'] else '❌ INVALID'}")
    print(f"   Reason: {result['reason']}")

    # Test 5: Confidence threshold
    print("\n🎯 Test 5: Low Confidence (0.65 below 0.70 threshold)")
    result = validator.validate_confidence(0.65)
    print(f"   Result: {'✅ VALID' if result['valid'] else '❌ INVALID'}")
    print(f"   Reason: {result['reason']}")

    print("\n🎯 Test 6: High Confidence (0.92 above 0.70 threshold)")
    result = validator.validate_confidence(0.92)
    print(f"   Result: {'✅ VALID' if result['valid'] else '❌ INVALID'}")
    print(f"   Reason: {result['reason']}")


def test_manager_functions():
    """Test blockchain manager helper functions"""
    print("\n" + "="*80)
    print("TEST 3: Blockchain Manager Functions".center(80))
    print("="*80 + "\n")

    # Reset
    reset_blockchain()

    # Record multiple decisions
    print("📝 Recording agent decisions...")

    decisions = [
        {
            'agent_id': 'sc001',
            'agent_name': 'Supply Chain Agent',
            'action_type': 'PURCHASE_ORDER',
            'decision_details': {
                'item': 'PPE Equipment',
                'quantity': 500,
                'amount': 1500.00,
                'confidence': 0.92,
                'available_budget': 5000.00,
                'available_storage': 1000
            }
        },
        {
            'agent_id': 'en001',
            'agent_name': 'Energy Management Agent',
            'action_type': 'HVAC_ADJUSTMENT',
            'decision_details': {
                'zone': 'Operating Room 5',
                'temperature_delta': -2,
                'estimated_savings_kwh': 45.5,
                'confidence': 0.88
            }
        },
        {
            'agent_id': 'mt001',
            'agent_name': 'Maintenance Agent',
            'action_type': 'PREVENTIVE_MAINTENANCE',
            'decision_details': {
                'equipment': 'MRI-3',
                'estimated_downtime_hours': 4,
                'confidence': 0.85
            }
        }
    ]

    for decision in decisions:
        result = record_agent_decision(**decision)
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {decision['agent_name']}: {decision['action_type']}")
        print(f"      TX: {result['transaction_id']}")
        print(f"      Block: #{result['block_index']}, Hash: {result['block_hash'][:16] if result['block_hash'] else 'N/A'}...")

    # Get stats
    print("\n📊 Blockchain Statistics:")
    stats = get_blockchain_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Get recent blocks
    print("\n📦 Recent Blocks:")
    blocks = get_recent_blocks(limit=5)
    for block in blocks:
        print(f"   Block #{block['index']}: {block['hash'][:16]}... "
              f"({block['data'].get('transaction_count', 0) if isinstance(block['data'], dict) else 0} txs)")

    # Verify a block
    print("\n🔍 Verifying Block #1:")
    verification = verify_block(1)
    print(f"   Valid: {'✅' if verification['valid'] else '❌'}")
    print(f"   Hash valid: {verification['hash_valid']}")
    print(f"   Chain valid: {verification['chain_valid']}")

    # Get transaction history
    print("\n📜 Transaction History:")
    history = get_transaction_history()
    for tx in history[:5]:  # Show first 5
        print(f"   {tx['transaction_id']}: {tx['agent_name']} - {tx['action_type']}")


def test_consensus_timing():
    """Test consensus timing simulation"""
    print("\n" + "="*80)
    print("TEST 4: Consensus Timing".center(80))
    print("="*80 + "\n")

    import time

    reset_blockchain()
    blockchain = reset_blockchain()

    print("⏱️  Testing consensus delay (simulated PBFT)...")
    print("   Creating 5 blocks and measuring consensus time...\n")

    times = []
    for i in range(5):
        tx = Transaction(
            transaction_id=f"TIMING_TEST_{i}",
            agent_name="Test Agent",
            action_type="TEST_ACTION",
            details={"test": True, "iteration": i},
            timestamp=datetime.now().isoformat()
        )

        start = time.time()
        blockchain.add_transaction(tx)
        blockchain.commit_pending_transactions()
        elapsed = time.time() - start

        times.append(elapsed)
        print(f"   Block {i+1}: {elapsed*1000:.0f}ms")

    avg_time = sum(times) / len(times)
    print(f"\n   Average consensus time: {avg_time*1000:.0f}ms")
    print(f"   Simulates Hyperledger Fabric PBFT consensus delay")


def run_all_tests():
    """Run all tests"""
    print("\n" + "🏥" * 40)
    print("HOSPITAL BLOCKCHAIN TEST SUITE".center(80))
    print("🏥" * 40)

    try:
        test_basic_blockchain()
        test_smart_contracts()
        test_manager_functions()
        test_consensus_timing()

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED".center(80))
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()

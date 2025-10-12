"""
Blockchain Manager for Flask API Integration

Provides a singleton blockchain instance and helper functions
for the Flask application to interact with the blockchain.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .ledger import Blockchain, Transaction, SmartContractValidator

# Global blockchain instance (singleton pattern)
_blockchain_instance: Optional[Blockchain] = None


def get_blockchain() -> Blockchain:
    """
    Get the global blockchain instance (singleton).
    Creates one if it doesn't exist.
    """
    global _blockchain_instance

    if _blockchain_instance is None:
        print("🔗 Initializing new blockchain instance...")
        _blockchain_instance = Blockchain(mining_difficulty=2)

    return _blockchain_instance


def reset_blockchain() -> Blockchain:
    """
    Reset blockchain (useful for testing/demo reset).
    """
    global _blockchain_instance
    print("♻️  Resetting blockchain...")
    _blockchain_instance = Blockchain(mining_difficulty=2)
    return _blockchain_instance


def record_agent_decision(
    agent_id: str,
    agent_name: str,
    action_type: str,
    decision_details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Record an agent decision to the blockchain.

    Args:
        agent_id: Unique agent identifier
        agent_name: Human-readable agent name
        action_type: Type of action (e.g., "PURCHASE_ORDER", "HVAC_ADJUSTMENT")
        decision_details: Dictionary with decision specifics

    Returns:
        Dictionary with transaction and blockchain recording results
    """
    blockchain = get_blockchain()

    # Create transaction
    transaction = Transaction(
        transaction_id=f"TX-{agent_id}-{int(datetime.now().timestamp() * 1000)}",
        agent_name=agent_name,
        action_type=action_type,
        details=decision_details,
        timestamp=datetime.now().isoformat()
    )

    # Add to blockchain (validates via smart contract)
    validation_result = blockchain.add_transaction(transaction)

    # Commit immediately for demo (in production, batch transactions)
    try:
        block = blockchain.commit_pending_transactions(batch_size=1)

        return {
            "success": True,
            "transaction_id": transaction.transaction_id,
            "validation": validation_result,
            "block_index": block.index,
            "block_hash": block.hash,
            "timestamp": transaction.timestamp
        }
    except ValueError as e:
        # No pending transactions (already committed or rejected)
        return {
            "success": validation_result["valid"],
            "transaction_id": transaction.transaction_id,
            "validation": validation_result,
            "block_index": None,
            "block_hash": None,
            "timestamp": transaction.timestamp
        }


def get_recent_blocks(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get the most recent blocks from the blockchain.

    Args:
        limit: Maximum number of blocks to return

    Returns:
        List of block dictionaries
    """
    blockchain = get_blockchain()
    chain = blockchain.get_chain()

    # Return most recent blocks (excluding genesis if limit reached)
    return chain[-limit:] if len(chain) <= limit else chain[-limit:]


def verify_block(block_index: int) -> Dict[str, Any]:
    """
    Verify a specific block's integrity.

    Args:
        block_index: Index of block to verify

    Returns:
        Verification result
    """
    blockchain = get_blockchain()
    block = blockchain.get_block(block_index)

    if not block:
        return {
            "valid": False,
            "error": f"Block {block_index} not found"
        }

    # Verify block hash
    calculated_hash = block.calculate_hash()
    hash_valid = calculated_hash == block.hash

    # Verify chain linkage (if not genesis)
    chain_valid = True
    if block_index > 0:
        previous_block = blockchain.get_block(block_index - 1)
        if previous_block:
            chain_valid = block.previous_hash == previous_block.hash

    return {
        "valid": hash_valid and chain_valid,
        "hash_valid": hash_valid,
        "chain_valid": chain_valid,
        "block_hash": block.hash,
        "calculated_hash": calculated_hash,
        "previous_hash": block.previous_hash
    }


def get_blockchain_stats() -> Dict[str, Any]:
    """
    Get comprehensive blockchain statistics.

    Returns:
        Statistics dictionary
    """
    blockchain = get_blockchain()
    return blockchain.get_stats()


def get_transaction_history(agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get transaction history, optionally filtered by agent.

    Args:
        agent_name: Optional agent name to filter by

    Returns:
        List of transaction dictionaries
    """
    blockchain = get_blockchain()
    return blockchain.get_transaction_history(agent_name)


def validate_constraints_preview(
    amount: Optional[float] = None,
    quantity: Optional[int] = None,
    confidence: Optional[float] = None
) -> Dict[str, Any]:
    """
    Preview constraint validation without committing.
    Useful for UI to show whether action will succeed.

    Args:
        amount: Budget amount to check
        quantity: Storage quantity to check
        confidence: Confidence score to check

    Returns:
        Validation result preview
    """
    validator = SmartContractValidator()
    checks = {}

    if amount is not None:
        checks["budget"] = validator.validate_budget(amount)

    if quantity is not None:
        checks["storage"] = validator.validate_storage(quantity)

    if confidence is not None:
        checks["confidence"] = validator.validate_confidence(confidence)

    all_valid = all(check["valid"] for check in checks.values())

    return {
        "valid": all_valid,
        "checks": checks
    }


def get_smart_contract_constraints() -> Dict[str, Any]:
    """
    Get current smart contract constraint values.
    Useful for UI to display limits.

    Returns:
        Dictionary of constraints
    """
    validator = SmartContractValidator()
    return validator.constraints.copy()


def update_smart_contract_constraints(updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update smart contract constraints (admin function).

    Args:
        updates: Dictionary of constraint updates

    Returns:
        Updated constraints
    """
    blockchain = get_blockchain()
    validator = blockchain.validator

    # Update constraints
    for key, value in updates.items():
        if key in validator.constraints:
            validator.constraints[key] = value

    return validator.constraints.copy()


# Utility functions for formatting
def format_hash(hash_string: str, length: int = 16) -> str:
    """Format hash for display (show first N characters)"""
    return f"{hash_string[:length]}..." if len(hash_string) > length else hash_string


def format_block_summary(block_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format block for compact API response.

    Returns summary with shortened hashes and key info.
    """
    return {
        "index": block_dict["index"],
        "hash": format_hash(block_dict["hash"]),
        "previous_hash": format_hash(block_dict["previous_hash"]),
        "timestamp": block_dict["timestamp"],
        "transaction_count": block_dict["data"].get("transaction_count", 0)
        if isinstance(block_dict["data"], dict)
        else 0,
        "type": block_dict["data"].get("type", "UNKNOWN")
        if isinstance(block_dict["data"], dict)
        else "LEGACY"
    }


# Example usage
if __name__ == "__main__":
    print("🔗 Testing Blockchain Manager\n")

    # Record a sample decision
    result = record_agent_decision(
        agent_id="sc001",
        agent_name="Supply Chain Agent",
        action_type="PURCHASE_ORDER",
        decision_details={
            "item": "Surgical Masks",
            "quantity": 1000,
            "amount": 500.00,
            "vendor": "MedSupply Inc",
            "confidence": 0.95,
            "available_budget": 2000.00,
            "available_storage": 1500
        }
    )

    print(f"Transaction recorded: {result['transaction_id']}")
    print(f"Block: #{result['block_index']}")
    print(f"Hash: {result['block_hash'][:16]}...")
    print(f"Valid: {result['validation']['valid']}")

    # Get stats
    print("\n📊 Blockchain Stats:")
    stats = get_blockchain_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Get recent blocks
    print("\n📦 Recent Blocks:")
    blocks = get_recent_blocks(limit=5)
    for block in blocks:
        summary = format_block_summary(block)
        print(f"  Block #{summary['index']}: {summary['hash']} ({summary['transaction_count']} txs)")

    # Verify blockchain
    print("\n✅ Chain Validation:")
    blockchain = get_blockchain()
    validation = blockchain.validate_chain()
    print(f"  Valid: {validation['valid']}")
    print(f"  Blocks Checked: {validation['blocks_checked']}")

"""
Simplified Blockchain Implementation for Hospital Operations Demo

This is a demonstration blockchain that simulates key concepts of Hyperledger Fabric
for educational and demo purposes.

REAL HYPERLEDGER FABRIC DIFFERENCES:
- Uses distributed peer-to-peer network (not single-node like this)
- PBFT consensus involves multiple nodes voting (we simulate with delay)
- Channels for privacy between organizations (we use single chain)
- Chaincode (smart contracts) runs in isolated containers (we use Python functions)
- Endorsement policies require multiple peer signatures (we use single validation)
- CouchDB/LevelDB for state database (we use in-memory)
- gRPC for inter-node communication (we use direct function calls)
- Cryptographic identities with x.509 certificates (we use simple hashes)
"""

import hashlib
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
import random


@dataclass
class Transaction:
    """
    Represents a single transaction in the blockchain.
    In Hyperledger Fabric, this would be a proposal submitted by a client.
    """
    transaction_id: str
    agent_name: str
    action_type: str
    details: Dict[str, Any]
    timestamp: str
    validation_status: str = "pending"  # pending, validated, rejected
    smart_contract_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary for serialization"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert transaction to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class Block:
    """
    Represents a single block in the blockchain.

    In Hyperledger Fabric:
    - Blocks contain multiple transactions (we support this too)
    - Blocks are created by orderer nodes after consensus
    - Blocks include config transactions and endorsement data
    - Merkle tree is used for efficient verification (we use simple hash)
    """

    def __init__(
        self,
        index: int,
        timestamp: str,
        data: Any,
        previous_hash: str,
        nonce: int = 0
    ):
        self.index = index
        self.timestamp = timestamp
        self.data = data  # Can be a Transaction or list of Transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Calculate SHA-256 hash of block contents.

        In Hyperledger Fabric:
        - Uses more sophisticated cryptographic hashing
        - Includes Merkle root of all transactions
        - Contains metadata about endorsements
        """
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data if isinstance(self.data, dict) else str(self.data),
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)

        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary for API responses"""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "nonce": self.nonce
        }

    def __repr__(self) -> str:
        return f"Block(index={self.index}, hash={self.hash[:16]}...)"


class SmartContractValidator:
    """
    Simulates smart contract validation (chaincode in Hyperledger Fabric).

    In Hyperledger Fabric:
    - Chaincode runs in Docker containers for isolation
    - Written in Go, Node.js, or Java (we use Python)
    - Executes on endorsing peers before consensus
    - Can read/write to state database
    - Supports complex business logic with multiple functions
    """

    def __init__(self):
        # Simulated hospital operational constraints
        self.constraints = {
            "total_budget": 5_000_000,  # $5M monthly budget
            "available_budget": 2_000_000,  # $2M remaining
            "total_storage": 10000,  # 10,000 units capacity
            "available_storage": 3000,  # 3,000 units available
            "max_single_purchase": 50_000,  # $50K limit for autonomous purchases
            "min_confidence_threshold": 0.7,  # 70% confidence required
        }

    def validate_budget(self, amount: float, available_budget: float = None) -> Dict[str, Any]:
        """
        Validate if transaction amount is within budget constraints.

        Returns: {
            "valid": bool,
            "reason": str,
            "remaining": float
        }
        """
        budget = available_budget if available_budget is not None else self.constraints["available_budget"]

        if amount <= 0:
            return {
                "valid": False,
                "reason": "Amount must be positive",
                "remaining": budget
            }

        if amount > budget:
            return {
                "valid": False,
                "reason": f"Insufficient budget. Required: ${amount:,.2f}, Available: ${budget:,.2f}",
                "remaining": budget
            }

        if amount > self.constraints["max_single_purchase"]:
            return {
                "valid": False,
                "reason": f"Single purchase exceeds limit of ${self.constraints['max_single_purchase']:,.2f}. Requires approval.",
                "remaining": budget
            }

        return {
            "valid": True,
            "reason": "Budget constraint satisfied",
            "remaining": budget - amount
        }

    def validate_storage(self, quantity: int, available_storage: int = None) -> Dict[str, Any]:
        """
        Validate if storage capacity is available for inventory.

        Returns: {
            "valid": bool,
            "reason": str,
            "remaining": int
        }
        """
        storage = available_storage if available_storage is not None else self.constraints["available_storage"]

        if quantity <= 0:
            return {
                "valid": False,
                "reason": "Quantity must be positive",
                "remaining": storage
            }

        if quantity > storage:
            return {
                "valid": False,
                "reason": f"Insufficient storage. Required: {quantity} units, Available: {storage} units",
                "remaining": storage
            }

        return {
            "valid": True,
            "reason": "Storage constraint satisfied",
            "remaining": storage - quantity
        }

    def validate_confidence(self, confidence: float) -> Dict[str, Any]:
        """
        Validate if agent confidence meets minimum threshold.
        """
        threshold = self.constraints["min_confidence_threshold"]

        if confidence < threshold:
            return {
                "valid": False,
                "reason": f"Confidence {confidence:.2%} below threshold {threshold:.2%}. Requires human approval.",
            }

        return {
            "valid": True,
            "reason": f"Confidence {confidence:.2%} meets threshold",
        }

    def validate_constraints(self, transaction: Transaction) -> Dict[str, Any]:
        """
        Comprehensive validation of all transaction constraints.

        In Hyperledger Fabric:
        - This would be a chaincode function called by endorsing peers
        - Would interact with state database to check current values
        - Multiple peers would execute and return results
        - Results must match for endorsement (determinism required)

        Returns: {
            "valid": bool,
            "checks": {
                "budget": {...},
                "storage": {...},
                "confidence": {...}
            },
            "overall_reason": str
        }
        """
        details = transaction.details
        checks = {}
        all_valid = True
        reasons = []

        # Budget check (if applicable)
        if "amount" in details:
            budget_check = self.validate_budget(
                float(details["amount"]),
                details.get("available_budget")
            )
            checks["budget"] = budget_check
            if not budget_check["valid"]:
                all_valid = False
                reasons.append(budget_check["reason"])

        # Storage check (if applicable)
        if "quantity" in details:
            storage_check = self.validate_storage(
                int(details["quantity"]),
                details.get("available_storage")
            )
            checks["storage"] = storage_check
            if not storage_check["valid"]:
                all_valid = False
                reasons.append(storage_check["reason"])

        # Confidence check (if applicable)
        if "confidence" in details:
            confidence_check = self.validate_confidence(float(details["confidence"]))
            checks["confidence"] = confidence_check
            if not confidence_check["valid"]:
                all_valid = False
                reasons.append(confidence_check["reason"])

        return {
            "valid": all_valid,
            "checks": checks,
            "overall_reason": "; ".join(reasons) if reasons else "All constraints satisfied",
            "timestamp": datetime.now().isoformat()
        }


class Blockchain:
    """
    Simplified blockchain implementation simulating Hyperledger Fabric.

    In Hyperledger Fabric:
    - Distributed ledger across multiple peer nodes
    - Orderer nodes sequence transactions into blocks
    - PBFT or Raft consensus among orderers
    - Peers validate and commit blocks
    - State database maintains current world state
    - This implementation is single-node for demo simplicity
    """

    def __init__(self, mining_difficulty: int = 2):
        self.chain: List[Block] = []
        self.mining_difficulty = mining_difficulty  # Simulates consensus delay
        self.validator = SmartContractValidator()
        self.pending_transactions: List[Transaction] = []

        # Create genesis block
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        """
        Create the first block in the chain (genesis block).

        In Hyperledger Fabric:
        - Genesis block contains network configuration
        - Defines consortium members and policies
        - Establishes initial channel configuration
        """
        genesis_data = {
            "type": "GENESIS",
            "message": "BlockOps Hospital Operations Blockchain - Genesis Block",
            "network": "Hospital Operations Network",
            "version": "1.0.0",
            "consensus": "Simulated PBFT",
            "created_at": datetime.now().isoformat()
        }

        genesis_block = Block(
            index=0,
            timestamp=datetime.now().isoformat(),
            data=genesis_data,
            previous_hash="0" * 64,  # No previous block
            nonce=0
        )

        self.chain.append(genesis_block)
        print(f"✅ Genesis block created: {genesis_block.hash[:16]}...")

    def _simulate_consensus(self) -> None:
        """
        Simulate consensus delay (PBFT in Hyperledger Fabric).

        In Hyperledger Fabric:
        - Orderer nodes run consensus protocol (PBFT, Raft, etc.)
        - Multiple nodes vote on transaction ordering
        - Requires 2f+1 nodes to agree (Byzantine fault tolerance)
        - Takes milliseconds in production networks

        We simulate this with a random delay between 100-250ms.
        """
        consensus_time = random.uniform(0.1, 0.25)  # 100-250ms
        time.sleep(consensus_time)

    def _proof_of_work(self, block: Block) -> Block:
        """
        Simple proof-of-work for demonstration (not used in Hyperledger Fabric).

        Note: Hyperledger Fabric does NOT use proof-of-work.
        We include this to show mining simulation and add realistic delay.
        Real Hyperledger uses permissioned consensus (PBFT/Raft).
        """
        target = "0" * self.mining_difficulty

        while block.hash[:self.mining_difficulty] != target:
            block.nonce += 1
            block.hash = block.calculate_hash()

        return block

    def add_transaction(self, transaction: Transaction) -> Dict[str, Any]:
        """
        Add transaction to pending pool and validate via smart contract.

        In Hyperledger Fabric:
        - Client submits transaction proposal to endorsing peers
        - Endorsers execute chaincode and return signed results
        - Client collects endorsements and submits to orderer
        - Orderer sequences into blocks

        Returns validation result.
        """
        # Validate transaction via smart contract
        validation_result = self.validator.validate_constraints(transaction)

        transaction.validation_status = "validated" if validation_result["valid"] else "rejected"
        transaction.smart_contract_result = validation_result

        if validation_result["valid"]:
            self.pending_transactions.append(transaction)
            print(f"✅ Transaction {transaction.transaction_id} validated and added to pool")
        else:
            print(f"❌ Transaction {transaction.transaction_id} rejected: {validation_result['overall_reason']}")

        return validation_result

    def add_block(self, data: Any, auto_commit: bool = True) -> Block:
        """
        Add a new block to the blockchain.

        In Hyperledger Fabric:
        - Orderer creates block from pending transactions
        - Block is broadcast to all peers
        - Peers validate block and commit to ledger
        - State database is updated

        Args:
            data: Transaction data or dict
            auto_commit: If True, simulate consensus and add immediately

        Returns: The created block
        """
        previous_block = self.get_latest_block()

        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now().isoformat(),
            data=data,
            previous_hash=previous_block.hash,
            nonce=0
        )

        # Simulate consensus process (PBFT in Hyperledger Fabric)
        print(f"⏳ Block {new_block.index} entering consensus...")
        self._simulate_consensus()

        # Optional: Simple proof-of-work for visual effect
        # (Not used in real Hyperledger Fabric)
        if self.mining_difficulty > 0:
            new_block = self._proof_of_work(new_block)

        if auto_commit:
            self.chain.append(new_block)
            print(f"✅ Block {new_block.index} committed to chain: {new_block.hash[:16]}...")

        return new_block

    def commit_pending_transactions(self, batch_size: int = 10) -> Block:
        """
        Create a block from pending transactions.

        In Hyperledger Fabric:
        - Orderer batches transactions into blocks
        - Block size and timeout configurable
        - Typically processes batches of 10-500 transactions
        """
        if not self.pending_transactions:
            raise ValueError("No pending transactions to commit")

        # Take up to batch_size transactions
        transactions_to_commit = self.pending_transactions[:batch_size]
        self.pending_transactions = self.pending_transactions[batch_size:]

        block_data = {
            "type": "TRANSACTION_BLOCK",
            "transaction_count": len(transactions_to_commit),
            "transactions": [tx.to_dict() for tx in transactions_to_commit]
        }

        return self.add_block(block_data)

    def get_chain(self) -> List[Dict[str, Any]]:
        """
        Return entire blockchain as list of dictionaries.
        """
        return [block.to_dict() for block in self.chain]

    def get_block(self, index: int) -> Optional[Block]:
        """
        Get block by index.
        """
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None

    def get_latest_block(self) -> Block:
        """
        Get the most recent block in the chain.
        """
        return self.chain[-1]

    def validate_chain(self) -> Dict[str, Any]:
        """
        Validate integrity of entire blockchain.

        In Hyperledger Fabric:
        - Peers can independently validate chain
        - Checks cryptographic hashes
        - Verifies endorsement policies
        - Checks against state database

        Returns: {
            "valid": bool,
            "errors": List[str],
            "blocks_checked": int
        }
        """
        errors = []

        # Check genesis block
        if len(self.chain) == 0:
            return {
                "valid": False,
                "errors": ["Chain is empty"],
                "blocks_checked": 0
            }

        if self.chain[0].previous_hash != "0" * 64:
            errors.append("Genesis block has invalid previous_hash")

        # Validate each subsequent block
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Check if previous_hash matches
            if current_block.previous_hash != previous_block.hash:
                errors.append(
                    f"Block {i} previous_hash mismatch. "
                    f"Expected: {previous_block.hash[:16]}..., "
                    f"Got: {current_block.previous_hash[:16]}..."
                )

            # Verify block's own hash is correct
            recalculated_hash = current_block.calculate_hash()
            if current_block.hash != recalculated_hash:
                errors.append(
                    f"Block {i} hash invalid. "
                    f"Stored: {current_block.hash[:16]}..., "
                    f"Calculated: {recalculated_hash[:16]}..."
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "blocks_checked": len(self.chain)
        }

    def get_transaction_history(self, agent_name: str = None) -> List[Dict[str, Any]]:
        """
        Get transaction history, optionally filtered by agent.

        In Hyperledger Fabric:
        - Query state database for transaction history
        - Rich queries using CouchDB
        - Indexed for efficient searching
        """
        transactions = []

        for block in self.chain[1:]:  # Skip genesis block
            if isinstance(block.data, dict) and block.data.get("type") == "TRANSACTION_BLOCK":
                for tx in block.data.get("transactions", []):
                    if agent_name is None or tx.get("agent_name") == agent_name:
                        transactions.append({
                            "block_index": block.index,
                            "block_hash": block.hash,
                            "block_timestamp": block.timestamp,
                            **tx
                        })

        return transactions

    def pretty_print(self) -> None:
        """
        Pretty print the entire blockchain for debugging.
        """
        print("\n" + "="*80)
        print("BLOCKCHAIN LEDGER".center(80))
        print("="*80)

        for block in self.chain:
            print(f"\nBlock #{block.index}")
            print(f"  Timestamp: {block.timestamp}")
            print(f"  Hash:      {block.hash}")
            print(f"  Prev Hash: {block.previous_hash}")
            print(f"  Nonce:     {block.nonce}")

            if isinstance(block.data, dict):
                print(f"  Data Type: {block.data.get('type', 'UNKNOWN')}")
                if block.data.get("type") == "TRANSACTION_BLOCK":
                    print(f"  Transactions: {block.data.get('transaction_count', 0)}")
            else:
                print(f"  Data:      {str(block.data)[:100]}...")

            print("-" * 80)

        validation = self.validate_chain()
        print(f"\n{'✅' if validation['valid'] else '❌'} Chain Validation: {'VALID' if validation['valid'] else 'INVALID'}")
        print(f"  Blocks Checked: {validation['blocks_checked']}")
        if validation['errors']:
            print(f"  Errors: {', '.join(validation['errors'])}")
        print("="*80 + "\n")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get blockchain statistics.
        """
        total_transactions = 0
        validated_transactions = 0
        rejected_transactions = 0

        for block in self.chain[1:]:
            if isinstance(block.data, dict) and block.data.get("type") == "TRANSACTION_BLOCK":
                for tx in block.data.get("transactions", []):
                    total_transactions += 1
                    if tx.get("validation_status") == "validated":
                        validated_transactions += 1
                    elif tx.get("validation_status") == "rejected":
                        rejected_transactions += 1

        return {
            "total_blocks": len(self.chain),
            "total_transactions": total_transactions,
            "validated_transactions": validated_transactions,
            "rejected_transactions": rejected_transactions,
            "pending_transactions": len(self.pending_transactions),
            "chain_valid": self.validate_chain()["valid"],
            "latest_block_hash": self.get_latest_block().hash,
            "genesis_hash": self.chain[0].hash if self.chain else None
        }


# Example usage and testing
if __name__ == "__main__":
    print("🏥 Hospital BlockOps Blockchain Demo\n")

    # Initialize blockchain
    blockchain = Blockchain(mining_difficulty=2)

    # Create sample transactions
    tx1 = Transaction(
        transaction_id="TX001",
        agent_name="Supply Chain Agent",
        action_type="PURCHASE_ORDER",
        details={
            "item": "PPE Equipment",
            "quantity": 500,
            "amount": 1500.00,
            "vendor": "MedSupply Corp",
            "confidence": 0.92,
            "available_budget": 2000.00,
            "available_storage": 800
        },
        timestamp=datetime.now().isoformat()
    )

    tx2 = Transaction(
        transaction_id="TX002",
        agent_name="Energy Management Agent",
        action_type="HVAC_ADJUSTMENT",
        details={
            "zone": "Operating Room 5",
            "temperature_delta": -2,
            "estimated_savings_kwh": 45.5,
            "confidence": 0.88
        },
        timestamp=datetime.now().isoformat()
    )

    # Add transactions
    print("\n--- Adding Transactions ---")
    blockchain.add_transaction(tx1)
    blockchain.add_transaction(tx2)

    # Commit to blockchain
    print("\n--- Committing to Blockchain ---")
    blockchain.commit_pending_transactions()

    # Display blockchain
    blockchain.pretty_print()

    # Show stats
    print("📊 Blockchain Statistics:")
    stats = blockchain.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

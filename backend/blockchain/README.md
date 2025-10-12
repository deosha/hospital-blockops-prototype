# Hospital BlockOps - Blockchain Implementation

A realistic but simplified blockchain simulation demonstrating key concepts of Hyperledger Fabric for hospital operations management.

## 🎯 Purpose

This blockchain implementation serves as an **educational demonstration** of how blockchain technology can provide trustless coordination and audit trails for multi-agent hospital operations. While simplified, it accurately demonstrates the core concepts.

## 📁 Files

- **`ledger.py`** - Core blockchain implementation (Block, Transaction, Blockchain classes)
- **`manager.py`** - Helper functions for Flask API integration
- **`test_blockchain.py`** - Comprehensive test suite

## 🏗️ Architecture

### Block Structure

```python
Block {
    index: int              # Block number (0 = genesis)
    timestamp: str          # ISO format timestamp
    data: dict/Any          # Transaction data or batch
    previous_hash: str      # Hash of previous block (links chain)
    hash: str              # SHA-256 hash of this block
    nonce: int             # Mining nonce (for PoW simulation)
}
```

### Transaction Structure

```python
Transaction {
    transaction_id: str                    # Unique ID
    agent_name: str                        # Agent that created it
    action_type: str                       # Type of action
    details: dict                          # Action-specific data
    timestamp: str                         # ISO timestamp
    validation_status: str                 # pending/validated/rejected
    smart_contract_result: dict           # Validation results
}
```

## 🔐 Smart Contract Validation

The `SmartContractValidator` class simulates Hyperledger Fabric chaincode with three main validators:

### 1. Budget Validation

```python
validate_budget(amount, available_budget) -> {
    "valid": bool,
    "reason": str,
    "remaining": float
}
```

**Rules:**
- Amount must be positive
- Amount ≤ available budget
- Single purchase ≤ $50,000 (autonomous limit)

### 2. Storage Validation

```python
validate_storage(quantity, available_storage) -> {
    "valid": bool,
    "reason": str,
    "remaining": int
}
```

**Rules:**
- Quantity must be positive
- Quantity ≤ available storage capacity

### 3. Confidence Validation

```python
validate_confidence(confidence) -> {
    "valid": bool,
    "reason": str
}
```

**Rules:**
- Confidence ≥ 0.70 (70% minimum threshold)
- Below threshold requires human approval

### Comprehensive Validation

```python
validate_constraints(transaction) -> {
    "valid": bool,
    "checks": {
        "budget": {...},
        "storage": {...},
        "confidence": {...}
    },
    "overall_reason": str,
    "timestamp": str
}
```

## 🚀 Usage Examples

### Basic Usage

```python
from blockchain.ledger import Blockchain, Transaction

# Initialize blockchain
blockchain = Blockchain(mining_difficulty=2)

# Create transaction
tx = Transaction(
    transaction_id="TX001",
    agent_name="Supply Chain Agent",
    action_type="PURCHASE_ORDER",
    details={
        "item": "PPE Equipment",
        "quantity": 500,
        "amount": 1500.00,
        "confidence": 0.92,
        "available_budget": 5000.00,
        "available_storage": 1000
    },
    timestamp=datetime.now().isoformat()
)

# Add transaction (validates automatically)
validation = blockchain.add_transaction(tx)
print(f"Valid: {validation['valid']}")

# Commit to blockchain
block = blockchain.commit_pending_transactions()
print(f"Block created: #{block.index}, Hash: {block.hash[:16]}...")

# Validate chain integrity
validation = blockchain.validate_chain()
print(f"Chain valid: {validation['valid']}")
```

### Using Manager Functions (Flask Integration)

```python
from blockchain.manager import (
    record_agent_decision,
    get_recent_blocks,
    get_blockchain_stats
)

# Record a decision
result = record_agent_decision(
    agent_id="sc001",
    agent_name="Supply Chain Agent",
    action_type="PURCHASE_ORDER",
    decision_details={
        "item": "Surgical Masks",
        "quantity": 1000,
        "amount": 500.00,
        "confidence": 0.95,
        "available_budget": 2000.00,
        "available_storage": 1500
    }
)

print(f"Transaction: {result['transaction_id']}")
print(f"Block: #{result['block_index']}")
print(f"Valid: {result['success']}")

# Get blockchain stats
stats = get_blockchain_stats()
print(f"Total blocks: {stats['total_blocks']}")
print(f"Total transactions: {stats['total_transactions']}")
print(f"Chain valid: {stats['chain_valid']}")

# Get recent blocks
blocks = get_recent_blocks(limit=5)
for block in blocks:
    print(f"Block #{block['index']}: {block['hash'][:16]}...")
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd backend
python test_blockchain.py
```

**Tests include:**
1. ✅ Basic blockchain operations (create, add, validate)
2. ✅ Smart contract validation (budget, storage, confidence)
3. ✅ Manager functions (record, query, verify)
4. ✅ Consensus timing simulation

**Expected output:**

```
🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥
        HOSPITAL BLOCKCHAIN TEST SUITE
🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥

TEST 1: Basic Blockchain Operations
✅ Blockchain initialized
✅ Transaction validated
✅ Block created
✅ Chain valid

TEST 2: Smart Contract Validation
✅ All validation tests passed

TEST 3: Blockchain Manager Functions
✅ All manager functions working

TEST 4: Consensus Timing
⏱️  Average consensus time: 150ms

✅ ALL TESTS PASSED
```

## 🔍 Key Features

### 1. Consensus Simulation

```python
def _simulate_consensus(self):
    """
    Simulates PBFT consensus with 100-250ms delay.
    Real Hyperledger Fabric involves multiple nodes voting.
    """
    consensus_time = random.uniform(0.1, 0.25)
    time.sleep(consensus_time)
```

### 2. Cryptographic Hashing

```python
def calculate_hash(self) -> str:
    """SHA-256 hash of block contents"""
    block_string = json.dumps({...}, sort_keys=True)
    return hashlib.sha256(block_string.encode()).hexdigest()
```

### 3. Chain Validation

```python
def validate_chain(self) -> dict:
    """
    Validates:
    - Genesis block integrity
    - Hash linkage between blocks
    - Individual block hash correctness
    """
```

### 4. Transaction Batching

```python
def commit_pending_transactions(self, batch_size=10):
    """
    Batches transactions into blocks (like Hyperledger orderer).
    Configurable batch size.
    """
```

## 🆚 Real Hyperledger Fabric vs This Implementation

| Feature | Real Hyperledger Fabric | This Implementation |
|---------|------------------------|---------------------|
| **Network** | Distributed P2P across multiple organizations | Single-node in-memory |
| **Consensus** | PBFT/Raft with multiple orderers voting | Simulated delay (100-250ms) |
| **Smart Contracts** | Go/Node.js chaincode in Docker containers | Python functions |
| **State Database** | CouchDB/LevelDB for world state | In-memory Python dict |
| **Identity** | x.509 certificates with MSP | Simple hashes |
| **Channels** | Private channels between orgs | Single chain |
| **Endorsement** | Multiple peer signatures required | Single validation |
| **Communication** | gRPC protocol | Direct function calls |
| **Performance** | 2000+ TPS (production) | Limited by Python/memory |
| **Persistence** | Persistent file/DB storage | In-memory (resets on restart) |

## 💡 Why These Simplifications?

1. **Educational**: Easy to understand without distributed systems complexity
2. **Demo-Ready**: Runs on single machine without setup
3. **Fast**: No network overhead, instant results
4. **Debuggable**: All code in Python, easy to trace
5. **Sufficient**: Demonstrates key concepts (immutability, validation, audit trail)

## 🎓 What This Demonstrates

Even with simplifications, this implementation demonstrates:

✅ **Immutability** - Once recorded, blocks cannot be altered
✅ **Chain Integrity** - Cryptographic linking prevents tampering
✅ **Smart Contract Validation** - Automated policy enforcement
✅ **Audit Trail** - Complete history of all decisions
✅ **Consensus Simulation** - Realistic timing delays
✅ **Transaction Batching** - Efficient block creation
✅ **Multi-Stakeholder Trust** - Verifiable by all parties

## 📊 Performance Characteristics

- **Block Creation**: ~100-250ms (simulated consensus)
- **Validation**: <1ms (Python function call)
- **Hash Calculation**: <1ms (SHA-256)
- **Chain Validation**: ~1ms per block
- **Memory Usage**: ~1KB per block (in-memory)

## 🔧 Configuration

Adjust blockchain behavior in `Blockchain.__init__()`:

```python
# Consensus delay (0 = instant, 2 = ~150ms average)
mining_difficulty = 2

# Smart contract constraints
constraints = {
    "total_budget": 5_000_000,
    "available_budget": 2_000_000,
    "total_storage": 10000,
    "available_storage": 3000,
    "max_single_purchase": 50_000,
    "min_confidence_threshold": 0.7,
}
```

## 🚀 Production Considerations

For real deployment, you would need:

1. **Deploy Hyperledger Fabric** - Multi-node network
2. **Write Real Chaincode** - Go/Node.js smart contracts
3. **Set Up Identities** - x.509 certificates for all participants
4. **Configure Channels** - Privacy between organizations
5. **Persistent Storage** - File-based or database ledger
6. **Monitoring** - Prometheus metrics, logging
7. **Security** - TLS, firewalls, access control
8. **Disaster Recovery** - Backup and restore procedures

## 📚 Further Reading

- [Hyperledger Fabric Documentation](https://hyperledger-fabric.readthedocs.io/)
- [Blockchain for Healthcare](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6361378/)
- [Smart Contracts in Healthcare](https://ieeexplore.ieee.org/document/8967594)

---

**This implementation is for demonstration and educational purposes.**
For production use, deploy actual Hyperledger Fabric infrastructure.

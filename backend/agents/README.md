# Hospital BlockOps - Multi-Agent System

Intelligent agents using Anthropic Claude API for autonomous hospital operations management.

---

## Overview

This package implements a multi-agent system where each agent:
- Uses **Anthropic Claude (claude-3-5-sonnet-20241022)** for decision-making
- Has specialized domain knowledge and responsibilities
- Coordinates with other agents via message passing
- Records decisions to blockchain for audit trail
- Operates autonomously within defined constraints

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Agent Base Class                      │
│  • perceive(state) → context                                │
│  • reason(context, prompt) → decision (via Claude API)      │
│  • act(decision) → result                                   │
│  • get_reasoning_trace() → history                          │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
┌───────┴────────┐                      ┌───────────┴──────────┐
│ Supply Chain   │                      │  Financial Agent     │
│     Agent      │◄────coordinates─────►│                      │
│                │                      │                      │
│ • Monitor inv  │                      │ • Approve/reject     │
│ • Propose buys │                      │ • Budget tracking    │
│ • Optimize qty │                      │ • Risk assessment    │
└────────────────┘                      └──────────────────────┘
```

---

## Agents

### 1. Agent Base Class

**File:** `agent_base.py`

Foundation for all specialized agents. Provides:

**Properties:**
- `name`: Agent identifier (e.g., "SC-001")
- `role`: Agent's role description
- `knowledge_base`: Dict of domain knowledge
- `decision_history`: List of past decisions
- `model`: Claude model name
- `client`: Anthropic API client

**Methods:**

#### `perceive(state: Dict[str, Any]) -> Dict[str, Any]`
Process incoming state and prepare context for reasoning.

```python
context = agent.perceive({
    "current_stock": 50,
    "reorder_point": 500,
    "budget_available": 10000
})
# Returns enhanced context with agent metadata
```

#### `reason(context, prompt_template, temperature, max_tokens) -> Dict[str, Any]`
Call Claude API to make decision. Includes:
- Automatic retry with exponential backoff
- JSON parsing with markdown code block extraction
- Error handling for rate limits and API errors
- Decision logging with timestamps

```python
decision = agent.reason(
    context=context,
    prompt_template=prompt,
    temperature=0.7,
    max_tokens=2048
)
# Returns parsed JSON decision
```

#### `act(decision: Dict[str, Any]) -> Dict[str, Any]`
Execute the decision. Override in subclasses for specialized actions.

#### `get_reasoning_trace(limit: int = 10) -> List[Dict[str, Any]]`
Get recent decision history for audit trail.

#### `get_stats() -> Dict[str, Any]`
Get agent statistics (total decisions, avg confidence, avg response time).

**Error Handling:**
- `RateLimitError`: Exponential backoff retry
- `APIConnectionError`: Retry with delay
- `APIError`: Retry up to max_retries
- `JSONDecodeError`: Extract from markdown code blocks

---

### 2. Supply Chain Agent

**File:** `supply_chain_agent.py`

Manages hospital inventory and procurement.

**Responsibilities:**
- Monitor inventory levels across all supplies
- Detect when reorder points are reached
- Propose optimal purchase orders
- Coordinate with Financial Agent for budget approval
- Coordinate with Facility Agent for storage capacity

**Knowledge Base:**
```python
{
    "reorder_policies": {
        "safety_stock_multiplier": 1.5,
        "lead_time_days": 7,
        "max_order_quantity": 10000,
        "min_order_quantity": 100
    },
    "priority_levels": {
        "critical": ["medications", "ppe", "surgical_supplies"],
        "high": ["lab_supplies", "cleaning_supplies"],
        "medium": ["office_supplies", "linens"],
        "low": ["non_essential"]
    },
    "cost_optimization": {
        "bulk_discount_threshold": 1000,
        "bulk_discount_rate": 0.15,
        "expedite_fee_multiplier": 1.3
    }
}
```

**Key Method:**

#### `decide_purchase(...) -> Dict[str, Any]`

Makes purchase decision using Claude API.

**Parameters:**
- `item_name`: Name of item
- `current_stock`: Current inventory level
- `reorder_point`: Reorder threshold
- `required_quantity`: Estimated need
- `price_per_unit`: Cost per unit
- `budget_remaining`: Available budget
- `storage_available`: Available storage
- `priority`: critical/high/medium/low
- `historical_usage`: Past consumption data
- `supplier_name`: Preferred supplier
- `lead_time_days`: Expected delivery time

**Returns:**
```python
{
    "analysis": "Detailed reasoning about situation",
    "recommended_quantity": 1200,
    "estimated_cost": 3000.00,
    "justification": "Why this quantity is optimal",
    "coordination_needed": ["Financial", "Facility"],
    "confidence": 0.92,
    "risk_assessment": "low",
    "alternative_options": ["Option 1", "Option 2"]
}
```

**Example:**
```python
from agents import SupplyChainAgent

sc_agent = SupplyChainAgent(name="SC-001")

decision = sc_agent.decide_purchase(
    item_name="Surgical Masks (N95)",
    current_stock=50,
    reorder_point=500,
    required_quantity=1000,
    price_per_unit=2.50,
    budget_remaining=50000.00,
    storage_available=5000,
    priority="critical",
    historical_usage=[800, 850, 900, 920, 950]
)

print(f"Recommended quantity: {decision['recommended_quantity']}")
print(f"Estimated cost: ${decision['estimated_cost']:,.2f}")
print(f"Confidence: {decision['confidence']:.1%}")
```

**Helper Method:**

#### `check_inventory_status(item_name, current_stock, reorder_point) -> Dict`

Quick check if item needs reordering without full Claude API call.

---

### 3. Financial Agent

**File:** `financial_agent.py`

Manages budget constraints and approves/rejects purchases.

**Responsibilities:**
- Monitor budget constraints across departments
- Approve or reject purchase requests
- Suggest cost optimizations
- Track spending trends
- Ensure fiscal responsibility

**Knowledge Base:**
```python
{
    "budget_policies": {
        "monthly_budget": 500_000,
        "emergency_reserve": 50_000,
        "autonomous_approval_limit": 50_000,
        "high_priority_allowance": 0.15
    },
    "spending_categories": {
        "medical_supplies": {"monthly_allocation": 200_000, "priority": "critical"},
        "equipment_maintenance": {"monthly_allocation": 100_000, "priority": "high"},
        "utilities": {"monthly_allocation": 80_000, "priority": "high"}
    },
    "risk_thresholds": {
        "low_risk_percentage": 0.70,
        "medium_risk_percentage": 0.85,
        "high_risk_percentage": 0.95
    }
}
```

**Key Method:**

#### `approve_purchase(...) -> Dict[str, Any]`

Approve or reject purchase request using Claude API.

**Parameters:**
- `item_name`: Item to purchase
- `quantity`: Quantity requested
- `total_cost`: Total cost
- `monthly_budget`: Total monthly budget
- `spent_so_far`: Amount spent this month
- `days_remaining`: Days left in month
- `priority`: critical/high/medium/low
- `historical_average`: Historical spend in category
- `stockout_risk`: Risk if not approved
- `requesting_agent`: Which agent made request
- `category`: Spending category

**Returns:**
```python
{
    "decision": "approve|approve_partial|reject",
    "approved_amount": 2500.00,
    "reasoning": "Detailed financial justification",
    "conditions": ["Condition 1", "Condition 2"],
    "confidence": 0.88,
    "risk_assessment": "low",
    "recommendations": ["Recommendation 1", "Recommendation 2"]
}
```

**Example:**
```python
from agents import FinancialAgent

fin_agent = FinancialAgent(name="FIN-001")

decision = fin_agent.approve_purchase(
    item_name="Surgical Masks (N95)",
    quantity=1000,
    total_cost=2500.00,
    monthly_budget=500000.00,
    spent_so_far=320000.00,
    days_remaining=12,
    priority="critical",
    stockout_risk="high",
    category="medical_supplies"
)

print(f"Decision: {decision['decision'].upper()}")
print(f"Approved amount: ${decision['approved_amount']:,.2f}")
print(f"Reasoning: {decision['reasoning']}")
```

**Helper Methods:**

#### `get_budget_summary() -> Dict`
Get current budget configuration and allocations.

#### `check_budget_health(spent_so_far, monthly_budget, days_remaining) -> Dict`
Quick health check of budget status without full Claude API call.

---

## Agent Coordination

Agents coordinate by passing messages and considering each other's constraints.

**Typical Flow:**

```python
from agents import SupplyChainAgent, FinancialAgent

# 1. Supply Chain detects low stock
sc_agent = SupplyChainAgent()
sc_decision = sc_agent.decide_purchase(
    item_name="IV Fluids",
    current_stock=100,
    reorder_point=500,
    required_quantity=800,
    price_per_unit=5.00,
    budget_remaining=100000.00,
    storage_available=2000,
    priority="critical"
)

# 2. Financial Agent reviews the purchase
fin_agent = FinancialAgent()
fin_decision = fin_agent.approve_purchase(
    item_name="IV Fluids",
    quantity=sc_decision['recommended_quantity'],
    total_cost=sc_decision['estimated_cost'],
    monthly_budget=500000.00,
    spent_so_far=380000.00,
    days_remaining=10,
    priority="critical",
    requesting_agent=sc_agent.name
)

# 3. Act based on coordination result
if fin_decision['decision'] == "approve":
    print("✅ Purchase approved - proceed with order")
elif fin_decision['decision'] == "approve_partial":
    print(f"⚠️ Partial approval: ${fin_decision['approved_amount']}")
    # Revise quantity or negotiate
else:
    print("❌ Purchase rejected - escalate to human")
```

---

## Testing

**Run comprehensive test suite:**

```bash
cd backend
python test_agents.py
```

**Test Coverage:**
- ✅ Supply Chain Agent with 3 scenarios
- ✅ Financial Agent with 4 scenarios
- ✅ Agent coordination workflow
- ✅ Error handling and retries
- ✅ Decision logging and statistics

**Example Output:**
```
🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥
  HOSPITAL BLOCKOPS - AGENT TEST SUITE
🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥🏥

TEST 1: SUPPLY CHAIN AGENT
  ✅ Critical shortage scenario
  ✅ Bulk discount scenario
  ✅ Storage constraint scenario

TEST 2: FINANCIAL AGENT
  ✅ Easy approval
  ✅ Borderline approval
  ✅ Budget exhausted
  ✅ Partial approval

TEST 3: AGENT COORDINATION
  ✅ Supply Chain → Financial workflow

🎉 Test suite completed!
```

---

## Performance

| Metric | Value |
|--------|-------|
| **Decision Time** | 2-5 seconds (Claude API call) |
| **Confidence** | 0.75-0.95 (75-95%) typical |
| **Retry Attempts** | Up to 3 retries with exponential backoff |
| **Rate Limits** | Handled automatically |
| **Error Rate** | <1% with retry logic |

---

## API Usage

**Model:** `claude-3-5-sonnet-20241022`

**Typical API call:**
- Temperature: 0.6-0.7 (balanced creativity/consistency)
- Max tokens: 2048 (sufficient for JSON response + reasoning)
- Response format: JSON (with markdown extraction fallback)
- Average tokens per call: ~1500-2000

**Cost Estimation (as of Oct 2024):**
- Input: ~$3.00 per million tokens
- Output: ~$15.00 per million tokens
- Typical decision: ~$0.05-0.10 per call

---

## Environment Setup

**Required:**
```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

**Optional Configuration:**
```python
# Custom model
agent = SupplyChainAgent(
    name="SC-001",
    model="claude-3-5-sonnet-20241022"
)

# Custom retry settings
agent = Agent(
    name="TEST",
    role="Testing",
    max_retries=5,
    retry_delay=2.0
)
```

---

## Error Handling

### Rate Limit Errors
```python
# Automatic exponential backoff
# Attempt 1: wait 1s
# Attempt 2: wait 2s
# Attempt 3: wait 4s
```

### API Connection Errors
```python
# Automatic retry with fixed delay
# Logs warning and retries up to max_retries
```

### JSON Parsing Errors
```python
# Attempts to extract JSON from markdown:
# 1. Look for ```json ... ```
# 2. Look for ``` ... ```
# 3. Raise error if neither works
```

---

## Logging

All agents log to console with structured format:

```
2025-10-12 20:30:45 - Agent.SC-001 - INFO - Initialized Supply Chain Management agent: SC-001
2025-10-12 20:30:46 - SupplyChainAgent.SC-001 - INFO - Perceived state for Surgical Masks: Stock=50, Reorder=500, Urgency=critical
2025-10-12 20:30:48 - Agent.SC-001 - INFO - Reasoning attempt 1/3 using model claude-3-5-sonnet-20241022
2025-10-12 20:30:51 - Agent.SC-001 - INFO - Decision made in 2.84s (confidence: 92.0%)
```

**Log Levels:**
- `INFO`: Normal operations, decisions, statistics
- `WARNING`: Retries, rate limits, JSON parsing issues
- `ERROR`: API errors, failures after retries
- `DEBUG`: Detailed state, prompts, raw responses

---

## Future Agents

**Planned additions:**
- Energy Management Agent
- Maintenance Agent
- Scheduling Agent
- Emergency Response Agent

All will inherit from `Agent` base class and follow same patterns.

---

## Integration with Blockchain

Agents can record decisions to blockchain:

```python
from blockchain.manager import record_agent_decision

# After agent makes decision
result = record_agent_decision(
    agent_id=sc_agent.name,
    agent_name=sc_agent.role,
    action_type="PURCHASE_ORDER",
    decision_details=decision
)

print(f"Recorded to blockchain: Block #{result['block_index']}")
```

See [blockchain/README.md](../blockchain/README.md) for details.

---

## Contributing

To add a new agent:

1. Create new file in `agents/` directory
2. Inherit from `Agent` base class
3. Override `perceive()` for specialized perception
4. Create decision method that calls `reason()`
5. Override `act()` for specialized actions
6. Add knowledge base with domain-specific rules
7. Add tests to `test_agents.py`
8. Update this README

---

## License

Part of Hospital BlockOps Demo project.

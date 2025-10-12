"""
Supply Chain Agent for Hospital BlockOps

Manages hospital inventory, monitors stock levels, and coordinates
with Financial and Facility agents for purchase decisions.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .agent_base import Agent


class SupplyChainAgent(Agent):
    """
    Supply Chain Agent specializing in inventory management.

    Responsibilities:
    - Monitor inventory levels across all hospital supplies
    - Detect when reorder points are reached
    - Propose optimal purchase orders
    - Coordinate with Financial Agent for budget approval
    - Coordinate with Facility Agent for storage capacity
    - Negotiate quantities and timing with other agents
    """

    def __init__(
        self,
        name: str = "SC-001",
        knowledge_base: Dict[str, Any] = None,
        model: str = "gpt-3.5-turbo"
    ):
        """
        Initialize Supply Chain Agent.

        Args:
            name: Agent identifier
            knowledge_base: Domain knowledge including reorder policies,
                          supplier info, lead times, etc.
            model: Claude model for decision-making
        """
        # Default knowledge base for supply chain
        default_kb = {
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
            "supplier_reliability": {
                "default": 0.95,  # 95% on-time delivery
                "preferred_vendors": ["MedSupply Inc", "HealthCare Direct"]
            },
            "cost_optimization": {
                "bulk_discount_threshold": 1000,
                "bulk_discount_rate": 0.15,
                "expedite_fee_multiplier": 1.3
            }
        }

        # Merge with provided knowledge base
        if knowledge_base:
            default_kb.update(knowledge_base)

        super().__init__(
            name=name,
            role="Supply Chain Management",
            knowledge_base=default_kb,
            model=model
        )

        self.logger = logging.getLogger(f"SupplyChainAgent.{name}")
        self.logger.info("Supply Chain Agent initialized")

    def perceive(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perceive current inventory state and related constraints.

        Args:
            state: Dict containing:
                - item_name: Name of inventory item
                - current_stock: Current quantity
                - reorder_point: When to trigger reorder
                - required_quantity: How much is needed
                - price_per_unit: Supplier price
                - budget_remaining: Available budget (from Financial)
                - storage_available: Available storage (from Facility)
                - priority: Item priority level
                - historical_usage: Past consumption data

        Returns:
            Enhanced context for decision-making
        """
        context = super().perceive(state)

        # Add supply chain specific analysis
        item_name = state.get("item_name", "Unknown")
        current_stock = state.get("current_stock", 0)
        reorder_point = state.get("reorder_point", 100)

        # Determine urgency
        stock_ratio = current_stock / reorder_point if reorder_point > 0 else 0
        if stock_ratio < 0.5:
            urgency = "critical"
        elif stock_ratio < 0.8:
            urgency = "high"
        elif stock_ratio < 1.0:
            urgency = "medium"
        else:
            urgency = "low"

        # Determine item priority
        priority = state.get("priority", "medium")
        if priority == "unknown":
            # Determine from knowledge base
            for level, items in self.knowledge_base["priority_levels"].items():
                if any(cat in item_name.lower() for cat in items):
                    priority = level
                    break

        context["analysis"] = {
            "urgency": urgency,
            "priority": priority,
            "stock_ratio": stock_ratio,
            "is_below_reorder_point": current_stock < reorder_point,
            "coordination_required": urgency in ["critical", "high"]
        }

        self.logger.info(
            f"Perceived state for {item_name}: "
            f"Stock={current_stock}, "
            f"Reorder={reorder_point}, "
            f"Urgency={urgency}"
        )

        return context

    def decide_purchase(
        self,
        item_name: str,
        current_stock: int,
        reorder_point: int,
        required_quantity: int,
        price_per_unit: float,
        budget_remaining: float,
        storage_available: int,
        priority: str = "medium",
        historical_usage: List[int] = None,
        supplier_name: str = "Default Supplier",
        lead_time_days: int = 7
    ) -> Dict[str, Any]:
        """
        Make purchase decision using Claude API.

        This is the main decision-making method for supply chain.

        Args:
            item_name: Name of item to purchase
            current_stock: Current inventory level
            reorder_point: Reorder threshold
            required_quantity: Estimated quantity needed
            price_per_unit: Cost per unit
            budget_remaining: Available budget from Financial Agent
            storage_available: Available storage from Facility Agent
            priority: Item priority (critical/high/medium/low)
            historical_usage: Past usage data
            supplier_name: Preferred supplier
            lead_time_days: Expected delivery time

        Returns:
            Decision dict with recommended_quantity, cost, justification, etc.
        """
        # Perceive state
        state = {
            "item_name": item_name,
            "current_stock": current_stock,
            "reorder_point": reorder_point,
            "required_quantity": required_quantity,
            "price_per_unit": price_per_unit,
            "budget_remaining": budget_remaining,
            "storage_available": storage_available,
            "priority": priority,
            "historical_usage": historical_usage or [],
            "supplier_name": supplier_name,
            "lead_time_days": lead_time_days
        }

        context = self.perceive(state)

        # Build prompt
        prompt = self._build_purchase_prompt(context)

        # Reason using Claude
        decision = self.reason(
            context=context,
            prompt_template=prompt,
            temperature=0.7,
            max_tokens=2048
        )

        self.logger.info(
            f"Purchase decision for {item_name}: "
            f"Qty={decision.get('recommended_quantity', 0)}, "
            f"Confidence={decision.get('confidence', 0):.2%}"
        )

        return decision

    def _build_purchase_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build detailed prompt for Claude API.

        Args:
            context: Perception context

        Returns:
            Formatted prompt string
        """
        state = context["state"]
        analysis = context["analysis"]
        kb = self.knowledge_base

        # Calculate potential bulk discount
        bulk_threshold = kb["cost_optimization"]["bulk_discount_threshold"]
        bulk_rate = kb["cost_optimization"]["bulk_discount_rate"]
        required_qty = state["required_quantity"]
        price = state["price_per_unit"]

        base_cost = required_qty * price
        if required_qty >= bulk_threshold:
            potential_savings = base_cost * bulk_rate
            bulk_info = f"✅ Bulk discount available: {bulk_rate:.0%} off (save ${potential_savings:.2f})"
        else:
            units_needed = bulk_threshold - required_qty
            bulk_info = f"⚠️ Need {units_needed} more units to qualify for {bulk_rate:.0%} bulk discount"

        # Historical usage analysis
        historical = state.get("historical_usage", [])
        if historical:
            avg_usage = sum(historical) / len(historical)
            usage_trend = "increasing" if historical[-1] > avg_usage else "stable or decreasing"
            usage_info = f"Average monthly usage: {avg_usage:.0f} units ({usage_trend} trend)"
        else:
            usage_info = "No historical usage data available"

        prompt = f"""You are a Supply Chain Agent for a hospital. Your goal is to ensure adequate inventory while minimizing costs and coordinating with other agents.

Current Situation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 Item: {state['item_name']}
📊 Current Stock: {state['current_stock']} units
⚠️  Reorder Point: {state['reorder_point']} units
🎯 Required Quantity: {required_qty} units
💰 Supplier Price: ${price:.2f}/unit
🏢 Supplier: {state.get('supplier_name', 'Default Supplier')}
🚚 Lead Time: {state.get('lead_time_days', 7)} days

Priority & Urgency:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 Priority Level: {state['priority'].upper()}
⏰ Urgency: {analysis['urgency'].upper()}
📈 Stock Ratio: {analysis['stock_ratio']:.1%} of reorder point
{'⛔ BELOW REORDER POINT - ACTION NEEDED' if analysis['is_below_reorder_point'] else '✅ Above reorder point'}

Constraints from Other Agents:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 Budget Available: ${state['budget_remaining']:,.2f} (Financial Agent)
📦 Storage Capacity: {state['storage_available']:,} units (Facility Agent)

Cost Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 Base Cost (required qty): ${base_cost:,.2f}
{bulk_info}

Historical Context:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{usage_info}

Knowledge Base:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Safety Stock Multiplier: {kb['reorder_policies']['safety_stock_multiplier']}x
• Min Order Quantity: {kb['reorder_policies']['min_order_quantity']} units
• Max Order Quantity: {kb['reorder_policies']['max_order_quantity']} units

Your Task:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Decide on the optimal order quantity considering:
1. Ensure adequate supply for patient care (priority: {state['priority']})
2. Minimize total cost (consider bulk discounts)
3. Stay within budget constraints from Financial Agent
4. Respect storage capacity from Facility Agent
5. Balance lead time risk vs. inventory holding cost

Respond in JSON format:
{{
  "analysis": "your detailed reasoning about the situation (2-3 sentences)",
  "recommended_quantity": <number between {kb['reorder_policies']['min_order_quantity']} and {min(kb['reorder_policies']['max_order_quantity'], state['storage_available'])}>,
  "estimated_cost": <number>,
  "justification": "why this quantity is optimal (1-2 sentences)",
  "coordination_needed": ["Financial", "Facility"],
  "confidence": <0.0-1.0>,
  "risk_assessment": "low|medium|high",
  "alternative_options": ["brief option 1", "brief option 2"]
}}

IMPORTANT: Return ONLY valid JSON, no markdown formatting or extra text."""

        return prompt

    def check_inventory_status(
        self,
        item_name: str,
        current_stock: int,
        reorder_point: int
    ) -> Dict[str, Any]:
        """
        Quick check if item needs reordering.

        Args:
            item_name: Item to check
            current_stock: Current inventory
            reorder_point: Reorder threshold

        Returns:
            Status dict with needs_reorder flag and recommendation
        """
        needs_reorder = current_stock < reorder_point
        stock_ratio = current_stock / reorder_point if reorder_point > 0 else 0

        if stock_ratio < 0.3:
            urgency = "critical"
            action = "Order immediately"
        elif stock_ratio < 0.6:
            urgency = "high"
            action = "Order soon"
        elif stock_ratio < 1.0:
            urgency = "medium"
            action = "Consider ordering"
        else:
            urgency = "low"
            action = "No action needed"

        return {
            "item_name": item_name,
            "current_stock": current_stock,
            "reorder_point": reorder_point,
            "needs_reorder": needs_reorder,
            "stock_ratio": stock_ratio,
            "urgency": urgency,
            "recommended_action": action,
            "timestamp": datetime.now().isoformat()
        }

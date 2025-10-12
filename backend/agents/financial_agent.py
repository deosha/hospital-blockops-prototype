"""
Financial Agent for Hospital BlockOps

Manages budget constraints, approves/rejects purchase requests,
and ensures fiscal responsibility while enabling operations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from calendar import monthrange
from .agent_base import Agent


class FinancialAgent(Agent):
    """
    Financial Agent specializing in budget management and fiscal oversight.

    Responsibilities:
    - Monitor budget constraints across all departments
    - Approve or reject purchase requests from other agents
    - Suggest cost optimizations and alternatives
    - Track spending trends and forecast budget needs
    - Coordinate with Supply Chain on purchase timing
    - Ensure compliance with financial policies
    """

    def __init__(
        self,
        name: str = "FIN-001",
        knowledge_base: Dict[str, Any] = None,
        model: str = "gpt-3.5-turbo"
    ):
        """
        Initialize Financial Agent.

        Args:
            name: Agent identifier
            knowledge_base: Domain knowledge including budget policies,
                          spending thresholds, approval limits, etc.
            model: Claude model for decision-making
        """
        # Default knowledge base for financial management
        default_kb = {
            "budget_policies": {
                "monthly_budget": 500_000,  # $500K monthly budget
                "emergency_reserve": 50_000,  # $50K emergency reserve
                "autonomous_approval_limit": 50_000,  # $50K max for auto-approval
                "high_priority_allowance": 0.15,  # 15% allowance for critical items
                "quarterly_rollover": True  # Unused budget rolls to next quarter
            },
            "spending_categories": {
                "medical_supplies": {
                    "monthly_allocation": 200_000,
                    "priority": "critical"
                },
                "equipment_maintenance": {
                    "monthly_allocation": 100_000,
                    "priority": "high"
                },
                "utilities": {
                    "monthly_allocation": 80_000,
                    "priority": "high"
                },
                "administrative": {
                    "monthly_allocation": 50_000,
                    "priority": "medium"
                },
                "miscellaneous": {
                    "monthly_allocation": 70_000,
                    "priority": "medium"
                }
            },
            "risk_thresholds": {
                "low_risk_percentage": 0.70,  # <70% of budget = low risk
                "medium_risk_percentage": 0.85,  # 70-85% = medium risk
                "high_risk_percentage": 0.95,  # 85-95% = high risk
                # >95% = critical risk
            },
            "approval_requirements": {
                "under_10k": "autonomous",
                "10k_to_50k": "approval_recommended",
                "over_50k": "human_approval_required"
            }
        }

        # Merge with provided knowledge base
        if knowledge_base:
            default_kb.update(knowledge_base)

        super().__init__(
            name=name,
            role="Financial Management",
            knowledge_base=default_kb,
            model=model
        )

        self.logger = logging.getLogger(f"FinancialAgent.{name}")
        self.logger.info("Financial Agent initialized")

    def perceive(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perceive financial state and purchase request context.

        Args:
            state: Dict containing:
                - purchase_request: Details of purchase
                - item_name: Item being purchased
                - quantity: Quantity requested
                - total_cost: Total cost of purchase
                - monthly_budget: Total monthly budget
                - spent_so_far: Amount spent this month
                - remaining_budget: Budget remaining
                - days_remaining: Days left in month
                - priority: Request priority
                - historical_average: Historical spending on category
                - stockout_risk: Risk level if not approved

        Returns:
            Enhanced context for decision-making
        """
        context = super().perceive(state)

        # Add financial analysis
        total_cost = state.get("total_cost", 0)
        monthly_budget = state.get("monthly_budget", self.knowledge_base["budget_policies"]["monthly_budget"])
        spent_so_far = state.get("spent_so_far", 0)
        remaining_budget = state.get("remaining_budget", monthly_budget - spent_so_far)
        days_remaining = state.get("days_remaining", 15)

        # Calculate budget utilization
        budget_utilization = spent_so_far / monthly_budget if monthly_budget > 0 else 0
        post_approval_utilization = (spent_so_far + total_cost) / monthly_budget

        # Determine risk level
        risk_thresholds = self.knowledge_base["risk_thresholds"]
        if post_approval_utilization < risk_thresholds["low_risk_percentage"]:
            risk_level = "low"
        elif post_approval_utilization < risk_thresholds["medium_risk_percentage"]:
            risk_level = "medium"
        elif post_approval_utilization < risk_thresholds["high_risk_percentage"]:
            risk_level = "high"
        else:
            risk_level = "critical"

        # Determine approval authority level
        autonomous_limit = self.knowledge_base["budget_policies"]["autonomous_approval_limit"]
        if total_cost < 10_000:
            authority = "autonomous"
        elif total_cost <= autonomous_limit:
            authority = "approval_recommended"
        else:
            authority = "human_approval_required"

        # Calculate daily burn rate
        days_in_month = 30  # Simplified
        days_elapsed = days_in_month - days_remaining
        if days_elapsed > 0:
            daily_burn_rate = spent_so_far / days_elapsed
            projected_month_end = spent_so_far + (daily_burn_rate * days_remaining)
        else:
            daily_burn_rate = 0
            projected_month_end = spent_so_far

        context["financial_analysis"] = {
            "budget_utilization": budget_utilization,
            "post_approval_utilization": post_approval_utilization,
            "risk_level": risk_level,
            "authority_level": authority,
            "daily_burn_rate": daily_burn_rate,
            "projected_month_end_spending": projected_month_end,
            "budget_cushion": remaining_budget - total_cost,
            "can_afford": remaining_budget >= total_cost
        }

        self.logger.info(
            f"Perceived purchase request: ${total_cost:,.2f}, "
            f"Remaining: ${remaining_budget:,.2f}, "
            f"Risk: {risk_level}"
        )

        return context

    def approve_purchase(
        self,
        item_name: str,
        quantity: int,
        total_cost: float,
        monthly_budget: float,
        spent_so_far: float,
        days_remaining: int,
        priority: str = "medium",
        historical_average: float = None,
        stockout_risk: str = "low",
        requesting_agent: str = "Unknown",
        category: str = "miscellaneous"
    ) -> Dict[str, Any]:
        """
        Approve or reject purchase request using Claude API.

        This is the main decision-making method for financial approval.

        Args:
            item_name: Item to purchase
            quantity: Quantity requested
            total_cost: Total cost of purchase
            monthly_budget: Total monthly budget
            spent_so_far: Amount spent this month
            days_remaining: Days left in current month
            priority: Request priority (critical/high/medium/low)
            historical_average: Historical monthly spend in this category
            stockout_risk: Risk if not approved (high/medium/low)
            requesting_agent: Which agent made the request
            category: Spending category

        Returns:
            Decision dict with approve/reject, reasoning, conditions, etc.
        """
        # Perceive state
        remaining_budget = monthly_budget - spent_so_far
        state = {
            "item_name": item_name,
            "quantity": quantity,
            "total_cost": total_cost,
            "monthly_budget": monthly_budget,
            "spent_so_far": spent_so_far,
            "remaining_budget": remaining_budget,
            "days_remaining": days_remaining,
            "priority": priority,
            "historical_average": historical_average,
            "stockout_risk": stockout_risk,
            "requesting_agent": requesting_agent,
            "category": category
        }

        context = self.perceive(state)

        # Build prompt
        prompt = self._build_approval_prompt(context)

        # Reason using Claude
        decision = self.reason(
            context=context,
            prompt_template=prompt,
            temperature=0.6,  # Slightly lower for financial decisions
            max_tokens=2048
        )

        self.logger.info(
            f"Approval decision for {item_name} (${total_cost:,.2f}): "
            f"{decision.get('decision', 'unknown').upper()}, "
            f"Confidence={decision.get('confidence', 0):.2%}"
        )

        return decision

    def _build_approval_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build detailed prompt for Claude API.

        Args:
            context: Perception context

        Returns:
            Formatted prompt string
        """
        state = context["state"]
        analysis = context["financial_analysis"]
        kb = self.knowledge_base

        # Get category allocation if available
        category = state.get("category", "miscellaneous")
        category_info = kb["spending_categories"].get(category, {})
        category_allocation = category_info.get("monthly_allocation", 0)
        category_priority = category_info.get("priority", "medium")

        # Format historical context
        historical = state.get("historical_average")
        if historical:
            variance = total_cost - historical
            variance_pct = (variance / historical * 100) if historical > 0 else 0
            if variance_pct > 20:
                historical_note = f"⚠️ ${abs(variance):,.2f} ABOVE historical average ({variance_pct:+.0f}%)"
            elif variance_pct < -20:
                historical_note = f"✅ ${abs(variance):,.2f} BELOW historical average ({variance_pct:+.0f}%)"
            else:
                historical_note = f"➡️ Similar to historical average ({variance_pct:+.0f}%)"
        else:
            historical_note = "No historical data available for comparison"

        # Emergency reserve check
        emergency_reserve = kb["budget_policies"]["emergency_reserve"]
        after_approval = analysis["budget_cushion"]
        reserve_warning = ""
        if after_approval < emergency_reserve:
            reserve_warning = f"\n⚠️ WARNING: Approval would leave ${after_approval:,.2f} remaining (below ${emergency_reserve:,.2f} emergency reserve)"

        total_cost = state["total_cost"]

        prompt = f"""You are a Financial Agent for a hospital. Your goal is to ensure fiscal responsibility while enabling critical operations.

Purchase Request:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 Item: {state['item_name']}
📊 Quantity: {state['quantity']:,} units
💰 Total Cost: ${total_cost:,.2f}
🏷️ Category: {category.replace('_', ' ').title()}
🤖 Requesting Agent: {state.get('requesting_agent', 'Unknown')}

Budget Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 Monthly Budget: ${state['monthly_budget']:,.2f}
💸 Spent This Month: ${state['spent_so_far']:,.2f} ({analysis['budget_utilization']:.1%})
💰 Remaining: ${state['remaining_budget']:,.2f}
📅 Days Left in Month: {state['days_remaining']} days
📈 Daily Burn Rate: ${analysis['daily_burn_rate']:,.2f}/day
🔮 Projected Month-End: ${analysis['projected_month_end_spending']:,.2f}

After Approval:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Budget Remaining: ${analysis['budget_cushion']:,.2f}
📊 Utilization: {analysis['post_approval_utilization']:.1%}
🚨 Risk Level: {analysis['risk_level'].upper()}
👤 Authority Level: {analysis['authority_level'].replace('_', ' ').title()}{reserve_warning}

Category Allocation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 Category: {category.replace('_', ' ').title()}
💵 Monthly Allocation: ${category_allocation:,.2f}
🎯 Category Priority: {category_priority.upper()}

Context:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 Request Priority: {state['priority'].upper()}
⚠️ Stockout Risk: {state['stockout_risk'].upper()}
📊 Historical Context: {historical_note}

Financial Policies:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Emergency Reserve Required: ${kb['budget_policies']['emergency_reserve']:,.2f}
• Autonomous Approval Limit: ${kb['budget_policies']['autonomous_approval_limit']:,.2f}
• Critical Priority Allowance: {kb['budget_policies']['high_priority_allowance']:.0%} over budget

Your Task:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Decide whether to approve, partially approve, or reject this purchase request.

Consider:
1. Budget availability and risk level
2. Request priority vs. spending category priority
3. Stockout risk to patient care
4. Days remaining in month and burn rate
5. Emergency reserve requirements
6. Historical spending patterns
7. Total fiscal responsibility

Decision Options:
• "approve" - Full approval for ${total_cost:,.2f}
• "approve_partial" - Approve reduced amount (specify approved_amount)
• "reject" - Reject the request

Respond in JSON format:
{{
  "decision": "approve|approve_partial|reject",
  "approved_amount": <number (full amount for approve, reduced for approve_partial, 0 for reject)>,
  "reasoning": "detailed financial justification (2-3 sentences)",
  "conditions": ["condition 1", "condition 2"],
  "confidence": <0.0-1.0>,
  "risk_assessment": "low|medium|high|critical",
  "recommendations": ["recommendation 1", "recommendation 2"]
}}

IMPORTANT:
- If priority is "critical" and stockout_risk is "high", strongly consider approval
- If budget_cushion after approval < emergency_reserve, reject or approve partial
- Return ONLY valid JSON, no markdown formatting or extra text."""

        return prompt

    def get_budget_summary(self) -> Dict[str, Any]:
        """
        Get current budget status summary.

        Returns:
            Dict with budget allocation, spending, and projections
        """
        policies = self.knowledge_base["budget_policies"]
        categories = self.knowledge_base["spending_categories"]

        return {
            "monthly_budget": policies["monthly_budget"],
            "emergency_reserve": policies["emergency_reserve"],
            "autonomous_limit": policies["autonomous_approval_limit"],
            "categories": categories,
            "timestamp": datetime.now().isoformat()
        }

    def check_budget_health(
        self,
        spent_so_far: float,
        monthly_budget: float,
        days_remaining: int
    ) -> Dict[str, Any]:
        """
        Quick health check of budget status.

        Args:
            spent_so_far: Amount spent this month
            monthly_budget: Total monthly budget
            days_remaining: Days left in month

        Returns:
            Health status dict with warnings and recommendations
        """
        utilization = spent_so_far / monthly_budget if monthly_budget > 0 else 0

        risk_thresholds = self.knowledge_base["risk_thresholds"]
        if utilization < risk_thresholds["low_risk_percentage"]:
            health = "excellent"
            warning = None
        elif utilization < risk_thresholds["medium_risk_percentage"]:
            health = "good"
            warning = "Monitor spending closely"
        elif utilization < risk_thresholds["high_risk_percentage"]:
            health = "caution"
            warning = "High budget utilization - restrict non-critical spending"
        else:
            health = "critical"
            warning = "CRITICAL: Budget nearly exhausted - emergency approvals only"

        # Calculate daily budget
        days_in_month = 30
        days_elapsed = days_in_month - days_remaining
        if days_elapsed > 0:
            daily_burn = spent_so_far / days_elapsed
            projected_end = spent_so_far + (daily_burn * days_remaining)
            on_track = projected_end <= monthly_budget
        else:
            daily_burn = 0
            projected_end = spent_so_far
            on_track = True

        return {
            "health": health,
            "utilization": utilization,
            "warning": warning,
            "spent": spent_so_far,
            "budget": monthly_budget,
            "remaining": monthly_budget - spent_so_far,
            "daily_burn_rate": daily_burn,
            "projected_month_end": projected_end,
            "on_track": on_track,
            "days_remaining": days_remaining,
            "timestamp": datetime.now().isoformat()
        }

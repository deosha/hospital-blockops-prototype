"""
Facility Agent for Hospital BlockOps

Manages storage capacity, space allocation, and facility constraints.
"""

import logging
from typing import Dict, Any
from .agent_base import Agent


class FacilityAgent(Agent):
    """
    Facility Agent specializing in storage and space management.

    Responsibilities:
    - Monitor storage capacity across hospital facilities
    - Track space utilization
    - Approve/reject storage requests
    - Coordinate with Supply Chain for inventory storage
    """

    def __init__(
        self,
        name: str = "FAC-001",
        knowledge_base: Dict[str, Any] = None,
        model: str = "gpt-3.5-turbo"
    ):
        """
        Initialize Facility Agent.

        Args:
            name: Agent identifier
            knowledge_base: Domain knowledge including storage capacity,
                          utilization thresholds, etc.
            model: Claude model for decision-making
        """
        # Default knowledge base for facility management
        default_kb = {
            "storage_capacity": {
                "total_capacity": 5000,  # 5000 units total
                "current_utilization": 3200,  # 3200 units used
                "available": 1800,  # 1800 units available
                "reserved": 200,  # 200 units reserved
                "utilization_percentage": 0.64  # 64% utilized
            },
            "storage_policies": {
                "max_utilization_threshold": 0.90,  # 90% max
                "warning_threshold": 0.80,  # 80% warning
                "reserved_emergency_space": 200,
                "min_available_buffer": 100
            },
            "storage_zones": {
                "medical_supplies": {"capacity": 2000, "used": 1200},
                "equipment": {"capacity": 1500, "used": 1000},
                "pharmacy": {"capacity": 1000, "used": 800},
                "general": {"capacity": 500, "used": 200}
            }
        }

        # Merge with provided knowledge base
        if knowledge_base:
            default_kb.update(knowledge_base)

        super().__init__(
            name=name,
            role="Facility Management",
            knowledge_base=default_kb,
            model=model
        )

        self.logger = logging.getLogger(f"FacilityAgent.{name}")
        self.logger.info("Facility Agent initialized")

    def check_storage_availability(
        self,
        requested_quantity: int,
        item_category: str = "medical_supplies"
    ) -> Dict[str, Any]:
        """
        Check if storage is available for requested quantity.

        Args:
            requested_quantity: Number of units requested
            item_category: Category of items (medical_supplies, equipment, etc.)

        Returns:
            Dict with availability status and details
        """
        capacity_info = self.knowledge_base["storage_capacity"]
        policies = self.knowledge_base["storage_policies"]

        available = capacity_info["available"]
        reserved = policies["reserved_emergency_space"]
        usable = available - reserved

        can_store = requested_quantity <= usable

        # Calculate post-storage utilization
        total_capacity = capacity_info["total_capacity"]
        current_used = capacity_info["current_utilization"]
        post_storage_used = current_used + requested_quantity
        post_storage_utilization = post_storage_used / total_capacity

        # Determine risk level
        if post_storage_utilization < policies["warning_threshold"]:
            risk_level = "low"
        elif post_storage_utilization < policies["max_utilization_threshold"]:
            risk_level = "medium"
        else:
            risk_level = "high"

        return {
            "can_store": can_store,
            "requested_quantity": requested_quantity,
            "available_storage": available,
            "usable_storage": usable,
            "reserved_space": reserved,
            "post_storage_utilization": post_storage_utilization,
            "risk_level": risk_level,
            "max_storable": usable,
            "recommendation": (
                "Approved" if can_store
                else f"Cannot store {requested_quantity} units. Max: {usable} units"
            )
        }

    def update_storage(self, quantity: int, operation: str = "add") -> Dict[str, Any]:
        """
        Update storage utilization.

        Args:
            quantity: Quantity to add or remove
            operation: "add" or "remove"

        Returns:
            Updated storage status
        """
        capacity_info = self.knowledge_base["storage_capacity"]

        if operation == "add":
            capacity_info["current_utilization"] += quantity
            capacity_info["available"] -= quantity
        elif operation == "remove":
            capacity_info["current_utilization"] -= quantity
            capacity_info["available"] += quantity

        # Recalculate utilization percentage
        capacity_info["utilization_percentage"] = (
            capacity_info["current_utilization"] / capacity_info["total_capacity"]
        )

        self.logger.info(
            f"Storage updated: {operation} {quantity} units. "
            f"Utilization: {capacity_info['utilization_percentage']:.1%}"
        )

        return capacity_info

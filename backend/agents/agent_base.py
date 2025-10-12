"""
Base Agent Class for Hospital BlockOps Multi-Agent System

This module provides the foundation for all specialized agents in the system.
Each agent uses OpenAI GPT API for reasoning and decision-making.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@dataclass
class Decision:
    """Represents a single agent decision"""
    timestamp: str
    agent_name: str
    context: Dict[str, Any]
    reasoning: str
    action: Dict[str, Any]
    confidence: float
    response_time: float
    model_used: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary"""
        return asdict(self)


class Agent:
    """
    Base Agent class using OpenAI GPT for decision-making.

    All specialized agents (Supply Chain, Financial, Energy, etc.) inherit from this class.
    Provides common infrastructure for perception, reasoning, and action.
    """

    def __init__(
        self,
        name: str,
        role: str,
        knowledge_base: Dict[str, Any] = None,
        model: str = "gpt-4-turbo-preview",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize Agent.

        Args:
            name: Agent's unique name (e.g., "SC-001")
            role: Agent's role (e.g., "Supply Chain Management")
            knowledge_base: Dict of policies, constraints, and domain knowledge
            model: OpenAI model to use for reasoning (gpt-4-turbo-preview, gpt-4, gpt-3.5-turbo)
            max_retries: Maximum API retry attempts
            retry_delay: Delay between retries (seconds)
        """
        self.name = name
        self.role = role
        self.knowledge_base = knowledge_base or {}
        self.decision_history: List[Decision] = []
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please add it to your .env file."
            )

        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(f"Agent.{name}")
        self.logger.info(f"Initialized {role} agent: {name}")

    def perceive(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perceive current system state.

        This method processes incoming state information and prepares it
        for reasoning. Can be overridden by subclasses for specialized perception.

        Args:
            state: Current system state (inventory, budgets, schedules, etc.)

        Returns:
            Processed context for decision-making
        """
        self.logger.debug(f"Perceiving state: {state}")

        # Default perception: pass through state with agent context
        context = {
            "timestamp": datetime.now().isoformat(),
            "agent": {
                "name": self.name,
                "role": self.role
            },
            "state": state,
            "knowledge_base": self.knowledge_base
        }

        return context

    def reason(
        self,
        context: Dict[str, Any],
        prompt_template: str,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        Use OpenAI GPT API to reason about context and make decision.

        This is the core reasoning method that calls OpenAI API with retry logic.

        Args:
            context: Decision context from perceive()
            prompt_template: Formatted prompt with placeholders filled
            temperature: GPT temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Returns:
            Dict containing GPT's decision (parsed from JSON response)

        Raises:
            APIError: If API call fails after all retries
        """
        start_time = time.time()
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info(
                    f"Reasoning attempt {attempt}/{self.max_retries} "
                    f"using model {self.model}"
                )

                # Call OpenAI API
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{
                        "role": "system",
                        "content": "You are an AI agent in a hospital operations system. Respond with valid JSON only."
                    }, {
                        "role": "user",
                        "content": prompt_template
                    }],
                    response_format={"type": "json_object"}
                )

                # Extract response text
                response_text = response.choices[0].message.content
                response_time = time.time() - start_time

                self.logger.debug(f"GPT response: {response_text}")

                # Parse JSON response
                try:
                    decision_data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    self.logger.warning(
                        f"Failed to parse JSON response: {e}. "
                        f"Response: {response_text[:200]}"
                    )
                    # Try to extract JSON from markdown code blocks
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        json_text = response_text[json_start:json_end].strip()
                        decision_data = json.loads(json_text)
                    elif "```" in response_text:
                        json_start = response_text.find("```") + 3
                        json_end = response_text.find("```", json_start)
                        json_text = response_text[json_start:json_end].strip()
                        decision_data = json.loads(json_text)
                    else:
                        raise

                # Create Decision record
                decision = Decision(
                    timestamp=datetime.now().isoformat(),
                    agent_name=self.name,
                    context=context,
                    reasoning=decision_data.get("reasoning", decision_data.get("analysis", "")),
                    action=decision_data,
                    confidence=decision_data.get("confidence", 0.0),
                    response_time=response_time,
                    model_used=self.model
                )

                # Store in history
                self.decision_history.append(decision)

                self.logger.info(
                    f"Decision made in {response_time:.2f}s "
                    f"(confidence: {decision.confidence:.2%})"
                )

                return decision_data

            except RateLimitError as e:
                last_error = e
                wait_time = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                self.logger.warning(
                    f"Rate limit hit. Waiting {wait_time:.1f}s before retry..."
                )
                time.sleep(wait_time)

            except APIConnectionError as e:
                last_error = e
                self.logger.warning(
                    f"API connection error: {e}. "
                    f"Retrying in {self.retry_delay}s..."
                )
                time.sleep(self.retry_delay)

            except APIError as e:
                last_error = e
                self.logger.error(f"API error: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    raise

            except Exception as e:
                last_error = e
                self.logger.error(f"Unexpected error during reasoning: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    raise

        # If we get here, all retries failed
        raise APIError(
            f"Failed to get decision after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )

    def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the decision.

        This method translates the decision into concrete actions.
        Should be overridden by subclasses for specialized actions.

        Args:
            decision: Decision dict from reason()

        Returns:
            Dict containing action results
        """
        self.logger.info(f"Executing action: {decision}")

        # Default implementation: return decision as action result
        result = {
            "success": True,
            "action": decision,
            "timestamp": datetime.now().isoformat()
        }

        return result

    def get_reasoning_trace(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent decision history.

        Args:
            limit: Maximum number of decisions to return

        Returns:
            List of recent decisions (newest first)
        """
        return [d.to_dict() for d in self.decision_history[-limit:][::-1]]

    def get_last_decision(self) -> Optional[Dict[str, Any]]:
        """Get the most recent decision"""
        if self.decision_history:
            return self.decision_history[-1].to_dict()
        return None

    def clear_history(self) -> None:
        """Clear decision history"""
        self.logger.info("Clearing decision history")
        self.decision_history.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics.

        Returns:
            Dict with stats about decisions, confidence, response times, etc.
        """
        if not self.decision_history:
            return {
                "total_decisions": 0,
                "avg_confidence": 0.0,
                "avg_response_time": 0.0,
                "model": self.model
            }

        total = len(self.decision_history)
        avg_confidence = sum(d.confidence for d in self.decision_history) / total
        avg_response_time = sum(d.response_time for d in self.decision_history) / total

        return {
            "total_decisions": total,
            "avg_confidence": avg_confidence,
            "avg_response_time": avg_response_time,
            "model": self.model,
            "first_decision": self.decision_history[0].timestamp,
            "last_decision": self.decision_history[-1].timestamp
        }

    def __repr__(self) -> str:
        return f"Agent(name={self.name}, role={self.role}, decisions={len(self.decision_history)})"

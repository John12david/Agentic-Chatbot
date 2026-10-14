"""
concierge_agent.py
------------------
Main orchestrator for the Agentic Concierge chatbot.
Wires together DataLoader, IntentClassifier, ActionExecutor,
and ResponseBuilder into a single session-aware agent.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .data_loader import DataLoader
from .intent_classifier import IntentClassifier
from .action_executor import ActionExecutor
from .response_builder import ResponseBuilder


class ConciergeAgent:
    """
    Session-scoped insurance concierge agent.

    Manages authentication, conversation history, intent routing,
    action execution, and response generation for one customer session.
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialise the agent and all sub-components.

        Args:
            data_dir: Optional custom path to data/ folder.
        """
        self.data_loader       = DataLoader(data_dir=data_dir)
        self.intent_classifier = IntentClassifier()
        self.action_executor   = ActionExecutor(self.data_loader)
        self.response_builder  = ResponseBuilder()

        # Session state
        self.authenticated:             bool             = False
        self.customer_data:             Dict[str, Any]   = {}
        self.conversation_history:      List[Dict]       = []
        self.consecutive_unknown_count: int              = 0
        self.session_start_time:        datetime         = datetime.utcnow()
        self.audit_log:                 List[Dict]       = []

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self, policy_number: str) -> Dict[str, Any]:
        """
        Authenticate a customer by policy number.

        Args:
            policy_number: The policy number entered by the customer.

        Returns:
            Dict with keys: success (bool), customer (dict), welcome_message (str).
        """
        try:
            customer = self.data_loader.get_customer_by_policy(policy_number.strip())

            if not customer:
                self._log("AUTH_FAILED", {"policy_number": policy_number})
                return {
                    "success": False,
                    "customer": {},
                    "welcome_message": (
                        f"I couldn't find a policy with number **{policy_number}**. "
                        f"Please check and try again, or contact support.\n\n"
                        f"**Demo policy numbers:**\n"
                        f"• AZ-2026-1001 (Aisha Patel — Auto)\n"
                        f"• AZ-2026-1002 (Luis Garcia — Home)"
                    ),
                }

            self.authenticated  = True
            self.customer_data  = customer
            first_name          = customer.get("first_name", "Customer")

            self._log("AUTH_SUCCESS", {"customer_id": customer.get("customer_id")})

            return {
                "success": True,
                "customer": customer,
                "welcome_message": (
                    f"Welcome back, **{first_name}**! 👋\n\n"
                    f"I'm your Agentic Concierge. I can help you with:\n"
                    f"✓ Policy details and coverage\n"
                    f"✓ Claim status and filing\n"
                    f"✓ Payments and billing\n"
                    f"✓ Renewals and contact updates\n\n"
                    f"What can I help you with today?"
                ),
            }

        except Exception as e:
            self._log("AUTH_ERROR", {"error": str(e)})
            return {
                "success": False,
                "customer": {},
                "welcome_message": f"An error occurred during authentication: {e}",
            }

    # ------------------------------------------------------------------
    # Message processing
    # ------------------------------------------------------------------

    def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process one user message through the full pipeline.

        Pipeline: classify intent → execute action → build response → check escalation.

        Args:
            user_message: Raw text from the customer.

        Returns:
            Dict with keys: response (str), intent (str),
            action_taken (str), escalation_needed (bool).
        """
        if not self.authenticated:
            return {
                "response": "Please authenticate by entering your policy number first.",
                "intent": "UNKNOWN",
                "action_taken": "Authentication required",
                "escalation_needed": False,
            }

        try:
            # Step 1 — classify intent
            classification = self.intent_classifier.classify(user_message)
            intent     = classification["intent"]
            confidence = classification["confidence"]
            entities   = classification.get("entities", {})

            # Track consecutive unknowns for auto-escalation
            if intent == "UNKNOWN":
                self.consecutive_unknown_count += 1
            else:
                self.consecutive_unknown_count = 0

            # Step 2 — execute action
            action_result = self.action_executor.execute(
                intent,
                self.customer_data,
                user_message,
                self.conversation_history,
            )

            # Step 3 — build natural language response
            response_text = self.response_builder.build_response(
                intent,
                action_result,
                self.customer_data.get("first_name", "there"),
            )

            # Step 4 — check if escalation is needed
            escalation_needed = self._check_escalation(intent)

            # Step 5 — log both turns to history
            self.conversation_history.append({
                "role":       "user",
                "content":    user_message,
                "intent":     intent,
                "confidence": confidence,
                "entities":   entities,
                "timestamp":  datetime.utcnow().isoformat() + "Z",
            })
            self.conversation_history.append({
                "role":         "assistant",
                "content":      response_text,
                "intent":       intent,
                "action_taken": action_result.get("action_taken"),
                "timestamp":    datetime.utcnow().isoformat() + "Z",
            })

            self._log("MSG_PROCESSED", {
                "intent":           intent,
                "confidence":       confidence,
                "action_success":   action_result.get("success"),
                "escalation_needed":escalation_needed,
            })

            return {
                "response":          response_text,
                "intent":            intent,
                "action_taken":      action_result.get("action_taken", ""),
                "escalation_needed": escalation_needed,
            }

        except Exception as e:
            self._log("MSG_ERROR", {"error": str(e)})
            return {
                "response": (
                    f"I encountered an error processing your message. "
                    f"Please try again or ask to speak with an agent."
                ),
                "intent":            "UNKNOWN",
                "action_taken":      "Error",
                "escalation_needed": True,
            }

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _check_escalation(self, intent: str) -> bool:
        """Return True if escalation should be triggered."""
        if intent == "ESCALATION":
            return True
        if self.consecutive_unknown_count >= 3:
            return True
        return False

    def get_conversation_summary(self) -> str:
        """Return a human-readable session summary string."""
        if not self.conversation_history:
            return "No conversation history yet."

        duration_minutes = int(
            (datetime.utcnow() - self.session_start_time).total_seconds() / 60
        )
        user_turns = [t for t in self.conversation_history if t["role"] == "user"]

        lines = [
            "=== SESSION SUMMARY ===",
            f"Customer : {self.customer_data.get('first_name')} {self.customer_data.get('last_name')}",
            f"Policy   : {self.customer_data.get('policy_number')}",
            f"Duration : {duration_minutes} minute(s)",
            f"Turns    : {len(user_turns)}",
            "",
            "=== INTERACTION LOG ===",
        ]

        for i, turn in enumerate(user_turns, start=1):
            lines.append(
                f"\n[{i}] User: {turn['content'][:80]}"
                f"\n    Intent: {turn.get('intent')} "
                f"(confidence {turn.get('confidence', 0):.0%})"
            )

        return "\n".join(lines)

    def reset_session(self) -> None:
        """Reset all session state, keeping the data loader alive."""
        self.authenticated             = False
        self.customer_data             = {}
        self.conversation_history      = []
        self.consecutive_unknown_count = 0
        self.session_start_time        = datetime.utcnow()
        # Reload fresh data copies for the next session
        self.data_loader._load_all()

    def _log(self, event: str, details: Dict) -> None:
        """Append an entry to the in-memory audit log."""
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event":     event,
            "details":   details,
        })

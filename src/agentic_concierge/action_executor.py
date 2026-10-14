"""
action_executor.py
------------------
Executes business logic actions for each classified intent.
Reads from and writes to the DataLoader session store.
"""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .data_loader import DataLoader


class ActionExecutor:
    """
    Executes the correct data action for a given intent and
    returns a structured result dict consumed by ResponseBuilder.
    """

    def __init__(self, data_loader: DataLoader):
        """
        Initialise with a shared DataLoader instance.

        Args:
            data_loader: Shared DataLoader used across the session.
        """
        self.data_loader = data_loader

        # Regex patterns for entity extraction from free-text messages
        self.patterns = {
            "date": re.compile(
                r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b"
            ),
            "phone": re.compile(
                r"\b(?:\+?1[-.\s]?)?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\b"
            ),
            "email": re.compile(
                r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b"
            ),
            "incident_type": re.compile(
                r"\b(accident|collision|theft|stolen|damage|fire|flood|"
                r"water damage|vandalism|break-in|hit and run)\b",
                re.I,
            ),
            "address": re.compile(
                r"(\d+\s+[A-Za-z\s]+(?:St|Ave|Blvd|Rd|Drive|Lane|Way|Court|Dr|Ln)\.?)",
                re.I,
            ),
        }

    def execute(
        self,
        intent: str,
        customer_data: Dict[str, Any],
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Route an intent to the correct handler and return a result dict.

        Args:
            intent: Classified intent string.
            customer_data: Authenticated customer record.
            user_message: Raw user input text.
            conversation_history: Prior conversation turns (optional).

        Returns:
            Dict with keys: success (bool), data (dict), action_taken (str),
            and optionally error (str).
        """
        try:
            handler_map = {
                "POLICY_INQUIRY":  lambda: self.handle_policy_inquiry(customer_data),
                "CLAIM_STATUS":    lambda: self.handle_claim_status(customer_data),
                "NEW_CLAIM":       lambda: self.handle_new_claim(customer_data, user_message),
                "PAYMENT_INQUIRY": lambda: self.handle_payment_inquiry(customer_data),
                "RENEWAL_CHECK":   lambda: self.handle_renewal_check(customer_data),
                "CONTACT_UPDATE":  lambda: self.handle_contact_update(customer_data, user_message),
                "DOCUMENT_REQUEST":lambda: self.handle_document_request(customer_data),
                "ESCALATION":      lambda: self.handle_escalation(customer_data, user_message),
                "GREETING":        lambda: self.handle_greeting(),
                "UNKNOWN":         lambda: self.handle_unknown(),
            }

            handler = handler_map.get(intent, lambda: self.handle_unknown())
            result = handler()
            return {
                "success": True,
                "data": result,
                "action_taken": result.get("action_taken", "Action completed"),
            }

        except Exception as err:
            return {
                "success": False,
                "data": {},
                "action_taken": "Error executing action",
                "error": str(err),
            }

    # ------------------------------------------------------------------
    # Intent handlers
    # ------------------------------------------------------------------

    def handle_policy_inquiry(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve all policies for the authenticated customer."""
        customer_id = customer_data.get("customer_id")
        if not customer_id:
            return {"action_taken": "Failed: no customer ID", "policies": []}

        policies = self.data_loader.get_policies_by_customer(customer_id)
        summaries = []
        for p in policies:
            summaries.append({
                "policy_id":        p.get("policy_id"),
                "policy_number":    p.get("policy_number"),
                "type":             p.get("policy_type"),
                "status":           p.get("status"),
                "effective_date":   p.get("effective_date"),
                "expiry_date":      p.get("expiry_date"),
                "premium":          p.get("premium_amount"),
                "payment_frequency":p.get("payment_frequency"),
                "coverages":        p.get("coverages", []),
            })

        return {
            "action_taken": f"Retrieved {len(summaries)} policy(ies)",
            "policies": summaries,
        }

    def handle_claim_status(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve all claims for the authenticated customer."""
        customer_id = customer_data.get("customer_id")
        if not customer_id:
            return {"action_taken": "Failed: no customer ID", "claims": []}

        claims = self.data_loader.get_claims_by_customer(customer_id)
        summaries = []
        for c in claims:
            summaries.append({
                "claim_id":        c.get("claim_id"),
                "claim_number":    c.get("claim_number"),
                "date_of_loss":    c.get("date_of_loss"),
                "status":          c.get("status"),
                "type":            c.get("claim_type"),
                "assigned_adjuster": c.get("assigned_adjuster", {}),
                "reserve_amount":  c.get("reserve_amount", 0),
                "paid_amount":     c.get("paid_amount", 0),
                "last_update":     c.get("updated_at"),
            })

        return {
            "action_taken": f"Retrieved {len(summaries)} claim(s)",
            "claims": summaries,
        }

    def handle_new_claim(
        self, customer_data: Dict[str, Any], user_message: str
    ) -> Dict[str, Any]:
        """
        Extract incident details from the message and create a new claim.
        Falls back to sensible defaults when extraction fails.
        """
        customer_id   = customer_data.get("customer_id", "")
        policy_number = customer_data.get("policy_number", "")

        # Extract date
        date_match = self.patterns["date"].search(user_message)
        incident_date = date_match.group(1) if date_match else datetime.utcnow().strftime("%Y-%m-%d")

        # Extract incident type
        type_match = self.patterns["incident_type"].search(user_message)
        incident_type = type_match.group(1).lower() if type_match else "general"

        # Use message as description (trimmed)
        description = user_message.strip()[:300] if user_message.strip() else "No description provided"

        new_claim = self.data_loader.create_claim(
            customer_id, policy_number, incident_type, incident_date, description
        )

        if not new_claim:
            return {"action_taken": "Failed to create claim", "claim": {}}

        return {
            "action_taken": f"Created claim {new_claim.get('claim_id')}",
            "claim": new_claim,
        }

    def handle_payment_inquiry(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve all payment records for the authenticated customer."""
        customer_id = customer_data.get("customer_id")
        if not customer_id:
            return {"action_taken": "Failed: no customer ID", "payment_info": []}

        payments = self.data_loader.get_all_payments_by_customer(customer_id)
        summaries = []
        for p in payments:
            summaries.append({
                "payment_id":           p.get("payment_id"),
                "invoice_number":       p.get("invoice_number"),
                "policy_number":        p.get("policy_number"),
                "due_date":             p.get("due_date"),
                "amount_due":           p.get("amount_due", 0),
                "amount_paid":          p.get("amount_paid", 0),
                "status":               p.get("status"),
                "payment_method_masked":p.get("payment_method_masked"),
            })

        return {
            "action_taken": f"Retrieved {len(summaries)} payment record(s)",
            "payment_info": summaries,
        }

    def handle_renewal_check(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return renewal information for all customer policies."""
        customer_id = customer_data.get("customer_id")
        if not customer_id:
            return {"action_taken": "Failed: no customer ID", "renewals": []}

        policies = self.data_loader.get_policies_by_customer(customer_id)
        renewals = []
        for p in policies:
            renewals.append({
                "policy_number":   p.get("policy_number"),
                "status":          p.get("status"),
                "current_expiry":  p.get("expiry_date"),
                "premium":         p.get("premium_amount", 0),
                "payment_frequency": p.get("payment_frequency"),
                "auto_pay":        p.get("auto_pay_enrolled", False),
            })

        return {
            "action_taken": f"Retrieved renewal info for {len(renewals)} policy(ies)",
            "renewals": renewals,
        }

    def handle_contact_update(
        self, customer_data: Dict[str, Any], user_message: str
    ) -> Dict[str, Any]:
        """Extract and apply a contact field update from the user message."""
        customer_id = customer_data.get("customer_id", "")
        updates: Dict[str, str] = {}

        # Try phone
        phone_match = self.patterns["phone"].search(user_message)
        if phone_match:
            phone = "-".join(phone_match.groups())
            if self.data_loader.update_customer_contact(customer_id, "phone", phone):
                updates["phone"] = phone

        # Try email
        email_match = self.patterns["email"].search(user_message)
        if email_match:
            email = email_match.group(1)
            if self.data_loader.update_customer_contact(customer_id, "email", email):
                updates["email"] = email

        # Try address
        address_match = self.patterns["address"].search(user_message)
        if address_match:
            address = address_match.group(1).strip()
            if self.data_loader.update_customer_contact(customer_id, "address", address):
                updates["address"] = address

        return {
            "action_taken": f"Updated {len(updates)} field(s)" if updates else "No contact info found in message",
            "updates": updates,
        }

    def handle_document_request(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock document upload reference."""
        doc_id = "DOC-" + str(uuid.uuid4())[:8].upper()
        return {
            "action_taken": "Document upload session created",
            "document_id": doc_id,
            "accepted_formats": ["jpg", "jpeg", "png", "pdf"],
            "max_size_mb": 10,
        }

    def handle_escalation(
        self, customer_data: Dict[str, Any], reason: str
    ) -> Dict[str, Any]:
        """Create a mock escalation ticket and return reference details."""
        ticket_id = "ESC-" + str(uuid.uuid4())[:6].upper()
        return {
            "action_taken": f"Escalation ticket created: {ticket_id}",
            "ticket": {
                "ticket_id": ticket_id,
                "customer_id": customer_data.get("customer_id"),
                "reason": reason[:200] if reason else "Customer requested agent",
                "priority": "high",
                "estimated_response_sla_minutes": 15,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "status": "open",
            },
        }

    def handle_greeting(self) -> Dict[str, Any]:
        """Return a welcome response payload."""
        return {
            "action_taken": "Greeting delivered",
            "capabilities": [
                "Policy details and coverage",
                "Claim status and filing",
                "Payment and billing",
                "Policy renewal",
                "Contact update",
                "Document upload",
                "Agent escalation",
            ],
        }

    def handle_unknown(self) -> Dict[str, Any]:
        """Return a fallback payload for unrecognised intents."""
        return {
            "action_taken": "Fallback: intent not recognised",
            "suggestions": [
                "Check my policy",
                "Claim status",
                "File a claim",
                "Payment due",
                "Talk to an agent",
            ],
        }

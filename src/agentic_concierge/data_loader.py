"""
data_loader.py
--------------
JSON data access layer for the Agentic Concierge chatbot.
Loads mock insurance data from /data folder and provides
read/write methods for all entities.
"""

import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class DataLoader:
    """
    Manages loading and access to mock insurance JSON data.

    Loads customers, policies, claims, and payments from JSON files
    at startup. Maintains session-level copies for writes so the
    canonical files remain read-only.
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize DataLoader and load all JSON files.

        Args:
            data_dir: Path to the data directory. Defaults to a 'data'
                      folder relative to this file's parent (project root).
        """
        if data_dir is None:
            # Resolve data/ relative to project root (two levels up from this file)
            this_file = Path(__file__).resolve()
            project_root = this_file.parent.parent.parent
            data_dir = str(project_root / "data")

        self.data_dir = Path(data_dir)
        self.customers: List[Dict] = []
        self.policies: List[Dict] = []
        self.claims: List[Dict] = []
        self.payments: List[Dict] = []

        # Session-level writable copies (writes go here, not to disk files)
        self._session_customers: List[Dict] = []
        self._session_claims: List[Dict] = []
        self._session_payments: List[Dict] = []

        self._load_all()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_json(self, filename: str) -> List[Dict]:
        """
        Load a JSON file from the data directory.

        Args:
            filename: Name of the JSON file.

        Returns:
            Parsed list of dicts, or empty list on error.
        """
        filepath = self.data_dir / filename
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[DataLoader] WARNING: {filepath} not found. Starting empty.")
            return []
        except json.JSONDecodeError as e:
            print(f"[DataLoader] ERROR: Could not parse {filepath}: {e}")
            return []

    def _load_all(self) -> None:
        """Load all four JSON data files and initialise session copies."""
        self.customers = self._load_json("customers.json")
        self.policies = self._load_json("policies.json")
        self.claims = self._load_json("claims.json")
        self.payments = self._load_json("payments.json")

        # Deep-copy lists into session stores for safe writes
        import copy
        self._session_customers = copy.deepcopy(self.customers)
        self._session_claims = copy.deepcopy(self.claims)
        self._session_payments = copy.deepcopy(self.payments)

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    def get_customer_by_policy(self, policy_number: str) -> Optional[Dict]:
        """
        Find a customer record by their policy number.

        Args:
            policy_number: The customer's policy number (e.g. 'AZ-2026-1001').

        Returns:
            Customer dict if found, None otherwise.
        """
        try:
            policy_number = policy_number.strip().upper()
            for customer in self._session_customers:
                if customer.get("policy_number", "").upper() == policy_number:
                    return customer
            return None
        except Exception as e:
            print(f"[DataLoader] ERROR in get_customer_by_policy: {e}")
            return None

    def get_policy(self, policy_number: str) -> Optional[Dict]:
        """
        Find a policy record by policy number.

        Args:
            policy_number: The policy number string.

        Returns:
            Policy dict if found, None otherwise.
        """
        try:
            policy_number = policy_number.strip().upper()
            for policy in self.policies:
                if policy.get("policy_number", "").upper() == policy_number:
                    return policy
            return None
        except Exception as e:
            print(f"[DataLoader] ERROR in get_policy: {e}")
            return None

    def get_policies_by_customer(self, customer_id: str) -> List[Dict]:
        """
        Retrieve all policies belonging to a customer.

        Args:
            customer_id: The customer's unique ID.

        Returns:
            List of matching policy dicts (empty if none found).
        """
        try:
            return [p for p in self.policies if p.get("customer_id") == customer_id]
        except Exception as e:
            print(f"[DataLoader] ERROR in get_policies_by_customer: {e}")
            return []

    def get_claims_by_customer(self, customer_id: str) -> List[Dict]:
        """
        Retrieve all claims for a given customer from session store.

        Args:
            customer_id: The customer's unique ID.

        Returns:
            List of claim dicts (empty if none found).
        """
        try:
            return [c for c in self._session_claims if c.get("customer_id") == customer_id]
        except Exception as e:
            print(f"[DataLoader] ERROR in get_claims_by_customer: {e}")
            return []

    def get_payment_info(self, policy_number: str) -> Optional[Dict]:
        """
        Retrieve the most recent pending payment for a policy.

        Args:
            policy_number: The policy number.

        Returns:
            Payment dict if found, None otherwise.
        """
        try:
            policy_number = policy_number.strip().upper()
            matches = [
                p for p in self._session_payments
                if p.get("policy_number", "").upper() == policy_number
            ]
            if not matches:
                return None
            # Return the most recent/pending first
            pending = [m for m in matches if m.get("status") == "pending"]
            return pending[0] if pending else matches[-1]
        except Exception as e:
            print(f"[DataLoader] ERROR in get_payment_info: {e}")
            return None

    def get_all_payments_by_customer(self, customer_id: str) -> List[Dict]:
        """
        Retrieve all payment records for a customer.

        Args:
            customer_id: The customer's unique ID.

        Returns:
            List of payment dicts.
        """
        try:
            return [p for p in self._session_payments if p.get("customer_id") == customer_id]
        except Exception as e:
            print(f"[DataLoader] ERROR in get_all_payments_by_customer: {e}")
            return []

    # ------------------------------------------------------------------
    # Write methods (session-scoped only)
    # ------------------------------------------------------------------

    def update_customer_contact(self, customer_id: str, field: str, value: str) -> bool:
        """
        Update a contact field on a customer record (session-level only).

        Args:
            customer_id: The customer's unique ID.
            field: Field name to update ('phone', 'email', or 'address').
            value: New value for the field.

        Returns:
            True if update succeeded, False otherwise.
        """
        allowed_fields = {"phone", "email", "address", "preferred_contact_method"}
        try:
            if field not in allowed_fields:
                print(f"[DataLoader] ERROR: Field '{field}' is not updatable.")
                return False

            for customer in self._session_customers:
                if customer.get("customer_id") == customer_id:
                    customer[field] = value
                    customer["updated_at"] = datetime.utcnow().isoformat() + "Z"
                    return True

            print(f"[DataLoader] ERROR: Customer '{customer_id}' not found.")
            return False
        except Exception as e:
            print(f"[DataLoader] ERROR in update_customer_contact: {e}")
            return False

    def create_claim(
        self,
        customer_id: str,
        policy_number: str,
        incident_type: str,
        incident_date: str,
        description: str,
    ) -> Dict[str, Any]:
        """
        Create a new claim record in the session store.

        Args:
            customer_id: The claimant's customer ID.
            policy_number: The policy under which the claim is filed.
            incident_type: Type of incident (e.g. 'auto', 'theft').
            incident_date: Date of loss in YYYY-MM-DD format.
            description: Short description of the incident.

        Returns:
            The newly created claim dict (with generated claim_id).
        """
        try:
            # Generate claim ID: CLM-YYYYMMDD-XXXX
            date_str = datetime.utcnow().strftime("%Y%m%d")
            suffix = str(random.randint(1000, 9999))
            claim_id = f"CLM-{date_str}-{suffix}"
            claim_number = f"CLM-{datetime.utcnow().year}-{suffix}"

            # Look up the policy_id from policy_number
            policy = self.get_policy(policy_number)
            policy_id = policy.get("policy_id", "UNKNOWN") if policy else "UNKNOWN"

            now = datetime.utcnow().isoformat() + "Z"
            new_claim = {
                "claim_id": claim_id,
                "claim_number": claim_number,
                "policy_id": policy_id,
                "policy_number": policy_number.upper(),
                "customer_id": customer_id,
                "date_of_loss": incident_date,
                "reported_at": now,
                "claim_type": incident_type.lower(),
                "status": "reported",
                "assigned_adjuster": {
                    "name": "Pending Assignment",
                    "email": "claims@insureco.example",
                    "phone": "+18005550000",
                },
                "reserve_amount": 0.00,
                "paid_amount": 0.00,
                "description": description,
                "attachments": [],
                "history": [
                    {
                        "timestamp": now,
                        "actor": "system",
                        "action": "reported",
                        "note": "FNOL created via Agentic Concierge",
                    }
                ],
                "created_at": now,
                "updated_at": now,
            }

            self._session_claims.append(new_claim)
            return new_claim

        except Exception as e:
            print(f"[DataLoader] ERROR in create_claim: {e}")
            return {}

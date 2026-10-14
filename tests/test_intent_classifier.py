"""
test_intent_classifier.py
--------------------------
Unit tests for the IntentClassifier.
Run with: pytest tests/ -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agentic_concierge.intent_classifier import IntentClassifier


class TestIntentClassifier:
    """Tests for rule-based intent classification."""

    def setup_method(self):
        self.clf = IntentClassifier()

    def test_policy_inquiry(self):
        result = self.clf.classify("What does my policy cover?")
        assert result["intent"] == "POLICY_INQUIRY"

    def test_claim_status(self):
        result = self.clf.classify("What is the status of my claim?")
        assert result["intent"] == "CLAIM_STATUS"

    def test_new_claim(self):
        result = self.clf.classify("I want to file a claim for an accident")
        assert result["intent"] == "NEW_CLAIM"

    def test_payment_inquiry(self):
        result = self.clf.classify("When is my next payment due?")
        assert result["intent"] == "PAYMENT_INQUIRY"

    def test_renewal_check(self):
        result = self.clf.classify("When does my policy expire?")
        assert result["intent"] == "RENEWAL_CHECK"

    def test_contact_update(self):
        result = self.clf.classify("I want to update my phone number")
        assert result["intent"] == "CONTACT_UPDATE"

    def test_escalation(self):
        result = self.clf.classify("I want to speak to a human agent")
        assert result["intent"] == "ESCALATION"

    def test_greeting(self):
        result = self.clf.classify("Hello!")
        assert result["intent"] == "GREETING"

    def test_unknown(self):
        result = self.clf.classify("xyzzy nonsense garbage text 123")
        assert result["intent"] == "UNKNOWN"

    def test_empty_string(self):
        result = self.clf.classify("")
        assert result["intent"] == "UNKNOWN"
        assert result["confidence"] == 0.0

    def test_confidence_present(self):
        result = self.clf.classify("What is my policy coverage?")
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_entity_extraction_policy_number(self):
        result = self.clf.classify("Tell me about policy AZ-2026-1001")
        assert "policy_number" in result["entities"]

    def test_entity_extraction_phone(self):
        result = self.clf.classify("Update my phone to 415-555-0199")
        assert "phone" in result["entities"]

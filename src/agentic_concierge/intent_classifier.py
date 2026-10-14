"""
intent_classifier.py
--------------------
Rule-based intent classifier for the Agentic Concierge chatbot.
Uses weighted keyword matching and regex entity extraction.
No external APIs or ML models required.
"""

import re
from typing import Any, Dict, List, Optional, Tuple


class IntentClassifier:
    """
    Classifies customer messages into insurance service intents
    using weighted keyword matching and confidence scoring.
    """

    INTENTS = [
        "POLICY_INQUIRY",
        "CLAIM_STATUS",
        "NEW_CLAIM",
        "PAYMENT_INQUIRY",
        "RENEWAL_CHECK",
        "CONTACT_UPDATE",
        "DOCUMENT_REQUEST",
        "ESCALATION",
        "GREETING",
        "UNKNOWN",
    ]

    def __init__(self, confidence_threshold: float = 0.05):
        """
        Initialise the classifier with keyword dictionaries.

        Args:
            confidence_threshold: Minimum normalised score to accept an intent.
                                  Lower = more permissive. Default 0.05.
        """
        self.confidence_threshold = confidence_threshold

        # Keyword weights: 3 = high signal, 2 = medium, 1 = low
        self.intent_keywords: Dict[str, Dict[str, int]] = {
            "POLICY_INQUIRY": {
                "policy": 3, "coverage": 3, "covered": 2, "cover": 2,
                "deductible": 3, "insured": 2, "insurance": 1,
                "limit": 2, "what does my policy": 3, "policy details": 3,
                "policy information": 3, "my policy": 2, "my plan": 2,
                "active policy": 3, "policy status": 3, "policy number": 2,
                "what am i covered": 3, "what is covered": 3,
            },
            "CLAIM_STATUS": {
                "claim status": 3, "where is my claim": 3, "check claim": 3,
                "claim update": 3, "status of my claim": 3, "my claim": 2,
                "claim number": 2, "adjuster": 2, "how is my claim": 3,
                "claim progress": 3, "track claim": 3, "claim inquiry": 3,
                "what happened to my claim": 3, "claim pending": 2,
                "investigation": 1, "approved": 1, "denied": 1,
            },
            "NEW_CLAIM": {
                "file a claim": 3, "report a claim": 3, "new claim": 3,
                "submit a claim": 3, "raise a claim": 3, "raise claim": 3,
                "i had an accident": 3, "accident": 2, "collision": 2,
                "theft": 2, "stolen": 2, "damage": 2, "damaged": 2,
                "fire": 2, "flood": 2, "vandalism": 2, "hit and run": 3,
                "break in": 2, "broke in": 2, "water damage": 2,
                "report incident": 3, "incident": 1, "make a claim": 3,
                "open a claim": 3, "i want to claim": 3,
            },
            "PAYMENT_INQUIRY": {
                "payment": 3, "pay": 2, "premium": 3, "bill": 2,
                "invoice": 3, "due": 2, "amount due": 3, "balance": 2,
                "when is my payment": 3, "next payment": 3, "how much do i owe": 3,
                "billing": 3, "autopay": 2, "auto pay": 2, "auto-pay": 2,
                "payment history": 3, "payment method": 2, "overdue": 2,
                "past due": 3, "payment due": 3,
            },
            "RENEWAL_CHECK": {
                "renewal": 3, "renew": 3, "expiry": 3, "expiration": 3,
                "when does my policy expire": 3, "expire": 2, "expires": 2,
                "policy renewal": 3, "renewal date": 3, "renewing": 2,
                "upcoming renewal": 3, "policy expiry": 3, "end date": 2,
                "valid until": 2, "policy end": 2,
            },
            "CONTACT_UPDATE": {
                "update": 2, "change my": 2, "update my": 3,
                "phone number": 3, "email address": 3, "email": 2,
                "address": 2, "mailing address": 3, "new phone": 3,
                "new email": 3, "new address": 3, "contact details": 3,
                "contact information": 3, "update contact": 3,
                "change my phone": 3, "change my email": 3,
                "change my address": 3,
            },
            "DOCUMENT_REQUEST": {
                "upload": 3, "document": 3, "documents": 3, "photo": 2,
                "photos": 2, "picture": 2, "send documents": 3,
                "policy document": 3, "certificate": 2, "proof": 2,
                "evidence": 2, "attach": 2, "attachment": 2,
                "id card": 2, "insurance card": 2, "police report": 2,
                "upload photos": 3,
            },
            "ESCALATION": {
                "human": 3, "agent": 3, "speak to someone": 3,
                "talk to a person": 3, "real person": 3, "manager": 3,
                "supervisor": 3, "escalate": 3, "frustrated": 2,
                "unhappy": 2, "dissatisfied": 2, "not helpful": 2,
                "useless": 2, "complaint": 3, "complain": 2,
                "this is ridiculous": 3, "transfer me": 2,
                "connect me": 2, "i want to speak": 3,
            },
            "GREETING": {
                "hello": 3, "hi": 3, "hey": 2, "good morning": 3,
                "good afternoon": 3, "good evening": 3, "howdy": 2,
                "greetings": 2, "help me": 1, "i need help": 1,
                "what can you do": 2, "how can you help": 2,
            },
        }

        # Regex patterns for extracting entities from messages
        self.entity_patterns: Dict[str, re.Pattern] = {
            "policy_number": re.compile(r"\b([A-Z]{2,3}-\d{4}-\d{4})\b", re.I),
            "claim_number": re.compile(r"\b(CLM-\d{4,8}-\d{3,4})\b", re.I),
            "date": re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b"),
            "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\b"),
            "email": re.compile(r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b"),
            "amount": re.compile(r"\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)"),
        }

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify a user message into the best-matching intent.

        Args:
            text: Raw user message string.

        Returns:
            Dict with keys:
              - intent (str): Best-matching intent name.
              - confidence (float): Normalised score 0..1.
              - matched_keywords (list): Keywords that contributed to the score.
              - entities (dict): Extracted entities by type.
        """
        if not text or not text.strip():
            return {
                "intent": "UNKNOWN",
                "confidence": 0.0,
                "matched_keywords": [],
                "entities": {},
            }

        normalized = text.lower().strip()

        best_intent = "UNKNOWN"
        best_score = 0.0
        best_matched: List[str] = []

        for intent_name, keywords in self.intent_keywords.items():
            raw_score, matched = self._score_intent(normalized, intent_name, keywords)
            normalized_score = self._normalize_score(raw_score, intent_name)

            if normalized_score > best_score:
                best_score = normalized_score
                best_intent = intent_name
                best_matched = matched

        if best_score < self.confidence_threshold:
            return {
                "intent": "UNKNOWN",
                "confidence": float(best_score),
                "matched_keywords": [],
                "entities": self.extract_entities(text),
            }

        return {
            "intent": best_intent,
            "confidence": float(best_score),
            "matched_keywords": best_matched,
            "entities": self.extract_entities(text),
        }

    def _score_intent(
        self, normalized_text: str, intent: str, keywords: Dict[str, int]
    ) -> Tuple[float, List[str]]:
        """Score an intent by counting weighted keyword matches."""
        score = 0.0
        matched: List[str] = []

        for keyword, weight in keywords.items():
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, normalized_text):
                score += weight
                matched.append(keyword)

        return score, matched

    def _normalize_score(self, raw_score: float, intent: str) -> float:
        """Normalise raw score to 0..1 using a stable, intent-aware scale.

        The previous formula divided by the full sum of every keyword weight for
        an intent, which became increasingly punitive as the dictionary grew.
        This version uses a bounded denominator so short, high-signal phrases
        still score clearly above the confidence threshold.
        """
        if raw_score <= 0:
            return 0.0

        max_possible = sum(self.intent_keywords[intent].values())
        if max_possible == 0:
            return 0.0

        # Keep the score from being overly diluted by large keyword lists.
        base_score = raw_score / max(3.0, max_possible / 2.0)
        # Give multi-word phrase matches a small boost without overpowering other intents.
        phrase_bonus = 0.05 if any(" " in keyword for keyword in self.intent_keywords[intent]) else 0.0
        normalized = min(1.0, base_score + phrase_bonus)
        return round(normalized, 6)

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract structured entities from a message using regex.

        Args:
            text: Raw user message.

        Returns:
            Dict mapping entity type to list of found values.
        """
        entities: Dict[str, List[str]] = {}
        for entity_type, pattern in self.entity_patterns.items():
            matches = pattern.findall(text)
            if matches:
                if matches and isinstance(matches[0], tuple):
                    entities[entity_type] = ["".join(m) for m in matches]
                else:
                    entities[entity_type] = list(matches)
        return entities

    def get_all_intents(self) -> List[str]:
        """Return all supported intent names."""
        return self.INTENTS

"""
response_builder.py
-------------------
Builds natural language responses from structured ActionExecutor results.
Uses string templates — no external LLM required.
"""

from typing import Any, Dict


class ResponseBuilder:
    """
    Converts ActionExecutor result dicts into conversational
    response strings for display in the Streamlit UI.
    """

    def build_response(
        self,
        intent: str,
        action_result: Dict[str, Any],
        customer_name: str = "there",
    ) -> str:
        """
        Build a conversational response string.

        Args:
            intent: Classified intent name.
            action_result: Dict returned by ActionExecutor.execute().
            customer_name: Customer's first name for personalisation.

        Returns:
            Formatted markdown string ready for Streamlit display.
        """
        if not action_result.get("success"):
            error = action_result.get("error", "An unexpected error occurred.")
            return (
                f"I apologise, {customer_name}. I encountered an issue.\n\n"
                f"**Error:** {error}\n\n"
                f"Please try again or ask to speak with an agent."
            )

        data = action_result.get("data", {})

        dispatch = {
            "POLICY_INQUIRY":   self._policy_response,
            "CLAIM_STATUS":     self._claim_status_response,
            "NEW_CLAIM":        self._new_claim_response,
            "PAYMENT_INQUIRY":  self._payment_response,
            "RENEWAL_CHECK":    self._renewal_response,
            "CONTACT_UPDATE":   self._contact_update_response,
            "DOCUMENT_REQUEST": self._document_response,
            "ESCALATION":       self._escalation_response,
            "GREETING":         self._greeting_response,
            "UNKNOWN":          self._unknown_response,
        }

        handler = dispatch.get(intent, self._unknown_response)
        return handler(data, customer_name)

    # ------------------------------------------------------------------
    # Intent-specific response builders
    # ------------------------------------------------------------------

    def _policy_response(self, data: Dict, name: str) -> str:
        policies = data.get("policies", [])
        if not policies:
            return (
                f"Hi {name}, I couldn't find any active policies on your account. "
                f"Please contact support if you believe this is an error."
            )
        cards = "\n\n".join(self._format_policy_card(p) for p in policies)
        count = len(policies)
        return (
            f"Hi {name}! Here {'is' if count == 1 else 'are'} your "
            f"{count} policy('s) on file:\n\n{cards}\n\n"
            f"Would you like more details on coverage limits or deductibles?"
        )

    def _claim_status_response(self, data: Dict, name: str) -> str:
        claims = data.get("claims", [])
        if not claims:
            return (
                f"Hi {name}, I don't see any existing claims on your account. "
                f"Would you like to file a new claim?"
            )
        cards = "\n\n".join(self._format_claim_card(c) for c in claims)
        count = len(claims)
        return (
            f"Hi {name}! Here {'is' if count == 1 else 'are'} your "
            f"{count} claim(s):\n\n{cards}\n\n"
            f"Would you like to take any action on these claims?"
        )

    def _new_claim_response(self, data: Dict, name: str) -> str:
        claim = data.get("claim", {})
        if not claim:
            return (
                f"I'd like to help you file a claim, {name}. "
                f"Please provide:\n"
                f"• When did the incident occur?\n"
                f"• What type of incident? (accident, theft, damage, etc.)\n"
                f"• A brief description of what happened."
            )
        return (
            f"✅ **Claim filed successfully, {name}!**\n\n"
            f"**Claim ID:** `{claim.get('claim_id', 'N/A')}`\n"
            f"**Claim Number:** {claim.get('claim_number', 'N/A')}\n"
            f"**Type:** {claim.get('claim_type', 'N/A').title()}\n"
            f"**Date of Loss:** {claim.get('date_of_loss', 'N/A')}\n"
            f"**Status:** {claim.get('status', 'Reported').title()}\n\n"
            f"Our claims team will review your case and be in touch shortly. "
            f"Please keep your Claim ID for future reference."
        )

    def _payment_response(self, data: Dict, name: str) -> str:
        payments = data.get("payment_info", [])
        if not payments:
            return (
                f"Hi {name}, no payment records found on your account. "
                f"Your policies may be fully paid up!"
            )
        cards = "\n\n".join(self._format_payment_card(p) for p in payments)
        return (
            f"Hi {name}! Here is your current billing information:\n\n{cards}\n\n"
            f"You can pay online, by phone, or set up auto-pay. "
            f"Would you like help with any payment options?"
        )

    def _renewal_response(self, data: Dict, name: str) -> str:
        renewals = data.get("renewals", [])
        if not renewals:
            return f"Hi {name}, I couldn't find renewal information for your account."
        cards = "\n\n".join(self._format_renewal_card(r) for r in renewals)
        return (
            f"Hi {name}! Here is your renewal information:\n\n{cards}\n\n"
            f"Your policy will renew automatically unless you request otherwise. "
            f"Have questions about your renewal? I'm here to help!"
        )

    def _contact_update_response(self, data: Dict, name: str) -> str:
        updates = data.get("updates", {})
        if not updates:
            return (
                f"I wasn't able to find new contact information in your message, {name}. "
                f"Could you provide the details you'd like to update?\n"
                f"(e.g. 'Change my phone to 415-555-0199' or 'Update my email to new@email.com')"
            )
        fields = "\n".join(f"• **{k.title()}:** {v}" for k, v in updates.items())
        return (
            f"✅ **Contact information updated, {name}!**\n\n"
            f"Updated fields:\n{fields}\n\n"
            f"We'll use this information for all future policy communications."
        )

    def _document_response(self, data: Dict, name: str) -> str:
        doc_id = data.get("document_id", "DOC-UNKNOWN")
        formats = ", ".join(data.get("accepted_formats", ["jpg", "png", "pdf"]))
        max_size = data.get("max_size_mb", 10)
        return (
            f"📎 **Ready to receive your documents, {name}!**\n\n"
            f"**Upload Reference:** `{doc_id}`\n"
            f"**Accepted formats:** {formats}\n"
            f"**Max file size:** {max_size} MB\n\n"
            f"Please attach your files (photos, police report, invoices). "
            f"Uploading relevant documents helps us process your case faster."
        )

    def _escalation_response(self, data: Dict, name: str) -> str:
        ticket = data.get("ticket", {})
        ticket_id = ticket.get("ticket_id", "ESC-UNKNOWN")
        sla = ticket.get("estimated_response_sla_minutes", 15)
        return (
            f"I understand, {name}, and I sincerely apologise for any frustration. "
            f"I'm connecting you with a senior agent right now.\n\n"
            f"**Escalation Ticket:** `{ticket_id}`\n"
            f"**Priority:** High\n"
            f"**Expected Response:** Within {sla} minutes\n\n"
            f"An agent will reach out to you at your registered contact. "
            f"Thank you for your patience."
        )

    def _greeting_response(self, data: Dict, name: str) -> str:
        capabilities = data.get("capabilities", [])
        cap_list = "\n".join(f"✓ {c}" for c in capabilities)
        return (
            f"Hello {name}! Welcome to the Insure Assist. 👋\n\n"
            f"I'm here to help you with:\n{cap_list}\n\n"
            f"What can I assist you with today?"
        )

    def _unknown_response(self, data: Dict, name: str) -> str:
        suggestions = data.get("suggestions", [])
        sug_list = "\n".join(f"• {s}" for s in suggestions) if suggestions else ""
        return (
            f"I'm not sure I understood that, {name}. Here's what I can help with:\n\n"
            f"• 📋 **Policy information** — coverage, limits, deductibles\n"
            f"• 📊 **Claim status** — check where your claim stands\n"
            f"• 📝 **File a claim** — report an accident or incident\n"
            f"• 💰 **Payments** — check due dates or payment history\n"
            f"• 🔄 **Renewals** — see your upcoming renewal dates\n"
            f"• 📞 **Update contact** — change phone, email, or address\n"
            f"• 📎 **Upload documents** — send photos or reports\n"
            f"• 👤 **Speak to an agent** — escalate to a human\n\n"
            f"Which of these would you like help with?"
        )

    # ------------------------------------------------------------------
    # Card formatters
    # ------------------------------------------------------------------

    def _format_policy_card(self, policy: Dict) -> str:
        coverages = policy.get("coverages", [])
        cov_lines = "\n".join(
            f"  - {c.get('coverage_type', '').title()}: "
            f"Limit ${c.get('limit', 0):,.0f} / Deductible ${c.get('deductible', 0):,.0f}"
            for c in coverages
        )
        return (
            f"**Policy: {policy.get('policy_number', 'N/A')}** "
            f"({policy.get('type', 'N/A').title()})\n"
            f"Status: **{policy.get('status', 'N/A').upper()}** | "
            f"Valid: {policy.get('effective_date', 'N/A')} → {policy.get('expiry_date', 'N/A')}\n"
            f"Premium: **${policy.get('premium', 0):,.2f}** / {policy.get('payment_frequency', 'year').title()}\n"
            f"Coverage:\n{cov_lines if cov_lines else '  - Not available'}"
        )

    def _format_claim_card(self, claim: Dict) -> str:
        status_emoji = {
            "reported": "📋", "open": "📂", "investigating": "🔍",
            "approved": "✅", "paid": "💚", "denied": "❌", "closed": "🔒",
        }.get(claim.get("status", "").lower(), "📌")
        adjuster = claim.get("assigned_adjuster", {})
        adj_name = adjuster.get("name", "TBD") if isinstance(adjuster, dict) else "TBD"
        return (
            f"{status_emoji} **{claim.get('claim_number', 'N/A')}**\n"
            f"Type: {claim.get('type', 'N/A').title()} | "
            f"Date of Loss: {claim.get('date_of_loss', 'N/A')}\n"
            f"Status: **{claim.get('status', 'N/A').title()}**\n"
            f"Reserve: ${claim.get('reserve_amount', 0):,.2f} | "
            f"Paid: ${claim.get('paid_amount', 0):,.2f}\n"
            f"Adjuster: {adj_name}"
        )

    def _format_payment_card(self, payment: Dict) -> str:
        status = payment.get("status", "unknown")
        emoji = "✅" if status == "paid" else "⏰" if status == "pending" else "⚠️"
        return (
            f"{emoji} **Policy: {payment.get('policy_number', 'N/A')}**\n"
            f"Invoice: {payment.get('invoice_number', 'N/A')} | "
            f"Due: {payment.get('due_date', 'N/A')}\n"
            f"Amount Due: **${payment.get('amount_due', 0):,.2f}** | "
            f"Paid: ${payment.get('amount_paid', 0):,.2f}\n"
            f"Status: **{status.upper()}** | "
            f"Method: {payment.get('payment_method_masked', 'N/A')}"
        )

    def _format_renewal_card(self, renewal: Dict) -> str:
        auto_pay = "✅ Auto-pay ON" if renewal.get("auto_pay") else "❌ Auto-pay OFF"
        return (
            f"**Policy: {renewal.get('policy_number', 'N/A')}**\n"
            f"Status: {renewal.get('status', 'N/A').upper()} | "
            f"Expires: {renewal.get('current_expiry', 'N/A')}\n"
            f"Annual Premium: **${renewal.get('premium', 0):,.2f}** "
            f"({renewal.get('payment_frequency', 'annual').title()}) | {auto_pay}"
        )

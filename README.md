# 🛡️ Agentic Concierge — Insurance Service Chatbot

> AI Practitioner+ Capstone Project | GitHub Copilot Batch

A fully rule-based, LLM-free insurance service chatbot built with Python and Streamlit.
Demonstrates an Agentic AI concierge that understands customer intent, retrieves data,
and takes actions — all without any external API calls.

---

## 🚀 Quick Start

```bash
# 1. Clone / unzip the project
cd agentic-concierge

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

Open your browser at **http://localhost:8501**

**Demo accounts:**
| Policy Number | Customer | Policy Type |
|---|---|---|
| `AZ-2026-1001` | Aisha Patel | Auto Insurance |
| `AZ-2026-1002` | Luis Garcia | Home Insurance |

---

## 💡 What It Does

| Capability | Description |
|---|---|
| 📋 Policy Inquiry | View coverage, limits, deductibles |
| 📊 Claim Status | Check status of existing claims |
| 📝 File a Claim | Report an incident and get a Claim ID |
| 💰 Payment Info | See due dates and payment history |
| 🔄 Renewal Check | View policy expiry and renewal details |
| 📞 Contact Update | Change phone, email, or address |
| 📎 Document Upload | Generate a document upload reference |
| 👤 Escalation | Connect to a human agent with ticket ID |

---

## 🗂️ Project Structure

```
agentic-concierge/
├── app.py                              # Streamlit UI entry point
├── requirements.txt
├── README.md
├── data/
│   ├── customers.json                  # Mock customer records
│   ├── policies.json                   # Mock policy data
│   ├── claims.json                     # Mock claims data
│   └── payments.json                   # Mock payment records
├── src/
│   └── agentic_concierge/
│       ├── __init__.py
│       ├── data_loader.py              # JSON read/write layer
│       ├── intent_classifier.py        # Keyword-based intent classification
│       ├── action_executor.py          # Business logic per intent
│       ├── response_builder.py         # Natural language response templates
│       └── concierge_agent.py          # Main orchestrator
└── tests/
    └── test_intent_classifier.py       # Unit tests (13 tests, all passing)
```

---

## 🤖 How GitHub Copilot Was Used

| Phase | Copilot Contribution |
|---|---|
| Requirements | Generated functional requirements table and user stories |
| Architecture | Designed component responsibilities and data flow |
| Schema Design | Generated all 4 JSON schemas with sample records |
| data_loader.py | Full module generated from a detailed spec prompt |
| intent_classifier.py | Keyword dictionaries and classification logic |
| action_executor.py | All 10 handler methods with regex extraction |
| response_builder.py | All response templates and card formatters |
| concierge_agent.py | Full orchestrator wiring all components |
| app.py | Complete Streamlit UI with session state |
| Tests | 13 unit tests generated from function signatures |
| README | This file generated with a single prompt |

---

## 🏗️ Architecture

```
Customer (Browser)
      │
      ▼
Streamlit UI (app.py)
      │
      ▼
ConciergeAgent (orchestrator)
      │
      ├── IntentClassifier  ──► keyword matching → intent + confidence
      ├── ActionExecutor    ──► DataLoader read/write → result dict
      ├── ResponseBuilder   ──► templates → natural language string
      └── DataLoader        ──► JSON files (session-scoped writes)
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Expected: **13 passed**

---

## 📋 Capstone Details

- **Program:** AI Practitioner+ (GitHub Copilot Batch)
- **Start Date:** 23 June 2026
- **Submission:** 30 June 2026
- **Developer:** John David — Senior Performance Test Engineer, Xebia

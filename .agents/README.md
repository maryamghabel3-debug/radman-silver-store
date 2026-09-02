# RADMAN SILVER 925 — Agent Platform Foundation

The **RADMAN Agent Platform** is a lightweight, human-in-the-loop (HITL) autonomous agent foundation designed for **RADMAN SILVER 925** (Persian luxury 925 sterling silver e-commerce store).

It introduces a structured skill-based architecture under `.agents/skills/` while maintaining 100% backward compatibility with all existing on-host and catalog agents in `agents/`.

---

## 1. Directory Structure

```text
.agents/
├── README.md                           # This document
├── config/
│   ├── agent-registry.json             # Skill definitions, capabilities, and contracts
│   ├── radman-business-rules.json      # Machine-readable luxury store business rules
│   └── approval-gates.json             # Human-In-The-Loop gate policies
├── skills/
│   ├── radman-orchestrator/
│   │   └── SKILL.md                    # Master task planner & gate routing
│   ├── radman-seo-agent/
│   │   └── SKILL.md                    # Luxury Persian SEO & Rank Math schema
│   ├── radman-content-agent/
│   │   └── SKILL.md                    # Brand storytelling, education & social copy
│   ├── radman-sales-agent/
│   │   └── SKILL.md                    # Consultative customer inquiries & size guides
│   ├── radman-media-agent/
│   │   └── SKILL.md                    # Media manifests & geometry-locked fidelity
│   └── radman-qa-guard/
│       └── SKILL.md                    # Preflight compliance & blocker reporting
└── templates/
    ├── task-brief.md                   # Task specification template
    ├── owner-approval.md               # Owner sign-off template
    └── qa-report.md                    # Preflight audit report template

agents/platform/
├── __init__.py                         # Platform exports & version
├── registry.py                         # Agent & skill registry loader
├── business_rules.py                   # Business rules validation engine
├── approval_gate.py                    # HITL gate evaluator
├── task_contract.py                    # Task brief, plan, and execution contracts
├── artifact_manifest.py                # Artifact and media manifest management
└── dry_run.py                          # Multi-skill dry-run orchestrator CLI
```

---

## 2. Core Principles & Safety Guarantees

1. **Validation-First & Read-Only Default:** All agent tools operate in dry-run mode by default. Zero automated writes to WordPress database or live host without explicit human approval.
2. **Strict Business Rule Compliance:**
   - **Currency:** Toman / IRT (no Rial/Toman multiplier errors).
   - **No Sale Prices:** `sale_price` and strikethrough prices are permanently prohibited.
   - **Exact Price Floor:** `final_price = max(excel_price, weight × gram_rate)` where gram rate is `650,000` (standard/small/unknown) or `590,000` (confirmed large-stone).
   - **1:1 Stock Model:** Unique jewelry items have `stock_quantity = 1`.
   - **Draft Lifecycle:** Products remain in `draft` status until explicitly approved.
   - **Content Purity:** Product descriptions are strictly free of direct phone numbers, unrealistic delivery promises, and absolute warranty claims.
   - **Product Truth Over AI Hallucination:** Authentic jewelry geometry and hallmarked 925 authenticity always supersede synthetic AI creativity.
3. **Approval Gates (HITL):**
   - `GATE_PUBLISH_PRODUCT`: Owner approval required to publish any product.
   - `GATE_PRICE_CHANGE_LARGE`: Owner approval required if price variance exceeds 5%.
   - `GATE_MEDIA_REPLACE`: Owner approval required to replace catalog images.
   - `GATE_AI_IMAGE_REPLACE`: Owner approval required if AI-cleaned image replaces real product photo.
   - `GATE_DIRECT_MUTATION`: Owner approval required for host file mutations.

---

## 3. Integration with Existing Standalone Agents

The platform coordinates with the existing standalone agents in `agents/`:

| Agent File | Schedule / Trigger | Platform Integration |
| :--- | :--- | :--- |
| `agents/agent_order_watch.py` | Cron (5 min) | Monitored by `radman-orchestrator` & `radman-sales-agent` |
| `agents/agent_price_engine.py` | Cron / Manual | Governed by `radman-business-rules.json` price engine rules |
| `agents/agent_stock_guard.py` | Cron (Hourly) | Feeds audit data into `radman-qa-guard` |
| `agents/agent_excel_product_pipeline.py` | Runner | Backs catalog ingestion and HTML spec extraction |
| `agents/agent_product_seo.py` | Pipeline | Deterministic generator behind `radman-seo-agent` skill |
| `agents/agent_product_seo_qa.py` | Gate | Pre-publication verification tool for `radman-qa-guard` |

---

## 4. Verification & Dry Run

Run the platform dry-run:
```bash
python -m agents.platform.dry_run
```

Run the test suite:
```bash
# Via pytest:
pytest tests/test_agent_platform_foundation.py

# Or directly via python:
python tests/test_agent_platform_foundation.py
```

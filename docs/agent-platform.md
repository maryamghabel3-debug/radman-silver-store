# RADMAN Agent Platform Specification

## 1. Executive Summary
The **RADMAN Agent Platform** is an enterprise-grade, human-in-the-loop (HITL) autonomous framework engineered for **RADMAN SILVER 925** (Persian fine jewelry and 925 sterling silver e-commerce store).

The platform introduces a decoupled, skill-oriented architecture under `.agents/skills/` supported by deterministic Python 3.11 scaffolding under `agents/platform/`. It bridges repository-based autonomous decision making with operational safety, strictly adhering to store business rules and preserving existing on-host cron and pipeline agents.

---

## 2. Architecture Overview

```text
                               +-----------------------------+
                               |     Task Brief / Trigger     |
                               +--------------+--------------+
                                              |
                                              v
+------------------------------------------------------------------------------------------+
|                                  radman-orchestrator                                     |
|  - Validates Task Brief schema                                                           |
|  - Resolves required skills from .agents/config/agent-registry.json                       |
|  - Checks Human-In-The-Loop gates from .agents/config/approval-gates.json                 |
|  - Builds deterministic multi-step Task Plan                                             |
+---------------------------------------------+--------------------------------------------+
                                              |
                       +----------------------+----------------------+
                       |                                             |
                       v                                             v
        +-----------------------------+               +-----------------------------+
        |       radman-qa-guard       |               |     Specialized Skills      |
        |  - Business rule compliance |               |  - radman-seo-agent         |
        |  - Price floor checks       | <===========> |  - radman-content-agent     |
        |  - Prohibited content scan  |               |  - radman-sales-agent       |
        |  - Stock model audit (1:1)  |               |  - radman-media-agent       |
        +-----------------------------+               +-----------------------------+
                       |                                             |
                       +----------------------+----------------------+
                                              |
                                              v
                               +-----------------------------+
                               |  Approval Gate Evaluation   |
                               +--------------+--------------+
                                              |
                        +---------------------+---------------------+
                        | (Requires Gate)                           | (Clean / Dry-Run)
                        v                                           v
         +-----------------------------+             +-----------------------------+
         |     Owner Sign-Off Block    |             |      Artifact Manifest      |
         | (.agents/templates/owner-   |             | (Saved to outbox/manifests) |
         |        approval.md)         |             +-----------------------------+
         +-----------------------------+
```

---

## 3. Skill Catalog

| Skill Identifier | Name | Risk Level | Primary Mission |
| :--- | :--- | :--- | :--- |
| `radman-orchestrator` | Master Orchestrator | `LOW` | Task routing, plan creation, gate enforcement |
| `radman-seo-agent` | SEO & AI Visibility | `LOW` | Persian luxury SEO titles, meta descriptions, Rank Math schema |
| `radman-content-agent` | Brand Story & Content | `LOW` | Persian care guides, Instagram captions, educational articles |
| `radman-sales-agent` | Advisory Sales & Support | `LOW` | Ring sizing guidance, gemstone care, consultative replies |
| `radman-media-agent` | Media Governance | `MEDIUM` | Media manifests, geometry lock validation, watermark audit |
| `radman-qa-guard` | Preflight QA Guard | `LOW` | Preflight compliance gate, price floor audit, blocker detection |

---

## 4. Integration with Existing Standalone Agents

The platform preserves all existing standalone agents without rewriting:
- **`agents/agent_order_watch.py`**: Monitored for incoming customer order signals.
- **`agents/agent_price_engine.py`**: Executes exact silver pricing when daily rate is supplied.
- **`agents/agent_stock_guard.py`**: Audits WooCommerce stock anomalies; feeds data into `radman-qa-guard`.
- **`agents/agent_excel_product_pipeline.py`**: Drives batch Excel ingestion, HTML spec extraction, and draft enrichment.
- **`agents/agent_product_seo.py`**: Deterministic generator wrapped by `radman-seo-agent`.
- **`agents/agent_product_seo_qa.py`**: Pre-publication verification gate.

---

## 5. Security & Safety Invariants
1. **Zero Production Mutation:** The agent platform operates in-repository and dry-run only. It never accesses production database or live WordPress directly.
2. **Strict Currency Rule:** Currency is always Toman (IRT). Multiplying or dividing by 10 (Rial/Toman conversions) is strictly prohibited.
3. **Permanent Ban on Sale Prices:** No `sale_price` or strikethrough prices may ever be computed or stored.
4. **Exact Price Floors:** `final_price >= max(legacy_price, weight * gram_rate)` with rates of 650,000 Toman (standard) and 590,000 Toman (large stone).
5. **Inventory Model:** 1:1 stock quantity for unique fine jewelry pieces.
6. **Draft Lifecycle:** Products remain in `draft` status until explicitly approved by the owner.
7. **Content Restrictions:** Product descriptions must never contain direct phone numbers, delivery guarantees, or lifetime warranty claims.

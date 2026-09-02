# Task Brief: [TASK-ID]

## Metadata
- **Task ID:** `TASK-YYYYMMDD-XXXX`
- **Created Date:** `YYYY-MM-DD`
- **Requester:** `agent-orchestrator` / `owner`
- **Target Skill:** `radman-orchestrator` | `radman-seo-agent` | `radman-content-agent` | `radman-sales-agent` | `radman-media-agent` | `radman-qa-guard`
- **Risk Level:** `LOW` | `MEDIUM` | `HIGH` | `CRITICAL`
- **Requires Owner Gate:** `YES` | `NO`

---

## 1. Objective
Clear, concise statement of what this task aims to accomplish.

## 2. Context & Input Data
- **Product ID / Target Entity:** `WP-ID` / `SKU` / `Topic`
- **Input Artifacts:**
  - `path/to/input.json`
  - `path/to/specs.html`
- **Parameters / Options:**
  - `dry_run: true`
  - `language: fa`

---

## 3. Applicable Business Rules & Safety Constraints
- [ ] No `sale_price` / strikethrough allowed
- [ ] Price ceiling: `max(excel_price, weight * gram_rate)`
- [ ] Stock model: 1:1
- [ ] Draft lifecycle: Product remains in `draft`
- [ ] No prohibited phone numbers, shipping promises, or guarantee claims
- [ ] Product truth prioritized over AI embellishment

---

## 4. Expected Deliverable
- **Output Artifacts:**
  - `outbox/task_[TASK-ID]_output.json`
  - `docs/reports/[TASK-ID]-report.md`
- **Acceptance Criteria:**
  - All automated validation gates PASS
  - No unapproved schema or data mutations

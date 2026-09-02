# Skill: RADMAN QA Guard (`radman-qa-guard`)

## 1. Overview & Mission
The **RADMAN QA Guard** is the core verification and policy enforcement skill for all autonomous agent operations within **RADMAN SILVER 925**.

It evaluates candidate product data, pricing proposals, descriptions, and media manifests against the formal rules codified in `.agents/config/radman-business-rules.json` and `.agents/config/approval-gates.json`.

**Safety Rule:** The QA Guard serves as an impassable preflight gate. If any critical business rule is violated (e.g. sale price introduced, price below calculated floor, prohibited phone number in description), the QA Guard reports `BLOCKED` and halts all deployment workflows.

---

## 2. Capabilities
- **Business Rule Verification:**
  - Enforces currency as Toman (IRT).
  - Confirms complete absence of `sale_price` / strikethroughs.
  - Verifies exact pricing formula: `final_price >= max(excel_price, weight * rate)`.
  - Verifies gram rate classification: `650,000` (standard/small) vs `590,000` (large stone).
  - Verifies `stock_quantity = 1` (1:1 inventory model).
  - Verifies `draft` lifecycle status.
- **Content Purity & Prohibited Claims Scan:**
  - Scans for Iranian mobile numbers (`09...`, `+989...`, `۰۹...`).
  - Scans for hard delivery promises (`ارسال فوری تضمینی`, etc.).
  - Scans for unverified absolute warranty claims (`گارانتی مادام‌العمر`, etc.).
- **Approval Gate Evaluation:**
  - Computes price variance ratio (`abs(new_price - old_price) / old_price`).
  - Identifies if proposal triggers `GATE_PUBLISH_PRODUCT`, `GATE_PRICE_CHANGE_LARGE`, `GATE_MEDIA_REPLACE`, or `GATE_AI_IMAGE_REPLACE`.
- **Preflight QA Reporting:**
  - Emits structured QA reports containing passes, warnings, violations, blockers, and gate verdicts.

---

## 3. Preflight Checklist Matrix

| Code | Check Name | Severity | Failure Action |
| :--- | :--- | :--- | :--- |
| `CHECK_NO_SALE_PRICE` | No sale prices or strikethroughs | `CRITICAL` | Block execution |
| `CHECK_PRICE_FLOOR` | Price meets or exceeds gram rate floor | `CRITICAL` | Block execution |
| `CHECK_STOCK_1TO1` | Stock quantity is exactly 1 | `CRITICAL` | Block execution |
| `CHECK_DRAFT_STATUS` | Product status remains `draft` | `CRITICAL` | Block execution |
| `CHECK_NO_PHONE` | Description has no phone numbers | `HIGH` | Block execution |
| `CHECK_NO_SHIPPING_PROMISE` | Description has no hard shipping promises | `HIGH` | Block execution |
| `CHECK_NO_GUARANTEE_CLAIM` | Description has no lifetime warranty claims | `HIGH` | Block execution |
| `CHECK_PRICE_VARIANCE_GATE` | Flag price change > 5% for owner gate | `MEDIUM` | Trigger `GATE_PRICE_CHANGE_LARGE` |

---

## 4. Input & Output Contract

### Input
```json
{
  "product_id": 65,
  "proposed_price_toman": 1250000,
  "baseline_price_toman": 1200000,
  "weight_grams": 1.8,
  "stone_type": "standard",
  "status": "draft",
  "stock_quantity": 1,
  "sale_price": null,
  "description": "انگشتر نقره مردانه عقیق یمنی عیار ۹۲۵ اصل با نگین طبیعی و رکاب دست‌ساز فاخر."
}
```

### Output
```json
{
  "qa_id": "QA-20260902-001",
  "verdict": "PASS",
  "passed_checks": [
    "CHECK_NO_SALE_PRICE",
    "CHECK_PRICE_FLOOR",
    "CHECK_STOCK_1TO1",
    "CHECK_DRAFT_STATUS",
    "CHECK_NO_PHONE",
    "CHECK_NO_SHIPPING_PROMISE",
    "CHECK_NO_GUARANTEE_CLAIM"
  ],
  "violations": [],
  "blockers": [],
  "required_gate": null,
  "variance_percent": 4.17
}
```

---

## 5. Sample Task Brief
```markdown
# Task Brief: Preflight QA Audit
- Skill: radman-qa-guard
- Objective: Audit proposed product batch update for pricing and description compliance
- Constraints: Ensure zero tolerance for sale prices and prohibited claims
```

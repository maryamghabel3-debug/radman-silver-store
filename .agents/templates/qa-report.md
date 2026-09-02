# RADMAN QA & Preflight Audit Report: [QA-REPORT-ID]

## Metadata
- **QA ID:** `QA-YYYYMMDD-XXXX`
- **Audit Date:** `YYYY-MM-DD HH:MM:SS`
- **Target Entity:** `Product [WP-ID / SKU]` | `Catalog Batch` | `Content Draft`
- **Audited By:** `radman-qa-guard v1.0.0`
- **Overall Verdict:** `PASS` | `WARN` | `FAIL` | `BLOCKED`

---

## 1. Executive Summary
Brief summary of preflight inspection results and policy conformance.

---

## 2. Business Rule Compliance Checklist

| Rule ID | Rule Description | Status | Details / Violations |
| :--- | :--- | :--- | :--- |
| **BR-CURR-01** | Currency is Toman (IRT) | `PASS` | No Rial/Toman factor distortion |
| **BR-PRC-01** | No sale price / strikethrough | `PASS` | `sale_price` is empty |
| **BR-PRC-02** | Exact price floor formula | `PASS` | `final_price >= weight * rate` |
| **BR-PRC-03** | Gram rates (650k / 590k) | `PASS` | Rate correctly classified |
| **BR-STK-01** | 1:1 Stock model | `PASS` | `stock_quantity = 1` |
| **BR-LFC-01** | Draft status preservation | `PASS` | Product status is `draft` |
| **BR-CNT-01** | Prohibited phone numbers | `PASS` | Zero mobile/tel patterns found |
| **BR-CNT-02** | Prohibited shipping promises | `PASS` | No delivery guarantees |
| **BR-CNT-03** | Prohibited warranty claims | `PASS` | No lifetime guarantee claims |
| **BR-MED-01** | Media fidelity & geometry lock | `PASS` | Authentic jewelry truth preserved |

---

## 3. Violations & Blockers Detail
*(List any blocking issues that prevent staging application or publication)*

- **Critical Blockers (0):** None
- **Warnings (0):** None

---

## 4. Gate Assessment & Next Actions
- **Required Approval Gate:** `NONE` (or e.g. `GATE_PUBLISH_PRODUCT`)
- **Ready for Staging Apply:** `YES`
- **Recommended Action:** Proceed with proposal review.

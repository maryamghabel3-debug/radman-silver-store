# Owner Approval Request: [APPROVAL-ID]

## Metadata
- **Approval ID:** `APR-YYYYMMDD-XXXX`
- **Gate ID:** `GATE_PUBLISH_PRODUCT` | `GATE_PRICE_CHANGE_LARGE` | `GATE_MEDIA_REPLACE` | `GATE_AI_IMAGE_REPLACE` | `GATE_DIRECT_MUTATION`
- **Triggered By Skill:** `radman-orchestrator` | `radman-seo-agent` | `radman-media-agent` | `radman-qa-guard`
- **Timestamp:** `YYYY-MM-DD HH:MM:SS UTC`
- **Status:** `PENDING_REVIEW` | `APPROVED` | `REJECTED` | `CHANGES_REQUESTED`

---

## 1. Proposal Summary
Executive summary of the requested action and the business rationale.

---

## 2. Impact Analysis & Before/After Comparison

| Dimension | Current State | Proposed State | Delta / Notes |
| :--- | :--- | :--- | :--- |
| **Product Status** | `draft` | `publish` | Transition requested |
| **Price (Toman)** | `1,250,000` | `1,380,000` | +10.4% variance |
| **Stock** | `1` | `1` | Maintained 1:1 |
| **Media / Asset** | `original.jpg` | `cleaned_v4.webp` | Geometry locked |

---

## 3. Preflight QA & Safety Evidence
- [x] Preflight QA Guard Status: `QA_PASS`
- [x] Business Rule Verification: `COMPLIANT`
- [x] No prohibited claims detected: `PASSED`
- [x] Backup created at: `backups/snapshot_before_change.tar.gz`

---

## 4. Owner Sign-Off Block

```text
Decision: [ APPROVED | REJECTED ]
Approver: Store Owner
Date: YYYY-MM-DD
Signature Token / Nonce: __________________________
Comments:
```

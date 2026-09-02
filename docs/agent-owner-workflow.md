# RADMAN Agent Platform — Owner Workflow & HITL Governance

## 1. Overview
The RADMAN Agent Platform operates under strict **Human-In-The-Loop (HITL)** governance. Autonomous agents assist in planning, drafting, calculating, and quality-checking, but store owners retain ultimate control over commercial decisions, pricing shifts, media replacements, and product publishing.

---

## 2. Standard Task Workflow

```text
[Owner / System] Creates Task Brief (.agents/templates/task-brief.md)
       │
       ▼
[radman-orchestrator] Parses Brief & Builds Deterministic Execution Plan
       │
       ▼
[radman-qa-guard] Runs Preflight Compliance Checks against Business Rules
       │
       ├───────────────────────────────────────────────────────┐
       ▼ (Check Failed)                                        ▼ (Check Passed)
[Report Blockers & Halt]                               [Execute Primary Skill]
                                                               │
                                                               ▼
                                               [Evaluate Approval Gates]
                                                               │
                              ┌────────────────────────────────┴────────────────────────────────┐
                              ▼ (Gate Triggered)                                                ▼ (No Gate Triggered)
               [Generate Owner Approval Request]                                     [Save Artifact Manifest]
              (.agents/templates/owner-approval.md)                                  (Ready for Staging Apply)
                              │
                              ▼
               [Owner Review & Sign-Off]
                              │
               ┌──────────────┴──────────────┐
               ▼ (Approved)                  ▼ (Rejected)
        [Apply to Staging]           [Discard / Revise]
```

---

## 3. Approval Gate Catalog

| Gate ID | Name | Trigger Condition | Required Evidence |
| :--- | :--- | :--- | :--- |
| `GATE_PUBLISH_PRODUCT` | Product Publication | Transitioning status from `draft` to `publish` | SEO QA report, price floor check, stock 1:1 check, owner sign-off |
| `GATE_PRICE_CHANGE_LARGE` | Large Price Variance | Price delta > 5% vs existing price baseline | Pricing formula breakdown, gram rate justification, owner sign-off |
| `GATE_MEDIA_REPLACE` | Catalog Media Replace | Replacing primary image or gallery set | Visual before/after diff, resolution check, owner sign-off |
| `GATE_AI_IMAGE_REPLACE` | AI Image Replacement | Replacing authentic photo with AI-cleaned image | Geometry lock audit, stone facet fidelity check, explicit sign-off |
| `GATE_DIRECT_MUTATION` | Direct Host Mutation | Writing database or non-staged files | Staging backup tarball, dry-run log, rollback script |

---

## 4. How the Store Owner Reviews an Approval Request

When an agent proposes an action that triggers a gate:
1. The agent writes a proposal to `.agents/templates/owner-approval.md` or `outbox/approval_[ID].md`.
2. The owner reviews:
   - **Executive Summary:** Why is this change proposed?
   - **Before / After Table:** Visual and numeric delta (e.g. price variance or image change).
   - **Compliance Evidence:** Confirmation that `radman-qa-guard` reported `QA_PASS`.
3. The owner fills in the sign-off block:
   ```text
   Decision: APPROVED
   Approver: Store Owner
   Date: 2026-09-02
   Comments: Pricing adjustment approved due to increased silver spot rate.
   ```

---

## 5. Rollback Procedures
- All staging changes are backed up in tarballs under `RADMAN_PRIVATE_DIR/backups/`.
- Price changes record prior prices in CSV logs (`backups/prices-<ts>.csv`).
- Theme CSS deployments include an automated rollback script (`theme/blocksy-child/deploy-luxury-product-ui.sh --rollback-latest`).

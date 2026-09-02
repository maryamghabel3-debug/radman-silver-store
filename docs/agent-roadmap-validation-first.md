# RADMAN Autonomous Agent Roadmap — Validation-First Strategy

## 1. Guiding Strategy: Validation-First
RADMAN SILVER 925 prioritizes **product truth, luxury brand dignity, and physical stock accuracy** over unconstrained agent autonomy. The agent platform follows a phased rollout where each capability is validated offline in dry-run mode before advancing to staging assistance.

---

## 2. Phased Roadmap

```text
+---------------------------------------------------------------------------------------+
| PHASE 1: Platform Foundation & Safety Scaffolding (CURRENT - PR-37)                   |
| - .agents/skills/ directory structure with 6 core skills                              |
| - .agents/config/ JSON schemas for business rules, registry, and approval gates        |
| - Python 3.11 platform contracts and deterministic dry-run orchestrator               |
| - 100% offline verification; zero WordPress or production mutation                    |
+---------------------------------------------------------------------------------------+
                                           │
                                           ▼
+---------------------------------------------------------------------------------------+
| PHASE 2: Advisory Mode & Catalog Enrichment (NEXT)                                    |
| - radman-seo-agent generates batch Rank Math metadata proposals                       |
| - radman-content-agent generates Persian luxury social captions & care guides         |
| - radman-sales-agent drafts consultative customer sizing responses                    |
| - radman-qa-guard validates all proposals prior to owner review                       |
+---------------------------------------------------------------------------------------+
                                           │
                                           ▼
+---------------------------------------------------------------------------------------+
| PHASE 3: Media Manifest Governance (Post-PR #36)                                      |
| - Once PR #36 (media pilot) is approved, integrate media governance with v4 system    |
| - radman-media-agent enforces geometry locks on 1600x1600 WebP assets                 |
| - Automated before/after visual manifest generation for owner sign-off                |
+---------------------------------------------------------------------------------------+
                                           │
                                           ▼
+---------------------------------------------------------------------------------------+
| PHASE 4: Supervised Staging Automation                                                |
| - One-command staging application for approved artifact manifests                     |
| - Automated staging rollback triggers upon anomaly detection                          |
| - Multi-agent coordination with hourly stock auditing and live order watching         |
+---------------------------------------------------------------------------------------+
```

---

## 3. Milestones & Success Criteria

| Milestone | Deliverable | Verification Gate |
| :--- | :--- | :--- |
| **M1 (Current)** | Agent Platform Foundation | `python -m agents.platform.dry_run` + 29 unit tests passing |
| **M2** | SEO & Content Advisory Pilot | Structured batch manifests generated in `outbox/` |
| **M3** | Media Manifest Governance | Geometry lock verification on 20 catalog products |
| **M4** | One-Command Staging Apply | Controlled apply with automated rollback capability |

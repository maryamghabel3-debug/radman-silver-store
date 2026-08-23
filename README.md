# RADMAN SILVER 925 — فروشگاه نقره رادمان (`radman-silver-store`)

> **اصالت در جزئیات (Authenticity in Details)**  
> *The Single Source of Truth for Store Architecture, Automation Agents, and Operations*

---

## 1. Executive Overview & Brand Specifications

- **Brand:** RADMAN SILVER 925 / `رادمان سیلور`
- **Tagline:** `اصالت در جزئیات`
- **Primary Domain:** [radmansilver.ir](http://radmansilver.ir) | **Secondary Domain:** [radman925.ir](http://radman925.ir)
- **Product Category:** 925 Sterling Silver Jewelry (`انگشتر نقره ۹۲۵` Rings, `گردنبند` Necklaces, `دستبند` Bracelets)
- **Technology Stack:** WordPress 6.x + WooCommerce + Blocksy Child Theme + Python 3.11+ Automation Agents (`MizbanFa Mars Plan — APPROVED FOR INITIAL TRIAL; NOT YET PURCHASED; RADMAN ONLY`) + Telegram Bot Interface (`[RADMAN_TELEGRAM_BOT_USERNAME: TBD]`)
- **Current Deployment Status:** **Staging live for RADMAN — Production pending** (`staging.radmansilver.ir` verified on MizbanFa Mars plan; `public_html` production untouched). See [docs/STAGING-EXECUTION-EVIDENCE-2026-08-12.md](docs/STAGING-EXECUTION-EVIDENCE-2026-08-12.md).
- **Payment Gateway Status:** **Gateland 2.4.5 installed on staging; payment configuration remains pending.**
- **Currency Safety Status (split):**
  - **Gate A (storage/product/cart display):** ✅ `IRT` Toman direct input verified for DB storage, product display and cart display.
  - **Gate B (checkout/order/email/Schema/payment callback):** ⏳ **PENDING** — must pass before payment activation or production launch.
  - Official status sentence: *"Toman direct input is verified for WooCommerce database storage, product display, and cart display. Payment, checkout, order, email, and Schema currency behavior remain PENDING and must pass before payment activation or production launch."*
- **Static Content Status:** 11 pages (IDs `21–31`) currently exist as **Draft placeholders** created during manual bootstrap. Repo content for all 11 pages is **complete and placeholder-free** in `content/static-pages/` (verified by `scripts/check_no_placeholders.py`; normal Persian ellipsis `…` is explicitly allowed). The plan runner (`scripts/radman_stage_apply.sh`, default `--plan`, staging only, never publish automatically) runs cleanly end-to-end and renders all 11 HTML fragments. Host-side Draft deployment is **PENDING** owner execution of the one-command batch tool. **Publication is BLOCKED** pending owner operational approval (all 11 pages) and legal review (returns, privacy, terms). The approval gate is tracked in [docs/STATIC-CONTENT-APPROVAL-REGISTRY.md](docs/STATIC-CONTENT-APPROVAL-REGISTRY.md).
- **One-Command Storefront Foundation:** `scripts/build_staging_storefront.sh` is the **single owner-facing command** that (on `--apply-staging`) performs idempotent backups + child-theme sync + 11 Draft pages upsert (via the reviewed runner) + Gutenberg homepage foundation on page ID 18 + 3 product categories + primary menu + WooCommerce/LiteSpeed baseline reporting. Defaults to `--plan`; requires `CONFIRM_STAGING_APPLY=YES` to mutate; refuses production/public_html; never enables payments/SMS/Redis/analytics and never publishes the 11 static pages. Full owner instructions: [docs/FINAL-STAGING-STOREFRONT-BATCH-RUNBOOK.md](docs/FINAL-STAGING-STOREFRONT-BATCH-RUNBOOK.md).
- **Duplicate Page Cleanup:** IDs `2` and `3` confirmed deleted. ID `10` (`refund_returns`) status **requires host verification** — it is not claimed deleted.
- **Host Operations Access:** Mode A (Ed25519 SSH key) requires persistent private-key storage; current sandbox reports **`PERSISTENT SSH PRIVATE-KEY STORAGE NOT AVAILABLE`**. Until the agent runtime lands on the host, Mode B (WordPress Application Password + one-command runner) is the fallback. See [docs/HOST-OPS-AGENT-ACCESS.md](docs/HOST-OPS-AGENT-ACCESS.md).
- **Official Brand Assets Repository:** [github.com/maryamghabel3-debug/brand-assets](https://github.com/maryamghabel3-debug/brand-assets)
  - English Canonical Logo Suite: `APPROVED/` (Didot serif, Shamsa crest)
  - Persian Final Approved Logo Suite: `APPROVED-FA/` (`Estedad Bold`, `S2` sizing, `T2` tagline / `T0` minimal header logo)
- **Inventory Reality (1:1 Stock):** Radman Silver maintains its own Inventory Registry (`legacy_stock = radman_stock`, `stock = 1` is normal and sellable; exact 1:1 mappings). Oversell protection = Human-in-the-Loop (`HITL`) Order Confirmation (mandatory SMS alert + optional Telegram convenience channel, with WooCommerce Admin fallback).
- **Pricing Reality (Simple Daily Rate):** Owner inputs one daily rate via Telegram (`نرخ امروز هر گرم نقره = X تومان`). Weight-based items compute `price = weight * daily_rate`. Special gemstone/labor items use `manual_locked`.
- **Luxury Pricing Policy:** product pages expose one price only. `regular_price` always equals the final selected/computed Toman price; sale prices, discount badges and strikethrough display are prohibited. Excel COL 10 is trace-only. See [docs/LUXURY-PRICING-HOTFIX.md](docs/LUXURY-PRICING-HOTFIX.md).
- **Luxury Public Title + Identity Policy (PR-30A):** explicit trailing legacy codes are removed from customer-facing titles, while normalized model code remains the searchable WooCommerce SKU and visible `کد مدل` specification. Legacy ID, raw code, original title, source URL and deterministic identity key remain private metadata; `--enrich-existing` updates Drafts in place and `--identity-report` audits mapping read-only.
- **Temporary Original-Product Overlay (reviewed `2026-08-21, Asia/Tehran`):** The create-only PR-25 migration treats every legacy price as Toman, uses `590000` Toman/gram only for `large_stone` rings at confidence `>=0.85`, uses `650000` otherwise, selects the higher of visible legacy price and weight floor, then rounds upward to `50000`. It does not replace the normal daily-rate architecture.
- **Definitive Excel Product Source:** `/home/radmansi/radman-deploy/products_20260821_182238.xlsx` controls selection, price, stock, category and active state. Newest selection is `legacy_id DESC`; public HTML is consulted only for original galleries and strict technical specs.
- **Original-Product Pipeline Status:** Excel remains authoritative for selection, price, stock and active state. PR-32 validates the resolved HTML page by SKU/code, legacy ID, or ≥60% title-token overlap; scopes extraction to the main spec container; rejects cross-product/free-text contamination; and cross-checks stone/color against the Draft title before updating an existing Draft.
- **Legacy Store:** [noghrehmashhad.ir](https://noghrehmashhad.ir) — API remains deferred; PR-32 uses identity-verified, container-scoped HTML specifications.

---

## 2. Official Documentation Index (`docs/`)

- [docs/BUSINESS-REQUIREMENTS.md](docs/BUSINESS-REQUIREMENTS.md) — Core business goals, 1:1 stock reality, simple daily rate pricing, and legal compliance.
- [docs/ROADMAP.md](docs/ROADMAP.md) — Multi-phase project roadmap from Phase 0 to Phase 6.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Technical ASCII architecture diagram, hosting infrastructure evaluation (`MizbanFa Mars Plan — APPROVED FOR INITIAL TRIAL; NOT YET PURCHASED; RADMAN ONLY`), and Admin Panel API integration.
- [docs/AGENT-STRATEGY.md](docs/AGENT-STRATEGY.md) — Human-in-the-loop governance, Telegram daily rate input, and order confirmation.
- [docs/PHASE-1-AGENTS.md](docs/PHASE-1-AGENTS.md) — Technical specifications for `Agent-LegacySync`, `Agent-Pricing`, and `Agent-OrderApproval`.
- [docs/SYNC-RULES.md](docs/SYNC-RULES.md) — Exact 1:1 stock mapping (`stock=1 is normal`), field ownership table, and overwrite protection.
- [docs/INVENTORY-REGISTRY.md](docs/INVENTORY-REGISTRY.md) — Radman Silver's own Inventory Registry (`inventory_registry` SQLite table), 1:1 stock mapping, and Telegram order verification.
- [docs/PRICING-RULES.md](docs/PRICING-RULES.md) — Simplified daily silver gram rate pricing (`price = weight * daily_rate`), 4 official pricing modes, and Telegram rate confirmation.
- [docs/LEGACY-API-ACCESS-STRATEGY.md](docs/LEGACY-API-ACCESS-STRATEGY.md) — Historical/deferred API strategy; not used by the PR-32 owner runner.
- [docs/LEGACY-CATALOG-ANALYSIS.md](docs/LEGACY-CATALOG-ANALYSIS.md) — Public-only legacy catalog structure, category mapping, field coverage, quality risks, and owner-review extraction approach.
- [docs/EXCEL-CATALOG-ANALYSIS.md](docs/EXCEL-CATALOG-ANALYSIS.md) / [scripts/run_catalog_analysis.sh](scripts/run_catalog_analysis.sh) — Read-only analysis of the owner XLSX export: all category counts, ID endpoints, weight/price/stock coverage, and a proposed two-level taxonomy; no WordPress, media, network, or import action.
- [docs/HTML-SPEC-ENRICHMENT-RUNBOOK.md](docs/HTML-SPEC-ENRICHMENT-RUNBOOK.md) / [scripts/run_excel_import.sh](scripts/run_excel_import.sh) — PR-32 identity validation, main-container scoping, value sanity checks, contamination reports, safe reruns, and guarded staging execution for the existing 20 Drafts.
- [docs/EXCEL-1000-PRODUCT-IMPORT-RUNBOOK.md](docs/EXCEL-1000-PRODUCT-IMPORT-RUNBOOK.md) — Excel selection/pricing and historical import operations.
- [docs/ORIGINAL-PRODUCT-IMPORT-RUNBOOK.md](docs/ORIGINAL-PRODUCT-IMPORT-RUNBOOK.md) — Historical PR-25 ten-product data-scrape runbook; deprecated for catalog data after PR-28.
- [docs/ORIGINAL-IMAGE-PROCESSING-RUNBOOK.md](docs/ORIGINAL-IMAGE-PROCESSING-RUNBOOK.md) — Original-byte archive, color/detail gates, before/after sheets, and untouched-original fallback policy.
- [docs/GEMSTONE-CLASSIFICATION-RUNBOOK.md](docs/GEMSTONE-CLASSIFICATION-RUNBOOK.md) — Text-first four-class ring classifier and the conservative confidence `0.85` gate.
- [docs/LEGACY-CODE-MAPPING-RUNBOOK.md](docs/LEGACY-CODE-MAPPING-RUNBOOK.md) — Exact-code SKU exception, deterministic normalization, duplicate handling, and conflict rules.
- [agents/agent_original_product_pipeline.py](agents/agent_original_product_pipeline.py) / [scripts/run_original_product_import.sh](scripts/run_original_product_import.sh) — Ten-product orchestrator and one-command POSIX host runner (`--plan`, `--scrape-only`, `--image-qa`, `--pricing-preview`, `--import-drafts`, `--full-pilot`).
- [scripts/test_original_product_pipeline.sh](scripts/test_original_product_pipeline.sh) — Offline compilation, POSIX/jailshell, secret, no-model, no-publish, mock-10, price, media-integrity, conflict, and idempotency acceptance gates.
- [docs/PRODUCT-DATA-MODEL.md](docs/PRODUCT-DATA-MODEL.md) — Standardized `RAD-*` taxonomy plus the narrow original-migration legacy-code exception and auditable metadata.
- [docs/PRODUCT-IMPORT-SCHEMA.md](docs/PRODUCT-IMPORT-SCHEMA.md) — Validated owner CSV/JSON contract for the four pricing modes and local image filenames.
- [docs/PRODUCT-IMPORT-RUNBOOK.md](docs/PRODUCT-IMPORT-RUNBOOK.md) — Persian cPanel guide for CSV/image upload, dry-run preview, staging apply, Draft review, and rollback.
- [scripts/import_products.sh](scripts/import_products.sh) — Staging-only, plan-by-default, backup-first product importer (idempotent by SKU; new products Draft only).
- [templates/product-import-sample.csv](templates/product-import-sample.csv) — Three deliberately non-importable SAMPLE rows for owner replacement.
- [docs/ORDER-WORKFLOW.md](docs/ORDER-WORKFLOW.md) — Order lifecycle states, hybrid SMS-primary / Telegram-optional notification model, WooCommerce Admin fallback approval, and out-of-stock exception handling.
- [docs/MEDIA-PROCESSING.md](docs/MEDIA-PROCESSING.md) — 1:1 square product images, 4:5 lifestyle images, WebP standard, and subtle logo watermarking.
- [docs/PRODUCT-MEDIA-PILOT-RUNBOOK.md](docs/PRODUCT-MEDIA-PILOT-RUNBOOK.md) — Persian owner guide for the license-gated, offline-model, three-product media QA pilot.
- [docs/PRODUCT-MEDIA-APPROVAL-SCHEMA.md](docs/PRODUCT-MEDIA-APPROVAL-SCHEMA.md) — Owner approval contract for a future, separately approved WordPress import stage.
- [agents/agent_legacy_catalog_pilot.py](agents/agent_legacy_catalog_pilot.py) / [agents/agent_product_media_processor.py](agents/agent_product_media_processor.py) — Public catalog extraction and non-generative 1600×1600 media/contact-sheet QA tooling.
- [scripts/run_product_media_pilot.sh](scripts/run_product_media_pilot.sh) — Staging-guarded orchestrator (`--plan`, `--scrape-three`, `--process-three`, `--full-pilot`); no WordPress import.
- [docs/SEO-STRATEGY.md](docs/SEO-STRATEGY.md) — RankMath SEO title format, JSON-LD Product/Review Schema, and Persian URL slug rules.
- [docs/MARKETING-PLAN.md](docs/MARKETING-PLAN.md) — Soft launch VIP cohort, Instagram/Telegram content plan, and cart-abandonment SMS rules.
- [docs/SUPPORT-SYSTEM.md](docs/SUPPORT-SYSTEM.md) — Rule-based FAQ chatbot engine and immediate Telegram human escalation protocol.
- [docs/SECURITY.md](docs/SECURITY.md) — WordPress/WooCommerce hardening, Wordfence firewall, `.env` encryption, and UpdraftPlus backup schedules.
- [docs/TELEGRAM-BOT.md](docs/TELEGRAM-BOT.md) — Webhook/polling architecture, interactive slash commands (`/price`, `/orders`), and admin ID whitelist.
- [docs/WHOLESALE-FUTURE.md](docs/WHOLESALE-FUTURE.md) — Future B2B tiered wholesale pricing model and partner gallery portal.
- [docs/MULTILINGUAL-FUTURE.md](docs/MULTILINGUAL-FUTURE.md) — Regional expansion roadmap for Arabic, Turkish, and English storefronts.

- [docs/HOSTING-ARCHITECTURE-DECISION.md](docs/HOSTING-ARCHITECTURE-DECISION.md) — Official hosting architecture decision record, candidate evaluations (MizbanFa/ParsPack), and mandatory acceptance criteria.
- [docs/POST-PURCHASE-SETUP-RUNBOOK.md](docs/POST-PURCHASE-SETUP-RUNBOOK.md) — Step-by-step operator guide and post-purchase setup runbook for MizbanFa Mars plan (RADMAN only).
- [docs/WORDPRESS-INSTALLATION-MARS-RUNBOOK.md](docs/WORDPRESS-INSTALLATION-MARS-RUNBOOK.md) — Detailed 11-Step WP-CLI installation runbook for WordPress 6.6, WooCommerce (IRR/Persian), and required plugins on MizbanFa Mars plan (RADMAN only).
- [docs/HOSTING-QUESTIONS-CHECKLIST.md](docs/HOSTING-QUESTIONS-CHECKLIST.md) — Pre-purchase questions checklist for hosting support and payment gateway support (6 tickets + Red Flags).

- [docs/STAGING-EXECUTION-EVIDENCE-2026-08-12.md](docs/STAGING-EXECUTION-EVIDENCE-2026-08-12.md) — Verified evidence report of successful WordPress/WooCommerce staging deployment on MizbanFa Mars plan.
- [docs/RADMAN-BRANDING-CONTENT-IMPORT-RUNBOOK.md](docs/RADMAN-BRANDING-CONTENT-IMPORT-RUNBOOK.md) — Truthful runbook for the idempotent staging runner that deploys the Blocksy child theme and upserts static-page content (default `--plan`, staging-only, no auto-publish).
- [docs/STATIC-PAGES-REGISTRY.md](docs/STATIC-PAGES-REGISTRY.md) — Official registry of 11 static Persian pages (slugs, initial Page IDs, and truthful deployment status: Draft placeholders pending full content import).
- [docs/HOST-OPS-AGENT-ACCESS.md](docs/HOST-OPS-AGENT-ACCESS.md) — Approved host access modes for the automation agent (SSH Ed25519 key preferred; Application Password + one-command runner fallback).
- [docs/STAGING-DEPLOYMENT-CHECKLIST.md](docs/STAGING-DEPLOYMENT-CHECKLIST.md) — Step-by-step staging deployment checklist (truthful split of DONE vs PENDING items, Currency Gate A vs B, owner/legal approval gates).
- [docs/STATIC-CONTENT-APPROVAL-REGISTRY.md](docs/STATIC-CONTENT-APPROVAL-REGISTRY.md) — Single Source of Truth for owner/legal approval status of all 11 static pages; Draft deploy allowed, publish BLOCKED until approved.
- [docs/FINAL-STAGING-STOREFRONT-BATCH-RUNBOOK.md](docs/FINAL-STAGING-STOREFRONT-BATCH-RUNBOOK.md) — Owner-facing runbook: single `build_staging_storefront.sh --apply-staging` command that performs all staging foundation steps (backups + Draft pages + child theme + homepage + categories + menu + baseline reports).
- [scripts/build_staging_storefront.sh](scripts/build_staging_storefront.sh) — Final one-command staging storefront batch runner (default `--plan`, `--check`, `--apply-staging`; strict staging guards; locks; backups; idempotent; never production, never publish, never enable payment/SMS/Redis).
- [scripts/test_plan_runner.sh](scripts/test_plan_runner.sh) — Local self-test that runs the staging runner in `--plan` mode, asserts the DEPLOY PLAN table prints, confirms all 11 rendered pages are placeholder-free, and runs ellipsis/bracketed-ellipsis/placeholder-class regression tests.
- [scripts/test_storefront_batch.sh](scripts/test_storefront_batch.sh) — Local self-test for the one-command batch runner (syntax, guards, Draft enforcement, menu whitelist, secret scanning, Gutenberg template validation, backup gating, Persian ellipsis regression).
- [scripts/check_no_placeholders.py](scripts/check_no_placeholders.py) — Rendered-HTML placeholder gate (fail-fast on `[…]` bracketed-ellipsis sentinel or `radman-placeholder` CSS class; normal Persian ellipsis `…` is explicitly allowed).
- [templates/home-page-gutenberg.html](templates/home-page-gutenberg.html) — Gutenberg block markup for the RADMAN staging homepage (hero, trust strip, categories, brand intro, staging notice; RTL/mobile-first; no scripts/fonts/trackers).
- [docs/PRODUCTION-CUTOVER-CHECKLIST.md](docs/PRODUCTION-CUTOVER-CHECKLIST.md) — Production go-live and cutover checklist after staging sign-off.
- [docs/SOFT-LAUNCH-GO-NO-GO.md](docs/SOFT-LAUNCH-GO-NO-GO.md) — Managerial Go/No-Go decision sheet and critical blockers audit for RADMAN soft launch.
- [docs/TEST-SCENARIOS-RADMAN.md](docs/TEST-SCENARIOS-RADMAN.md) — Comprehensive 20+ operational QA test scenarios for staging and pre-launch validation.

### Strategy & Growth Documentation (Phase 3.5)

- [docs/STRATEGY-CONVERSION-UX.md](docs/STRATEGY-CONVERSION-UX.md) — RADMAN Conversion & UX Strategy (product page anatomy, category/cart/checkout UX, micro-interactions, exit intent, homepage architecture, performance budget, and a curated plugin list with Perfmatters/ASE recommendations and an explicit "do NOT install" list).
- [docs/STRATEGY-SEO-AI-VISIBILITY.md](docs/STRATEGY-SEO-AI-VISIBILITY.md) — RADMAN SEO & AI Visibility Strategy (technical SEO baseline, Schema.org plan — Product with IRR for schema, Organization, BreadcrumbList, FAQPage, HowTo, WebSite — RankMath title/meta templates, AI/GEO content guidance, topic clusters, competitor analysis framework, monthly content calendar template).
- [docs/STRATEGY-RETENTION-GROWTH.md](docs/STRATEGY-RETENTION-GROWTH.md) — RADMAN Customer Retention & Growth Strategy (phased loyalty program, Kavenegar SMS flows, future email plan, UGC/social proof, phased gamification, and the 7-day return/refund policy design).
- [docs/STRATEGY-ANTI-FRAUD-KYC.md](docs/STRATEGY-ANTI-FRAUD-KYC.md) — RADMAN Anti-Fraud & Customer Verification Policy (three-tier KYC model, fraud signals, legal/privacy notes, phased implementation from OTP-only Soft Launch to Shahkar-backed Scale).
- [docs/STRATEGY-CONTENT-WRITING-GUIDELINES.md](docs/STRATEGY-CONTENT-WRITING-GUIDELINES.md) — RADMAN Content Writing Standards (tone of voice, Persian language rules, content review checklist, and templates for product/category/article/FAQ content).

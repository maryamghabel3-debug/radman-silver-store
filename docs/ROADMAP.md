# RADMAN SILVER 925 Store — Deployment & Launch Roadmap (`docs/ROADMAP.md`)

> **Single Source of Truth Roadmap (PR-01 Alignment)**  
> *Date Convention: All repository dates use Asia/Tehran timezone (UTC+3:30) in ISO format YYYY-MM-DD.*

---

## 1. Official Phase Model & Current Target Status

```text
RADMAN SILVER 925: [Phase 0: DONE] ──> [Phase 1: DONE] ──> [Phase 2: CURRENT] ──> [Phase 3: NEXT]
```

- **Phase 0: Documentation & Brand Identity** — **DONE ✅**
- **Phase 1: Repository Setup & Architecture** — **DONE ✅**
- **Phase 2: Infrastructure & Hosting Setup** — **CURRENT ⏭**
- **Phase 3: WordPress/WooCommerce Deployment** — **NEXT ⏳**
- **Phase 4: Agent Integration & Testing** — **PENDING ⏳**
- **Phase 5: Soft Launch & VIP Cohort** — **PENDING ⏳**
- **Phase 6: Public Launch & Scale** — **PENDING 🎯**

---

## 2. Master Execution Schedule

### Phase 0: Documentation & Brand Identity (DONE ✅ — 2026-08-06)
- [x] Integrate canonical English Didot and Persian Estedad Bold logo suites (`brand-assets/radman-silver/APPROVED/` and `APPROVED-FA/`).
- [x] Lock 3-tier pricing model and 1:1 stock reality (`stock = 1` is sellable, zero buffers).

### Phase 1: Repository Setup & Architecture (DONE ✅ — 2026-08-06)
- [x] Establish 19 core documentation files (`docs/BUSINESS-REQUIREMENTS.md` through `docs/MULTILINGUAL-FUTURE.md`).
- [x] Build and test `Agent-LegacySync` (`agents/agent_legacy_sync.py`) for catalog migration from `noghrehmashhad.ir` Admin Panel API.
- [x] Complete 11 static Persian pages in `content/static-pages/`.

### Phase 2: Infrastructure & Hosting Setup (CURRENT ⏭)
> **Current Architecture Decision Status:** APPROVED FOR INITIAL ONE-MONTH PURCHASE AND STAGING TRIAL — STAGING LIVE (`MizbanFa Mars`, RADMAN only, storefront approved, agent co-location conditional; Review within 30 days after actual provisioning date and before production launch). RIDELIN must not be installed or deployed on this host. See [docs/STAGING-EXECUTION-EVIDENCE-2026-08-12.md](STAGING-EXECUTION-EVIDENCE-2026-08-12.md), [docs/HOSTING-ARCHITECTURE-DECISION.md](HOSTING-ARCHITECTURE-DECISION.md), and [docs/POST-PURCHASE-SETUP-RUNBOOK.md](POST-PURCHASE-SETUP-RUNBOOK.md).
- [x] **Staging WordPress/WooCommerce installation for RADMAN:** Verified live on MizbanFa Mars plan (`staging.radmansilver.ir`, WP 7.0.3, WC 11.0.1, MariaDB 11.4.12, PHP 8.2.31, LiteSpeed, noindex `blog_public=0`). See [docs/STAGING-EXECUTION-EVIDENCE-2026-08-12.md](STAGING-EXECUTION-EVIDENCE-2026-08-12.md).
- [ ] **Deployment Readiness Governance:** Apply official step-by-step execution checklists (`docs/POST-PURCHASE-SETUP-RUNBOOK.md`, `docs/STAGING-DEPLOYMENT-CHECKLIST.md`, `docs/PRODUCTION-CUTOVER-CHECKLIST.md`, `docs/SOFT-LAUNCH-GO-NO-GO.md`, `docs/TEST-SCENARIOS-RADMAN.md`, and `docs/HOSTING-ARCHITECTURE-DECISION.md`) to govern zero-ambiguity transition from staging to QA validation and Soft Launch.
- [x] Provision temporary single-host Iranian WooCommerce cloud hosting (`MizbanFa Mars plan`, RADMAN only, required for domestic Shetab banking gateways and legacy API reachability).
- [x] Configure Let's Encrypt TLS 1.3 HTTPS, LiteSpeed / PHP 8.2.31, and MariaDB 11.4.12 (`utf8mb4_unicode_ci` verified on staging).
- [x] Configure staging `.env` securely in private account directory (`/home/radmansi/.config/radman/staging.env`, `chmod 600`, never committed to Git).
- [x] Verify DNS propagation and SSL certificate for `staging.radmansilver.ir`.
- [ ] Verify DNS propagation and SSL certificate for production domain `radmansilver.ir` (Production untouched).

### Phase 3: WordPress/WooCommerce Deployment (NEXT ⏳)
- [ ] **Next Step:** Staging configuration hardening + agent runtime prep (Currency Safety Gate verification, Redis configuration, Wordfence hardening, UpdraftPlus cloud backup destination, LiteSpeed Cache tuning).
- [ ] Deploy and customize **Blocksy Child Theme** (`#0B0B0E` matte black background, `#FAF7F2` ivory typography).
- [ ] Install and configure essential free production plugins (RankMath SEO wizard, UpdraftPlus cloud destination, Wordfence firewall rules, Redis Object Cache).
- [ ] Apply for Enamad trust badge, connect Zarinpal sandbox, connect Kavenegar SMS sandbox, and configure `[RADMAN_TELEGRAM_BOT_USERNAME: TBD]`.
- [ ] Production Deployment (`public_html` untouched — PENDING QA sign-off).

### Phase 4: Agent Integration & Testing (PENDING ⏳)
- [ ] Deploy `Agent-LegacySync` on the Iranian hosting server (`MizbanFa Mars plan` — CONDITIONAL: pending post-purchase Python/Cron/outbound connectivity acceptance tests) to connect to `noghrehmashhad.ir` Admin Panel API.
- [ ] Execute batch import of initial 50 legacy products as **Draft (`پیش‌نویس`)**.
- [ ] Deploy `Agent-Pricing` with daily Telegram rate confirmation workflow (`/price 85000`).
- [ ] Deploy `Agent-OrderApproval` Telegram HITL fulfillment bot.
- [ ] Execute end-to-end sandbox checkout test with Shetab debit card and SMS receipt.

### Phase 5: Soft Launch & VIP Cohort (PENDING ⏳)
- [ ] Conduct Soft Launch 1 (`RADMAN-VIP15` voucher cohort of 10-20 test customers).
- [ ] Verify courier shipping (Tipax/Post) and customer support chatbot responsiveness.

### Phase 6: Public Launch & Scale (PENDING 🎯)
- [ ] Official public launch of `radmansilver.ir`.
- [ ] Roll out SEO indexing, Google Merchant / Torob integration, and Instagram/Telegram content calendars.

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
> **Current Architecture Decision Status:** PENDING TECHNICAL DUE DILIGENCE — NO PURCHASE APPROVED YET. RADMAN hosting vendor and architecture are NOT yet selected; **MizbanFa** (`میزبان‌فا`) and **ParsPack** (`پارس‌پک`) are candidates under technical due diligence (see [docs/HOSTING-ARCHITECTURE-DECISION.md](HOSTING-ARCHITECTURE-DECISION.md)).
- [ ] **Deployment Readiness Governance:** Apply official step-by-step execution checklists (`docs/STAGING-DEPLOYMENT-CHECKLIST.md`, `docs/PRODUCTION-CUTOVER-CHECKLIST.md`, `docs/SOFT-LAUNCH-GO-NO-GO.md`, `docs/TEST-SCENARIOS-RADMAN.md`, and `docs/HOSTING-ARCHITECTURE-DECISION.md`) to govern zero-ambiguity transition from hosting purchase to staging, QA validation, and Soft Launch.
- [ ] Provision Iranian Linux cloud hosting (`[HOSTING VENDOR / PLAN / ARCHITECTURE: TBD — pending technical due diligence]`, required for domestic Shetab banking gateways and legacy API reachability).
- [ ] Configure Nginx reverse proxy, LiteSpeed / PHP-FPM 8.2+, MySQL 8.0+ / MariaDB 10.11+ (`utf8mb4_unicode_ci`), and Let's Encrypt TLS 1.3.
- [ ] Configure `.env` securely in repository root (never committed to Git).
- [ ] Verify DNS propagation for `radmansilver.ir` and `radman925.ir`.

### Phase 3: WordPress/WooCommerce Deployment (NEXT ⏳)
- [ ] Install WordPress 6.x core and WooCommerce e-commerce engine.
- [ ] Deploy and customize **Blocksy Child Theme** (`#0B0B0E` matte black background, `#FAF7F2` ivory typography).
- [ ] Install essential free production plugins (WooCommerce, Persian WooCommerce, Zarinpal Payment Gateway, RankMath SEO, WP Super Cache, Wordfence Security, UpdraftPlus Backup).
- [ ] Apply for Enamad trust badge, connect Zarinpal sandbox, connect Kavenegar SMS sandbox, and configure `[RADMAN_TELEGRAM_BOT_USERNAME: TBD]`.

### Phase 4: Agent Integration & Testing (PENDING ⏳)
- [ ] Deploy `Agent-LegacySync` on the selected Iranian hosting server (`[HOSTING VENDOR / PLAN / ARCHITECTURE: TBD — pending technical due diligence]`) to connect to `noghrehmashhad.ir` Admin Panel API.
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

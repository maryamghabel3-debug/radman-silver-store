# نقشه راه پروژه رادمان سیلور (`ROADMAP.md`)

This document outlines the multi-phase execution schedule for **RADMAN SILVER 925** from brand locking to international market expansion.

---

## Phase 0 — Brand & Planning (COMPLETED ✅)
- [x] Brand name selected and locked: **RADMAN SILVER 925 / رادمان سیلور**
- [x] Domains purchased and verified: `radmansilver.ir` (primary), `radman925.ir` (redirect)
- [x] Logo suite designed, validated, and locked in GitHub:
  - English Didot serif canonical suite (`brand-assets/radman-silver/APPROVED/`)
  - Persian Estedad Bold final suite (`brand-assets/radman-silver/APPROVED-FA/` — S2 secondary size, T2 tagline / T0 minimal)
- [x] Business requirements and operational rules documented (`BUSINESS-REQUIREMENTS.md`)
- [x] AI Automation Agent architecture and governance planned

---

## Phase 1 — Infrastructure Setup (CURRENT ⏭)
- [ ] Provision high-speed Iranian hosting (`Iran Server Sonic 30` Linux cloud hosting).
- [ ] Install WordPress 6.x core and configure Nginx/LiteSpeed caching rules.
- [ ] Deploy WooCommerce e-commerce engine and Persian WooCommerce localization plugin.
- [ ] Install and activate **Blocksy Child Theme** configured for luxury jewelry (`#0B0B0E` matte black background, `#FAF7F2` ivory typography).
- [ ] Install essential free production plugins:
  - **WooCommerce** & **Persian WooCommerce (`ووکامرس فارسی`)**
  - **Zarinpal Payment Gateway (`درگاه پرداخت زرین‌پال`)**
  - **RankMath SEO** (Persian schema & XML sitemaps)
  - **WP Super Cache** / **LiteSpeed Cache**
  - **Wordfence Security** (Firewall & login hardening)
  - **UpdraftPlus Backup** (Automated S3/ArvanCloud database backups)
- [ ] Enforce SSL TLS 1.3 HTTPS encryption across all routes.
- [ ] Create essential storefront pages: About Us (`درباره ما`), Contact Us (`تماس با ما`), Return Policy (`شرایط بازگشت کالا`), Privacy Policy (`حریم خصوصی`), FAQ (`سوالات متداول`).
- [ ] Register and integrate **Enamad (`اینماد`)** electronic trust badge.
- [ ] Connect and verify Zarinpal sandbox merchant gateway.
- [ ] Connect and verify Kavenegar SMS gateway sandbox for OTP and order notifications.
- [ ] Provision Telegram Bot (`@RadmanSilverStoreBot`) for management alerts and human-in-the-loop approvals.
- [ ] Ensure repository security and `.env` secret exclusion.

---

## Phase 2 — Product Migration & Catalog Seeding (PENDING ⏳)
- [ ] Build and deploy `Agent-LegacySync` to connect to `noghrehmashhad.ir` API.
- [ ] Define SKU taxonomy (`RAD-[CAT]-[GENDER]-[ID]`) and initialize custom WooCommerce attribute schema.
- [ ] Run `Agent-LegacySync` to import initial cohort of 50 legacy products as **Draft (`پیش‌نویس`)**.
- [ ] Conduct human review and approve draft products via Telegram management interface.
- [ ] Execute `Agent-Media` to process, crop (1:1 square), convert to WebP, and watermark product gallery images.
- [ ] Write RankMath-optimized Persian SEO titles and descriptions for first 50 products.
- [ ] Configure product attributes: Purity (`۹۲۵ استرلینگ`), Weight in grams, Gemstone type, Plating, Gender, and Ring Size.
- [ ] Deploy `Agent-Pricing` with daily 10:30 AM Telegram confirmation workflow.
- [ ] Execute end-to-end sandbox checkout test with real Shetab debit card payment and SMS receipt.

---

## Phase 3 — Launch Preparation & Hardening (PENDING ⏳)
- [ ] Migrate remaining legacy product catalog from `noghrehmashhad.ir`.
- [ ] Build and deploy `Agent-OrderApproval` (Telegram interactive order fulfillment bot).
- [ ] Build and deploy `Agent-Inventory` for automated twice-daily stock reconciliation.
- [ ] Build and deploy `Agent-Intake` for new Tehran Grand Bazaar supplier products.
- [ ] Build and deploy `Agent-Support` rule-based FAQ chatbot engine.
- [ ] Build and deploy `Agent-Reporting` for daily sales and gross margin Telegram digests.
- [ ] Perform comprehensive Wordfence security audit and penetration testing.
- [ ] Verify automated UpdraftPlus restoration procedure from ArvanCloud Object Storage.
- [ ] Conduct **Soft Launch (`راه اندازی آزمایشی`)**: Invite cohort of 10-20 VIP test customers with launch vouchers.

---

## Phase 4 — Official Launch & Marketing Scale (PENDING 🎯)
- [ ] **Official Store Launch on `radmansilver.ir`.**
- [ ] Launch official Instagram page (`@radmansilver.ir`) with luxury unboxing reels and brand story posts.
- [ ] Launch official Telegram channel for customer product drops and seasonal collections.
- [ ] Allocate initial performance advertising budget (Torob / Emalls CPC campaign).
- [ ] Monitor product page conversion rate (`CR`) and optimize checkout friction.
- [ ] Enable automated Kavenegar cart-abandonment SMS after 2 hours.
- [ ] Enable post-purchase SMS review request with 5% discount incentive.

---

## Phase 5 — Growth, CRM & Conversion Optimization (PENDING 🚀)
- [ ] Implement AI-powered product description generator for unique SEO enrichment.
- [ ] Upgrade customer chatbot to LLM-powered luxury jewelry concierge.
- [ ] Deploy recommendation engine (similar rings, matching necklace sets).
- [ ] Integrate automated customer relationship management (`CRM` — Dittofeed / Mautic).
- [ ] Deploy competitor price monitoring script for Tehran silver market rates.
- [ ] Create bundled gift sets (`ست هدیه عروس`, `ست انگشتر و دستبند مردانه`).
- [ ] Perform A/B testing on product detail page call-to-action (`CTA`) buttons.

---

## Phase 6 — Regional & International Expansion (PENDING 🌍)
- [ ] Deploy WPML / Polylang multi-language architecture.
- [ ] Add Arabic (`ar_AE` / `ar_IQ`) regional storefront for UAE and Iraq markets.
- [ ] Add Turkish (`tr_TR`) regional storefront.
- [ ] Add English (`en_US`) international storefront.
- [ ] Integrate multi-currency switcher (`IRR`, `AED`, `TRY`, `USD`).
- [ ] Integrate international shipping and logistics gateway.

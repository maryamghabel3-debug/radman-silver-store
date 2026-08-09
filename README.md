# RADMAN SILVER 925 — فروشگاه نقره رادمان (`radman-silver-store`)

> **اصالت در جزئیات (Authenticity in Details)**  
> *The Single Source of Truth for Store Architecture, Automation Agents, and Operations*

---

## 1. Executive Overview & Brand Specifications

- **Brand:** RADMAN SILVER 925 / `رادمان سیلور`
- **Tagline:** `اصالت در جزئیات`
- **Primary Domain:** [radmansilver.ir](http://radmansilver.ir) | **Secondary Domain:** [radman925.ir](http://radman925.ir)
- **Product Category:** 925 Sterling Silver Jewelry (`انگشتر نقره ۹۲۵` Rings, `گردنبند` Necklaces, `دستبند` Bracelets)
- **Technology Stack:** WordPress 6.x + WooCommerce + Blocksy Child Theme + Python 3.11+ Automation Agents (hosted on **Iran Server Sonic 30**) + Telegram Bot Interface
- **Official Brand Assets Repository:** [github.com/maryamghabel3-debug/brand-assets](https://github.com/maryamghabel3-debug/brand-assets)
  - English Canonical Logo Suite: `APPROVED/` (Didot serif, Shamsa crest)
  - Persian Final Approved Logo Suite: `APPROVED-FA/` (`Estedad Bold`, `S2` sizing, `T2` tagline / `T0` minimal header logo)
- **Inventory Reality (1:1 Stock):** Radman Silver maintains its own Inventory Registry (`legacy_stock = radman_stock`, `stock = 1` is normal and sellable; exact 1:1 mappings). Oversell protection = Human Order Confirmation via Telegram.
- **Pricing Reality (Simple Daily Rate):** Owner inputs one daily rate via Telegram (`نرخ امروز هر گرم نقره = X تومان`). Weight-based items compute `price = weight * daily_rate`. Special gemstone/labor items use `manual_locked`.
- **Legacy Store (Admin Panel API):** [noghrehmashhad.ir](http://noghrehmashhad.ir) (Admin Panel API accessed from Iran Server Sonic 30).

---

## 2. Official Documentation Index (`docs/`)

- [docs/BUSINESS-REQUIREMENTS.md](docs/BUSINESS-REQUIREMENTS.md) — Core business goals, 1:1 stock reality, simple daily rate pricing, and legal compliance.
- [docs/ROADMAP.md](docs/ROADMAP.md) — Multi-phase project roadmap from Phase 0 to Phase 6.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Technical ASCII architecture diagram, Iran Server Sonic 30 hosting specs, and Admin Panel API integration.
- [docs/AGENT-STRATEGY.md](docs/AGENT-STRATEGY.md) — Human-in-the-loop governance, Telegram daily rate input, and order confirmation.
- [docs/PHASE-1-AGENTS.md](docs/PHASE-1-AGENTS.md) — Technical specifications for `Agent-LegacySync`, `Agent-Pricing`, and `Agent-OrderApproval`.
- [docs/SYNC-RULES.md](docs/SYNC-RULES.md) — Exact 1:1 stock mapping (`stock=1 is normal`), field ownership table, and overwrite protection.
- [docs/INVENTORY-REGISTRY.md](docs/INVENTORY-REGISTRY.md) — Radman Silver's own Inventory Registry (`inventory_registry` SQLite table), 1:1 stock mapping, and Telegram order verification.
- [docs/PRICING-RULES.md](docs/PRICING-RULES.md) — Simplified daily silver gram rate pricing (`price = weight * daily_rate`), 3-tier pricing modes, and Telegram rate confirmation.
- [docs/LEGACY-API-ACCESS-STRATEGY.md](docs/LEGACY-API-ACCESS-STRATEGY.md) — Admin Panel API architecture, Iranian hosting server (`Sonic 30`) requirement, and read-only field audit workflow.
- [docs/PRODUCT-DATA-MODEL.md](docs/PRODUCT-DATA-MODEL.md) — Standardized `SKU` taxonomy (`RAD-[CAT]-[GENDER]-[ID]`) and WooCommerce attribute schema.
- [docs/ORDER-WORKFLOW.md](docs/ORDER-WORKFLOW.md) — Order lifecycle states, Telegram interactive approval buttons, and out-of-stock exception handling.
- [docs/MEDIA-PROCESSING.md](docs/MEDIA-PROCESSING.md) — 1:1 square product images, 4:5 lifestyle images, WebP standard, and subtle logo watermarking.
- [docs/SEO-STRATEGY.md](docs/SEO-STRATEGY.md) — RankMath SEO title format, JSON-LD Product/Review Schema, and Persian URL slug rules.
- [docs/MARKETING-PLAN.md](docs/MARKETING-PLAN.md) — Soft launch VIP cohort, Instagram/Telegram content plan, and cart-abandonment SMS rules.
- [docs/SUPPORT-SYSTEM.md](docs/SUPPORT-SYSTEM.md) — Rule-based FAQ chatbot engine and immediate Telegram human escalation protocol.
- [docs/SECURITY.md](docs/SECURITY.md) — WordPress/WooCommerce hardening, Wordfence firewall, `.env` encryption, and UpdraftPlus backup schedules.
- [docs/TELEGRAM-BOT.md](docs/TELEGRAM-BOT.md) — Webhook/polling architecture, interactive slash commands (`/price`, `/orders`), and admin ID whitelist.
- [docs/WHOLESALE-FUTURE.md](docs/WHOLESALE-FUTURE.md) — Future B2B tiered wholesale pricing model and partner gallery portal.
- [docs/MULTILINGUAL-FUTURE.md](docs/MULTILINGUAL-FUTURE.md) — Regional expansion roadmap for Arabic, Turkish, and English storefronts.

- [docs/HOSTING-QUESTIONS-CHECKLIST.md](docs/HOSTING-QUESTIONS-CHECKLIST.md) — Pre-purchase questions checklist for hosting support and payment gateway support (6 tickets + Red Flags).

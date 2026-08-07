# RADMAN SILVER 925 — فروشگاه نقره رادمان (`radman-silver-store`)

> **اصالت در جزئیات (Authenticity in Details)**  
> *The Single Source of Truth for Store Architecture, Automation Agents, and Operations*

---

## 1. Executive Overview & Brand Specifications

- **Brand:** RADMAN SILVER 925 / `رادمان سیلور`
- **Tagline:** `اصالت در جزئیات`
- **Primary Domain:** [radmansilver.ir](http://radmansilver.ir)
- **Secondary Domain (Redirect):** [radman925.ir](http://radman925.ir)
- **Product Category:** 925 Sterling Silver Jewelry (`انگشتر نقره ۹۲۵` Rings, `گردنبند` Necklaces, `دستبند` Bracelets)
- **Business Model:** Online B2C retail + future B2B wholesale
- **Language:** Persian (`fa_IR`) in Phase 1; Arabic, Turkish, English in future regional expansion
- **Technology Stack:** WordPress 6.x + WooCommerce + Blocksy Child Theme + Python 3.11+ Automation Agents + Telegram Bot Interface
- **Official Brand Assets Repository:** [github.com/maryamghabel3-debug/brand-assets](https://github.com/maryamghabel3-debug/brand-assets)
- **Typography & Font Rules:**
  - **English Wordmark:** French Didot serif (`RADMAN`) with 8-pointed Royal Shamsa crest
  - **Persian Wordmark:** **Estedad Bold (`استعداد Bold`)** with **S2 secondary sizing** for `سیلور ۹۲۵` (~50% width of `رادمان`)
- **Locked Colorway Palette:**
  - **Matte Black (`#0B0B0E`)** — Primary background
  - **Ivory (`#FAF7F2`)** — Primary artwork and typography
  - *Rule: 100% clean Shamsa interior on Ivory colorways; zero background rectangles behind text.*
- **Legacy Store (Inventory & Catalog Source 1):** [noghrehmashhad.ir](http://noghrehmashhad.ir) (Owner's legacy store API used for stock & product seeding)
- **Current Lifecycle Phase:** **Phase 1 — Infrastructure Setup & Product Migration**
- **Repository Purpose:** Contains all Python automation agents, legacy sync scripts, operational documentation, and WooCommerce deployment configurations.

---

## 2. Quick Start Guide for Developers & Automation Agents

```bash
# 1. Clone the repository
git clone https://github.com/maryamghabel3-debug/radman-silver-store.git
cd radman-silver-store

# 2. Configure environment credentials
cp .env.example .env
# Open .env and populate WordPress REST API keys, Legacy Store API credentials, Telegram Bot Token, and Zarinpal Merchant ID

# 3. Check current project roadmap and operational rules
cat docs/ROADMAP.md
cat docs/PHASE-1-AGENTS.md
```

---

## 3. Official Documentation Index (`docs/`)

- [docs/BUSINESS-REQUIREMENTS.md](docs/BUSINESS-REQUIREMENTS.md) — Core business goals, legacy sources, rules, metrics, and Iranian legal compliance.
- [docs/ROADMAP.md](docs/ROADMAP.md) — Multi-phase project roadmap from Phase 0 to Phase 6.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Technical ASCII architecture diagram, hosting specs, database schema, and security boundaries.
- [docs/AGENT-STRATEGY.md](docs/AGENT-STRATEGY.md) — Human-in-the-loop governance, event bus, and agent orchestration.
- [docs/PHASE-1-AGENTS.md](docs/PHASE-1-AGENTS.md) — Technical specifications for `Agent-LegacySync`, `Agent-Pricing`, and `Agent-OrderApproval`.
- [docs/SYNC-RULES.md](docs/SYNC-RULES.md) — Legacy store API sync policy, field-level ownership table, and overwrite protection.
- [docs/PRICING-RULES.md](docs/PRICING-RULES.md) — Daily silver gram mathematical pricing formula, currency rounding, and Toman presentation.
- [docs/PRODUCT-DATA-MODEL.md](docs/PRODUCT-DATA-MODEL.md) — Standardized `SKU` taxonomy (`RAD-[CAT]-[GENDER]-[ID]`) and WooCommerce attribute schema.
- [docs/ORDER-WORKFLOW.md](docs/ORDER-WORKFLOW.md) — Order lifecycle states, Telegram interactive approval buttons, and out-of-stock exception handling.
- [docs/MEDIA-PROCESSING.md](docs/MEDIA-PROCESSING.md) — 1:1 square product images, 4:5 lifestyle images, WebP standard, and subtle logo watermarking.
- [docs/SEO-STRATEGY.md](docs/SEO-STRATEGY.md) — RankMath SEO title format, JSON-LD Product/Review Schema, and Persian URL slug rules.
- [docs/MARKETING-PLAN.md](docs/MARKETING-PLAN.md) — Soft launch VIP cohort, Instagram/Telegram content plan, and cart-abandonment SMS rules.
- [docs/SUPPORT-SYSTEM.md](docs/SUPPORT-SYSTEM.md) — Rule-based FAQ chatbot engine and immediate Telegram human escalation protocol.
- [docs/SECURITY.md](docs/SECURITY.md) — WordPress/WooCommerce hardening, Wordfence firewall, `.env` encryption, and UpdraftPlus backup schedules.
- [docs/TELEGRAM-BOT.md](docs/TELEGRAM-BOT.md) — Webhook/polling architecture, interactive slash commands, and owner Telegram admin ID whitelist.
- [docs/WHOLESALE-FUTURE.md](docs/WHOLESALE-FUTURE.md) — Future B2B tiered wholesale pricing model and partner gallery portal.
- [docs/MULTILINGUAL-FUTURE.md](docs/MULTILINGUAL-FUTURE.md) — Regional expansion roadmap for Arabic, Turkish, and English storefronts.
- [docs/LEGACY-API-RECONNAISSANCE.md](docs/LEGACY-API-RECONNAISSANCE.md) — Legacy API technical reconnaissance, custom MVC platform analysis, hybrid extraction mapping, and the Python inventory buffer rule.
- [docs/LEGACY-ADMIN-API-AUDIT.md](docs/LEGACY-ADMIN-API-AUDIT.md) — Authoritative Admin Panel API Audit (noghrehmashhad.ir): 1:1 Stock Reality, 3-Tier Pricing Model, Field Inventory, and Sanitized Schema.
- [docs/EXTERNAL-AGENT-PROMPTS.md](docs/EXTERNAL-AGENT-PROMPTS.md) — External Agent Skill Injection guide (3 system prompts for ChatGPT/Claude: Instagram Content Creator, Sales Closer, and Jewelry SEO Specialist).
- [docs/AGENT-LEGACY-SYNC-GUIDE.md](docs/AGENT-LEGACY-SYNC-GUIDE.md) — Operational guide for running Agent-LegacySync (catalog migration, inventory buffer rule, SQLite staging, and CLI reference).
- [agents/agent_legacy_sync.py](agents/agent_legacy_sync.py) — Authoritative Python 3 automation module for Legacy Store Catalog & Inventory Sync.

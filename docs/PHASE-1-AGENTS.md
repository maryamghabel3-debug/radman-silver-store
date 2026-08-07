# مشخصات فنی ایجنت‌های فاز اول (`PHASE-1-AGENTS.md`)

This document provides detailed technical specifications and operational logic for the core automation agents deployed in Phase 1 on **Iran Server Sonic 30**.

---

## 1. Legacy Sync Agent (`Agent-LegacySync`)

- **Purpose:** Connect to `noghrehmashhad.ir`'s Admin Panel API from an Iranian hosting server, extract silver jewelry product data, and import them into `radman-silver-store` as **Draft (`پیش‌نویس`)**.
- **Stock Reality Enforcement:**
  - Exact 1:1 stock mapping (`legacy_stock = radman_stock`).
  - `stock = 1` is completely normal and sellable. **Zero safety buffers are applied.**
- **Three-Tier Pricing Enforcement:**
  1. *Weight-based products:* `final_price = weight_grams * daily_rate`
  2. *Special gemstone/labor products:* `pricing_mode = manual_locked`
  3. *Missing weight products:* `pricing_mode = legacy_mirror`

---

## 2. Pricing Agent (`Agent-Pricing`)

- **Purpose:** Implement the owner's simplified daily rate pricing model.
- **Execution Workflow:**
  1. The owner sends slash command `/price 85000` via Telegram Bot (`@RadmanSilverStoreBot`).
  2. `Agent-Pricing` calculates `final_price = weight_grams * 85000` for all products where `pricing_mode = weight_based`.
  3. Products marked `manual_locked` (special gemstone/labor items) remain untouched.
  4. The bot returns a confirmation summary of updated products.

---

## 3. Order Approval Agent (`Agent-OrderApproval`)

- **Purpose:** Enforce Human Order Confirmation via Telegram as the sole oversell protection mechanism.
- **Execution Workflow:**
  1. On order checkout, `Agent-OrderApproval` sends an interactive alert to Telegram with customer details and ordered SKUs.
  2. The owner checks physical stock and clicks `[تأیید موجودی و ارسال]` to approve dispatch, or `[عدم موجودی و لغو]` if out of stock.

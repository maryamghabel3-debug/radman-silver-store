# مشخصات فنی ایجنت‌های فاز اول (`PHASE-1-AGENTS.md`)

This document provides detailed technical specifications and operational logic for the core automation agents deployed in Phase 1 on **Iran Server Sonic 30**.

---

## 1. Legacy Sync Agent (`Agent-LegacySync`)

- **Purpose:** Connect to `noghrehmashhad.ir`'s Admin Panel API from an Iranian hosting server, extract silver jewelry product data, and import them into `radman-silver-store` as **Draft (`پیش‌نویس`)**.
- **1:1 Stock Reality Enforcement:**
  - Exact 1:1 stock mapping (`legacy_stock = radman_stock`).
  - `stock = 1` is sellable. Exact 1:1 mappings are applied.
- **Pricing Mode Assignment:**
  - If item has verified weight and no gemstone -> `pricing_mode = silver_weight_only`.
  - If item has verified weight + gemstone -> `pricing_mode = silver_weight_plus_stone`.
  - If weight is missing -> `pricing_mode = legacy_mirror`.
  - If custom jewelry -> `pricing_mode = manual_locked`.

---

## 2. Pricing Agent (`Agent-Pricing`)

- **Purpose:** Implement the owner's simplified daily silver rate + fixed gemstone valuation model.
- **Recalculation Scope:**
  - **Recalculates:** Products in `silver_weight_only` and `silver_weight_plus_stone` modes.
  - **Does NOT change:** Products in `manual_locked` mode, products where `price_locked = true`, or products missing required `silver_weight_grams` / `stone_fixed_value_toman` fields.
- **Human Approval & Preview Workflow:**
  1. Owner sends `/price 85000` via Telegram Bot.
  2. `Agent-Pricing` generates an interactive **Preview Summary**:
     - Affected weight-only products count
     - Affected weight+stone products count
     - Skipped locked products count
     - Skipped missing-data products count
     - **Top 20 price changes list** (SKU, old price -> new price Toman, % change)
  3. No WooCommerce price changes occur until the owner clicks `[تأیید و اعمال قیمت در فروشگاه]`.

---

## 3. Order Approval Agent (`Agent-OrderApproval`)

- **Purpose:** Enforce Human Order Confirmation via Telegram as the sole oversell protection mechanism.
- **Execution Workflow:**
  1. On order checkout, `Agent-OrderApproval` sends an interactive alert to Telegram with customer details and ordered SKUs.
  2. The owner checks physical stock and clicks `[تأیید موجودی و ارسال]` to approve dispatch, or `[عدم موجودی و لغو]` if out of stock.

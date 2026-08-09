# نیازمندی‌های کسب‌وکار رادمان سیلور (`BUSINESS-REQUIREMENTS.md`)

This document defines the core business objectives, sourcing models, operational rules, key performance indicators, and Iranian legal compliance requirements for **RADMAN SILVER 925**.

---

## 1. Core Business & Inventory Rules (`قوانین اساسی کسب‌وکار و انبار`)

1. **Unique SKU Mandatory:** Every product variation must possess a standardized SKU (`RAD-[CAT]-[GENDER]-[ID]`).
2. **1:1 Stock Reality (Exact 1:1 Mappings):**
   - Silver rings are unique handcrafted pieces; **`stock = 1` is completely normal and sellable**.
   - **All historical stock-offset logic is strictly removed.** Rule: `legacy_stock = radman_stock` (1:1 mapping).
   - Oversell protection is handled exclusively by **Human Order Confirmation via Telegram** for every paid order before shipping.
3. **Simplified Daily Rate Pricing Model:**
   - The owner enters ONE daily silver gram rate via Telegram Bot: `نرخ امروز هر گرم نقره = X تومان`.
   - *Weight-based products:* `final_price = weight_grams * daily_rate`.
   - *Special gemstone/labor items:* `pricing_mode = manual_locked` (owner sets price manually).
   - *Missing weight items:* `pricing_mode = legacy_mirror` (temporarily mirror old site price).
4. **Admin Panel API & Iranian Host Requirement:**
   - Sourcing from `noghrehmashhad.ir` uses its internal Admin Panel API.
   - To prevent cloud firewall timeouts, all sync scripts execute from an Iranian hosting server (**`Iran Server Sonic 30`**).

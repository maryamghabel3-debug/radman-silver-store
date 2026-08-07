# قوانین قیمت‌گذاری و محاسبه نرخ روز نقره (`PRICING-RULES.md`)

This document defines the authoritative, simplified pricing model for **RADMAN SILVER 925** (`radman-silver-store`), replacing all legacy complex formulas with a direct daily gram-rate calculation.

---

## 1. Extremely Simple Daily Rate Model (`مدل قیمت‌گذاری ساده روزانه`)

To ensure absolute operational clarity and eliminate unnecessary pricing complexity, **RADMAN SILVER** operates on a direct daily silver gram rate model:
- The business owner enters **ONE number daily** (or whenever market conditions require) via Telegram Bot:
  ```text
  نرخ امروز هر گرم نقره = X تومان
  ```
- No complex formulas involving global spot silver prices, Tether (`USDT`) exchange rates, or separate silversmithing labor calculations are used.

---

## 2. Three-Tier Product Pricing Reality (`قوانین ۳ گانه محاسبه قیمت محصولات`)

Every product in `radman-silver-store` falls into exactly one of three deterministic pricing modes:

### A. Weight-Based Products (`pricing_mode = weight_based`)
- **Applies to:** Plain silver rings, bracelets, necklaces, and standard sterling silver jewelry items with a verified net weight in grams.
- **Formula:**
  ```text
  final_price_toman = weight_grams * daily_rate_toman_per_gram
  ```
- **Example:** If `weight_grams = 5.40` and `daily_rate = 85,000 Toman`, then `final_price = 459,000 Toman`.

### B. Special / Gemstone / Unique Products (`pricing_mode = manual_locked`)
- **Applies to:** Jewelry pieces featuring precious or semi-precious gemstones (`عقیق یمنی`, `فیروزه نیشابور`), custom engraving, or intricate silversmithing labor.
- **Rule:** The owner sets the retail price **manually** in WooCommerce. Automated pricing scripts **NEVER overwrite** a product marked with `pricing_mode = manual_locked`.

### C. Missing Weight Products (`pricing_mode = legacy_mirror`)
- **Applies to:** Products imported from the legacy store (`noghrehmashhad.ir`) where the gram weight field is missing or unverified.
- **Rule:** Temporarily mirror the legacy store's final price (`legacy_price`) until the owner weighs the item and updates its metadata to `weight_based` or `manual_locked`.

---

## 3. Telegram Daily Rate Confirmation Workflow (`گردش کار تلگرامی`)

1. The owner sends slash command `/price 85000` in the `@RadmanSilverStoreBot` Telegram channel.
2. `Agent-Pricing` recalculates all active products where `pricing_mode = weight_based`.
3. The bot replies with a summary report:
   ```text
   نرخ جدید هر گرم نقره: ۸۵,۰۰۰ تومان
   تعداد محصولات وزن‌محور به‌روزرسانی‌شده: ۱۴۵ محصول
   محصولات قفل‌شده دستی (بدون تغییر): ۴۲ محصول
   ```

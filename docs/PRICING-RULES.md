# قوانین قیمت‌گذاری، محاسبه وزن نقره و نگین (`PRICING-RULES.md`)

This document defines the authoritative 4-mode pricing architecture, fixed gemstone value rules, rounding standard, and human-in-the-loop Telegram preview workflow for **RADMAN SILVER 925** (`radman-silver-store`).

---

## 1. Extremely Simple Daily Rate Model (`مدل قیمت‌گذاری ساده روزانه`)

- The business owner enters **ONE number daily** (or whenever market conditions require) via Telegram Bot:
  ```text
  نرخ امروز هر گرم نقره = X تومان
  ```
  *(Example slash command in Telegram: `/price 85000`)*
- No complex formulas involving global spot silver prices, Tether (`USDT`) exchange rates, or separate silversmithing labor calculations are used.

---

## 2. Four Authoritative Pricing Modes (`قوانین ۴ گانه محاسبه قیمت محصولات`)

Every product in `radman-silver-store` operates under exactly one of four locked `pricing_mode` classifications:

```text
       [ Owner enters Daily Rate in Telegram: /price 85000 ]
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
[ AUTOMATED RECALCULATION ]                  [ UNTOUCHED / SKIPPED ]
  ├── 1. silver_weight_only                    ├── 3. legacy_mirror
  │      price = weight * rate                 │      price = legacy_price
  └── 2. silver_weight_plus_stone              └── 4. manual_locked
         price = (weight * rate) + stone              price = manual_price
```

### 1. `silver_weight_only`
- **Applies to:** Plain silver rings, bracelets, necklaces, and standard sterling silver jewelry items without gemstones.
- **Mathematical Formula:**
  ```text
  final_price_toman = silver_weight_grams * daily_rate_toman_per_gram
  ```
- **Example:** If `silver_weight_grams = 5.40` and `daily_rate = 85,000 Toman`, then `final_price = 459,000 Toman`.

### 2. `silver_weight_plus_stone`
- **Applies to:** Semi-automated gemstone jewelry pieces where the silver weight is known and the gemstone has a fixed valuation (`e.g., عقیق یمنی`, `فیروزه نیشابور`).
- **Mathematical Formula:**
  ```text
  final_price_toman = (silver_weight_grams * daily_rate_toman_per_gram) + stone_fixed_value_toman
  ```
- **Example:** If `silver_weight_grams = 6.80`, `daily_rate = 85,000 Toman`, and `stone_fixed_value_toman = 500,000 Toman`, then:
  `final_price = (6.80 * 85,000) + 500,000 = 578,000 + 500,000 = 1,078,000 Toman`.
- **Why this excels:** Keeps pricing simple while allowing gemstone rings to be semi-automated without manual re-entry every time silver fluctuates.

### 3. `legacy_mirror`
- **Applies to:** Products imported from the legacy store (`noghrehmashhad.ir`) where `silver_weight_grams` is missing or unverified.
- **Rule:** Temporarily mirror the legacy store's final price (`legacy_price_toman`) until the owner weighs the item and transitions it to `silver_weight_only` or `silver_weight_plus_stone`.

### 4. `manual_locked`
- **Applies to:** Custom masterwork jewelry, rare collector gemstones, or pieces where `price_locked = true`.
- **Rule:** The owner sets the retail price manually (`manual_price_toman`). Automated pricing scripts **NEVER overwrite** a product marked with `pricing_mode = manual_locked`.

---

## 3. Mandatory Rounding Standard (`قانون گرد کردن قیمت به تومان`)

- **Internal Database Currency:** All prices stored in WooCommerce in **IRR / Toman** based on localization settings.
- **Rounding Step (`rounding_step_toman`):** All calculated retail prices are rounded up to the nearest **`10,000 Toman`** (`100,000 IRR`) for clean luxury presentation.
  - *Example:* Calculated `1,078,000 Toman` -> Displayed as **`۱,۰۸۰,۰۰۰ تومان`**.

---

## 4. Telegram Pricing Preview & Human Approval Workflow (`گردش کار تلگرامی`)

1. **Owner Input:** Owner sends command `/price 85000` to `@RadmanSilverStoreBot`.
2. **Automated Recalculation:** `Agent-Pricing` recalculates all products in `silver_weight_only` and `silver_weight_plus_stone` modes. It skips `manual_locked` products and any products missing required weight/stone fields.
3. **Mandatory Preview Summary:** Before applying any changes to WooCommerce, the bot sends an interactive summary report:
   ```text
   📊 پیش‌نمایش به‌روزرسانی قیمت روز نقره: ۸۵,۰۰۰ تومان/گرم
   
   تعداد محصولات وزن‌محور آماده تغییر (silver_weight_only): ۱۱۲ محصول
   تعداد محصولات وزن + نگین آماده تغییر (silver_weight_plus_stone): ۶۴ محصول
   محصولات قفل‌شده دستی (manual_locked - بدون تغییر): ۴۲ محصول
   محصولات دارای نقص اطلاعات (skipped missing data): ۸ محصول
   
   🔥 ۲۰ تغییر بزرگ قیمت امروز (Top 20 Price Changes):
   1. RAD-RNG-M-1014: ۲,۴۵۰,۰۰۰ ➔ ۲,۵۸۰,۰۰۰ تومان (+۵.۳٪)
   2. RAD-RNG-W-1089: ۳,۱۰۰,۰۰۰ ➔ ۳,۲۷۰,۰۰۰ تومان (+۵.۵٪)
   3. RAD-NEC-W-2015: ۱,۸۵۰,۰۰۰ ➔ ۱,۹۵۰,۰۰۰ تومان (+۵.۴٪)
   ...
   
   [تأیید و اعمال قیمت در فروشگاه]     [لغو عملیات]
   ```
4. **Human Approval Gate:** Only upon the owner clicking `[تأیید و اعمال قیمت در فروشگاه]` does `Agent-Pricing` execute batch price updates against WooCommerce.

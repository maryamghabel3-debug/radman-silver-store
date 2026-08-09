# قوانین قیمت‌گذاری، محاسبه وزن نقره و نگین (`PRICING-RULES.md`)

This document defines the authoritative 4-mode pricing architecture, fixed gemstone value rules, rounding standard, and human-in-the-loop Telegram preview workflow for **RADMAN SILVER 925** (`radman-silver-store`).

---

## 1. Extremely Simple Daily Rate Model (`مدل قیمت‌گذاری ساده روزانه`)

- The business owner enters **ONE number daily** (or whenever market conditions require) via Telegram Bot:
  ```text
  نرخ امروز هر گرم نقره = X تومان
  ```
  *(Example slash command in Telegram: `/price 85000`)*
- No complex legacy formulas or automated external rate feeds are used in the pricing engine.

---

## 2. Official Pricing Taxonomy (`۴ حالت رسمی قیمت‌گذاری`)

| Mode | Description | Formula |
|------|-------------|---------|
| `silver_weight_only` | Pure silver items | weight_grams × daily_rate |
| `silver_weight_plus_stone` | Silver + gemstone | (weight_grams × daily_rate) + stone_fixed_value_toman |
| `legacy_mirror` | No trusted weight | Copy legacy price as-is |
| `manual_locked` | Special/masterwork | Manual price, never auto-updated |

---

## 3. Daily Rate Input Method (`روش وارد کردن نرخ روزانه`)

- **Source:** Telegram owner command
- **Format:** `/price [amount in Toman per gram]`
- **Frequency:** Owner updates as needed (typically daily)
- **Preview:** Agent must show affected product count and top changes
- **Approval:** Owner must click confirm button before WooCommerce update
- **No automatic live market feed in current roadmap (Phase 1-5)**

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

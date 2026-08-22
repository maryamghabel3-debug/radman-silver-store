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

1. **Owner Input:** Owner sends command `/price 85000` to `[RADMAN_TELEGRAM_BOT_USERNAME: TBD]`.
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

---

## 5. Temporary PR-25 legacy floor overlay

**Owner-approved temporary rates reviewed:** `2026-08-21, Asia/Tehran`.

This overlay applies only to products created through the ten-product original-image migration. It does **not** replace the four-mode daily-rate architecture above and must not be generalized to owner-authored inventory. Imported Drafts are stored as `manual_locked` with `radman_pricing_overlay=legacy_gemstone_floor_v1` until the owner reviews and migrates them to a permanent mode.

### Currency invariant

- Every visible legacy price is already **Toman**.
- WooCommerce currency must be exactly `IRT`.
- No Rial/Toman conversion is allowed: never multiply or divide a source price by `10`.

### Temporary rates

| Product/evidence | Rate (Toman/gram) |
|---|---:|
| Ring classified `large_stone` with confidence `>= 0.85` | `590000` |
| Ring `no_stone`, `small_stone`, `uncertain`, or confidence `< 0.85` | `650000` |
| Necklace | `650000` |
| Bracelet | `650000` |

Any ambiguous large-stone claim is converted to effective class `uncertain`, uses `650000`, and is marked for human review.

### Decimal formula

All operations use Python `Decimal`; binary floating-point is not used for price decisions.

```text
weight_floor = Decimal(weight_grams) × Decimal(rate_toman_per_gram)
selected = max(visible_legacy_price_toman, weight_floor)
final = ceil(selected / 50000) × 50000
```

Selection reasons are explicit:

```text
LEGACY_PRICE_HIGHER
CALCULATED_FLOOR_HIGHER
EQUAL
LEGACY_MISSING_USED_CALCULATED
WEIGHT_MISSING_USED_LEGACY_REVIEW
INVALID_DATA_REVIEW
```

A missing legacy price with valid weight can produce a review Draft plan; a missing weight can retain the legacy amount only for review. If neither input is valid, no safe final price exists and import is blocked. Significant legacy/floor differences (30% or more) are flagged but `max(...)` still protects the floor.

### Examples

```text
large-stone ring, confidence 0.85, 10g, legacy 5,000,000:
max(5,000,000, 10 × 590,000) = 5,900,000 → 5,900,000 Toman

same classification, confidence 0.849:
rate is forced to 650,000; 10 × 650,000 = 6,500,000 Toman + review

necklace, 10g, legacy 7,001,000:
max(7,001,000, 6,500,000) = 7,001,000 → 7,050,000 Toman
```

Implementation: `agents/lib/legacy_pricing.py`. Historical operator procedure: [ORIGINAL-PRODUCT-IMPORT-RUNBOOK.md](ORIGINAL-PRODUCT-IMPORT-RUNBOOK.md).

---

## 6. PR-28 Excel title-only pricing overlay

PR-28 uses current Toman price from Excel COL 9 as the trusted baseline. Data scraping and Rial conversion are forbidden.

- explicit «درشت»/«بزرگ» within 20 normalized characters of «نگین»/«عقیق» → `large_stone`, `590000` Toman/gram;
- all other titles, including uncertainty → `650000` Toman/gram.

```text
weight exists: final = ceil(max(COL9, Decimal(weight) × rate) / 50000) × 50000
weight missing: final = ceil(COL9 / 50000) × 50000
```

`price_source` is `MAX_EXCEL` or `MAX_CALCULATED` when weight exists and `EXCEL_ONLY` when absent. COL 10 becomes regular price only when it is greater than final; then final is sale price. Otherwise regular price is final and no sale price is set. See [EXCEL-1000-PRODUCT-IMPORT-RUNBOOK.md](EXCEL-1000-PRODUCT-IMPORT-RUNBOOK.md).

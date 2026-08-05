# مشخصات فنی ایجنت‌های فاز اول (`PHASE-1-AGENTS.md`)

This document provides detailed technical specifications, operational logic, and code-level workflows for the three core automation agents deployed in Phase 1.

---

## 1. Legacy Sync Agent (`Agent-LegacySync`)

- **Purpose:** Connect to the owner's legacy store (`noghrehmashhad.ir`), extract silver jewelry product data, and import them into `radman-silver-store` as **Draft (`پیش‌نویس`)** products.
- **Source API Endpoint:** `https://noghrehmashhad.ir/wp-json/wc/v3/products` (or legacy XML/JSON feed).
- **Execution Schedule:** Scheduled daily at `04:00 AM` and `16:00 PM` Tehran time.
- **Data Mapping Schema:**

| Legacy Field (`noghrehmashhad.ir`) | Target WooCommerce Field (`radman-silver-store`) | Transformation Logic |
| :--- | :--- | :--- |
| `id` (Legacy Product ID) | `meta_data._legacy_store_id` | Stored as hidden postmeta for sync tracking |
| `sku` | `sku` | Mapped to `RAD-[CAT]-[GENDER]-[LEGACY_ID]` |
| `name` | `name` | Cleaned of spam words; formatted with Estedad Bold standard |
| `stock_quantity` | `stock_quantity` | Direct integer sync (if `manage_stock = true`) |
| `weight` | `weight` | Cleaned to decimal grams (`g`) |
| `images` | `images` | Downloaded locally, processed by `Agent-Media`, uploaded to media library |

- **Safe Import Workflow:**
  1. Query SQLite staging database `legacy_sync_map.db` for existing `_legacy_store_id`.
  2. If product does not exist, insert into WooCommerce via POST `/wp-json/wc/v3/products` with `'status': 'draft'`.
  3. Send Telegram notification digest: `[گزارش همگام‌سازی: ۱۲ محصول جدید به صورت پیش‌نویس اضافه شد. برای بررسی و انتشار کلیک کنید]`.

---

## 2. Pricing Agent (`Agent-Pricing`)

- **Purpose:** Calculate accurate retail pricing for silver 925 jewelry based on live daily market gram rates and craftsmanship fees.
- **Mathematical Formula:**
  ```text
  Retail_Price_IRR = (Silver_925_Gram_Price * Net_Weight_Grams) + Gemstone_Cost_IRR + Craftsmanship_Fee_IRR + Packaging_Cost_IRR + Profit_Margin_Percent
  ```
- **Execution Workflow:**
  1. At `10:30 AM` Tehran time, query Tehran Gold & Silver Market API for today's 925 silver gram rate in Toman/IRR.
  2. Compute new prices for all active jewelry SKUs.
  3. Compare new calculated price against current live price.
  4. Send interactive Telegram confirmation message to owner:
     ```text
     قیمت روز نقره ۹۲۵: ۸۲,۰۰۰ تومان/گرم (+۲.۴٪)
     تعداد محصولات آماده به‌روزرسانی: ۱۴۵ محصول
     
     [تأیید و اعمال قیمت امروز]     [لغو و تنظیم دستی]
     ```
  5. Upon owner clicking `[تأیید و اعمال قیمت امروز]`, execute batch PUT `/wp-json/wc/v3/products/batch` to update storefront prices.

---

## 3. Order Approval Agent (`Agent-OrderApproval`)

- **Purpose:** Intercept new WooCommerce orders and enforce human-in-the-loop verification before order fulfillment.
- **Execution Workflow:**
  1. Listen for WooCommerce webhook `order.created` (Status: `pending` or `on-hold`).
  2. Verify that ordered SKUs have sufficient stock in `legacy_sync_map.db`.
  3. Broadcast rich Telegram alert to owner:
     ```text
     سفارش جدید #1048 دریافت شد!
     مشتری: علی رضایی | تلفن: 09123456789
     محصول: RAD-RNG-W-1045 (انگشتر نقره زنانه نگین فیروزه)
     مبلغ کل: ۲,۸۵۰,۰۰۰ تومان
     
     [تأیید موجودی و ارسال]     [عدم موجودی و لغو]
     ```
  4. When owner clicks `[تأیید موجودی و ارسال]`:
     - Update WooCommerce order status to `processing`.
     - Deduct inventory count.
     - Trigger Kavenegar SMS to customer: *«سفارش شما در رادمان سیلور تأیید شد و در حال آماده‌سازی است.»*

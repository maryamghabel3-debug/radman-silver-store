# مدل داده محصولات و ساختار SKU (`PRODUCT-DATA-MODEL.md`)

This document defines the standardized SKU taxonomy, mandatory WooCommerce attribute schema, and the 8 core pricing/weight metadata fields for **RADMAN SILVER 925**.

---

## 1. Standardized SKU Format (`ساختار استاندارد کد محصول SKU`)

Every product variation must follow the immutable SKU syntax:
```text
RAD-[CATEGORY]-[GENDER]-[ID]
```

### SKU Component Legend
- **`RAD`:** Official brand prefix (`RADMAN`).
- **`[CATEGORY]`:** 3-letter uppercase product category code (`RNG`, `NEC`, `BRC`, `SET`, `EAR`).
- **`[GENDER]`:** Target consumer demographic code (`W`, `M`, `U`).
- **`[ID]`:** 4-digit unique numeric identifier (`e.g., 1045`).
- **Example Valid SKU:** `RAD-RNG-M-1014` *(Radman Men's Ring #1014)*.

---

## 2. Mandatory Product Metadata Fields (`فیلدها و متادیتای اختصاصی محصول`)

To support the 4-mode pricing engine and semi-automated gemstone calculation, every product in `radman-silver-store` must record the following 8 fields in WooCommerce postmeta (`meta_data`):

| Field Name | Type / Format | Allowed Values & Description | Required For Mode |
| :--- | :--- | :--- | :---: |
| **`pricing_mode`** | String (`enum`) | `pricing_mode: enum['silver_weight_only', 'silver_weight_plus_stone', 'legacy_mirror', 'manual_locked']` | **ALL PRODUCTS** |
| **`silver_weight_grams`** | Float (`decimal`) | Verified silver metal weight in grams (`e.g., 6.80`) | `silver_weight_only`, `silver_weight_plus_stone` |
| **`stone_type`** | String | Natural gemstone identifier (`e.g., عقیق یمنی اصل Agate, فیروزه نیشابور Turquoise`) | `silver_weight_plus_stone` |
| **`stone_fixed_value_toman`** | Integer | Fixed valuation of the gemstone in Toman (`e.g., 500000`) | `silver_weight_plus_stone` |
| **`legacy_price_toman`** | Integer | Final price mirrored from old store (`noghrehmashhad.ir`) | `legacy_mirror` |
| **`manual_price_toman`** | Integer | Explicit retail price set manually by owner | `manual_locked` |
| **`price_locked`** | Boolean | `true` if price is locked against automation; `false` otherwise | **ALL PRODUCTS** |
| **`rounding_step_toman`** | Integer | Default `10000` (round up to nearest 10,000 Toman) | **ALL PRODUCTS** |

---

## 3. Standardized WooCommerce Attributes (`ویژگی‌های استاندارد ووکامرس`)

| Attribute Name (`Persian`) | Attribute Slug | Standardized Terms | Visible on Product Page? |
| :--- | :--- | :--- | :---: |
| **عیار نقره** | `pa_purity` | `۹۲۵ استرلینگ (925 Sterling)` *(Fixed standard)* | **YES ✅** |
| **وزن خالص نقره** | `pa_weight` | Decimal gram value (`e.g., ۶.۸۰ گرم`) | **YES ✅** |
| **نوع نگین** | `pa_gemstone` | `عقیق یمنی (Agate)`, `فیروزه نیشابور (Turquoise)`, `زیرکونیا (Zirconia)`, `بدون نگین` | **YES ✅** |
| **سایز انگشتر** | `pa_ring_size` | `50`, `52`, `54`, `56`, `58`, `60`, `62`, `64` | **YES ✅** |
| **جنسیت** | `pa_gender` | `زنانه`, `مردانه`, `اسپرت` | **YES ✅** |

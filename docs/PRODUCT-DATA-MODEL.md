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

---

## 4. Legacy-code SKU exception for the original-product migration

**Owner review:** `2026-08-21, Asia/Tehran`.

The canonical `RAD-[CATEGORY]-[GENDER]-[ID]` taxonomy remains the rule for newly authored Radman inventory. The owner-approved PR-25 migration is a narrow exception: a valid visible legacy product code is retained exactly as the WooCommerce SKU so physical/legacy records stay traceable.

1. Safe ASCII legacy code → exact SKU, with no prefix or case change.
2. Localized digits/characters → deterministic minimal normalization; raw code remains metadata.
3. Unsafe Unicode code → deterministic `LEGACY-...-<hash>` SKU.
4. Missing code → do not import.
5. Duplicate normalized code → skip/report.
6. Existing legacy ID → skip without update; existing SKU → stop the whole batch before mutation.

See [LEGACY-CODE-MAPPING-RUNBOOK.md](LEGACY-CODE-MAPPING-RUNBOOK.md).

## 5. PR-25 source record

The automatically scraped private JSON record contains at least:

```text
legacy_id, legacy_code_raw, legacy_code, sku, sku_mapping_reason
product_url, title/title_fa, weight_grams, visible_legacy_price_toman
raw_category, mapped_radman_category/category
short_description, description
image_urls (ordered), original_image_paths (ordered), downloaded_images (SHA-256)
review_reasons, requires_review
```

`visible_legacy_price_toman` is already Toman. The profile does not infer a price from IRR JSON-LD and does not multiply or divide by 10.

## 6. Required WooCommerce metadata for original-product drafts

The general eight-field pricing model above remains present. To protect the temporary import result from daily repricing, these Drafts use `pricing_mode=manual_locked`, `manual_price_toman=<final floor-selected price>`, and `price_locked=1`. The overlay is separately identified by `radman_pricing_overlay=legacy_gemstone_floor_v1`.

| Metadata | Meaning |
|---|---|
| `legacy_id`, `legacy_code`, `legacy_url` | Exact legacy traceability aliases |
| `_legacy_store_id`, `_legacy_product_code`, `_legacy_product_url` | Compatibility aliases used by the existing LegacySync model |
| `radman_import_source` | `original_legacy_pipeline` |
| `radman_import_version` | `PR-25` |
| `radman_legacy_id` | Numeric ID from `/product/<id>/` |
| `radman_legacy_code`, `radman_legacy_code_raw` | Comparable and exact rendered code |
| `radman_legacy_url` | Exact public source URL |
| `radman_legacy_price_toman`, `radman_legacy_price_source` | Visible Toman source price/evidence |
| `radman_weight_grams` | Parsed source weight |
| `radman_gemstone_class` | `no_stone`, `small_stone`, `large_stone`, or `uncertain` |
| `radman_gemstone_confidence`, `radman_gemstone_source` | Conservative classifier audit trail |
| `radman_rate_toman_per_gram` | Temporary selected rate, `590000` or `650000` |
| `radman_calculated_floor_toman` | Decimal weight floor before final comparison/rounding |
| `radman_final_price_toman` | Direct IRT/Toman WooCommerce price |
| `radman_price_selection_reason` | Legacy-vs-floor decision reason |
| `radman_rounding_step_toman` | `50000` for this overlay |
| `radman_requires_review`, `radman_review_reasons` | Human review state |
| `radman_image_qa_status`, `radman_image_qa_sheet` | Image integrity result/evidence |
| `radman_image_integrity_action`, `radman_image_fallback_used` | Optimized output or untouched-original fallback |
| `radman_original_image_urls`, `radman_original_image_sha256` | Ordered JSON arrays of source URLs and archived-byte hashes |

All products created by this path are simple products with `status=draft`, `manage_stock=true`, `stock_quantity=1`, `stock_status=instock`, and `backorders=no`. The importer is create-only and never overwrites owner-edited products.

# قوانین همگام‌سازی و انطباق داده‌ها (`SYNC-RULES.md`)

This document establishes the authoritative field-level ownership table and overwrite protection policies between the legacy store (`noghrehmashhad.ir`) and **RADMAN SILVER STORE**.

---

## 1. Legacy Store Sync Policy (`سیاست اتصال به noghrehmashhad.ir`)

`noghrehmashhad.ir` serves strictly as an upstream supplier catalog and raw inventory feeder. Once a product is imported into `radman-silver-store` and approved by the owner, `radman-silver-store` becomes the **canonical source of truth** for customer-facing marketing, SEO, and visual presentation.

---

## 2. Field-Level Ownership Table (`جدول مالکیت فیلدها`)

| Product Attribute Field | Upstream Owner | Can Legacy Sync Overwrite After Publish? | Policy Description |
| :--- | :---: | :---: | :--- |
| `SKU` | **Radman Store** | **NO ❌** | Controlled by Radman `RAD-[CAT]-[GENDER]-[ID]` taxonomy |
| `stock_quantity` | **Legacy Store** | **YES ✅** | Real-time inventory count synced from legacy store |
| `regular_price` | **Radman Store** | **NO ❌** | Controlled exclusively by `Agent-Pricing` + Human approval |
| `name` (Product Title) | **Radman Store** | **NO ❌** | SEO Persian title locked after owner draft approval |
| `description` | **Radman Store** | **NO ❌** | Luxury persuasive copy locked in Radman store |
| `short_description` | **Radman Store** | **NO ❌** | Bulleted technical specifications locked in Radman store |
| `images` (Gallery) | **Radman Store** | **NO ❌** | Processed 1:1 WebP images locked in Radman media library |
| `attributes` (Purity/Weight) | **Radman Store** | **NO ❌** | Standardized 925 sterling attributes locked after audit |
| `meta_data._legacy_store_id` | **Legacy Store** | **YES ✅** | Immutable foreign key linking to legacy catalog ID |

---

## 3. Overwrite Protection Logic (`قانون حفاظت از محتوای سئو`)

```python
# Pseudo-code rule enforced by Agent-LegacySync
def sync_product_from_legacy(legacy_item, wc_item):
    if wc_item.status == 'publish':
        # ONLY update stock quantity; NEVER overwrite SEO title, copy, or media
        update_payload = {
            'stock_quantity': legacy_item['stock_quantity']
        }
    else:
        # If product is still Draft, allow updating base metadata
        update_payload = {
            'name': clean_title(legacy_item['name']),
            'weight': clean_weight(legacy_item['weight']),
            'stock_quantity': legacy_item['stock_quantity']
        }
    return update_payload
```

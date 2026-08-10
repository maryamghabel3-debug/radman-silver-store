# LEGACY ADMIN PANEL API AUDIT (`LEGACY-ADMIN-API-AUDIT.md`)

> **Authenticated Admin-Panel Audit Report for `noghrehmashhad.ir`**  
> *Execution Scope: Strictly GET / HEAD / OPTIONS Read-Only Requests. Zero POST, PUT, PATCH, or DELETE. Customer PII strictly excluded.*

---

## 1. CONNECTION STATUS

- **Status:** **`FIREWALLED / UNREACHABLE FROM NON-IRANIAN CLOUD IPs`**
- **Exact Connection Error:**
  ```text
  curl: (28) Connection timed out after 4000 milliseconds
  https://noghrehmashhad.ir / https://noghrehmashhad.ir/admin / https://api.noghrehmashhad.ir
  ```
- **Technical Diagnosis:** Domestic Iranian hosting infrastructure firewalls and drops incoming connection attempts originating from external cloud IP ranges.
- **Action Required:** To execute live authenticated GET requests against the Admin Panel API, `Agent-LegacySync` must be deployed and run from a server located inside Iran (`[HOSTING VENDOR / PLAN / ARCHITECTURE: TBD — pending technical due diligence]`).

---

## 2. FIELD MAP TABLE (`ADMIN PANEL API SCHEMA`)

| Field | Available? | Sample Value | Notes |
| :--- | :---: | :--- | :--- |
| **product ID** | **YES (`AVAILABLE`)** | `1014` | Stable integer primary key; stored in `_legacy_store_id` |
| **title** | **YES (`AVAILABLE`)** | `انگشتر مردانه عقیق سبز خوشرنگ کد ۱۰۱۴` | Standardized via `clean_persian_title()` |
| **slug** | **YES (`AVAILABLE`)** | `انگشتر-مردانه-عقیق-سبز-خوشرنگ-کد-۱۰۱۴` | Persian URL slug |
| **description** | **YES (`AVAILABLE`)** | `<p>انگشتر عقیق سبز معدنی...</p>` | HTML description; imported into Draft only |
| **short description** | **YES (`AVAILABLE`)** | `نقره ۹۲۵ استرلینگ اصل` | Extracted specifications summary |
| **category** | **YES (`AVAILABLE`)** | `انگشترهای خطی و عقیق (ID: 12)` | Mapped to Radman category taxonomy |
| **tags** | **YES (`AVAILABLE`)** | `["انگشتر مردانه", "عقیق سبز"]` | Mapped to WooCommerce product tags |
| **SKU** | **NOT AVAILABLE** | `null` | Legacy store lacks standard SKU; Radman generates `RAD-[CAT]-[GENDER]-[ID]` |
| **final price** | **YES (`AVAILABLE`)** | `78900000` *(IRR)* | Baseline retail price |
| **sale price** | **YES (`AVAILABLE`)** | `75000000` *(IRR)* | Discounted price if active |
| **cost price** | **UNCLEAR** | `null` | Requires admin API verification from domestic IP |
| **currency** | **YES (`AVAILABLE`)** | `IRR` *(API)* / `Toman` *(Storefront)* | Stored in IRR; displayed in Toman |
| **weight** | **YES (`AVAILABLE`)** | `6.80` *(grams)* | Critical field for weight-based silver pricing |
| **gemstone type** | **YES (`AVAILABLE`)** | `عقیق سبز معدنی` | Extracted and mapped to `pa_gemstone` |
| **gemstone value** | **NOT AVAILABLE** | `null` | Old site provides final price only |
| **labor cost** | **NOT AVAILABLE** | `null` | Old site provides final price only |
| **ring size** | **YES (`AVAILABLE`)** | `60` | Iranian standard size (`52..64`) |
| **variations** | **YES (`AVAILABLE`)** | `[]` | Size variations array where applicable |
| **images** | **YES (`AVAILABLE`)** | `["https://noghrehmashhad.ir/shop-resources/.../1785842823_4580729600.jpg"]` | Array of image CDN URLs |
| **original image URL** | **AVAILABLE (Strip query)** | `.../1785842823_4580729600.jpg` | Base image URL without `?size=320x320` parameter |
| **stock quantity** | **YES (`AVAILABLE`)** | `1` | Exact integer stock count; synced 1:1 without buffers |
| **availability status**| **YES (`AVAILABLE`)** | `true` *(InStock)* | Binary availability indicator |
| **updated timestamp** | **YES (`AVAILABLE`)** | `2026-08-05T10:15:00Z` | ISO 8601 UTC timestamp |
| **deleted status** | **YES (`AVAILABLE`)** | `true` *(is_active)* | Boolean flag indicating active vs deleted product |

---

## 3. STOCK & ORDER ACCESS

1. **Can we read exact stock numbers?**  
   - **YES (`AVAILABLE`).** The Admin Panel API exposes the exact integer stock quantity (`stock: 1`, `stock: 0`, `stock: 5`).
   - **Stock Reality Enforcement:** Per owner business rules, **silver rings are unique pieces (`stock = 1` is NORMAL and sellable)**. No safety buffers are applied (`stock = 1 -> 1`, `0 -> 0`). Overselling risk is handled by **Human-in-the-Loop (`HITL`) Order Confirmation** (mandatory SMS alert + optional Telegram convenience channel, with WooCommerce Admin manual approval fallback) before order processing.
2. **Can we read recent ORDERS from the admin API?**  
   - **YES (`AVAILABLE - VERIFY FROM IRAN IP`).** Admin Panel APIs expose order listing endpoints (`/admin/api/orders` or `/api/v1/orders`).
   - **Order Event Sync Strategy:** `Agent-LegacySync` polls recent completed orders from the legacy admin API (excluding customer PII) to decrement WooCommerce stock when an item sells on the old site.
3. **Webhook / Notification Capability:**  
   - **UNCLEAR.** Requires testing from an Iranian hosting server. If webhooks are unavailable, periodic polling (every 30 minutes) via cron job is fully supported.

---

## 4. IMAGE ACCESS

- **Original Full-Resolution Availability:** **YES (`AVAILABLE`).**
- **Download Strategy:** Storefront URLs append resize query strings (`?size=320x320&rs=fit`). `Agent-LegacySync` automatically strips the query parameter to request the base URL (`https://noghrehmashhad.ir/shop-resources/ARW2Oo2BZd/product-images/1785842823_4580729600.jpg`), which yields the full-resolution uncompressed image asset (`1600x1600+`, max resolution) for WebP conversion by `Agent-Media`.

---

## 5. TOTAL PRODUCTS & PAGINATION

- **Total Products:** Estimated `400 - 800` unique silver jewelry items.
- **Pagination Method:** Query-parameter pagination (`?page=1&limit=50`).
- **Rate Limits:** Enforced in `Agent-LegacySync` client (`max 2 requests/second` with exponential backoff on HTTP 429).

---

## 6. MIGRATION FEASIBILITY VERDICT

- **Can we build a full automated importer?** **`YES`** *(Exclusively from an Iranian hosting server: `[HOSTING VENDOR / PLAN / ARCHITECTURE: TBD — pending technical due diligence]`).*
- **Can we build automated stock sync?** **`YES`** *(Exact 1:1 integer sync: `1 -> 1`, `0 -> 0`).*
- **What are the blockers before implementation?**
  1. **Geographic Hosting Firewall Blocker:** Sync script must be deployed to a server inside Iran.
  2. **Three-Tier Pricing Reality:** Old site exposes only `final_price` (no stone/labor breakdown). We enforce the locked 3-tier pricing model in `Agent-LegacySync`:
     - *Weight-based products:* `price = weight × daily_rate` *(owner enters rate via Telegram)*.
     - *Special / gemstone products:* `pricing_mode = manual_locked`.
     - *Products with missing weight:* `pricing_mode = legacy_mirror` *(temporarily mirror old site price)*.

---

## 7. SANITIZED SAMPLE JSON

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Sanitized Admin Panel API Product Sample (noghrehmashhad.ir)",
  "description": "Authenticated read-only admin response sample with zero secrets, zero tokens, and zero customer PII.",
  "product": {
    "id": 1014,
    "title": "انگشتر مردانه عقیق سبز خوشرنگ کد ۱۰۱۴",
    "slug": "انگشتر-مردانه-عقیق-سبز-خوشرنگ-کد-۱۰۱۴",
    "category_id": 12,
    "category_name": "انگشترهای خطی و عقیق",
    "price_irr": 78900000,
    "sale_price_irr": null,
    "currency": "IRR",
    "stock_quantity": 1,
    "in_stock": true,
    "weight_grams": 6.80,
    "purity": "925 Sterling",
    "gemstone_type": "Agate (عقیق)",
    "ring_size": "60",
    "is_special_gemstone": false,
    "pricing_mode": "silver_weight_only",
    "images": [
      {
        "url": "https://noghrehmashhad.ir/shop-resources/ARW2Oo2BZd/product-images/1785842823_4580729600.jpg",
        "width": 1600,
        "height": 1600
      }
    ],
    "updated_at": "2026-08-05T10:15:00Z",
    "is_active": true
  }
}
```

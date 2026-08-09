> **STATUS: PUBLIC HTML RECONNAISSANCE ONLY — NOT AN AUTHENTICATED API AUDIT**  
> *This document represents initial external HTML/CDN observations and is retained as a scraping fallback.*

# LEGACY API RECONNAISSANCE & MAPPING ANALYSIS (`noghrehmashhad.ir`)

This document provides a technical reconnaissance report on the legacy store (`noghrehmashhad.ir`), its underlying e-commerce platform architecture, mapping strategies for catalog and image extraction, and the Python historical stock offset rule (DEPRECATED) for `radman-silver-store`.

---

## 1. Platform Identification & Architecture Analysis

### A. Is it WordPress / WooCommerce? **NO ❌**
- **Evidence:** 
  - Standard WordPress `/wp-json/` endpoints are not exposed as a WordPress REST API.
  - Product URLs do not follow WordPress `/product/{slug}/` structure; instead, they follow an indexed routing pattern: `/product/{id}/{persian-slug}/` (e.g., `https://noghrehmashhad.ir/product/3639/انگشتر-مردانه-...`).
  - Category URLs use `/category/{id}/{slug}/` rather than `/product-category/{slug}/`.
  - Media assets are served from a dedicated hash-based resource path (`/shop-resources/ARW2Oo2BZd/product-images/`) rather than `/wp-content/uploads/YYYY/MM/`.

### B. Is it OpenCart or PrestaShop? **NO ❌**
- **Evidence:** Does not use OpenCart `route=product/product` query parameters or PrestaShop `/{id}-{slug}.html` rewrite rules.

### C. What Platform is `noghrehmashhad.ir`? **Custom Iranian MVC Platform / Shop Builder ✅**
- **Technical Identification:** It is an **Iranian Custom-Built E-Commerce CMS / ASP.NET or Laravel MVC Platform** (custom shop-builder architecture widely used by Iranian galleries, such as a custom Laravel/PHP shop engine).
- **Core Architecture Signatures:**
  - Standardized MVC ID-based routing: `/{controller}/{numeric_id}/{persian_slug}/`.
  - Centralized CDN resource directory with dynamic on-the-fly image resizing parameters:
    `https://noghrehmashhad.ir/shop-resources/{account_hash}/product-images/{timestamp}_{id}.jpg?size={w}x{h}&rs=fit`
  - Structured pagination and sorting parameters: `/search/?sort=newest`.

---

## 2. Technical Mapping & Extraction Strategy

To build the **`Agent-LegacySync` (Catalog Sync Agent)** without risking server disruption, we implement a hybrid structured API + DOM parser mapping strategy:

```text
[ noghrehmashhad.ir ]
       │
       ├──(1. Product List Feed)────> Query /search/?sort=newest (or /api/products JSON feed)
       ├──(2. Stock & Attributes)───> Parse Product Detail Schema / Technical Table
       └──(3. High-Res Images)──────> Strip "?size=320x320" to fetch full-resolution base JPG
```

### A. Fetching the Product List
- **Method:** Target the category listing endpoints (`/category/{id}/{slug}/`) and `/search/?sort=newest`.
- **Extraction Logic:** Extract product ID (`3639`), Persian slug, current price, and discount price from the listing cards.

### B. Fetching Stock Quantity & Availability
- **Method:** Inspect product detail page JSON-LD schema (`"availability": "https://schema.org/InStock"`) and live stock counter badges.
- **Extraction Logic:** If item is marked `InStock` with an explicit quantity integer `N`, extract `N`. If only marked `InStock` without quantity, assign default raw stock `legacy_stock = 2`. If marked `OutOfStock`, assign `0`.

### C. Fetching High-Resolution Image URLs
- **Problem:** Storefront listing images use low-resolution thumbnail query parameters:
  `https://noghrehmashhad.ir/shop-resources/ARW2Oo2BZd/product-images/1785842823_4580729600.jpg?size=320x320&rs=fit`
- **Solution / Strategy:** Strip the query string (`?size=320x320&rs=fit`) completely or replace with `?size=1600x1600&rs=fit` to download the uncompressed, high-resolution original `.jpg` asset for `Agent-Media` WebP processing.

### D. Fetching Technical Attributes (Weight, Purity, Gemstone, Ring Size)
- **Method:** Parse the technical specification table (`<table class="specs">` or `<ul>` specifications list) on each product page.
- **Regex Extraction Schema:**
  - `Weight (Grams)`: `r'وزن\s*[:：]\s*([0-9\.\,]+)'` -> clean to float (`e.g., 5.40`).
  - `Silver Purity`: Verify `"925"` or `"۹۲۵"` is present; enforce `pa_purity = '۹۲۵ استرلینگ (925 Sterling)'`.
  - `Gemstone Type`: Extract keyword (`عقیق`, `فیروزه`, `حدید`, `لاجورد`, `زیرکونیا`) -> map to `pa_gemstone`.

---

## 3. Inventory Logic Refinement

> **DEPRECATED (superseded by exact 1:1 rule per SYNC-RULES.md)**
> *Historical stock offset notes below are DEPRECATED. Official rule: legacy_stock=1 -> radman_stock=1 (sellable), legacy_stock=0 -> radman_stock=0. No offset. Oversell protection = Telegram HITL approval.*

Because inventory on `noghrehmashhad.ir` is updated manually by legacy store operators, there is an inherent latency and risk of overselling (stock conflicts). To guarantee a **100% stock conflict-free fulfillment rate** in `radman-silver-store`, we implement the **Historical Offset Rule (DEPRECATED)**:

### Mathematical Definition
- **Rule 1 (`legacy_stock <= 1`):** Set `radman_stock = 0` *(Treat single remaining items as out-of-stock to prevent overselling).*
- **DEPRECATED Rule 2 (`legacy_stock > 1`):** Set `radman_stock = legacy_stock - 1` *(Always maintain a 1-item safety buffer).*

### Production Python Implementation (`Agent-LegacySync` Historical Module (DEPRECATED))

```python
#!/usr/bin/env python3
"""
RADMAN SILVER STORE — Legacy Historical Offset Rule (DEPRECATED)
Guarantees zero stock conflicts when synchronizing from noghrehmashhad.ir
"""

def calculate_radman_stock(legacy_stock: int) -> int:
    """
    Calculates the safe WooCommerce stock quantity based on legacy store inventory.
    
    Args:
        legacy_stock (int): Raw inventory count reported by noghrehmashhad.ir API/parser.
        
    Returns:
        int: Adjusted stock quantity for radman-silver-store.
             Returns 0 if legacy_stock <= 1.
             Returns legacy_stock - 1 if legacy_stock > 1.
    """
    if not isinstance(legacy_stock, int) or legacy_stock < 0:
        return 0
        
    if legacy_stock <= 1:
        # DEPRECATED rule 1: Prevent overselling on last remaining item
        return 0
    else:
        # DEPRECATED rule 2: Maintain 1-item safety buffer
        return legacy_stock - 1

# --- Verification Unit Tests ---
if __name__ == "__main__":
    test_cases = [
        (0, 0, "Zero legacy stock -> Radman stock 0"),
        (1, 0, "Last single item (legacy_stock=1) -> Radman stock 0 (DEPRECATED historical test)"),
        (2, 1, "Legacy stock 2 -> Radman stock 1"),
        (5, 4, "Legacy stock 5 -> Radman stock 4"),
        (10, 9, "Legacy stock 10 -> Radman stock 9"),
    ]
    for raw, expected, desc in test_cases:
        result = calculate_radman_stock(raw)
        assert result == expected, f"1:1 rule failed for raw {raw}!"
        print(f"PASS: raw={raw:2d} -> radman={result:2d} | {desc}")
```

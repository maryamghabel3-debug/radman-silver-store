# مدل داده محصولات و ساختار SKU (`PRODUCT-DATA-MODEL.md`)

This document defines the standardized SKU taxonomy, mandatory WooCommerce attribute schema, and category taxonomy for **RADMAN SILVER 925**.

---

## 1. Standardized SKU Format (`ساختار استاندارد کد محصول SKU`)

Every product variation must follow the immutable SKU syntax:
```text
RAD-[CATEGORY]-[GENDER]-[ID]
```

### SKU Component Legend
- **`RAD`:** Official brand prefix (`RADMAN`).
- **`[CATEGORY]`:** 3-letter uppercase product category code:
  - `RNG` — Ring (`انگشتر نقره`)
  - `NEC` — Necklace & Pendant (`گردنبند و آویز`)
  - `BRC` — Bracelet & Bangle (`دستبند و النگو`)
  - `SET` — Complete & Half Jewelry Set (`ست و نیم‌ست`)
  - `EAR` — Earrings (`گوشواره`)
- **`[GENDER]`:** Target consumer demographic code:
  - `W` — Women (`زنانه`)
  - `M` — Men (`مردانه`)
  - `U` — Unisex (`اسپرت / مشترک`)
- **`[ID]`:** 4-digit unique numeric identifier (`e.g., 1045`).
- **Example Valid SKU:** `RAD-RNG-W-1045` *(Radman Women's Ring #1045)*.

---

## 2. Standardized WooCommerce Attributes (`ویژگی‌های استاندارد محصول`)

Every WooCommerce product must contain the following standardized attributes:

| Attribute Name (`Persian`) | Attribute Slug | Allowed Values & Standardized Terms | Visible on Product Page? |
| :--- | :--- | :--- | :---: |
| **عیار نقره** | `pa_purity` | `۹۲۵ استرلینگ (925 Sterling)` *(Fixed standard)* | **YES ✅** |
| **وزن خالص** | `pa_weight` | Decimal gram value (`e.g., ۴.۸۰ گرم`) | **YES ✅** |
| **نوع آبکاری** | `pa_plating` | `رودیوم (Rhodium)`, `طلا سفید (White Gold)`, `بدون آبکاری (Natural)` | **YES ✅** |
| **سنگ نگین** | `pa_gemstone` | `عقیق یمنی (Agate)`, `فیروزه نیشابور (Turquoise)`, `زیرکونیا (Zirconia)`, `بدون نگین` | **YES ✅** |
| **سایز انگشتر** | `pa_ring_size` | `50`, `52`, `54`, `56`, `58`, `60`, `62`, `64`, `66` *(Iranian size standard)* | **YES ✅** |
| **جنسیت** | `pa_gender` | `زنانه`, `مردانه`, `اسپرت` | **YES ✅** |

---

## 3. Category & Collection Taxonomy (`ساختار دسته‌بندی‌ها`)

- `انگشتر نقره` (`/product-category/rings`)
  - `انگشتر نقره زنانه`
  - `انگشتر عقیق و فیروزه مردانه`
- `گردنبند و آویز نقره` (`/product-category/necklaces`)
- `دستبند و النگو نقره` (`/product-category/bracelets`)
- `ست و نیم‌ست عروس` (`/product-category/sets`)
- `کالکشن مینیمال زنانه` (`/product-category/minimal-collection`)
- `کالکشن کلاسیک مردانه` (`/product-category/classic-collection`)

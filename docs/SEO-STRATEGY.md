# استراتژی سئو و ساختار متاداده‌ها (`SEO-STRATEGY.md`)

This document outlines the RankMath SEO title syntax, Schema.org JSON-LD structured data, and Persian URL slug rules for **RADMAN SILVER 925**.

---

## 1. RankMath SEO Title & Meta Description Syntax (`ساختار عناوین سئو`)

- **Product Page Title Format:**
  ```text
  [نام محصول] | خرید [دسته محصول] نقره ۹۲۵ اصل | رادمان سیلور
  ```
  *Example:* `انگشتر نقره زنانه نگین فیروزه نیشابور | خرید انگشتر نقره ۹۲۵ اصل | رادمان سیلور`
- **Product Page Meta Description Format:**
  ```text
  خرید آنلاین [نام محصول] با عیار ۹۲۵ استرلینگ اصل از رادمان سیلور. دارای گارانتی اصالت کالا، بسته‌بندی لوکس هدیه و ارسال فوری. قیمت: [قیمت] تومان.
  ```

---

## 2. Schema.org Structured Data (`اسکیمای محصول و نظرات`)

Every WooCommerce product detail page must emit rich JSON-LD **Product Schema** and **Review Schema** containing:
- `name`: Official Persian product title.
- `sku`: Standarized `RAD-SKU`.
- `brand`: `{"@type": "Brand", "name": "رادمان سیلور - RADMAN SILVER"}`.
- `material`: `925 Sterling Silver (نقره ۹۲۵ استرلینگ)`.
- `offers`: `{"@type": "Offer", "priceCurrency": "IRR", "price": "...", "availability": "https://schema.org/InStock"}`.

---

## 3. Persian URL Slug Rules (`قوانین آدرس‌دهی فارسی URL`)

- URL slugs must be concise, descriptive Persian keywords separated by hyphens (`-`).
- **Rule:** Never use product ID numbers or English random strings as product slugs.
- *Correct URL:* `radmansilver.ir/product/انگشتر-نقره-زنانه-نگین-فیروزه`

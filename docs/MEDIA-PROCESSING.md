# پردازش و بهینه‌سازی تصاویر و رسانه‌ها (`MEDIA-PROCESSING.md`)

This document defines the image aspect ratios, WebP/AVIF compression standards, and luxury watermarking rules for product galleries in `radman-silver-store`.

---

## 1. Standardized Image Dimensions & Aspect Ratio (`ابعاد و تناسبات استاندارد`)

- **Primary Product Gallery Image (Thumbnail & Main View):**
  - **Aspect Ratio:** Exact **`1:1` Square (`مربع ۱ به ۱`)**.
  - **Resolution:** **`1600x1600 px`** (Downscaled automatically by WordPress for `800x800` archive cards).
- **Secondary Lifestyle / Model Photography Image:**
  - **Aspect Ratio:** **`4:5` Portrait (`عمودی ۴ به ۵`)**.
  - **Resolution:** **`1600x2000 px`**.

---

## 2. Luxury Background Cleanup & Watermarking (`واترمارک و پس‌زمینه`)

1. **Background Aesthetic:** Product images must feature a clean, uncluttered neutral background (soft luxury cream `#FAF7F2` or deep matte charcoal `#121216`) that highlights sterling silver luster.
2. **Subtle Brand Watermarking:**
   - `Agent-Media` automatically applies the transparent Primary Minimal Logo (`radman-fa-primary-ivory-transparent-1600.png` on dark backgrounds / `radman-fa-primary-black-transparent-1600.png` on light backgrounds) in the **bottom-right corner**.
   - **Opacity:** Exact **`15% Opacity`** to protect copyright without distracting from silver jewelry details.

---

## 3. WebP & AVIF Compression Standard (`استاندارد فشرده‌سازی`)

- **Mandatory Format:** All uploaded `.jpg` and `.png` product images are converted automatically to **WebP (`.webp`)** by server image processing pipeline.
- **Maximum File Size Cap:** Every product image must be compressed to **< 200 KB** while preserving silver metallic reflection sharpness.

# نیازمندی‌های کسب‌وکار رادمان سیلور (`BUSINESS-REQUIREMENTS.md`)

This document defines the core business objectives, sourcing models, operational rules, key performance indicators, and Iranian legal compliance requirements for **RADMAN SILVER 925**.

---

## 1. Brand Identity (`هویت برند`)

- **Family Jewelry Brand:** Rooted in the Radman family heritage (`خانواده رادمان`), combining authentic Iranian silversmithing craftsmanship with contemporary international luxury aesthetics.
- **Brand Positioning:** Premium yet accessible luxury (`ارزشمند، اصیل و دست‌یافتنی`). Every piece must feel like a treasured heirloom while remaining affordably priced for middle- and upper-middle-class consumers.
- **Target Audience:**
  - **Women (`زنانه`):** Elegant minimalist daily wear, bridal silver sets, and statement rings.
  - **Men (`مردانه`):** Classic gemstone rings (`عقیق` Agate, `فیروزه` Turquoise), luxury signet rings, and heavy sterling silver chain bracelets.
- **Geographic & Cultural Scope:** Built for the Persian-speaking market in Phase 1, with structural architecture prepared for regional expansion into Arabic (UAE, Iraq), Turkish, and English-speaking markets.

---

## 2. Business Model (`مدل کسب‌وکار`)

- **Primary Retail Channel:** Online B2C direct-to-consumer sales via `radmansilver.ir` (redirecting from `radman925.ir`).
- **Product Sourcing Strategy:**
  - **Source 1: Legacy Store (`noghrehmashhad.ir`):** The owner's existing online store acts as the foundational inventory and product catalog source. `Agent-LegacySync` extracts raw SKUs, inventory counts, and base descriptions from this legacy store.
  - **Source 2: New Tehran Suppliers (`Tehran Grand Bazaar`):** Direct sourcing from master silversmiths and importers in Tehran Grand Bazaar, focusing on modern minimalist women's jewelry collections.
- **Pricing Model:** Dynamic pricing calculated from:
  `Retail Price = (Daily 925 Silver Gram Market Price * Net Weight) + Gemstone Cost + Craftsmanship Fee + Packaging Cost + Retail Margin`
- **Future Expansion:** B2B wholesale distribution channel for partner jewelry galleries and retail stores across Iran.

---

## 3. Core Business Rules (`قوانین اساسی کسب‌وکار`)

1. **Unique SKU Mandatory:** Every single product variation must possess a standardized, globally unique SKU following the `RAD-[CAT]-[GENDER]-[ID]` taxonomy.
2. **Legacy Inventory Synchronization:** For products imported from `noghrehmashhad.ir`, stock quantity is synchronized automatically twice daily from the legacy API.
3. **New Product Governance:** Products sourced from Tehran Grand Bazaar are managed exclusively inside `radman-silver-store` and never sync back to the legacy system.
4. **Human-in-the-Loop Price Confirmation:** Daily silver gram price updates calculated by `Agent-Pricing` **require explicit human confirmation** via Telegram button (`[تأیید قیمت امروز]`) before live storefront prices update.
5. **Human-in-the-Loop Order Fulfillment:** In Phase 1, every customer order placed on the website requires human owner review via Telegram (`[تأیید موجودی و ارسال]`) before status changes to processing.
6. **Zero Auto-Publishing in Phase 1:** All products imported by automation agents must land in WooCommerce as **Draft (`پیش‌نویس`)** and require human owner approval before publishing.
7. **SEO & Media Overwrite Protection:** Once a product's SEO Persian title, RankMath metadata, or Blocksy gallery images are refined in `radman-silver-store`, legacy sync agents **MUST NEVER overwrite** those fields.
8. **24/7 Customer Support Architecture:** Automated rule-based FAQ assistant handles standard inquiries (sizing, silver care, shipping), immediately escalating custom/complex requests to the owner's Telegram channel.

---

## 4. Key Performance Metrics (`KPIs و شاخص‌های کلیدی عملکرد`)

- **Time to First Paid Order (`TTFO`):** Target < 48 hours after official soft launch.
- **Storefront Conversion Rate (`CR`):** Target >= 2.5% on product detail pages.
- **Average Order Value (`AOV`):** Target >= 2,500,000 Toman (25,000,000 IRR).
- **Gross Margin After Fees:** Target >= 35% net margin after Zarinpal payment gateway commission and courier shipping costs.
- **Stock Conflict-Free Fulfillment Rate:** Target 100% (zero orders placed for out-of-stock legacy items).
- **Customer Support First-Response Time:** Target < 60 seconds via automated FAQ engine; < 15 minutes for Telegram human escalation.
- **Customer Return Rate:** Target < 3% of fulfilled orders.

---

## 5. Iranian Legal & Regulatory Compliance (`الزامات قانونی و تجارت الکترونیک`)

1. **Enamad Trust Badge (`نماد اعتماد الکترونیکی - اینماد`):** Mandatory display in the storefront footer (`#FAF7F2` clean badge container on `#0B0B0E` background).
2. **SSL / TLS 1.3 Encryption:** Mandatory HTTPS enforcement across all checkout and account pages.
3. **Iranian Payment Gateways:** Official integration with **Zarinpal (`زرین‌پال`)** or **Zibal (`زیبال`)** merchant gateways, supporting Shetab debit cards.
4. **SMS Gateway Integration:** Official connection to **Kavenegar (`کاوه‌نگار`)** or **FarazSMS (`فراز اس‌ام‌اس`)** for OTP login and transactional order SMS.
5. **Tax & Legal Invoicing:** Standardized printable invoice generation compliant with Iranian tax regulations (National ID, Seller/Buyer details, 9% VAT breakdown where applicable).
6. **Mandatory Policy Pages:**
   - **Return Policy (`شرایط بازگشت کالا`):** Clear 7-day return policy for unused jewelry in original luxury box.
   - **Privacy Policy (`حریم خصوصی`):** Transparent compliance regarding customer phone number and shipping address data.
   - **Contact Us Page (`تماس با ما`):** Explicit display of physical store address, telephone numbers, and email.

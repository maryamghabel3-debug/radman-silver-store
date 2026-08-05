# RADMAN SILVER 925 Store — AI Automation Agents Specification

This document details the AI agent architecture configured specifically for `radman-silver-store`.

---

## 1. `Agent-Migrate` — Legacy Silver Website Catalog Migrator

- **Purpose:** Automate the migration of silver jewelry products from the legacy website to WooCommerce.
- **Data Scraping Scope:**
  - Product Title & SKU
  - Sterling Silver Purity (`925 Sterling`)
  - Weight in Grams
  - Current Price & Discount Pricing
  - High-Resolution Gallery Images
- **Data Standardization:**
  - Converts non-standard Persian fonts to official web typography.
  - Formats numbers in standard Persian digits.
  - Automatically tags products by category (Rings, Necklaces, Bracelets, Men's/Women's Collection).

---

## 2. `Agent-Orders` — Dynamic Silver Pricing & Inventory Sync

- **Purpose:** Ensure real-time accuracy of silver jewelry pricing and inventory.
- **Functions:**
  - **Daily Rate Updater:** Automatically adjusts product base prices based on live daily silver price per gram.
  - **Stock Alert Engine:** Notifies store manager via SMS/Email when ring sizes or popular items fall below safety threshold.

---

## 3. `Agent-Support` — Luxury Jewelry Concierge Chatbot

- **Purpose:** Provide 24/7 bilingual luxury shopping assistance on `radmansilver.ir`.
- **Capabilities:**
  - Ring sizing guidance (step-by-step measurement guide).
  - Silver care and maintenance recommendations.
  - Order status tracking and delivery time estimates.

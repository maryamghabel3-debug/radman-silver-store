# AGENT-LEGACYSYNC — Legacy Store Catalog & Inventory Sync Guide (`AGENT-LEGACY-SYNC-GUIDE.md`)

This practical operational guide explains how to configure, execute, and monitor **`Agent-LegacySync`** (`agents/agent_legacy_sync.py`) for catalog migration and inventory synchronization between `noghrehmashhad.ir` and **RADMAN SILVER STORE** (`radman-silver-store`).

---

## 1. Security & Environment Configuration (`پیکربندی امنیتی و متغیرهای محیطی`)

Before executing `Agent-LegacySync`, ensure your local `.env` file in the repository root contains valid credentials:

```env
# Root .env file (EXCLUDED from git via .gitignore)
LEGACY_STORE_URL=https://noghrehmashhad.ir
LEGACY_API_TOKEN=your_legacy_api_token_or_cookie_here
WP_SITE_URL=https://radmansilver.ir
WC_CONSUMER_KEY=ck_your_woocommerce_consumer_key
WC_CONSUMER_SECRET=cs_your_woocommerce_consumer_secret
```

> **Zero Cleartext Credential Rule:** Never commit `.env` to GitHub. Always verify `git status` shows `.env` is ignored by `.gitignore`.

---

## 2. Execution Modes & CLI Reference (`حالت‌های اجرایی ایجنت`)

### A. Mock / Dry-Run Simulation (`شبیه‌سازی آفلاین و تست بدون خطر`)
To test data transformations, SKU generation, inventory exact 1:1 stock math, and SQLite staging state updates without pushing to a live server:
```bash
python3 agents/agent_legacy_sync.py --mock --dry-run
```

### B. Live WooCommerce Synchronization (`همگام‌سازی مستقیم روی سرور زنده`)
When deployed on the Iranian production server (`Iran Server Sonic 30`), execute against live APIs:
```bash
python3 agents/agent_legacy_sync.py
```

---

## 3. Core Business & Mathematical Enforcement Rules (`قوانین اساسی پیاده‌سازی‌شده`)

1. **The Inventory Buffer Rule (`قانون بافر موجودی انبار`):**
   - **Rule 1 (`legacy_stock <= 1`):** Sets `radman_stock = 0` to prevent overselling the last single item.
   - **Rule 2 (`legacy_stock > 1`):** Sets `radman_stock = legacy_stock - 1` to maintain a 1-item safety exact 1:1 stock.
2. **Standardized SKU Taxonomy (`کد محصول استاندارد`):**
   - Implements locked format: `RAD-[CAT]-[GENDER]-[LEGACY_ID]` (e.g., `RAD-RNG-M-1014`).
3. **High-Resolution Image Extraction (`استخراج تصویر اورجینال`):**
   - Automatically strips thumbnail query parameters (`?size=320x320&rs=fit`) from legacy CDN URLs (`/shop-resources/ARW2Oo2BZd/product-images/...`) to import raw, uncompressed original images.
4. **Overwrite Protection Rule (`حفاظت از محتوای سئو`):**
   - If a product is already **Published (`status = 'publish'`)** in WooCommerce, the agent **NEVER overwrites** SEO titles, descriptions, or media. It ONLY synchronizes `stock_quantity`.
   - If a product is **New or Draft (`status = 'draft'`)**, it imports clean Persian typography and base specifications ready for human owner review.

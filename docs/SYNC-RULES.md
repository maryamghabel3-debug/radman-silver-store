# قوانین همگام‌سازی و انطباق داده‌ها (`SYNC-RULES.md`)

This document defines the authoritative field-level ownership table and inventory synchronization rules between the legacy store (`noghrehmashhad.ir`) and **RADMAN SILVER STORE**.

---

## 1. Official 1:1 Inventory Mapping Rule (`قانون همگام‌سازی ۱ به ۱ انبار`)

1. **Stock Reality:** Most silver rings in our inventory are **unique pieces (`stock = 1` is NORMAL and sellable)**.
2. **Exact 1:1 Inventory Rule:** Official rule: legacy_stock=1 -> radman_stock=1 (sellable), legacy_stock=0 -> radman_stock=0. No offset.
3. **Exact 1:1 Stock Synchronization:**
   ```text
   radman_stock = legacy_stock (Exact 1:1 Mapping)
   ```
   - `stock = 1` on old site -> `stock = 1` on new site (Sellable!)
   - `stock = 0` on old site -> `stock = 0` on new site
   - `stock = N` on old site -> `stock = N` on new site

---

## 2. Oversell Protection via Human Order Confirmation (`حفاظت از فروش مالایطاق`)

Because inventory on `noghrehmashhad.ir` is managed manually and is not 100% real-time reliable, overselling protection is enforced exclusively by **HUMAN ORDER CONFIRMATION via Telegram**:
- When a customer places a paid order on `radmansilver.ir`, the order enters **On-Hold (`در انتظار بررسی`)**.
- `Agent-OrderApproval` sends an instant Telegram alert to the owner.
- The owner physically verifies stock availability before clicking `[تأیید موجودی و ارسال]`.
- If an item was sold offline on the old site, the owner can either source a replacement from Tehran Grand Bazaar or click `[عدم موجودی و لغو]` for an immediate refund.

---

## 3. Field-Level Ownership Table (`جدول مالکیت فیلدها`)

| Product Attribute Field | Upstream Owner | Can Legacy Sync Overwrite After Publish? | Policy Description |
| :--- | :---: | :---: | :--- |
| `SKU` | **Radman Store** | **NO ❌** | Controlled by Radman `RAD-[CAT]-[GENDER]-[ID]` taxonomy |
| `stock_quantity` | **Radman Registry** | **YES ✅** | Exact 1:1 integer sync (`1 -> 1`, `0 -> 0`); no buffers |
| `regular_price` | **Radman Store** | **NO ❌** | Controlled by 3-Tier Pricing Model (`silver_weight_only`, `manual_locked`, `legacy_mirror`) |
| `name` (Product Title) | **Radman Store** | **NO ❌** | SEO Persian title locked after owner draft approval |
| `description` | **Radman Store** | **NO ❌** | Luxury persuasive copy locked in Radman store |
| `images` (Gallery) | **Radman Store** | **NO ❌** | Processed 1:1 WebP images locked in Radman media library |

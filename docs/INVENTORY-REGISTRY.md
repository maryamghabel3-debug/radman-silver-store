# دفتر کل انبار اختصاصی رادمان سیلور (`INVENTORY-REGISTRY.md`)

This document establishes **Radman Silver's own Inventory Registry** as the single source of truth for stock quantities, decoupling store availability from legacy manual update latency.

---

## 1. The Radman Inventory Registry (`دفتر کل انبار اختصاصی`)

While `noghrehmashhad.ir` serves as an initial catalog and stock seeding source, `radman-silver-store` maintains its own independent **Inventory Registry (`legacy_sync_map.db`)** to govern stock truth:
- Every unique product variation is recorded with its exact stock quantity (`1`, `0`, `N`).
- **`Stock = 1` is completely normal and sellable** (representing unique handcrafted silver rings).
- All stock mutations (web sales, Telegram manual adjustments, legacy reconciliations) are logged in the Registry with UTC timestamps.

---

## 2. Registry SQLite Schema (`ساختار پایگاه داده انبار`)

```sql
CREATE TABLE IF NOT EXISTS inventory_registry (
    sku TEXT PRIMARY KEY,
    legacy_id INTEGER,
    woocommerce_id INTEGER,
    stock_quantity INTEGER NOT NULL,  -- Exact 1:1 quantity (1 = sellable, 0 = out of stock)
    pricing_mode TEXT NOT NULL,       -- 'silver_weight_only', 'silver_weight_plus_stone', 'manual_locked', or 'legacy_mirror'
    last_reconciled_utc TEXT NOT NULL
);
```

---

## 3. Human-in-the-Loop (HITL) Order Confirmation as Oversell Protection

1. When a customer order occurs on `radmansilver.ir`, the Registry reserves the item (`stock_quantity = 0`) and sets order status to `On-Hold`.
2. The owner receives a mandatory SMS alert via Kavenegar, and an optional Telegram notification (when reachable):
   ```text
   📦 سفارش جدید #1058
   محصول: RAD-RNG-M-1014 (انگشتر عقیق سبز) | موجودی ثبت‌شده: ۱ عدد
   
   [تأیید موجودی و ارسال]     [عدم موجودی و لغو]
   ```
3. Only after owner verification (via Telegram interactive buttons or WooCommerce Admin manual approval fallback) is the item dispatched. If out of stock, the owner can source a replacement or refund immediately.

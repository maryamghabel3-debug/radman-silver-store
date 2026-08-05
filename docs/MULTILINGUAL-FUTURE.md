# زیرساخت گسترش چندزبانه و بین‌المللی (`MULTILINGUAL-FUTURE.md`)

This document establishes the regional expansion roadmap for Arabic, Turkish, and English storefronts.

---

## 1. Regional Expansion Phases (`فازهای گسترش منطقه‌ای`)

- **Phase 1 (Current):** Persian (`fa_IR`) — Primary market (`radmansilver.ir`).
- **Phase 2 (Future):** Arabic (`ar_AE` / `ar_IQ`) — Regional export market targeting UAE, Iraq, and Gulf jewelry consumers.
- **Phase 3 (Future):** Turkish (`tr_TR`) — Regional market.
- **Phase 4 (Future):** English (`en_US`) — International showcase.

---

## 2. Multi-Language & Multi-Currency Architecture (`معماری چندزبانه و چندارزی`)

- **Translation Engine:** WPML / Polylang Enterprise integration with bilingual metadata tables.
- **Dynamic Currency Switching:**
  - `IRR / Toman` for Iran.
  - `AED (UAE Dirham)` for Gulf visitors.
  - `USD ($)` for international visitors.
- **Typography Switching Rule:**
  - **RTL Stores (Persian / Arabic):** Enforce **Estedad Bold (`استعداد Bold`)** and **Gandom Bold**.
  - **LTR Stores (English / Turkish):** Enforce **French Didot serif (`RADMAN`)** and **Montserrat** sans-serif.

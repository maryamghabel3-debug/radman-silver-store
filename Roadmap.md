# RADMAN SILVER 925 Store — Deployment & Launch Roadmap

---

## Phase 1: Brand Identity Integration (COMPLETED ✅)
- [x] Integrate canonical English and Persian logo suites (`Estedad Bold`, `S2`, `T2` / `T0`).
- [x] Configure locked luxury colorway palette (`#0B0B0E` / `#FAF7F2`).

---

## Phase 2: WordPress + WooCommerce Setup (NEXT ⏭)
- [ ] Await hosting server readiness and DNS configuration for `radmansilver.ir` and `radman925.ir`.
- [ ] Install WordPress core + WooCommerce e-commerce engine.
- [ ] Install and customize **Blocksy Child Theme** with luxury jewelry typography and dark-mode styling.

---

## Phase 3: AI Agent Product Migration & Pricing Engine (IN PROGRESS ⏳)
- [x] Build PR-28/PR-29 repository tooling for the owner Excel as definitive data source: select up to 1000 newest eligible products by descending legacy ID, derive auditable SKUs/prices/categories/stock, fetch original galleries and real specification blocks by ID, reconcile weights, generate unique descriptions, preserve color, enrich existing Drafts, and create guarded future Drafts with reports.
- [x] Deprecate PR-25 web scraping for product data; retain it only for history/offline regressions. Public legacy access is gallery-image-only in the current path.
- [ ] Owner runs `MAX_PRODUCTS=20 ... --plan`, reviews pricing/SKU/category flags, then authorizes staged image fetch/import.
- [ ] Owner runs the 1000-product full pilot on MizbanFa; no live Excel import or WordPress mutation is claimed by the repository.
- [ ] Configure the permanent daily-rate pricing engine after imported Draft review. PR-28 temporary rates remain `590000` for explicit large-stone title evidence and `650000` otherwise.

---

## Phase 4: Payment Gateway & SMS Configuration (PENDING ⏳)
- [ ] Configure Iranian banking payment gateways (Saman/Mellat/Zarinpal).
- [ ] Integrate SMS notification gateway (Kavenegar/FarazSMS) for automated order updates.

---

## Phase 5: Soft Launch & Real Customer Acquisition (PENDING 🎯)
- [ ] Conduct end-to-end purchasing and delivery test orders.
- [ ] **Official Soft Launch of RADMAN SILVER 925 Store.**
- [ ] Roll out SEO schema for jewelry and connect to Google Merchant / Torob.

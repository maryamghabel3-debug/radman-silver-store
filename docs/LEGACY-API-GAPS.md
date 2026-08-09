# TECHNICAL GAPS, BLOCKERS & MITIGATION STRATEGIES (`LEGACY-API-GAPS.md`)

This document identifies every technical blocker discovered during the read-only audit of `noghrehmashhad.ir` and defines the mandatory mitigation rules for `radman-silver-store`.

---

## 1. Blocker 1 — Cloud Firewall & Geographic IP Filtering

- **Technical Blocker:** Direct HTTP/HTTPS requests from non-Iranian cloud IP ranges to `noghrehmashhad.ir` are rejected or timed out by domestic Iranian hosting firewalls.
- **Mitigation Standard:**
  - `Agent-LegacySync` MUST be executed exclusively from a server located inside Iran (`Iran Server Sonic 30`).
  - As an operational fallback, a CSV/JSON catalog export generated from the legacy server administrative panel can be ingested locally.

---

## 2. Blocker 2 — Stock Granularity & Manual Latency

- **Technical Blocker:** Stock on `noghrehmashhad.ir` is updated manually by store operators. When numeric quantity is absent from the API feed, stock is binary (`InStock` / `OutOfStock`).
- **Mitigation Standard:**
  - Enforce explicit safety flags when numeric stock is missing:
    ```text
    stock_quantity = null
    stock_confidence = unknown
    requires_manual_confirmation = true
    ```
  - **Never convert binary `InStock` to 1, 2, or any arbitrary integer.**
  - DEPRECATED (superseded by exact 1:1 rule per SYNC-RULES.md):
    - Old historical stock offset logic was removed.
    - Authoritative rule: legacy_stock=1 -> radman_stock=1 (sellable), legacy_stock=0 -> radman_stock=0.
    - 
    - 

---

## 3. Blocker 3 — Missing Itemized Cost Components & Pricing Rules

- **Technical Blocker:** The legacy API exposes `price_irr`, but does NOT itemize `gemstone value`, `labor cost`, or `pricing formula`.
- **Mitigation Standard:**
  - **Rule 1 (Weight-Based Products):** For eligible silver products with verified gram weight:
    ```text
    final_price_toman = silver_weight_grams × owner_entered_rate_toman_per_gram
    ```
  - **Rule 2 (Special Gemstone / Labor Items):** Assign explicit flag `pricing_mode = manual_locked` to prevent automated calculation from overwriting custom jewelry valuations.
  - **Rule 3 (Missing Weight Products):** Settle as `pricing_mode = legacy_mirror` or `pricing_mode = requires_review`.

---

## 4. Blocker 4 — CDN Thumbnail vs Original Resolution Verification

- **Technical Blocker:** Storefront image links use parameter suffixes (`?size=320x320&rs=fit`). Cannot verify from cloud IPs whether stripping query strings returns full-resolution original assets.
- **Mitigation Standard (Safest Image-Download Strategy):**
  1. Attempt HTTP `HEAD` request to base URL without parameters (`1785842823_4580729600.jpg`).
  2. Inspect response headers: if `200 OK` and `Content-Length > 100000` (100 KB), download base image.
  3. If base URL returns `404` or `403`, request explicitly upscaled parameter `?size=1600x1600&rs=fit`.

---
⚠️ **SECURITY NOTICE:**  
Never commit actual credentials, tokens, or API keys to this repository.  
All sensitive values MUST reside in `.env` (excluded via `.gitignore`).  
Use placeholder syntax `[VARIABLE_NAME]` in documentation.
---

# استراتژی دسترسی و ممیزی وب‌سرویس ادمین سایت قدیمی (`LEGACY-API-ACCESS-STRATEGY.md`)

This document defines the access architecture, Iranian domestic server requirements, and read-only audit workflow for the legacy store (`noghrehmashhad.ir`).

---

## 1. Admin Panel API Architecture (`مشخصات وب‌سرویس پنل مدیریت`)

- **API Nature:** The provided token (`Authorization: Bearer [LEGACY_API_TOKEN from .env]`) belongs to the **ADMIN PANEL API** of `noghrehmashhad.ir`, not a public customer-facing API.
- **Privilege Scope:** As an internal administrative endpoint, it exposes richer catalog data than public feeds, including full product metadata, exact stock integers (`1`, `0`), and technical specifications.
- **Read-Only Enforcement:** All automation scripts and audit tools MUST restrict HTTP requests strictly to **`GET`**, **`HEAD`**, and **`OPTIONS`**. Zero write operations (`POST`, `PUT`, `PATCH`, `DELETE`) are permitted against the legacy store.

---

## 2. Iranian Server Hosting Requirement (`الزام استقرار روی سرور ایران`)

- **Firewall Routing Constraint:** Domestic Iranian hosting infrastructure blocks or times out connection attempts originating from foreign/cloud IP ranges.
- **Mandatory Host Server:** To communicate with `noghrehmashhad.ir`'s Admin Panel API without timing out, all import agents and audit scripts MUST be executed from an Iranian hosting server (**`Iran Server Sonic 30`** Linux cloud host).

---

## 3. Phased Audit & Import Strategy (`مراحل ممیزی و تصمیم‌گیری واردات`)

```text
[ Deploy Audit Script on Sonic 30 (Iran IP) ]
                     │
                     v
[ Execute Read-Only GET Field Audit ] ──> Map available fields (price, weight, stock=1)
                     │
                     v
[ Determine Final Import Strategy ] ──> Direct REST API vs JSON/CSV Admin Export
```

1. **Step 1 — Read-Only Field Audit:** We will first run a read-only audit script from the domestic Iranian server (`Sonic 30`) to inspect available product fields, exact stock numbers, and image CDN resolutions.
2. **Step 2 — Import Strategy Selection:** Based on the audit findings, we will decide the optimal import method (Direct API synchronization vs Admin Panel JSON/CSV export) before deploying the live `Agent-LegacySync` importer.

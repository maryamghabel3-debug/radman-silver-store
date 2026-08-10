# RADMAN Hosting Architecture Decision

## Status
APPROVED TEMPORARY DECISION — CURRENT MONTH

## Date
2026-08-10 (Asia/Tehran)

---

## 1. Executive Summary & Approved Temporary Decision
This document records the official architectural evaluation and approved temporary hosting decision for the **RADMAN SILVER 925** (`radmansilver.ir`, `radman925.ir`) e-commerce platform and its Python 3.11+ async automation agent ecosystem.

- **Current Status:** `APPROVED TEMPORARY DECISION — CURRENT MONTH`
- **Official Temporary Decision (Current Month):**
  1. **Hosting vendor for current month:** MizbanFa Iran WooCommerce hosting (`میزبان‌فا`).
  2. **Selected plan:** Mars (`مارس`).
  3. **Scope:** RADMAN SILVER only.
  4. **RIDELIN Scope Limitation:** **RIDELIN is not deployed on this host during the current month.**
  5. **Architecture for current month:** Single-host temporary architecture — Storefront + agents on the same MizbanFa Mars plan.
  6. **Owner notification model:** SMS mandatory, Telegram optional, WooCommerce Admin fallback allowed.
  7. **Future separation:** Host separation / architecture revision will be re-evaluated next month after real usage data. **Architecture may be split next month after real usage and operational validation.**
  8. **Operational Philosophy:** This is a temporary operational decision for launch speed, not a permanent multi-year architecture lock.

### Confirmed Vendor Facts (MizbanFa Mars Plan)
- **Plan:** Mars (`مارس`)
- **Disk:** 60 GB NVMe
- **CPU:** 12 cores / 12 GHz equivalent
- **RAM:** 12 GB
- **Panel:** cPanel
- **Cache stack:** LSCache + WP Rocket + Object Cache + Redis Cache
- **Backups:** daily DB + weekly full
- **Datacenter:** Iran
- **Remote MySQL:** not available / not required
- **Python + Cron + WooCommerce REST API + Outbound HTTPS:** supported per vendor response
- **Money-back/test window:** up to 14 days after purchase

### Yellow Flag & Database Baseline Risk
- **Reported DB version from vendor support:** MariaDB 10.3.39
- **Technical Baseline Comparison:** This is below current preferred baseline (`MariaDB 10.6+`/`10.11+` or `MySQL 8.0+`).
- **Status:** `ACCEPTED TEMPORARILY FOR LAUNCH TESTING`
- **Action:** Verify actual version after purchase and request upgrade path if needed.

---

## 2. Candidate Architectures Evaluation History

### Candidate A: Managed WooCommerce hosting for storefront and agents on the same host
- **Status:** **`SELECTED TEMPORARILY FOR CURRENT MONTH (RADMAN ONLY)`**
- **Description:** A single managed WordPress/WooCommerce hosting environment located in Iran that hosts both the storefront (`radmansilver.ir`) and executes scheduled Python automation agents (`Agent-LegacySync`, `Agent-Pricing`, `Agent-OrderApproval`) directly on the same server.
- **Acceptance conditions:**
  - Python 3.11+
  - pip and venv
  - scheduled Python execution
  - sufficient Cron runtime
  - outbound HTTPS connectivity
  - reliable WooCommerce REST API
  - no requirement for static outbound IP, or an acceptable allowlisting solution
  - all resource limits documented

### Candidate B: Managed WooCommerce hosting plus separate Iran VPS for Python agents
- **Status:** **`DEFERRED / RE-EVALUATE NEXT MONTH`**
- **Description:** A hybrid architecture where the WordPress/WooCommerce storefront runs on a specialized managed WooCommerce host in Iran, while the Python automation agent ecosystem runs on an independent Linux Virtual Private Server (VPS) located in Iran.
- **Benefits:**
  - managed storefront
  - static Iran IP for agents if supplied
  - unrestricted Python runtime
  - independent scaling and isolation
- **Costs/risks:**
  - two services
  - VPS maintenance and monitoring
  - secure REST API communication required

### Candidate C: One Iran VPS for WordPress, WooCommerce, and Python agents
- **Status:** **`DEFERRED / RE-EVALUATE NEXT MONTH`**
- **Description:** A consolidated Virtual Private Server (VPS) hosted inside Iran where the DevOps team manages the full software stack (Linux OS, Nginx/LiteSpeed, MySQL/MariaDB, PHP 8.2/8.3, WordPress/WooCommerce, and Python 3.11+ agents) on a single server.
- **Benefits:**
  - full control
  - one server and static IP
  - Python/systemd/Cron flexibility
- **Costs/risks:**
  - full DevOps responsibility
  - OS hardening, patching, backups, database, web server, monitoring, malware protection, and incident response

---

## 3. Mandatory Acceptance Criteria
Every candidate hosting vendor and architecture must satisfy all of the following mandatory acceptance criteria before permanent purchase authorization is granted:
- Iran server location
- WooCommerce REST API POST/PUT support
- Authorization header preservation
- firewall/ModSecurity whitelist support
- outbound HTTPS to Telegram, Kavenegar, Zarinpal, GitHub, PyPI, legacy API, and WordPress/WooCommerce services
- static outbound IP or approved alternative if legacy allowlisting is required
- PHP 8.2/8.3 and required extensions
- supported MySQL/MariaDB version and utf8mb4
- Redis/Object Cache availability or documented alternative
- staging support
- SSL
- backup retention and restore procedure
- resource limits and scalability
- Python 3.11, pip, venv, Cron/systemd requirements based on architecture
- documented monthly and initial costs

---

## 4. Decision Rule
No permanent multi-year purchase and no permanent architecture approval until temporary launch testing and real usage data are evaluated. **Architecture may be split next month after real usage and operational validation.**

---

## 5. Hybrid Owner Notification Model (Phase 1-5)
- **Primary Mandatory Channel (`SMS via Kavenegar`):** SMS is the mandatory primary notification channel for alerting the brand owner of new orders (`On-Hold` / pending human review state) and sending customer order-status updates.
- **Secondary Optional Channel (`Telegram Bot`):** Telegram is an optional secondary convenience channel. It provides interactive approval buttons (`[تأیید موجودی و ارسال]` / `[عدم موجودی و لغو]`), but operations and launch are **never blocked** solely because Telegram is unavailable or unreachable.
- **Human-in-the-Loop (`HITL`) Fallback Approval Path:** Owner approval must remain possible even during international internet disruptions or Telegram connectivity loss. When Telegram is unavailable, the owner logs into the **WooCommerce Admin Panel** and manually changes the order status from `On-Hold` (`در انتظار بررسی`) to `Processing` (`در حال پردازش` / approved) or `Cancelled` (`لغو شده` / rejected). Automation agents observe this status change and trigger appropriate SMS customer notifications.
- **Impact on Architecture Viability:** Because Telegram is no longer a single point of operational failure, consolidated one-host architectures (Candidate A hosted temporarily on MizbanFa Mars) become significantly more viable and resilient.
- **Hosting Decision Status:** **`APPROVED TEMPORARY DECISION — CURRENT MONTH`** (MizbanFa Mars, RADMAN only, single-host temporary architecture, re-evaluate next month).

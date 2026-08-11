# RADMAN Hosting Architecture Decision

## Status
APPROVED FOR INITIAL ONE-MONTH PURCHASE AND STAGING TRIAL — NOT YET PURCHASED

## Date
2026-08-10 (Asia/Tehran)

---

## 1. Executive Summary & Approved Temporary Decision
This document records the official architectural evaluation and approved temporary hosting decision for the **RADMAN SILVER 925** (`radmansilver.ir`, `radman925.ir`) e-commerce platform and its Python 3.11+ async automation agent ecosystem.

- **Official Status:** `APPROVED FOR INITIAL ONE-MONTH PURCHASE AND STAGING TRIAL — NOT YET PURCHASED` (Approved to purchase, but not yet purchased).
- **Vendor and Plan:**
  - **Hosting Vendor:** MizbanFa Iran managed WooCommerce hosting (`میزبان‌فا`)
  - **Selected Plan:** Mars plan (`مارس`)
  - **Advertised Hardware Specs:** 60 GB NVMe disk, advertised 12 CPU cores / 12 GHz equivalent, advertised 12 GB RAM, cPanel.
- **Scope Limitation:**
  - **RADMAN SILVER only.**
  - **RIDELIN Scope Rule:** RIDELIN must not be installed or deployed on this host.
  - **Staging Requirement:** Staging must be provisioned before any production deployment.
  - **Production Gate:** Production deployment requires a separate reviewed approval after staging QA.
- **Architecture & Agent Co-Location:**
  - Storefront hosting on MizbanFa Mars is approved for the initial trial.
  - Co-locating Python agents on the same host is **`CONDITIONAL — pending post-purchase Python/Cron/outbound connectivity acceptance tests.`**
  - Python agents may be deployed on the same host only after real verification of Python, pip, venv, Cron runtime, outbound HTTPS, filesystem permissions, process limits, and Legacy API connectivity.
  - If those checks fail during the refund/test window, agents must be moved to a separate runner without blocking the WooCommerce storefront.
- **Review Deadline:**
  - **Review within 30 days after the actual provisioning date and before production launch, whichever occurs first. Provisioning date: TBD.**
  - All architecture evaluations and host separations obey this absolute decision/review rule.
- **Owner Notification Model:**
  - SMS via Kavenegar is mandatory.
  - Telegram is optional.
  - WooCommerce Admin is the fallback HITL approval path.
  - Telegram availability must not be a single point of failure.

### Confirmed Vendor Facts & Cache Policy (MizbanFa Mars Plan)
- **Plan:** Mars (`مارس`)
- **Disk:** 60 GB NVMe
- **CPU:** Advertised 12 cores / 12 GHz equivalent
- **RAM:** Advertised 12 GB
- **Panel:** cPanel
- **Vendor Advertised Cache Stack:** LSCache + WP Rocket + Object Cache + Redis Cache
- **Project-Approved Active Cache Configuration:** **`LiteSpeed Cache active, WP Rocket inactive, Redis conditional.`** (LiteSpeed Cache is the selected project page-cache plugin; LiteSpeed Cache and WP Rocket must not be activated simultaneously. Redis persistent object cache may only be activated after real connectivity verification. Distinguish vendor-provided advertised features from project-approved active configuration).
- **Backups:** daily DB + weekly full
- **Datacenter:** Iran
- **Remote MySQL:** not available / not required
- **Python + Cron + WooCommerce REST API + Outbound HTTPS:** supported per vendor response
- **Refund/Test Window:** Vendor support stated a 14-day test/refund window. Mark it: **`TO BE RECONFIRMED AGAINST THE PURCHASE TERMS AT CHECKOUT.`** Do not present it as an unconditional legal guarantee.

### Database Yellow Flag & Risk Assessment
- **Reported DB Version from Vendor Support:** MariaDB 10.3.39
- **Staging & Production Policy:** **`STAGING-ONLY TEMPORARY COMPATIBILITY WAIVER; production acceptance pending.`**
- **Requirements:** Actual database version must be detected after provisioning. MariaDB 10.3.x is accepted only for staging compatibility testing with an explicit waiver (`ALLOW_LEGACY_DB_FOR_STAGING=1`). It is not automatically approved as the permanent production database. Production Go/No-Go must remain blocked until database compatibility, security risk, and upgrade options are reviewed.

---

## 2. Candidate Architectures Evaluation History

### Candidate A: Managed WooCommerce hosting for storefront and agents on the same host
- **Status:** **`APPROVED FOR INITIAL ONE-MONTH PURCHASE AND STAGING TRIAL (RADMAN ONLY — STOREFRONT APPROVED; AGENTS CONDITIONAL)`**
- **Description:** A single managed WordPress/WooCommerce hosting environment located in Iran that hosts both the storefront (`radmansilver.ir`) and executes scheduled Python automation agents (`Agent-LegacySync`, `Agent-Pricing`, `Agent-OrderApproval`) directly on the same server. Co-locating Python agents on the same host is **`CONDITIONAL — pending post-purchase Python/Cron/outbound connectivity acceptance tests.`**
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
- **Status:** **`DEFERRED — Review within 30 days after the actual provisioning date and before production launch, whichever occurs first. Provisioning date: TBD.`**
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
- **Status:** **`DEFERRED — Review within 30 days after the actual provisioning date and before production launch, whichever occurs first. Provisioning date: TBD.`**
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
Every candidate hosting vendor and architecture must satisfy all of the following mandatory acceptance criteria before permanent production authorization is granted:
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
**Review within 30 days after the actual provisioning date and before production launch, whichever occurs first. Provisioning date: TBD.** Storefront hosting on MizbanFa Mars is approved for the initial trial. Co-locating Python agents on the same host is **`CONDITIONAL — pending post-purchase Python/Cron/outbound connectivity acceptance tests.`**

---

## 5. Hybrid Owner Notification Model (Phase 1-5)
- **Primary Mandatory Channel (`SMS via Kavenegar`):** SMS is the mandatory primary notification channel for alerting the brand owner of new orders (`On-Hold` / pending human review state) and sending customer order-status updates.
- **Secondary Optional Channel (`Telegram Bot`):** Telegram is an optional secondary convenience channel. It provides interactive approval buttons (`[تأیید موجودی و ارسال]` / `[عدم موجودی و لغو]`), but operations and launch are **never blocked** solely because Telegram is unavailable or unreachable.
- **Human-in-the-Loop (`HITL`) Fallback Approval Path:** Owner approval must remain possible even during international internet disruptions or Telegram connectivity loss. When Telegram is unavailable, the owner logs into the **WooCommerce Admin Panel** and manually changes the order status from `On-Hold` (`در انتظار بررسی`) to `Processing` (`در حال پردازش` / approved) or `Cancelled` (`لغو شده` / rejected). Automation agents observe this status change and trigger appropriate SMS customer notifications.
- **Impact on Architecture Viability:** Because Telegram is no longer a single point of operational failure, consolidated one-host architectures (Candidate A hosted on MizbanFa Mars) become significantly more viable and resilient.
- **Hosting Decision Status:** **`APPROVED FOR INITIAL ONE-MONTH PURCHASE AND STAGING TRIAL — NOT YET PURCHASED`** (MizbanFa Mars, RADMAN only, storefront approved, agent co-location conditional; review within 30 days after actual provisioning date and before production launch, whichever occurs first. Provisioning date: TBD).

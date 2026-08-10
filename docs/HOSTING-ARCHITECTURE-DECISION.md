# RADMAN Hosting Architecture Decision

## Status
PENDING TECHNICAL DUE DILIGENCE — NO PURCHASE APPROVED

## Date
2026-08-09 (Asia/Tehran)

---

## 1. Executive Summary & Current Status
This document records the official architectural evaluation for hosting the **RADMAN SILVER 925** (`radmansilver.ir`, `radman925.ir`) e-commerce platform and its Python 3.11+ async automation agent ecosystem.

- **Current Status:** `PENDING TECHNICAL DUE DILIGENCE — NO PURCHASE APPROVED`
- **Candidate Hosting Providers Under Evaluation:** **MizbanFa** (`میزبان‌فا`) and **ParsPack** (`پارس‌پک`).
- **Vendor Selection Rule:** Neither MizbanFa nor ParsPack is selected, approved, or preferred at this stage. Both are candidates awaiting technical due diligence responses to our formal support tickets.
- **Launch Priority Strategy:** RADMAN SILVER 925 has launch priority over RIDELIN. RIDELIN hosting procurement is deferred until RADMAN reaches stable staging/production operation.

---

## 2. Candidate Architectures Under Evaluation

### Candidate A: Managed WooCommerce hosting for storefront and agents on the same host
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
Every candidate hosting vendor and architecture must satisfy all of the following mandatory acceptance criteria before any purchase authorization is granted:
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
No purchase and no final architecture approval until the technical answers from both vendors are reviewed by the project manager and owner.

---

## 5. Hybrid Owner Notification Model (Phase 1-5)
- **Primary Mandatory Channel (`SMS via Kavenegar`):** SMS is the mandatory primary notification channel for alerting the brand owner of new orders (`On-Hold` / pending human review state) and sending customer order-status updates.
- **Secondary Optional Channel (`Telegram Bot`):** Telegram is an optional secondary convenience channel. It provides interactive approval buttons (`[تأیید موجودی و ارسال]` / `[عدم موجودی و لغو]`), but operations and launch are **never blocked** solely because Telegram is unavailable or unreachable.
- **Human-in-the-Loop (`HITL`) Fallback Approval Path:** Owner approval must remain possible even during international internet disruptions or Telegram connectivity loss. When Telegram is unavailable, the owner logs into the **WooCommerce Admin Panel** and manually changes the order status from `On-Hold` (`در انتظار بررسی`) to `Processing` (`در حال پردازش` / approved) or `Cancelled` (`لغو شده` / rejected). Automation agents observe this status change and trigger appropriate SMS customer notifications.
- **Impact on Architecture Viability:** Because Telegram is no longer a single point of operational failure, consolidated one-host architectures (Candidate A and Candidate C hosted in Iran) become significantly more viable and resilient.
- **Hosting Decision Status:** **`PENDING TECHNICAL DUE DILIGENCE — NO PURCHASE APPROVED`** (Status remains strictly unchanged).

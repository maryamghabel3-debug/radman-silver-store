# نقشه راه استقرار و راه‌اندازی رادمان سیلور (`docs/ROADMAP.md`)

> **Single Source of Truth Roadmap**
> *تمام تاریخ‌ها به‌وقت Asia/Tehran و فرمت ISO (YYYY-MM-DD) ثبت می‌شوند. ادعاهای مربوط به اتمام کار فقط در صورتی ثبت می‌شوند که evidence یا تست پاس شده باشند.*

---

## ۱. فازها و وضعیت فعلی

```text
[Phase 0: DONE] ──> [Phase 1: DONE] ──> [Phase 2: DONE (staging up)] ──> [Phase 3: IN PROGRESS] ──> [Phase 4: NEXT]
```

- **Phase 0** — Documentation & Brand Identity ✅
- **Phase 1** — Repository Setup & Architecture ✅
- **Phase 2** — Infrastructure & Hosting Setup (Staging live on MizbanFa Mars) ✅
- **Phase 3** — WordPress/WooCommerce Deployment & Safe Automation ⏭
- **Phase 4** — Agent Integration & E2E Testing ⏳
- **Phase 5** — Soft Launch & VIP Cohort ⏳
- **Phase 6** — Public Launch & Scale 🎯

---

## ۲. خلاصه پیشرفت هر فاز

### Phase 0/1 — DONE ✅
- هویت برند و پالت رنگی (`#0B0B0E` / `#FAF7F2`) در مخزن ثبت شده.
- ۱۱ صفحه استاتیک فارسی در `content/static-pages/` نهایی و بازبینی شده‌اند.
- قوانین 1:1 موجودی، چهار مد قیمت‌گذاری، و مدل HITL (SMS اصلی/Telegram اختیاری/WC Admin fallback) در `docs/PRICING-RULES.md` و `docs/BUSINESS-REQUIREMENTS.md` قفل شده‌اند.

### Phase 2 — DONE ✅ (staging live)
- میزبانی روی پلن MizbanFa Mars (RADMAN only) با موفقیت تأیید شد.
- استیجینگ `https://staging.radmansilver.ir` فعال است (WP 7.0.3، WC 11.0.1، PHP 8.2.31، MariaDB 11.4.12، LiteSpeed).
- `blog_public = 0` (noindex) برقرار است.
- گواهی Let's Encrypt فعال.
- رانر نصب اولیه در `scripts/install_wordpress_mars.sh` و اسناد evidence در `docs/STAGING-EXECUTION-EVIDENCE-2026-08-12.md` موجود است.

### Phase 3 — IN PROGRESS ⏭
**وضعیت واقعی (truthful status):**

- ✅ زبان فارسی `fa_IR` فعال.
- ✅ Blocksy Child Theme (`blocksy-child v1.0.0`) روی استیجینگ فعال است (فایل‌های پالت و enqueue در `theme/blocksy-child/`).
- ⚠️ صفحات استاتیک با شناسه‌های `21–31` به‌صورت **Draft placeholder** وجود دارند. متن کامل `content/static-pages/` هنوز از طریق رانر اعمال نشده و **PENDING** است.
- ⚠️ پاکسازی صفحات تکراری: ID `2` و ID `3` تأیید شده حذف شده‌اند. وضعیت ID `10` (refund_returns) نیازمند بررسی میزبان است.
- ✅ **Currency Gate A** (ذخیره/نمایش تومان در محصول و سبد خرید) پاس شده است (`IRT`، ذخیره ۱۲۳۴۵۶ = ۱۲۳۴۵۶، نمایش 123,456 Toman).
- ⏳ **Currency Gate B** (checkout/order/email/Schema/payment callback) **PENDING** و قبل از فعال‌سازی پرداخت یا راه‌اندازی پروداکشن باید پاس شود.
- ✅ رانرهای ایمن و idempotent استیجینگ در مخزن آماده شده‌اند:
  - `scripts/render_static_pages.py` (رندر امن Markdown → HTML، stdlib only، بدون انتشار یادداشت‌های داخلی).
  - `scripts/radman_branding_and_content_import.sh` (guards استیجینگ، `flock`، بک‌آپ DB/child-theme، upsert by slug، عدم publish خودکار).
  - `scripts/radman_stage_apply.sh` (رانر تک‌دستور مالک، پیش‌فرض `--plan`).
- ⏳ تنظیمات هاردنینگ باقی‌مانده (Wordfence, LiteSpeed Cache, UpdraftPlus cloud, RankMath wizard, Redis).
- ⏳ راه‌اندازی Host Operations Agent Access (مراجعه شود به [HOST-OPS-AGENT-ACCESS.md](HOST-OPS-AGENT-ACCESS.md)).

### Phase 4 — Agent Integration & Testing (NEXT)
- استقرار `Agent-LegacySync` (مشروط به تأیید اتصال و Python/Cron).
- ایمپورت دسته اول محصولات به‌صورت Draft (۵۰ محصول).
- استقرار `Agent-Pricing` با ورود نرخ روزانه از طریق تلگرام.
- استقرار `Agent-OrderApproval` (HITL).
- تست کامل E2E سندباکس با درگاه و پیامک.

### Phase 5/6 — Soft Launch / Public Launch (PENDING)
- VIP cohort soft launch.
- QA، سئو و راه‌اندازی نهایی (تأیید صریح مأموریت cutover).

---

## ۳. قفل‌های غیرقابل مصالحه (Go/No-Go قبل از پروداکشن)

- Currency Gate B (پرداخت/چک‌اوت/ایمیل/Schema) باید پاس شده باشد.
- صفحات استاتیک از Draft به Published (با بررسی نهایی مالک در مورد placeholders) در یک مأموریت مجزا درآیند.
- بک‌آپ، Wordfence، LiteSpeed Cache، و Redis پیکربندی شده باشند.
- پروداکشن (`public_html`) فقط پس از مأموریت صریح cutover لمس خواهد شد.
- **هیچ رمز، کلید یا توکنی در گیت ذخیره نمی‌شود.**

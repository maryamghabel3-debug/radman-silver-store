# راهنمای به‌روزرسانی پوسته فرزند و محتوای استاتیک استیجینگ (Runbook)
# (`RADMAN-BRANDING-CONTENT-IMPORT-RUNBOOK.md`)

> **وضعیت سند:** READY — زیرساخت رانر تأیید شده. برای اجرای نهایی روی میزبان از رانر واحد `scripts/build_staging_storefront.sh` استفاده شود (رجوع به [FINAL-STAGING-STOREFRONT-BATCH-RUNBOOK.md](FINAL-STAGING-STOREFRONT-BATCH-RUNBOOK.md)).
> **تاریخ:** 2026-08-18 (Asia/Tehran)
> **محدوده:** RADMAN ONLY — `staging.radmansilver.ir` — پروداکشن (`public_html`) و RIDELIN خارج از محدوده‌اند.

---

## ۱. هدف و وضعیت فعلی (Truthful Status)

این سند، روند ایمن و **idempotent** استقرار پوسته فرزند Blocksy و محتوای استاتیک فارسی را در محیط استیجینگ توصیف می‌کند.

**وضعیت واقعی روی میزبان در لحظهٔ نگارش این سند:**

- زبان فارسی `fa_IR` فعال است.
- پوستهٔ فرزند `blocksy-child v1.0.0` با پالت `#0B0B0E` (زمینه) / `#FAF7F2` (متن) فعال است.
- ۱۱ صفحه با شناسه‌های `21–31` به‌صورت **Draft placeholder** (متن موقت bootstrap) وجود دارند.
- **محتوای کامل ۱۱ صفحه در `content/static-pages/` آماده و placeholder-free است (در ریپو).**
- **محتوا هنوز روی میزبان مستقر نشده و میزبان-استقرار PENDING است (نیازمند مأموریت مصوب میزبانی).**
- **انتشار عمومی (Publish) برای همهٔ ۱۱ صفحه BLOCKED است تا تأیید نهایی مالک و (در صورت نیاز) بازبینی حقوقی.** رجوع شود به [STATIC-CONTENT-APPROVAL-REGISTRY.md](STATIC-CONTENT-APPROVAL-REGISTRY.md).
- صفحه اصلی شناسه `18` منتشر و front-page است (توسط رانر تغییر داده نمی‌شود).
- پاکسازی صفحات تکراری:
  - تأییدشده: ID `2` و ID `3`
  - **تأیید نشده / نیازمند بررسی میزبان:** ID `10` (refund_returns) — *"Page ID 10 cleanup status requires host verification."*
- واحد پول:
  - **Gate A (ذخیره/نمایش محصول/سبد خرید به تومان): PASS** (گزینهٔ پولی `IRT`، `123456 → 123,456 Toman`).
  - **Gate B (پرداخت/چک‌اوت/ایمیل/Schema/callback درگاه): PENDING** — باید قبل از فعال‌سازی پرداخت یا راه‌اندازی پروداکشن پاس شود.
- **عبارت رسمی:**
  > *Toman direct input is verified for WooCommerce database storage, product display, and cart display. Payment, checkout, order, email, and Schema currency behavior remain PENDING and must pass before payment activation or production launch.*

---

## ۲. تفکیک ابزارها

| ابزار | نقش | اجرای پیش‌فرض |
|:------|:----|:--------------|
| `scripts/render_static_pages.py` | رندر ایمن Markdown استاتیک به HTML (stdlib-only، بدون انتشار بخش‌های داخلی)، با به‌رسمیت شناختن لینک‌های مارک‌داون فارسی | خواندن از `content/static-pages/`، نوشتن در build dir |
| `scripts/radman_branding_and_content_import.sh` | رانر پایین‌لایه با guards سخت‌گیرانه، بک‌آپ، `flock`، upsert by slug، **بدون process substitution** (سازگار با jailshell/cPanel)؛ build dir با `mktemp -d` ساخته می‌شود | `--plan` (read-only) |
| `scripts/radman_stage_apply.sh` | رانر تک‌دستور مالک که به رانر پایین‌لایه تفویض می‌کند | `--plan` (read-only) |
| `scripts/check_no_placeholders.py` | gate پس از رندر: اگر `[…]` (بایدد سه کاراکتر: براکت باز + U+2026 بیضی + براکت بسته = نشانهٔ owner-fill-later) یا کلاس CSS `radman-placeholder` در HTML خروجی باقی‌مانده باشد، با کد خطای تمیز خاتمه می‌دهد. بیضی عادی/مستقل `…` در نثر فارسی **مجاز** است و fail نمی‌کند | در هر اجرا (حتی plan) |
| `scripts/test_plan_runner.sh` | self-test محلی: `--plan` را روی محتوای واقعی اجرا می‌کند، جدول DEPLOY PLAN و عدم وجود placeholder را تست می‌کند | محلی، بدون میزبان |

همه ابزارها **به‌صورت پیش‌فرض در حالت plan** اجرا می‌شوند. اعمال تغییر واقعی روی استیجینگ فقط در صورتی رخ می‌دهد که `--apply-staging` و `CONFIRM_STAGING_APPLY=YES` همزمان با سایر شرایط محیطی ارائه شوند.

### نکته رفع باگ جیل‌شل (cPanel/CloudLinux)
نسخه اولیه رانر از process substitution (الگوی `done < <(cmd)`) استفاده می‌کرد که در jailshell برخی سرویس‌های میزبانی به‌علت محدودبودن `/dev/fd` با خطای زیر می‌شکست:

```
line 248: /dev/fd/62: No such file or directory
```

این باگ در نسخه فعلی رفع شده است:
- حلقه‌های `while read` با فراخوانی مستقیم تابع جایگزین شده‌اند (نه `< <(page_entry)`).
- build dir در حالت plan با `mktemp -d` زیر `TMPDIR` ساخته می‌شود (در دسترس حتی در جیل).
- gate جدید `check_no_placeholders.py` اطمینان می‌دهد که اگر محتوای ناقص/جای‌دار (placeholder) رندر شده باشد، plan با خطای واضح متوقف می‌شود.
- self-test محلی `bash scripts/test_plan_runner.sh` روی لپ‌تاپ/سرور بدون دسترسی به وردپرس اجرا می‌شود.

---

## ۳. پیش‌نیازهای محیطی (اعمال روی میزبان)

متغیرهای محیطی زیر باید در shell اطراف تنظیم شوند (هیچ‌کدام داخل اسکریپت hardcode نمی‌شوند):

```bash
export APP_ENV=staging
export WP_URL=https://staging.radmansilver.ir
export WP_PATH=/home/<CPANEL_USER>/staging.radmansilver.ir
export RADMAN_REPO_ROOT=/home/<CPANEL_USER>/radman-deploy/repo
export RADMAN_PRIVATE_DIR=/home/<CPANEL_USER>/.config/radman
# برای apply:
export CONFIRM_STAGING_APPLY=YES
```

### Guards سخت‌گیرانه قبل از اعمال
- `APP_ENV == staging`
- `WP_URL == https://staging.radmansilver.ir`
- `WP_PATH` شامل `public_html` نباشد (پروداکشن ممنوع)
- `WP_PATH/wp-settings.php` موجود باشد (وجود وردپرس)
- `blog_public == 0` (noindex استیجینگ)
- `RADMAN_REPO_ROOT/content/static-pages/` و `theme/blocksy-child/` موجود باشند
- `CONFIRM_STAGING_APPLY == YES` (فقط در apply)
- `flock` روی `RADMAN_PRIVATE_DIR/radman-stage-deploy.lock` گرفته شود (جلوگیری از اجرای هم‌زمان)

---

## ۴. اجرای Plan (Dry-run) — توصیه اول

```bash
APP_ENV=staging \
WP_PATH=/home/<CPANEL_USER>/staging.radmansilver.ir \
WP_URL=https://staging.radmansilver.ir \
RADMAN_REPO_ROOT=/home/<CPANEL_USER>/radman-deploy/repo \
RADMAN_PRIVATE_DIR=/home/<CPANEL_USER>/.config/radman \
bash scripts/radman_stage_apply.sh --plan
```

خروجی plan شامل جدولی از ۱۱ اسلاگ رسمی خواهد بود:
- `slug`, `title`, `existing ID` (یا `will-create`)، `action` (UPDATE/CREATE)، `status=draft`، `rendered bytes`.

---

## ۵. اجرای Apply (اعمال روی استیجینگ پس از تأیید ریویو)

```bash
APP_ENV=staging \
CONFIRM_STAGING_APPLY=YES \
WP_PATH=/home/<CPANEL_USER>/staging.radmansilver.ir \
WP_URL=https://staging.radmansilver.ir \
RADMAN_REPO_ROOT=/home/<CPANEL_USER>/radman-deploy/repo \
RADMAN_PRIVATE_DIR=/home/<CPANEL_USER>/.config/radman \
bash scripts/radman_stage_apply.sh --apply-staging
```

### مراحل apply در رانر پایین‌لایه
1. بررسی staging guards (بالا).
2. گرفتن `flock`.
3. رندر HTML از Markdown ها در پوشهٔ build.
4. ساخت بک‌آپ:
   - DB dump در `RADMAN_PRIVATE_DIR/backups/wordpress-db-<TS>.sql` با `chmod 600`
   - آرشیو child theme موجود (اگر وجود داشته باشد) در `RADMAN_PRIVATE_DIR/backups/blocksy-child-<TS>.tar.gz`
5. کپی ایمن سه فایل child theme (`style.css`, `functions.php`, `README.md`) به `wp-content/themes/blocksy-child/`.
6. فعال‌سازی `blocksy-child` و تأیید `wp theme list --status=active`.
7. برای هر یک از اسلاگ‌های رسمی:
   - جستجو بر اساس `post_name` (slug).
   - اگر یافت شد: `wp post update <ID>` (همواره `--post_status=draft`).
   - اگر یافت نشد: `wp post create` با `--post_status=draft`.
8. خروجی خلاصه شامل: تعداد UPDATE/CREATE، مسیر بک‌آپ، تأیید عدم دست‌زدن به پروداکشن و عدم publish صفحات.

---

## ۶. Idempotency

رانر **هیچ‌گاه** به‌صورت غیرشرطی `wp post create` صدا نمی‌زند. همهٔ صفحات از طریق اسلاگ جستجو می‌شوند و یا به‌روزرسانی می‌گردند یا در صورت نبودن، ساخته می‌شوند. در نتیجه اجرای مکرر آن منجر به ایجاد صفحه تکراری نخواهد شد.

همچنین:
- صفحات **Draft** باقی می‌مانند و به‌صورت خودکار منتشر نمی‌شوند.
- محصولات، سفارشات، کاربران، منوها، پلاگین‌های پرداخت و پیامک تغییر داده نمی‌شوند.
- صفحه اصلی (front page) تغییر داده نمی‌شود.

---

## ۷. Renderer Markdown

`render_static_pages.py` فقط بخش `## Content` را استخراج می‌کند و قبل از سرفصل‌های داخلی زیر متوقف می‌شود:
- `## SEO`
- `## Page Purpose`
- `## Trust Notes` / `## Owner Fill Later`
- `## Internal Link Suggestions`

Markdown پشتیبانی‌شده محدود به: headings (h2–h4)، پاراگراف، لیست‌های ul/ol، **bold** و `[لینک](url)` با sanitize امن (فقط http/https/mailto/path-absolute). ترتیب پردازش در رندرر: ابتدا لینک‌های Markdown و **bold** با جای‌گذارهای امن (token stash) محافظت می‌شوند و بعد از HTML-escape، placeholder های `[متنی]` (که لینک Markdown نیستند — به لطف negative lookahead برای `(`) به عنصر `<span class="radman-placeholder">` تبدیل می‌شوند تا قابل ردیابی باشند. بیضی عادی فارسی `…` در متن به‌هیچ‌وجه placeholder محسوب نمی‌شود و همان‌طور که هست از رندر عبور می‌کند.

### اجرای Self-Test (بدون نیاز به میزبان/وردپرس)
```bash
bash scripts/test_plan_runner.sh
```
خروجی باید با `[PASS] plan runner self-test succeeded.` خاتمه یابد و بخش‌های زیر را شامل شود:
- اجرای کامل `--plan` در برابر ۱۱ صفحه واقعی ریپو.
- تست رگرسیون B1: بیضی عادی `…` → PASS.
- تست رگرسیون B2: نشانهٔ `[…]` (براکت+بیضی) → FAIL.
- تست رگرسیون B3: کلاس `radman-placeholder` → FAIL.
- تست رگرسیون B4: لینک‌های Markdown فارسی و بیضی در متن placeholder تولید نمی‌کنند.

---

## ۸. Child Theme (Source of Truth)

پوشهٔ مرجع در مخزن: `theme/blocksy-child/`
- `style.css`: هدر پوسته + متغیرهای رنگی `:root` + قوانین پایه برای پس‌زمینه/متن/سرفصل‌ها.
- `functions.php`: enqueue تنها stylesheet فرزند با وابستگی به handle والد `blocksy-style` در صورت ثبت. از double-loading استایل والد جلوگیری می‌شود.
- `README.md`: این فایل راهنما + فهرست ممنوعات (Google Fonts، tracking، credentials، رنگ‌های تأیید نشده).

ادعای «هر دو stylesheet والد و فرزند با هم enqueue می‌شوند» در مستندی ثبت نمی‌شود؛ بلکه رفتار دقیق `functions.php` (وابستگی به handle والد) مستند شده است و تأیید فعال‌سازی پوسته از طریق `wp theme list` توسط رانر انجام می‌شود.

---

## ۹. دسترسی عامل (Host Ops)

در سند [HOST-OPS-AGENT-ACCESS.md](HOST-OPS-AGENT-ACCESS.md) توضیح داده شده است. در محیط اجرایی فعلی (sandbox)، نگهداری دائمی کلید خصوصی SSH در دسترس نیست: **`PERSISTENT SSH PRIVATE-KEY STORAGE NOT AVAILABLE`**، بنابراین تا استقرار runtime دائمی روی میزبان، Mode B (کاربر اتوماسیون وردپرس + Application Password + رانر تک‌دستور) مسیر پیش‌فرض است.

---

## ۱۰. ممنوعات صریح

- ❌ اعمال روی پروداکشن (`public_html`)
- ❌ publish خودکار صفحات استاتیک
- ❌ فعال‌سازی پرداخت یا پیامک
- ❌ حذف/تغییر محصولات، سفارشات یا کاربران
- ❌ قرار دادن رمزها/توکن‌ها در گیت یا در خروجی لاگ
- ❌ استفاده از فونت‌های خارجی (Google Fonts)
- ❌ کدهای ردیابی/تبلیغاتی در پوسته

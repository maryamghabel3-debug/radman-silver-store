# اجرای نهایی پایه فروشگاه استیجینگ با یک دستور
# (`FINAL-STAGING-STOREFRONT-BATCH-RUNBOOK.md`)

> **مخاطب این سند:** مالک فروشگاه (کاربر cPanel) که از داخل ایران به SSH میزبان MizbanFa دسترسی دارد.
> **هدف:** با اجرای **یک بلوک دستور**، پایه فروشگاه رادمان سیلور ۹۲۵ روی استیجینگ مستقر شود.
> **وضعیت:** READY FOR OWNER EXECUTION
> **تاریخ:** 2026-08-18 (Asia/Tehran)

---

## ۱. پیش از اجرا: چه چیزی تغییر خواهد کرد؟

اجرای نهایی (با `--apply-staging`) به‌صورت **idempotent** (اجرای مجدد امن) و **فقط روی استیجینگ** این کارها را انجام می‌دهد:

1. **بک‌آپ کامل** از دیتابیس و پوشهٔ child theme در `~/.config/radman/backups/` (با `chmod 600`).
2. **همگام‌سازی پوسته فرزند Blocksy** (فایل‌های `style.css`, `functions.php`, `README.md` از ریپو).
3. **Upsert ۱۱ صفحه استاتیک** (درباره ما، تماس، سؤالات متداول، روش‌های ارسال، بازگشت کالا، حریم خصوصی، قوانین، راهنمای سایز، نگهداری نقره، اصالت نقره ۹۲۵، سنگ‌ها) به‌صورت **Draft** (هرگز منتشر نمی‌شوند).
4. **به‌روزرسانی صفحه اصلی (ID 18)** با قالب Gutenberg تمیز (هیرو، نوار اعتماد، دسته‌بندی‌ها، معرفی برند، اعلان «نسخه آزمایشی»).
5. **ایجاد/به‌روزرسانی ۳ دسته‌بندی محصول** به‌صورت idempotent (بر اساس slug):
   - `rings` → انگشتر
   - `necklaces` → گردنبند
   - `bracelets` → دستبند
6. **ایجاد/به‌روزرسانی منوی اصلی «منوی اصلی رادمان»** با لینک‌های مصوب (خانه، فروشگاه، انگشتر، گردنبند، دستبند، حساب کاربری، سبد خرید) — بدون ارجاع به صفحات Draft.
7. **گزارش وضعیت پایه** (خواندنی، بدون تغییر):
   - Currency = IRT / 0 decimals (انتظار).
   - Shipping methods و Payment gateways: فقط خوانده و گزارش می‌شوند — **هیچ‌کدام فعال یا پیکربندی نمی‌شوند**.
   - LiteSpeed: فقط گزارش وضعیت.

### ✅ مواردی که عمداً تغییر نخواهند کرد (LOCKED)
- ❌ **پروداکشن (`public_html`)** اصلاً لمس نمی‌شود (در کد ممنوع شده است).
- ❌ **هیچ‌یک از ۱۱ صفحه استاتیک منتشر نمی‌شوند** — همه Draft می‌مانند تا تأیید نهایی مالک/حقوقی.
- ❌ **درگاه پرداخت فعال/پیکربندی نمی‌شود** — Gateland فقط نصب شده باقی می‌ماند.
- ❌ **SMS (Kavenegar) پیکربندی یا ارسال نمی‌شود**.
- ❌ **Redis Object Cache فعال نمی‌شود**.
- ❌ **Google Fonts / کد رهگیری / آنالیتیکس** اضافه نمی‌شود.
- ❌ **محصولات، سفارشات، کاربران** تغییر یا حذف نمی‌شوند.
- ❌ **blog_public = 0 (noindex)** استیجینگ تغییر نمی‌کند.

---

## ۲. آماده‌سازی روی سیستم خودتان (یک بار)

### مرحله ۰ (روی لپ‌تاپ): دریافت آخرین نسخه ریپو
1. به صفحه زیر بروید:
   <https://github.com/maryamghabel3-debug/radman-silver-store>
2. دکمه سبز **Code** → **Download ZIP** را بزنید (فایل `radman-silver-store-main.zip` دانلود می‌شود).
3. ZIP را از طریق **cPanel File Manager** یا `scp` به مسیر زیر روی هاست آپلود کنید:
   `/home/radmansi/radman-deploy/`
4. روی SSH هاست:
   ```bash
   cd /home/radmansi/radman-deploy
   # اگر نسخهٔ قبلی repo وجود داشت، آن را به یک پوشه با تاریخ تغییر نام دهید (نه حذف)
   [ -d repo ] && mv repo repo.backup.$(date +%Y%m%d-%H%M%S)
   # فایل ZIP تازه را اکستراکت کنید
   unzip -q radman-silver-store-main.zip
   mv radman-silver-store-main repo
   ls -la repo/scripts/build_staging_storefront.sh
   ```
   آخرین دستور باید فایل رانر را نشان دهد (وجود داشته باشد).

### مرحله ۰.۵: اطمینان از فایل‌های لازم
این فایل‌ها باید در ریپو وجود داشته باشند:
```bash
ls repo/scripts/build_staging_storefront.sh
ls repo/scripts/radman_stage_apply.sh
ls repo/scripts/check_no_placeholders.py
ls repo/scripts/render_static_pages.py
ls repo/templates/home-page-gutenberg.html
ls repo/theme/blocksy-child/
ls repo/content/static-pages/
ls repo/docs/STATIC-CONTENT-APPROVAL-REGISTRY.md
```

---

## ۳. اجرای Dry-Run (اجباری قبل از apply)

ابتدا **حتماً یک بار** در حالت `--plan` اجرا کنید تا خروجی را مرور کنید (هیچ تغییری روی سایت ایجاد نمی‌کند):

```bash
export PATH="$HOME/bin:$PATH"

APP_ENV=staging \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
WP_URL=https://staging.radmansilver.ir \
RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
bash /home/radmansi/radman-deploy/repo/scripts/build_staging_storefront.sh --plan
```

### خروجی مورد انتظار:
- یک جدول `DEPLOY PLAN` با ۱۱ اسلاگ (`about-us` تا `gemstones`).
- ستون `placeholders` برای همه `no` باشد.
- بخش homepage: `Target: page ID 18 (slug=home)`.
- بخش categories: ۳ سطر `rings / necklaces / bracelets` با `action = CREATE` (اگر قبلاً ایجاد نشده باشند) یا `EXISTING`.
- بخش menu: `Would CREATE menu 'منوی اصلی رادمان'`.
- بخش WooCommerce/LiteSpeed baseline: گزارش خواندنی.
- خط پایانی: `Dry-run (--plan) complete. No WordPress content was modified.`

اگر خطایی به‌صورت `[ERROR]` ظاهر شد، **متوقف شوید** و خروجی را برای بررسی بازگردید.

---

## ۴. اجرای نهایی (Apply) — فقط پس از تأیید dry-run

وقتی خروجی `--plan` بی‌خطی بود:

```bash
export PATH="$HOME/bin:$PATH"

APP_ENV=staging \
CONFIRM_STAGING_APPLY=YES \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
WP_URL=https://staging.radmansilver.ir \
RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
bash /home/radmansi/radman-deploy/repo/scripts/build_staging_storefront.sh --apply-staging
```

### خروجی موفقیت‌آمیز باید شامل این موارد باشد:
- `[APPLY] DB backup → /home/radmansi/.config/radman/backups/pre-storefront-<TS>.sql`
- `[APPLY] Active theme: blocksy-child`
- `[APPLY] UPDATE slug=... ID=... status=draft` برای ۱۱ صفحه
- `[APPLY] Page 18 updated with Gutenberg template.`
- `[APPLY] Hero H1 verified in rendered homepage content.`
- `Categories: created=... existing=...`
- `Menu items: added=... reconciled=...`
- خط پایانی:
  ```
  STOREFRONT FOUNDATION APPLIED TO STAGING (https://staging.radmansilver.ir)
  PRODUCTION (public_html) WAS NOT TOUCHED.
  Payments / SMS / Redis / analytics / indexing WERE NOT ENABLED.
  ```

---

## ۵. بررسی دستی پس از اجرا

1. به <https://staging.radmansilver.ir> بروید (از IP داخل ایران یا VPN).
   - صفحه اصلی باید هیروی تیره «نقره ۹۲۵؛ اصالت در جزئیات» + ۳ کارت دسته‌بندی + متن معرفی + نوار زرد «نسخه آزمایشی» را نشان دهد.
2. به <https://staging.radmansilver.ir/wp-admin> بروید:
   - **Pages → All Pages**: باید ۱۱ صفحه Draft با اسلاگ‌های درست دیده شوند.
   - **Posts**: پست پیش‌فرض «Hello World» اگر هنوز هست، دستی حذف شود (خود اسکریپت حذف نمی‌کند تا از حذف اتفاقی محتوا جلوگیری شود).
   - **Products → Categories**: سه دسته انگشتر / گردنبند / دستبند باید موجود باشند.
   - **Appearance → Menus**: منوی «منوی اصلی رادمان» باید موجود باشد؛ اگر به‌صورت خودکار به لوکیشن primary اختصاص داده نشده بود، از بخش Manage Locations آن را به موقعیت هدر اختصاص دهید.
3. **Settings → Reading** بررسی کنید:
   - `Your homepage displays` روی `A static page` و `Homepage = Home` باشد.
4. **WooCommerce → Settings** بررسی کنید:
   - Currency = Toman (IRT) و تعداد اعشار = 0 (تغییری در این مأموریت ایجاد نشده، صرفاً گزارش می‌شود).

---

## ۶. در صورت بروز خطا یا نیاز به بازگرداندن (Rollback)

- **بک‌آپ‌ها اینجا هستند** (با `chmod 600`):
  ```bash
  ls -la /home/radmansi/.config/radman/backups/
  ```
  - `pre-storefront-<TS>.sql` — دامپ کامل دیتابیس پیش از اجرا.
  - `blocksy-child-pre-storefront-<TS>.tar.gz` — آرشیو پوشه child theme پیش از اجرا.
  - `home-page-18-<TS>.html` — محتوای قبلی صفحه اصلی.
- **بازگردانی سریع دیتابیس** (فقط اگر خواسته باشید):
  ```bash
  wp db import /home/radmansi/.config/radman/backups/pre-storefront-<TS>.sql --path=/home/radmansi/staging.radmansilver.ir
  ```
- **بازگردانی child theme**:
  ```bash
  cd /home/radmansi/staging.radmansilver.ir/wp-content/themes
  mv blocksy-child blocksy-child.broken
  tar -xzf /home/radmansi/.config/radman/backups/blocksy-child-pre-storefront-<TS>.tar.gz
  ```
- پوشهٔ قدیمی ریپو نیز با نام `repo.backup.<تاریخ>` در کنار `repo` موجود است (مرحله ۰).

---

## ۷. چه چیزهایی هنوز در انتظار تأیید مالک هستند؟

پس از اجرای موفق این دستور، فروشگاه استیجینگ از نظر ساختاری آماده است اما **انتشار عمومی (Publish) مسدود است** تا این موارد تکمیل شوند:

- ⏳ **تأیید عملیاتی مالک** برای محتوای ۱۱ صفحه (اطلاعات تماس/ساعت، روش‌های ارسال، بسته‌بندی، SLA، سنگ‌های موجود و ...). ر.ک. [STATIC-CONTENT-APPROVAL-REGISTRY.md](STATIC-CONTENT-APPROVAL-REGISTRY.md).
- ⏳ **بازبینی حقوقی** برای صفحات `returns`, `privacy-policy-radman`, `terms`.
- ⏳ **پیکربندی درگاه پرداخت** (Currency Gate B) و تنظیم Gateland/Zarinpal — در مأموریت آتی و فقط روی استیجینگ.
- ⏳ **پیکربندی SMS (Kavenegar)** — نصب و تست انجام نشده.
- ⏳ **وارد کردن محصولات واقعی** و فعال‌سازی عامل قیمت‌گذاری و HITL تأیید سفارش.
- ⏳ **بهینه‌سازی LiteSpeed** (CSS/JS combine, UCSS, Guest Opti, QUIC.cloud) در مأموریت جداگانه.

---

## ۸. زمان‌بندی تقریبی و نیازمندی‌ها

- آپلود ZIP: ~۱–۲ دقیقه (حجم فایل ناچیز، زیر ۵ مگابایت).
- اکسترکت و آماده‌سازی: <۱۰ ثانیه.
- `--plan`: ~۵–۱۰ ثانیه (فقط رندر محلی + بررسی‌ها).
- `--apply-staging`: ~۱۵–۴۰ ثانیه (شامل بک‌آپ DB + upsert صفحه‌ها + ساخت دسته/منو).
- نیازمندی‌ها: دسترسی SSH به cPanel MizbanFa با کاربر `radmansi`، اجرای `wp` بدون خطا، فضای خالی حداقل ۱۰۰ مگابایت در `~/.config/radman/backups/`.

---

## ۹. خلاصه دستورات (کپی-پیست آماده)

### گام ۱: Dry-Run
```bash
export PATH="$HOME/bin:$PATH"
APP_ENV=staging \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
WP_URL=https://staging.radmansilver.ir \
RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
bash /home/radmansi/radman-deploy/repo/scripts/build_staging_storefront.sh --plan
```

### گام ۲: Apply (فقط پس از تأیید خروجی dry-run)
```bash
export PATH="$HOME/bin:$PATH"
APP_ENV=staging \
CONFIRM_STAGING_APPLY=YES \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
WP_URL=https://staging.radmansilver.ir \
RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
bash /home/radmansi/radman-deploy/repo/scripts/build_staging_storefront.sh --apply-staging
```

---

> ⚠️ **یادآوری مهم**: هیچ‌گاه پروداکشن (`public_html`) با این اسکریپت لمس نمی‌شود. اگر نیاز به استقرار روی پروداکشن باشد، مأموریت جداگانه‌ای با مجوز صریح مالک لازم است.

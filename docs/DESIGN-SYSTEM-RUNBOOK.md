# RADMAN SILVER 925 — Professional Design System Runbook

> Runbook for PR-18: Luxury storefront visual design system.
> **Staging only.** Do NOT run on production.

---

## 1. خلاصه تغییرات (فارسی)

این ران‌بوک نسخهٔ بصری فروشگاه آزمایشی را از حالت ساده و پایه به یک استورفرانت لوکس و حرفه‌ای ارتقا می‌دهد:

- لوگوی رسمی فارسی رادمان (T0 minimal — black-transparent) در هدر نصب می‌شود.
- فونت‌های **Estedad** (برای تیترها) و **Vazirmatn** (برای متن) به‌صورت **کاملاً محلی** (WOFF2، بدون Google Fonts و بدون اتصال به منابع خارجی) روی سایت قرار می‌گیرند.
- سیستم طراحی یکپارچه شامل تایپوگرافی مقیاس‌پذیر، رنگ‌بندی طلایی/مشکی/عاجی، دکمه‌های لوکس، کارت‌های محصول حرفه‌ای، هدر، فوتر، نوار اعتماد، فرم‌ها، صفحه‌بندی، بردکرامب و تایب‌شده و تایپوگرافی مخصوص صفحات ایستا (قوانین، دربارهٔ ما، راهنماها).
- قالب صفحهٔ اصلی (Gutenberg) بهبود یافته: هیروی قوی‌تر، trust strip ظریف‌تر، کارت‌های دسته‌بندی با CTA کامل، بخش CTA فروشگاه و داستان برند.
- فاوایکون (monogram) به‌عنوان `site_icon` تنظیم می‌شود.
- همهٔ تغییرات staging-only هستند؛ `blog_public=0` (noindex) باقی می‌ماند.
- هیچ سرویس پرداخت، پیامک، ردیس، آنالیتیکس یا بهینه‌سازی‌های تهاجمی LiteSpeed (CSS/JS combine, UCSS, Delayed JS, Guest Mode, QUIC.cloud) فعال نمی‌شوند.

---

## 2. پیش‌نیازها

1. دسترسی SSH به اکانت cPanel میزبان (MizbanFa) از **داخل ایران**.
2. بچ استورفرانت قبلاً با موفقیت از `scripts/build_staging_storefront.sh --apply-staging` روی استیجینگ اجرا شده باشد (صفحهٔ اصلی ID=18 و منوی اصلی موجود باشند).
3. آخرین نسخهٔ ZIP ریپو را از آدرس زیر دانلود کنید (روی دکمهٔ سبز Code ← Download ZIP):
   - `https://github.com/maryamghabel3-debug/radman-silver-store/archive/refs/heads/main.zip`
   - دقت کنید **پس از merge شدن PR-18** این ZIP حاوی فایل‌های جدید خواهد بود.

---

## 3. مراحل آپلود و استقرار (یک دستور)

### مرحله ۱ — آپلود ZIP از داخل cPanel یا SSH

1. وارد File Manager در cPanel شوید.
2. به مسیر `/home/radmansi/radman-deploy/` بروید.
3. اگر پوشهٔ `repo` از قبل وجود دارد، برای اطمینان آن را به `repo.bak.<تاریخ>` تغییر نام دهید.
4. فایل ZIP جدید را آپلود و در همان‌جا Extract کنید تا پوشه‌ای به نام `radman-silver-store-main` ایجاد شود.
5. آن پوشه را به `repo` تغییر نام دهید تا ساختار نهایی به این شکل باشد:
   ```
   /home/radmansi/radman-deploy/repo/scripts/apply_design_system.sh
   /home/radmansi/radman-deploy/repo/theme/blocksy-child/...
   /home/radmansi/radman-deploy/repo/assets/fonts/*.woff2
   /home/radmansi/radman-deploy/repo/assets/branding/*.png
   /home/radmansi/radman-deploy/repo/templates/home-page-gutenberg.html
   ```

### مرحله ۲ — اجرای Dry-Run (پیش‌نمایش بدون تغییر)

ابتدا در SSH (از داخل ایران):

```bash
export PATH="$HOME/bin:$PATH"
APP_ENV=staging \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
WP_URL=https://staging.radmansilver.ir \
RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
bash /home/radmansi/radman-deploy/repo/scripts/apply_design_system.sh --plan
```

خروجی باید در پایان شامل این خط باشد:
```
PLAN mode complete. No host changes were made.
```

### مرحله ۳ — اجرای واقعی روی استیجینگ

```bash
export PATH="$HOME/bin:$PATH"
APP_ENV=staging \
CONFIRM_STAGING_APPLY=YES \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
WP_URL=https://staging.radmansilver.ir \
RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
bash /home/radmansi/radman-deploy/repo/scripts/apply_design_system.sh --apply-staging
```

اسکریپت به‌ترتیب این کارها را انجام می‌دهد:

1. **گاردهای استیجینگ** را بررسی می‌کند (APP_ENV، WP_URL، WP_PATH، عدم وجود public_html، فعال بودن blocksy-child یا blocksy). اگر `blog_public` خالی یا غلط باشد خودش آن را روی 0 می‌گذارد و ادامه می‌دهد (برخلاف اسکریپت قبلی که روی این مورد خطا می‌داد).
2. **بک‌آپ‌های زمان‌دار** می‌سازد در `~/.config/radman/backups/`:
   - `wordpress-db-<TS>.sql` (چمد 600)
   - `blocksy-child-<TS>.tar.gz`
   - `home-page-18-<TS>.html`
3. **فایل‌های چایلد تم** را همگام می‌کند (style.css نسخه 1.1.0، functions.php با enqueue سه فایل CSS، assets/ و fonts/).
4. **لوگو و فاوایکون** را به کتابخانهٔ رسانه وردپرس وارد می‌کند و `custom_logo` و `site_icon` را تنظیم می‌کند.
5. **theme_mod های امن** را اعمال می‌کند (پس‌زمینه هدر تیره، sticky خاموش، ارتفاع لوگو، گوشه‌های دکمه صاف).
6. **صفحهٔ اصلی (ID=18)** را با قالب بهبودیافتهٔ Gutenberg به‌روزرسانی می‌کند.
7. **کش‌ها** را flush می‌کند (`wp cache flush` و در صورت وجود `wp litespeed-purge all`).

---

## 4. چک‌لیست بصری پس از اجرا

پس از اجرا، `https://staging.radmansilver.ir` را در پنجرهٔ Incognito/Private باز کنید:

- [ ] لوگوی فارسی «رادمان» در هدر نمایش داده می‌شود.
- [ ] فونت کل سایت به فونت فارسی حرفه‌ای تغییر کرده (تیترها Estedad، متن Vazirmatn).
- [ ] H1 هیرو «نقره ۹۲۵؛ اصالت در جزئیات» درشت و سفید روی پس‌زمینه مشکی، با لیبل طلایی بالای آن.
- [ ] دو دکمهٔ CTA (مشاهده فروشگاه طلایی / دسته‌بندی‌ها outline طلایی) در هیرو.
- [ ] نوار اعتماد کرم‌رنگ با چهار وعده (نقره ۹۲۵، موجودی واقعی، اطلاعات شفاف، تأیید انسانی).
- [ ] سه کارت تیره دسته‌بندی (انگشتر / گردنبند / دستبند) با CTA کامل و هاور ظریف.
- [ ] بخش «درباره رادمان» روی پس‌زمینه کرم با خط طلایی زیر عنوان.
- [ ] بخش CTA «ورود به فروشگاه» با دکمه طلایی.
- [ ] نوار «نسخه آزمایشی» در پایین باقی مانده.
- [ ] هاور روی آیتم‌های منو زیرخط طلایی نمایش می‌دهد.
- [ ] دکمه‌های «افزودن به سبد خرید» / «ثبت سفارش» طلایی با گوشهٔ صاف.
- [ ] فاوایکون مونوگرام در تب مرورگر.

---

## 5. تنظیمات دستی کمینه در Customizer

اکثر جنبه‌های طراحی از طریق CSS اعمال شده و نیازی به تغییر دستی ندارند. فقط موارد زیر اگر مطلوب نبودند از طریق Customizer وردپرس تنظیم شوند:

| مورد | مسیر دقیق در Customizer | مقدار پیشنهادی |
|---|---|---|
| نوع هدر (transparent / sticky) | **Appearance → Customize → Header → General** | Non-sticky, non-transparent |
| چیدمان لوگو و منو | **Appearance → Customize → Header → Logo** | Logo max height = 52px (desktop) / 42px (mobile) |
| رنگ‌های سراسری پس‌زمینه | **Appearance → Customize → Colors → General** | Background = #0B0B0E, Text = #FAF7F2 |
| دکمه‌ها | **Appearance → Customize → Buttons** | Border radius = 0, padding ~14px 28px |
| فونت هدر و منو | **Appearance → Customize → Typography → Heading** | اگر Blocksy فونت‌های محلی را شناسایی نکند، روی "System" یا همان پیش‌فرض بگذارید تا CSS ما اعمال شود. |
| ابزارک‌های فوتر | **Appearance → Customize → Footer** | 2 یا 3 ستاره؛ متن تماس و ساعت کاری پس از تأیید نهایی مالک درج شود. |

> ⚠ لطفاً در این مرحله **LiteSpeed Cache → Page Optimization** را دست نزنید؛ فعال‌سازی CSS/JS combine، UCSS، Delayed JS، Guest Mode و QUIC.cloud برای مأموریت آتی محفوظ است و در این اسکریپت اعمال نمی‌شود.

---

## 6. در صورتی که لوگو به‌صورت خودکار نصب نشد

اگر اسکریپت در مرحله `media import` خطا داد (مثلاً به دلیل محدودیت‌های Imagick یا GD روی هاست)، مراحل دستی زیر را انجام دهید:

1. از File Manager به این مسیر بروید:
   ```
   /home/radmansi/radman-deploy/repo/assets/branding/
   ```
2. فایل `radman-logo-header-black.png` را در **Media Library** (پیشخوان وردپرس → رسانه → افزودن) آپلود کنید.
3. به **Appearance → Customize → Header → Logo** بروید و لوگوی آپلودشده را انتخاب کنید.
4. همین کار را برای فایل `logo-icon-512.png` به‌عنوان Site Icon از مسیر **Appearance → Customize → Site Identity → Site Icon** انجام دهید.

---

## 7. بازگردانی (Rollback)

اگر پس از اجرا مشکلی مشاهده کردید، می‌توانید از بک‌آپ‌هایی که اسکریپت در `~/.config/radman/backups/` ساخته استفاده کنید:

```bash
# بازگردانی چایلد تم
cd /home/radmansi/staging.radmansilver.ir/wp-content/themes
rm -rf blocksy-child
tar -xzf ~/.config/radman/backups/blocksy-child-<TS>.tar.gz

# بازگردانی صفحه اصلی (با wp-cli)
wp --path=/home/radmansi/staging.radmansilver.ir post update 18 \
  --post_content="$(cat ~/.config/radman/backups/home-page-18-<TS>.html)"

# بازگردانی کامل دیتابیس (در صورت نیاز)
wp --path=/home/radmansi/staging.radmansilver.ir db import \
  ~/.config/radman/backups/wordpress-db-<TS>.sql
```

---

## 8. نکات مهم

- ✅ هیچ قلم خارجی از Google Fonts، Fonts Bunny، CDN و... بارگذاری نمی‌شود.
- ✅ هیچ `admin_password`، `API_KEY`، `TOKEN` یا credential در اسکریپت وجود ندارد.
- ✅ اسکریپت jailshell-compatible است (بدون `local` در اسکوپ بالا، بدون process substitution `< <(...)`، بدون `/dev/fd`).
- ✅ اسکریپت idempotent است (چندبار اجرا مشکلی ایجاد نمی‌کند).
- ✅ همهٔ 11 صفحهٔ ایستا Draft باقی می‌مانند و منتشر نمی‌شوند.
- ✅ هیچ‌کدام از سرویس‌های پرداخت، پیامک، ردیس، آنالیتیکس یا SEO indexing فعال نمی‌شوند.
- ❌ این اسکریپت را **هرگز** روی `public_html` یا محیط production اجرا نکنید (در کد هم مسدود شده).

---

## 9. پشتیبانی

در صورت بروز خطا در اجرا، متن کامل خطا (همراه با خروجی انتهایی) را ارسال کنید تا روی همان اسکریپت Patch تهیه شود.

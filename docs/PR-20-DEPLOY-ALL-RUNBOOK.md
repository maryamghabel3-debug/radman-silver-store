# RADMAN SILVER 925 — Runbook نهایی استیجینگ با یک دستور (PR-20 نسخه‌ی اصلاح‌شده)

این سند جایگزین قدم‌های چندمرحله‌ای قبلی می‌شود و **تنها با اجرای یک دستور** سه مرحله‌ی ایمن و تکرارپذیر را پشت سر هم اجرا می‌کند:

1. **بررسی فقط-خواندنی (read-only) فوندیشن** — تأیید می‌کند که وردپرس/ووکامرس/کودتم/صفحات/دسته‌بندی‌ها/منو درست نصب هستند؛ **هیچ محتوایی بازنویسی نمی‌شود**.
2. **اعمال سیستم طراحی (PR-18/PR-20)** — فونت‌های محلی، CSS سیستم طراحی، تم‌مادهای امن، و قالب پالایش‌شده‌ی صفحه اصلی.
3. **نصب ایجنت‌های روی هاست (PR-19)** — ساخت پوشه‌های خصوصی، smoke test در حالت `DRY_RUN=1`، چاپ خطوط کرون برای ورود دستی در cPanel.

> ⚠️ این دستور فقط روی **استیجینگ** اجرا می‌شود (`https://staging.radmansilver.ir`).
> اجرای روی `public_html` یا مسیر پروداکشن **در کد مسدود شده است**.

---

## 🔒 تضمین‌های ایمنی این نسخه (PR-20 اصلاح‌شده)

- ✅ **فوندیشن دوباره apply نمی‌شود** — مرحله 1 فقط `--check` (read-only) است و هیچ صفحه/منو/دسته‌ای را دوباره نمی‌سازد یا بازنویسی نمی‌کند.
- ✅ **وضعیت انتشار (publish/draft) صفحات از قبل منتشرشده حفظ می‌شود** — پنج صفحه آموزشی تأییدشده که روی هاست publish هستند، draft نمی‌شوند.
- ✅ **لوگوی آئیوُری (ivory) هدر و site_icon موجود حفظ می‌شوند** — اگر مالک قبلاً لوگوی آئیوُری را روی هدر تیره تنظیم کرده باشد، اسکریپت آن را **overwrite نمی‌کند**.
- ✅ **محتوای ۱۱ صفحه ایستا دوباره نوشته نمی‌شود**.
- ✅ **فایل `staging.env` موجود هیچ‌گاه overwrite نمی‌شود** — کلمات عبور DB و سایر secrets دست‌نخورده باقی می‌مانند.
- ✅ **ایجنت‌ها در smoke test با `DRY_RUN=1` اجرا می‌شوند** — هیچ SMS واقعی ارسال نمی‌شود، هیچ قیمتی نوشته نمی‌شود، هیچ وضعیت سفارشی تغییر نمی‌کند.
- ✅ **کرون‌جاب‌ها به‌طور خودکار ثبت نمی‌شوند** — خطوط کرون فقط در لاگ چاپ می‌شوند تا مالک بعداً در cPanel وارد کند.
- ✅ **بک‌آپ پایگاه‌داده + child theme + صفحه اصلی قبل از هر تغییر گرفته می‌شود**.
- ✅ **بلاگ در حالت noindex باقی می‌ماند** (`blog_public=0` خودکار ترمیم می‌شود).

---

## ۱. پیش‌نیازها

- دسترسی SSH به اکانت cPanel میزبان (MizbanFa) **از داخل ایران**.
- پایتون ۳.۱۱ در مسیر `/opt/alt/python311/bin/python3.11` (پیش‌فرض MizbanFa) یا هر `python3` دیگر در `PATH`.
- دستور `wp` (WP-CLI) در دسترس باشد (در `~/bin/wp` یا PATH).
- وردپرس استیجینگ قبلاً در مسیر `/home/radmansi/staging.radmansilver.ir` نصب شده باشد (نصب اولیه در PR-16 انجام شد).

---

## ۲. آماده‌سازی فایل‌ها روی هاست

۱. از داخل ایران به آدرس زیر بروید و ZIP ریپو را دانلود کنید:
```
https://github.com/maryamghabel3-debug/radman-silver-store/archive/refs/heads/main.zip
```
(پس از merge شدن PR-20 روی main)

۲. از طریق **cPanel → File Manager** یا SFTP، فایل ZIP را در این مسیر آپلود کنید:
```
/home/radmansi/radman-deploy/
```

۳. اگر پوشه‌ی `repo` از قبل در این مسیر وجود دارد، آن را به `repo.bak.<تاریخ>` تغییر نام دهید.

۴. ZIP را Extract کنید تا پوشه‌ای به نام `radman-silver-store-main` ساخته شود. نام آن را به `repo` تغییر دهید تا ساختار نهایی این‌گونه باشد:
```
/home/radmansi/radman-deploy/repo/scripts/deploy_all.sh
/home/radmansi/radman-deploy/repo/theme/blocksy-child/...
/home/radmansi/radman-deploy/repo/agents/...
```

---

## ۳. اجرای Dry-Run (پیش‌نمایش بدون تغییر)

ابتدا در SSH، حالت پیش‌نمایش را اجرا کنید تا مطمئن شوید همه‌ی گاردها برقرارند:

```bash
export PATH="$HOME/bin:$PATH"
bash /home/radmansi/radman-deploy/repo/scripts/deploy_all.sh --plan
```

خروجی باید در پایان این خطوط را نشان دهد:
```
[INFO]  PLAN MODE COMPLETE. No host changes were made.
...
[INFO]  <<<<<<<<< Stage 'On-host cron agents ...' completed.
```

---

## ۴. اجرای واقعی روی استیجینگ

بعد از بررسی خروجی dry-run:

```bash
export PATH="$HOME/bin:$PATH"
APP_ENV=staging \
CONFIRM_STAGING_APPLY=YES \
WP_PATH=/home/radmansi/staging.radmansilver.ir \
WP_URL=https://staging.radmansilver.ir \
RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
bash /home/radmansi/radman-deploy/repo/scripts/deploy_all.sh --apply-staging
```

این دستور به ترتیب سه مرحله را اجرا می‌کند:

| مرحله | اسکریپت | پرچم | کار اصلی |
|------|---------|------|---------|
| ۱ | `scripts/build_staging_storefront.sh` | `--check` (read-only) | **فقط بررسی** وضعیت موجود: وردپرس، ووکامرس، قالب فعال، شناسه صفحه‌ها، منو، دسته‌بندی‌ها. **هیچ تغییری ایجاد نمی‌کند**. |
| ۲ | `scripts/apply_design_system.sh` | `--apply-staging` | کپی فونت‌های محلی (Estedad/Vazirmatn) و CSS سیستم طراحی. **حفظ لوگوی آئیوُری موجود و site_icon** (تنها در صورت نبودن import/set می‌کند). اعمال theme_mod های امن (هدر تیره، لوگو ۵۲px، گوشه‌های ۰). به‌روزرسانی صفحه اصلی با قالب Gutenberg پالایش‌شده. ترمیم خودکار `blog_public=0`. بک‌آپ‌ DB+child theme+homepage. |
| ۳ | `scripts/install_agents.sh` | `--install` | ساخت پوشه‌های `state/ outbox/ logs/ backups/ locks/` در `~/.config/radman/` (فقط اگر وجود نداشته باشند). ساخت فایل `staging.env` **فقط اگر از قبل وجود نداشته باشد** (فایل موجود overwrite **نمی‌شود**). اجرای دود سه ایجنت در حالت `DRY_RUN=1` به‌عنوان smoke test. **چاپ** خطوط کرون (به‌طور خودکار ثبت **نمی‌شوند**). |

---

## ۵. بهبودهای کلیدی نسخه PR-20

- **تشخیص مقاوم قالب فعال**: `wp option get stylesheet` (مقدار واحد مطمئن) → `wp theme list --format=csv` → بررسی فایل‌سیستم؛ دیگر خطای `Active theme 'unknown'` در jailshell نمی‌دهد.
- **ترمیم خودکار `blog_public=0`**: اگر `blog_public` خالی یا غلط بود، اسکریپت خودکار آن را 0 می‌گذارد (استیجینگ باید noindex بماند).
- **حفظ لوگوی آئیوُری موجود**: چک می‌کند آیا `custom_logo` از قبل یک attachment ID معتبر است؛ اگر بود، همان را حفظ می‌کند و لاگ می‌زند `Existing custom logo preserved: attachment ID N`.
- **حفظ site_icon**: به همین شکل اگر `site_icon` معتبر بود آن را حفظ می‌کند.
- **اجرای زنجیره‌ای ایمن**: سه اسکریپت پشت سر هم، با env مشترک، بدون بازنویسی فوندیشن.
- **نصب ایجنت بدون overwrite**: `staging.env` فقط در صورت نبودن ساخته می‌شود.

---

## ۶. بعد از اجرای موفق

۱. در مرورگر incognito آدرس `https://staging.radmansilver.ir` را باز کنید و موارد زیر را چک کنید:
   - [ ] لوگوی فارسی «رادمان» به رنگ **آئیوُری (روشن)** در هدر تیره نمایش داده می‌شود.
   - [ ] لوگو overwrite نشده (اگر قبلاً لوگوی درست را import کرده بودید باید همان باقی بماند).
   - [ ] فونت کل سایت عوض شده (Estedad در تیترها، Vazirmatn در متن).
   - [ ] H1 هیرو «نقره ۹۲۵؛ اصالت در جزئیات» درشت و آئیوُری روی پس‌زمینه مشکی.
   - [ ] نوار اعتماد (trust strip) روی کرم، با چهار وعده.
   - [ ] سه کارت دسته‌بندی (انگشتر / گردنبند / دستبند) تیره روی پس‌زمینه کرم، با هاور طلایی.
   - [ ] دکمه‌های طلایی با گوشه‌های تیز (border-radius 0).
   - [ ] فوتر تیره با متن ivory-muted و لینک‌های طلایی.
   - [ ] نوار «نسخه آزمایشی» در پایین صفحه.
   - [ ] فاوایکون (مونوگرام) در تب مرورگر.
   - [ ] پنج صفحه آموزشی که قبلاً publish شده بودند همچنان publish باقی مانده‌اند.

۲. فایل `~/.config/radman/staging.env` را **فقط اگر تازه ساخته شده بود** ویرایش کنید و `OWNER_MOBILE=...` را با شماره موبایل مالک (با پیشوند 09) پر کنید. **فعلاً `DRY_RUN=1` باقی بماند** — اعلان‌ها به‌جای SMS واقعی در `outbox/sms-*.txt` ذخیره می‌شوند. اگر فایل از قبل وجود داشت، تغییر ندهید (secrets موجود حفظ شده‌اند).

۳. نرخ روز نقره را در فایل زیر وارد کنید (یک عدد صحیح به تومان/گرم):
```
~/.config/radman/state/daily_rate.txt
```

۴. سه خط Cron که توسط installer در پایان لاگ چاپ شده است را **به‌صورت دستی** از طریق cPanel → Advanced → Cron Jobs اضافه کنید (دقیقاً همان‌هایی که در خروجی چاپ شده). اسکریپت به‌طور خودکار کرون ثبت نمی‌کند.

۵. پس از یک یا دو روز بررسی اعلان‌ها در `outbox/` و قیمت‌ها در `price_preview_*.txt`، در صورت اطمینان می‌توانید `DRY_RUN=0` و `KAVENEGAR_API_KEY=...` را در env تنظیم کنید تا SMS واقعی فعال شود.

---

## ۷. بازگردانی (Rollback)

هر مرحله قبل از تغییر، بک‌آپ می‌گیرد:

- **دیتابیس**: `~/.config/radman/backups/wordpress-db-<TS>.sql`
- **Child theme**: `~/.config/radman/backups/blocksy-child-<TS>.tar.gz`
- **صفحه اصلی**: `~/.config/radman/backups/home-page-18-<TS>.html`
- **قیمت‌ها**: `~/.config/radman/backups/prices-<TS>.csv` (فقط در صورت اجرای `--apply` ایجنت قیمت)

برای بازگردانی دیتابیس (اجرا در SSH):
```bash
wp --path=/home/radmansi/staging.radmansilver.ir db import ~/.config/radman/backups/wordpress-db-<TS>.sql
```

برای بازگردانی child theme:
```bash
cd /home/radmansi/staging.radmansilver.ir/wp-content/themes
rm -rf blocksy-child
tar -xzf ~/.config/radman/backups/blocksy-child-<TS>.tar.gz
```

---

## ۸. قوانین مهم

- ❌ هیچ‌گاه این دستور را روی `public_html` یا WP_URL غیر از `staging.radmansilver.ir` اجرا نکنید. گاردها در کد مسدود کرده‌اند.
- ❌ تا زمان تأیید نهایی مالک و بازبینی حقوقی، ۱۱ صفحه ایستای تأییدنشده **Publish** نمی‌شوند (هرچند صفحاتی که از قبل publish بوده‌اند حفظ می‌شوند).
- ❌ پرداخت، SMS واقعی (پیش از تنظیم API key)، Redis، آنالیتیکس، و بهینه‌سازی‌های تهاجمی LiteSpeed (CSS/JS combine, UCSS, Delayed JS, Guest Mode, QUIC.cloud) توسط این اسکریپت‌ها فعال **نمی‌شوند**.
- ❌ فوندیشن دوباره apply **نمی‌شود** (صفحات/منو/دسته‌بندی‌های موجود دست‌نخورده باقی می‌مانند).
- ❌ `staging.env` موجود overwrite **نمی‌شود**.
- ✅ لوگو و favicon موجود حفظ می‌شوند.
- ✅ تمام اعلان‌های ایجنت‌ها به‌صورت پیش‌فرض در `outbox/` ذخیره می‌شوند تا قبل از فعال‌سازی SMS واقعی بازبینی شوند.
- ✅ تمام لاگ‌ها در `~/.config/radman/logs/` با چرخش ۱ مگابایت نگه داشته می‌شوند.

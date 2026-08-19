# RADMAN SILVER 925 — Runbook نهایی استیجینگ با یک دستور (PR-20)

این سند جایگزین قدم‌های چندمرحله‌ای قبلی می‌شود و **تنها با اجرای یک دستور** تمام مراحل استقرار را انجام می‌دهد:
فوندیشن فروشگاه (PR-16)، سیستم طراحی لوکس (PR-18)، و ایجنت‌های روی هاست (PR-19).

> ⚠️ این دستور فقط روی **استیجینگ** اجرا می‌شود (`https://staging.radmansilver.ir`).
> اجرای روی `public_html` یا مسیر پروداکشن **در کد مسدود شده است**.

---

## ۱. پیش‌نیازها

- دسترسی SSH به اکانت cPanel میزبان (MizbanFa) **از داخل ایران**.
- پایتون ۳.۱۱ در مسیر `/opt/alt/python311/bin/python3.11` (پیش‌فرض MizbanFa) یا
  هر `python3` دیگر در `PATH`.
- دستور `wp` (WP-CLI) در دسترس باشد (در `~/bin/wp` یا PATH).
- وردپرس استیجینگ قبلاً در مسیر `/home/radmansi/staging.radmansilver.ir` نصب شده باشد.

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

## ۳. اجرای Dry-Run (بدون تغییر)

ابتدا در SSH، حالت پیش‌نمایش (dry-run) را اجرا کنید تا مطمئن شوید همه‌ی گاردها برقرارند:

```bash
export PATH="$HOME/bin:$PATH"
bash /home/radmansi/radman-deploy/repo/scripts/deploy_all.sh --plan
```

خروجی باید در پایان این خطوط را نشان دهد:
```
[INFO]  PLAN MODE COMPLETE. No host changes were made.
...
[INFO]  <<<<<<<<<< Stage 'On-host cron agents ...' completed.
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

این دستور به ترتیب سه زیراسکریپت را اجرا می‌کند:

| مرحله | اسکریپت | کار اصلی |
|------|---------|---------|
| ۱ | `scripts/build_staging_storefront.sh --apply-staging` | فعال‌سازی child theme، آپلود ۱۱ صفحه ایستا به‌صورت Draft، قالب صفحه اصلی، ۳ دسته‌بندی محصول، منوی اصلی، گزارشات پایه Woo/LiteSpeed |
| ۲ | `scripts/apply_design_system.sh --apply-staging` | کپی فونت‌های محلی (Estedad/Vazirmatn) و CSS سیستم طراحی، ایمپورت لوگو و فاوایکن، اعمال theme_mod های امن (هدر تیره، لوگو ۵۲px، گوشه‌های ۰) |
| ۳ | `scripts/install_agents.sh --install` | ساخت پوشه‌های `state/ outbox/ logs/ backups/ locks/` در `~/.config/radman/`، ساخت فایل `staging.env` (اگر وجود نداشته باشد)، اجرای دود سه ایجنت در حالت DRY_RUN=1 به‌عنوان smoke test |

---

## ۵. بهبودهای کلیدی نسخه PR-20 (در مقایسه با PR-18)

- **تشخیص مقاوم قالب فعال**: قبلاً `wp theme list --field=name --format=trim` در jailshell گاهی خالی برمی‌گشت و خطای `Active theme 'unknown'` می‌داد. نسخه جدید ابتدا با `wp option get stylesheet` (که یک مقدار واحد مطمئن برمی‌گرداند) سعی می‌کند؛ در صورت خالی بودن، به `wp theme list --status=active --format=csv` و در نهایت به بررسی وجود پوشه‌ی `wp-content/themes/blocksy-child` روی فایل‌سیستم فال‌بک می‌زند.
- **auto-heal شدن `blog_public=0`**: قبلاً اگر `blog_public` خالی بود اسکریپت abort می‌کرد. حالا خودکار آن را روی 0 می‌گذارد (استیجینگ باید noindex بماند).
- **اجرای زنجیره‌ای**: سه اسکریپت پشت سر هم، با env های مشترک، و با بک‌آپ‌های جداگانه در هر مرحله.

---

## ۶. بعد از اجرای موفق

۱. در مرورگر incognito آدرس `https://staging.radmansilver.ir` را باز کنید و موارد زیر را چک کنید:
   - [ ] لوگوی فارسی «رادمان» در هدر نمایش داده می‌شود.
   - [ ] فونت کل سایت عوض شده (Estedad در تیترها، Vazirmatn در متن).
   - [ ] H1 هیرو «نقره ۹۲۵؛ اصالت در جزئیات» درشت و سفید روی پس‌زمینه مشکی.
   - [ ] نوار اعتماد (trust strip) روی کرم، با چهار وعده (نقره ۹۲۵ / موجودی واقعی / ...).
   - [ ] سه کارت دسته‌بندی (انگشتر / گردنبند / دستبند) تیره روی پس‌زمینه کرم، با هاور طلایی.
   - [ ] دکمه‌های طلایی با گوشه‌های تیز (border-radius 0).
   - [ ] فوتر تیره با متن ivory-muted و لینک‌های طلایی.
   - [ ] نوار «نسخه آزمایشی» در پایین صفحه.
   - [ ] فاوایکون (مونوگرام) در تب مرورگر.

۲. فایل `~/.config/radman/staging.env` را ویرایش کنید و `OWNER_MOBILE=...` را با شماره موبایل مالک (با پیشوند 09) پر کنید. **فعلاً `DRY_RUN=1` باقی بماند** — اعلان‌ها به‌جای SMS واقعی در `outbox/sms-*.txt` ذخیره می‌شوند.

۳. نرخ روز نقره را در فایل زیر وارد کنید (یک عدد صحیح به تومان/گرم):
```
~/.config/radman/state/daily_rate.txt
```

۴. سه خط Cron که توسط installer در پایان لاگ چاپ می‌شود از طریق cPanel → Advanced → Cron Jobs اضافه کنید (دقیقاً همان‌هایی که در خروجی `deploy_all.sh --apply-staging` چاپ شده).

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
- ❌ تا زمان تأیید نهایی مالک و بازبینی حقوقی، هیچ‌کدام از ۱۱ صفحه ایستا Publish نمی‌شوند (همه Draft باقی می‌مانند).
- ❌ پرداخت، SMS واقعی (پیش از تنظیم API key)، Redis، آنالیتیکس، و بهینه‌سازی‌های تهاجمی LiteSpeed (CSS/JS combine, UCSS, Delayed JS, Guest Mode, QUIC.cloud) توسط این اسکریپت‌ها فعال **نمی‌شوند**.
- ✅ تمام اعلان‌های ایجنت‌ها به‌صورت پیش‌فرض در `outbox/` ذخیره می‌شوند تا قبل از فعال‌سازی SMS واقعی بازبینی شوند.
- ✅ تمام لاگ‌ها در `~/.config/radman/logs/` با چرخش ۱ مگابایت نگه داشته می‌شوند.

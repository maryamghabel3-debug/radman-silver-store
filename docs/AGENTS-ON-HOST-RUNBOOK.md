# راهنمای نصب و اجرای ایجنت‌های روی هاست (PR-19)

این سند نحوه‌ی نصب، پیکربندی و اجرای سه **ایجنت پایتون روی هاست** (cPanel / MizbanFa / jailshell) را توضیح می‌دهد.

> ⚠️ این ایجنت‌ها **فقط روی STAGING** تست می‌شوند و تا زمان تأیید نهایی، `DRY_RUN=1` باقی می‌مانند (یعنی فقط فایل پیش‌نمایش/گزارش می‌نویسند و هیچ سفارشی را تأیید یا قیمتی را روی سایت اعمال نمی‌کنند).
> ⚠️ تلگرام از میزبان‌های داخل ایران در دسترس نیست؛ **کانال اصلی اطلاع‌رسانی SMS از طریق Kavenegar** است و تا زمان تکمیل پیکربندی، تمام اعلان‌ها در پوشه‌ی `outbox/` ذخیره می‌شوند.

---

## ۱. پیش‌نیازها

- دسترسی SSH به اکانت cPanel میزبان (MizbanFa) **از داخل ایران**.
- پایتون ۳.۱۱ یا بالاتر روی هاست موجود است (مسیر `/opt/alt/python311/bin/python3.11` در MizbanFa).
- دستور `wp` (WP-CLI) در PATH در دسترس باشد.
- دسترسی به staging از قبل روی مسیر `/home/radmansi/staging.radmansilver.ir` نصب شده باشد (یعنی PR-16 و PR-17/PR-18 قبلاً با موفقیت روی staging اجرا شده باشند).

---

## ۲. فایل‌های ایجنت (درون ریپو)

| فایل | کاربرد | اجرا به صورت |
|---|---|---|
| `agents/lib/radman_common.py` | کتابخانه‌ی مشترک (لودر env، wrapper برای wp-cli، لاگر چرخشی، قفل فایل، ارسال SMS) | `import` |
| `agents/agent_order_watch.py` | پایش سفارش‌های جدید (processing/on-hold) و ارسال اعلان به مالک | Cron هر ۵ دقیقه |
| `agents/agent_price_engine.py` | محاسبه‌ی قیمت محصولات وزن‌محور بر اساس نرخ روز نقره و اعمال در حالت `--apply` | Cron روزانه ۰۹:۰۷ (فقط پیش‌نمایش)؛ دستی برای apply |
| `agents/agent_stock_guard.py` | گزارش ناهنجاری‌های موجودی (read-only) | Cron هر ساعت |
| `scripts/install_agents.sh` | نصب‌کننده‌ی یک‌دستوره‌ای + چاپ خطوط Cron | یک‌بار اجرا در SSH |

---

## ۳. مراحل نصب

### مرحله ۱ — دانلود ZIP جدید از گیت‌هاب
1. از داخل ایران وارد آدرس زیر شوید:
   `https://github.com/maryamghabel3-debug/radman-silver-store`
2. روی دکمه‌ی سبز **Code** کلیک و **Download ZIP** را بزنید.
3. از طریق cPanel → File Manager یا SFTP، فایل ZIP را در مسیر زیر آپلود کنید:
   `/home/radmansi/radman-deploy/`
4. اگر پوشه‌ی `repo` از قبل موجود است، برای اطمینان آن را به `repo.bak.<تاریخ>` تغییر نام دهید.
5. ZIP را در همان‌جا Extract کنید تا پوشه‌ای به نام `radman-silver-store-main` ایجاد شود، سپس آن را به `repo` تغییر نام دهید تا ساختار نهایی به این شکل باشد:
   ```
   /home/radmansi/radman-deploy/repo/scripts/install_agents.sh
   /home/radmansi/radman-deploy/repo/agents/agent_order_watch.py
   ```

### مرحله ۲ — اجرای نصب‌کننده (plan + apply-staging)
1. وارد SSH شوید.
2. ابتدا dry-run را اجرا کنید (هیچ تغییری نمی‌دهد و فقط برنامه را اعلام می‌کند):
   ```bash
   export PATH="$HOME/bin:$PATH"
   bash /home/radmansi/radman-deploy/repo/scripts/install_agents.sh --plan
   ```
3. اگر خروجی بدون خطا بود، نصب واقعی را اجرا کنید:
   ```bash
   export PATH="$HOME/bin:$PATH"
   CONFIRM_STAGING_APPLY=YES bash /home/radmansi/radman-deploy/repo/scripts/install_agents.sh --apply-staging
   ```
   این دستور:
   - پیش از هر تغییر، از تنظیمات/وضعیت قبلی در `~/.config/radman/backups/agents-preinstall-<timestamp>.tar.gz` بکاپ می‌گیرد.
   - پوشه‌های `~/.config/radman/{state,outbox,logs,backups,locks}` را با دسترسی `chmod 700` می‌سازد.
   - فایل محیطی `~/.config/radman/staging.env` را **فقط در صورتی که از قبل وجود نداشته باشد** می‌سازد (مقادیر قبلی را overwrite نمی‌کند).
   - یک فایل نمونه برای نرخ روز نقره در `~/.config/radman/state/daily_rate.txt` می‌سازد.
   - هر سه ایجنت را **در حالت DRY_RUN=1** اجرا می‌کند تا از درست بودن محیط اطمینان حاصل شود.

### مرحله ۳ — تنظیم شماره موبایل مالک
فایل `~/.config/radman/staging.env` را با ویرایشگر دلخواه (مثلاً `nano` یا از File Manager cPanel) باز کنید و خط `OWNER_MOBILE=` را با شماره‌ی موبایل مالک کامل کنید:
```
OWNER_MOBILE=0912xxxxxxx
```
فعلاً خط `KAVENEGAR_API_KEY=` را **خالی** بگذارید تا اعلان‌ها در فایل‌های `outbox/` ذخیره شوند.

### مرحله ۴ — ثبت نرخ روز نقره
فایل `~/.config/radman/state/daily_rate.txt` را باز کنید و خط کامنت را پاک کرده و فقط یک عدد صحیح (قیمت هر گرم نقره به **تومان**) وارد کنید، مثلاً:
```
85000
```

---

## ۴. اضافه کردن Cron Job ها در cPanel

1. وارد cPanel شوید.
2. به بخش **Advanced → Cron Jobs** بروید.
3. ایمیل اعلان Cron را (در صورت تمایل) روی ایمیل مالک تنظیم کنید.
4. هر یک از سه خط زیر را به عنوان یک Cron Job جدید **با Shell بش (`bash` یا `sh`)** اضافه کنید. این خطوط دقیقاً همان چیزی هستند که `install_agents.sh` در خروجی چاپ می‌کند:

### 4.1 — Order Watch (هر ۵ دقیقه)
- **Common Settings:** Once Per 5 Minutes (`*/5 * * * *`)
- **Command:**
  ```bash
  APP_ENV=staging WP_PATH=/home/radmansi/staging.radmansilver.ir WP_URL=https://staging.radmansilver.ir RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman DRY_RUN=1 /opt/alt/python311/bin/python3.11 /home/radmansi/radman-deploy/repo/agents/agent_order_watch.py >/dev/null 2>&1
  ```

### 4.2 — Stock Guard (هر ساعت، دقیقه‌ی ۷)
- **Common Settings:** Once Per Hour (دقیقه را روی 7 بگذارید → `7 * * * *`)
- **Command:**
  ```bash
  APP_ENV=staging WP_PATH=/home/radmansi/staging.radmansilver.ir WP_URL=https://staging.radmansilver.ir RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman DRY_RUN=1 /opt/alt/python311/bin/python3.11 /home/radmansi/radman-deploy/repo/agents/agent_stock_guard.py >/dev/null 2>&1
  ```

### 4.3 — Price Engine (هر روز ساعت ۰۹:۰۷، فقط پیش‌نمایش)
- **Schedule:** `7 9 * * *`
- **Command:**
  ```bash
  APP_ENV=staging WP_PATH=/home/radmansi/staging.radmansilver.ir WP_URL=https://staging.radmansilver.ir RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman DRY_RUN=1 /opt/alt/python311/bin/python3.11 /home/radmansi/radman-deploy/repo/agents/agent_price_engine.py >/dev/null 2>&1
  ```

> ⚠️ **توجه:** این Cron فقط **پیش‌نمایش** تغییرات قیمت را در `outbox/price_preview_<timestamp>.txt` می‌نویسد. برای اعمال واقعی قیمت، باید دستی بعد از بازبینی، دستور apply را در SSH اجرا کنید (بخش ۶).
>
> خروجی استاندارد Cron عمداً به `/dev/null` می‌رود؛ هر ایجنت لاگ داخلی چرخشی خود را در `logs/<agent>.log` با سقف ۱ مگابایت نگه می‌دارد تا فایل Cron بدون محدودیت رشد نکند.

---

## ۵. اجرای دستی ایجنت‌ها (آزمایشی)

می‌توانید هر ایجنت را مستقیماً در SSH اجرا کنید:

```bash
# Order Watch (خشک / بدون ارسال SMS)
APP_ENV=staging WP_PATH=/home/radmansi/staging.radmansilver.ir WP_URL=https://staging.radmansilver.ir \
  RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \
  RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
  DRY_RUN=1 \
  /opt/alt/python311/bin/python3.11 /home/radmansi/radman-deploy/repo/agents/agent_order_watch.py --dry-run

# Stock Guard (همیشه read-only)
APP_ENV=staging WP_PATH=/home/radmansi/staging.radmansilver.ir WP_URL=https://staging.radmansilver.ir \
  RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \
  RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
  /opt/alt/python311/bin/python3.11 /home/radmansi/radman-deploy/repo/agents/agent_stock_guard.py

# Price Engine (پیش‌نمایش)
APP_ENV=staging WP_PATH=/home/radmansi/staging.radmansilver.ir WP_URL=https://staging.radmansilver.ir \
  RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \
  RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
  DRY_RUN=1 \
  /opt/alt/python311/bin/python3.11 /home/radmansi/radman-deploy/repo/agents/agent_price_engine.py --dry-run
```

---

## ۶. چرخه‌ی روزانه قیمت نقره

1. هر روز صبح، مالک پس از بررسی نرخ روز، یک عدد صحیح (تومان/گرم) در فایل زیر می‌نویسد:
   ```
   ~/.config/radman/state/daily_rate.txt
   ```
2. Cron ساعت ۰۹:۰۷ به طور خودکار اجرا می‌شود و یک **پیش‌نمایش تغییرات قیمت** در این مسیر می‌سازد:
   ```
   ~/.config/radman/outbox/price_preview_<YYYYMMDD-HHMMSS>.txt
   ```
3. مالک فایل پیش‌نمایش را در File Manager یا SSH باز کرده و بررسی می‌کند (لیست محصول، قیمت قدیم، قیمت جدید، درصد تغییر).
4. **فقط در صورت تأیید**، دستور apply دستی اجرا شود:
   ```bash
   APP_ENV=staging WP_PATH=/home/radmansi/staging.radmansilver.ir WP_URL=https://staging.radmansilver.ir \
     RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \
     RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \
     DRY_RUN=0 \
     /opt/alt/python311/bin/python3.11 /home/radmansi/radman-deploy/repo/agents/agent_price_engine.py --apply
   ```
   قبل از اعمال، بکاپ CSV قیمت‌های قبلی در `~/.config/radman/backups/prices-<timestamp>.csv` ذخیره می‌شود.

> در حالت `legacy_mirror` مقدار معتبر `legacy_price_toman` عیناً mirror می‌شود. حالت `manual_locked` هرگز خودکار تغییر نمی‌کند. حالت `silver_weight_only` به نزدیک‌ترین ۱۰٬۰۰۰ تومان گرد می‌شود و `silver_weight_plus_stone` ارزش ثابت نگین را بدون گردکردن ۱۰هزارتومانی حفظ می‌کند.

---

## ۷. فعال کردن ارسال SMS واقعی (Kavenegar)

پس از چند روز کار در حالت `DRY_RUN=1` و اطمینان از صحت اعلان‌ها:

1. از پنل Kavenegar، API Key خود را دریافت کنید.
2. فایل `~/.config/radman/staging.env` را ویرایش کنید:
   ```
   DRY_RUN=0
   KAVENEGAR_API_KEY= <کلید واقعی شما>
   OWNER_MOBILE=0912xxxxxxx
   KAVENEGAR_SENDER=10008445
   ```
3. در خط Cron مربوط به Order Watch هم `DRY_RUN=1` را به `DRY_RUN=0` تغییر دهید.
4. پس از اجرای بعدی Cron، اعلان‌ها به صورت SMS واقعی ارسال می‌شوند و یک کپی از هر پیامک در `outbox/order_<ID>.sent.txt` ذخیره می‌شود.
   - در صورت خطا (مثل قطع بودن Kavenegar یا نبود اینترنت)، اعلان به صورت `order_<ID>.txt` در outbox ذخیره می‌شود تا از دست نرود.

---

## ۸. مکان فایل‌های خروجی و بکاپ

| نوع فایل | مسیر |
|---|---|
| لاگ چرخشی ایجنت‌ها | `~/.config/radman/logs/<agent>.log` |
| اعلان سفارش (در حالت dry یا خطای SMS) | `~/.config/radman/outbox/order_<ID>.txt` |
| گزارش Stock Guard | `~/.config/radman/outbox/stock_report_<timestamp>.txt` |
| پیش‌نمایش قیمت | `~/.config/radman/outbox/price_preview_<timestamp>.txt` |
| بکاپ نصب/وضعیت قبلی ایجنت‌ها | `~/.config/radman/backups/agents-preinstall-<timestamp>.tar.gz` |
| بکاپ CSV قیمت‌ها قبل از apply | `~/.config/radman/backups/prices-<timestamp>.csv` |
| وضعیت آخرین سفارش دیده‌شده (cursor) | `~/.config/radman/state/order_watch.json` |
| نرخ روز نقره | `~/.config/radman/state/daily_rate.txt` |
| فایل env (chmod 600) | `~/.config/radman/staging.env` |

---

## ۹. عیب‌یابی

| مشکل | راه‌حل |
|---|---|
| `No such file or directory: wp` | مطمئن شوید `export PATH="$HOME/bin:$PATH"` قبل از اجرا تنظیم شده و `wp-cli` در `~/bin/wp` نصب است. |
| `Python not found` | از مسیر کامل `/opt/alt/python311/bin/python3.11` استفاده کنید. |
| پیام `Another deployment appears to be running` | یک اجرای قبلی هنوز قفل را نگه داشته. اگر از نبود اجرای همزمان مطمئن هستید، فایل قفل را حذف کنید: `rm -f ~/.config/radman/locks/*.lock` |
| `blog_public is ...` | ایجنت‌های جدید نسبت به این مورد سخت‌گیر نیستند، اما برای staging بهتر است `wp option update blog_public 0` اجرا شود. |
| سفارش‌های دیده‌شده در outbox ارسال نمی‌شوند | `DRY_RUN=1` است. مادامی که این متغیر برابر 1 باشد، هیچ SMS واقعی ارسال نمی‌شود. |
| گزارش قیمت خالی است | مطمئن شوید `daily_rate.txt` فقط شامل یک عدد صحیح مثبت (بدون خط کامنت) باشد. |

---

## ۱۰. قوانین مهم ایمنی و کسب‌وکاری

1. **HITL (Human-in-the-loop):** هیچ ایجنتی وضعیت سفارش را به «در حال ارسال» یا «تکمیل‌شده» تغییر نمی‌دهد؛ فقط اعلان می‌فرستد.
2. **عدم انتشار خودکار صفحات Draft:** ایجنت‌ها صفحات ایستا را منتشر یا ویرایش نمی‌کنند.
3. **عدم فعال‌سازی درگاه/SMS/Redis/Analytics:** این ایجنت‌ها هیچ درگاه پرداخت، Kavenegar (جز با صلاحدید مالک)، Redis، رتبه‌ماه یا ابزار تحلیلی را به طور خودکار فعال نمی‌کنند.
4. **محدود به STAGING:** هر سه ایجنت `APP_ENV`، آدرس، مسیر دقیق `/home/radmansi/staging.radmansilver.ir` و خارج‌بودن private dir از `public_html` را بررسی می‌کنند.
5. **لاگ‌ها هرگز شامل کلیدهای API یا رمز عبور نیستند** (تابع `redact()` هر کلید شناخته‌شده را قبل از نوشتن در لاگ ماسک می‌کند).
6. **بکاپ قبل از تغییر قیمت:** هر بار که قیمت‌ها apply شوند، یک CSV پشتیبان از قیمت‌های قبلی گرفته می‌شود.
7. **تلگرام در این نسخه کاملاً غیرفعال است** (به‌دلیل مسدود بودن از میزبان ایران). کانال رسمی اعلان، **SMS از طریق Kavenegar** (با پیش‌فرض outbox) است؛ مدیریت سفارش از طریق پنل ووکامرس انجام می‌شود.

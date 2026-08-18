# رجیستری تأیید محتوای استاتیک (`STATIC-CONTENT-APPROVAL-REGISTRY.md`)

> **وضعیت سند:** Source of Truth برای وضعیت تأیید ۱۱ صفحه استاتیک رادمان سیلور.
> **تاریخ:** 2026-08-16 (Asia/Tehran)
> **مخزن:** `maryamghabel3-debug/radman-silver-store`
> **قاعده انتشار:** هیچ‌یک از صفحات زیر **نباید** روی سایت عمومی (پروداکشن) منتشر شوند مگر آن که ستون‌های «Owner approval» و (در صورت نیاز) «Legal review» برای آن‌ها به مقدار `APPROVED` رسیده باشند. انتشار روی استیجینگ به‌صورت Draft **مجاز** است (Draft deploy allowed = YES).

---

## وضعیت فاز محتوا

- **Repository content complete:** ✅ YES — محتوای کامل ۱۱ صفحه در `content/static-pages/` موجود است.
- **Placeholder-free (در Content section):** ✅ YES — در بخش محتوای عمومی (`## Content`) هیچ `[…]`ی باقی نمانده است. هرجا دادهٔ نهایی موجود نباشد، صریحاً از عباراتی نظیر «به‌زودی اعلام می‌شود» یا «پس از تأیید نهایی» استفاده شده است.
- **Draft deploy allowed:** ✅ YES — همه ۱۱ صفحه می‌توانند به‌صورت Draft روی استیجینگ قرار بگیرند.
- **Publish allowed:** ❌ NO — همه ۱۱ صفحه تا زمان تأیید نهایی مالک و (در صورت نیاز) بازبینی حقوقی، **BLOCKED** برای انتشار هستند.

---

## جدول رجیستری

| # | Slug | Title (FA) | Repo content complete | Placeholder-free | Draft deploy allowed | Owner approval | Legal review required | Publish allowed | Notes |
|---:|:------|:-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | `about-us` | درباره رادمان | ✅ YES | ✅ YES | ✅ YES | ⏳ PENDING | ❌ NO | 🚫 BLOCKED | معرفی برند. تایید نهایی لحن و تاریخچه توسط مالک. |
| 2 | `contact-us` | تماس با ما | ✅ YES | ✅ YES | ✅ YES | ⏳ PENDING (تماس/ساعت) | ❌ NO | 🚫 BLOCKED | تلفن/ساعت/نشانی هنوز تأییدنشده‌اند. |
| 3 | `faq` | سؤالات متداول | ✅ YES | ✅ YES | ✅ YES | ⏳ PENDING | ❌ NO | 🚫 BLOCKED | متن‌ها با زبان واقع‌بینانه (بدون تعهد فعال‌نبودن سرویس‌ها) نوشته شده‌اند. |
| 4 | `shipping` | روش‌های ارسال | ✅ YES | ✅ YES | ✅ YES | ⏳ PENDING | ❌ NO | 🚫 BLOCKED | روش‌های ارسال، تعرفه، COD و بسته‌بندی نهایی‌نشده. |
| 5 | `returns` | شرایط بازگشت کالا | ✅ YES | ✅ YES | ✅ YES | ⏳ PENDING | ✅ REQUIRED | 🚫 BLOCKED | نیاز به تایید نهایی مهلت بازگشت/هزینه/SLA و بازبینی حقوقی. |
| 6 | `privacy-policy-radman` | حریم خصوصی | ✅ YES | ✅ YES | ✅ YES | ⏳ PENDING | ✅ REQUIRED | 🚫 BLOCKED | سیاست حریم‌خصوصی نیازمند بازبینی حقوقی قبل از انتشار. |
| 7 | `terms` | قوانین و مقررات | ✅ YES | ✅ YES | ✅ YES | ⏳ PENDING | ✅ REQUIRED | 🚫 BLOCKED | قوانین خرید نیازمند تایید نهایی و بازبینی حقوقی است. |
| 8 | `ring-size-guide` | راهنمای سایز انگشتر | ✅ YES | ✅ YES | ✅ YES | ⏳ PENDING | ❌ NO | 🚫 BLOCKED | جدول سایز/اینفوگرافیک نیاز به تطبیق با قالب‌های کارگاه دارد. |
| 9 | `silver-care` | راهنمای نگهداری نقره | ✅ YES | ✅ YES | ✅ YES | ⏳ PENDING | ❌ NO | 🚫 BLOCKED | تایید نکات تخصصی نگهداری سنگ/نقره و اقلام همراه. |
| 10 | `silver-925-authenticity` | اصالت نقره ۹۲۵ | ✅ YES | ✅ YES | ✅ YES | ⏳ PENDING | ❌ NO | 🚫 BLOCKED | تایید نهایی نحوه ارائه ضمانت‌اصالت/فاکتور. |
| 11 | `gemstones` | راهنمای سنگ‌های زینتی | ✅ YES | ✅ YES | ✅ YES | ⏳ PENDING | ❌ NO | 🚫 BLOCKED | تایید لیست سنگ‌های موجود و توضیحات توسط مالک. |

---

## صفحات استاتیک وضعیت در وردپرس (استیجینگ)

- شناسه‌های صفحات در استیجینگ (ثبت‌شده در دوره bootstrap):
  - ID 21 `about-us` (Draft placeholder)
  - ID 22 `contact-us` (Draft placeholder)
  - ID 23 `faq` (Draft placeholder)
  - ID 24 `shipping` (Draft placeholder)
  - ID 25 `returns` (Draft placeholder)
  - ID 26 `privacy-policy-radman` (Draft placeholder)
  - ID 27 `terms` (Draft placeholder)
  - ID 28 `ring-size-guide` (Draft placeholder)
  - ID 29 `silver-care` (Draft placeholder)
  - ID 30 `silver-925-authenticity` (Draft placeholder)
  - ID 31 `gemstones` (Draft placeholder)
- صفحه اصلی (Home) ID `18` — منتشر شده و front-page است.
- پس از اجرای `scripts/radman_stage_apply.sh --apply-staging` با `CONFIRM_STAGING_APPLY=YES` (در یک مأموریت مصوب آتی)، محتوای نهایی به‌صورت **Draft** روی استیجینگ به صفحات موجود upsert خواهد شد (بدون انتشار خودکار).

---

## تعاریف ستون‌ها

- **Repo content complete:** آیا محتوای کامل و نهایی‌نویسی‌شده در `content/static-pages/` وجود دارد؟
- **Placeholder-free:** آیا در بخش عمومی `## Content` هیچ `[…]` یا متن‌جای خالی تأییدنشده‌ای باقی نمانده است؟
- **Draft deploy allowed:** آیا می‌توان محتوای این صفحه را به‌صورت Draft روی استیجینگ/پروداکشن (برای پیش‌نمایش) قرار داد؟
- **Owner approval:** تایید نهایی مالک بر صحت اطلاعات (تماس، قیمت‌گذاری، سیاست‌ها، آدرس‌ها، ساعات، ...). مقادیر: `PENDING` / `APPROVED` / `REJECTED`.
- **Legal review required:** آیا صفحه نیاز به بازبینی حقوقی (مطابقت با قوانین تجارت الکترونیک، حریم‌خصوصی، اینماد) دارد؟
- **Publish allowed:** فقط زمانی `YES` می‌شود که `Owner approval = APPROVED` و (در صورت نیاز) `Legal review = APPROVED` باشد.

---

## قاعده به‌روزرسانی

- این سند **تنها** همراه با PRهای محتوایی به‌روز می‌شود.
- هر بار که یک صفحه توسط مالک یا مشاور حقوقی تأیید شد، مقدار ستون متناظر در این جدول به `APPROVED` تغییر می‌کند.
- هیچ‌گاه صرفاً بر اساس این سند پلاگین‌ یا تغییری روی هاست اعمال نمی‌شود؛ اعمال روی هاست نیاز به مأموریت صریح مجزا دارد.

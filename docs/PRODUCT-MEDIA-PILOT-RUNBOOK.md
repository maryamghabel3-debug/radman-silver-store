# راهنمای پایلوت سه‌محصولی رسانه و تصویر رادمان

> این پایلوت فقط JSON، تصاویر اصلی، previewهای پس‌زمینه و گزارش QA می‌سازد. هیچ محصول یا تصویری را وارد WordPress نمی‌کند و هیچ محصولی را منتشر نمی‌کند.

## ۱. سیاست مدل و مجوز

### مدل production ترجیحی

```text
MODEL_NAME=birefnet-general-lite
```

fallback مجاز:

```text
MODEL_NAME=u2net
```

این allowlist بر اساس سیاست تأییدشده مالک برای pipeline فعلی است. مالک باید نسخه مدل و مستند مجوز استفاده تجاری را همراه سوابق پروژه نگه دارد.

### BRIA RMBG 2.0

BRIA در این پروژه **فقط evaluation داخلی** است و بدون مجوز تجاری BRIA نباید برای تصویر محصول منتشرشده استفاده شود. انتخاب آن فقط با هر دو متغیر زیر ممکن است:

```text
MODEL_NAME=bria-rmbg
IMAGE_PIPELINE_EVALUATION_ONLY=1
```

تمام خروجی‌های BRIA برچسب واضح زیر را داخل تصویر دارند:

```text
EVALUATION ONLY — NOT FOR COMMERCIAL PUBLICATION
```

این برچسب watermark تجاری نیست؛ گیت اجباری جلوگیری از انتشار خروجی evaluation است.

## ۲. آپلود دستی مدل مجاز

میزبان ایران نباید مدل را از GitHub دانلود کند. فایل را روی یک workstation مجاز تهیه و سپس با cPanel → File Manager آپلود کنید.

برای rembgهای جدید، مسیر پیش‌فرض مورد انتظار مدل ترجیحی معمولاً این است:

```text
/home/radmansi/.rembg/models/birefnet-general-lite/birefnet-general-lite.onnx
```

نام رسمی فایل منتشرشده مدل:

```text
BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx
```

پس از upload، فایل رسمی را در مسیر بالا به نام زیر rename کنید:

```text
birefnet-general-lite.onnx
```

نسخه‌های قدیمی rembg ممکن است مسیر flat زیر را استفاده کنند:

```text
/home/radmansi/.u2net/birefnet-general-lite.onnx
```

**مسیر را حدس نزنید.** ابتدا دستور `--plan` را اجرا کنید. agent کلاس session نسخه نصب‌شده rembg را inspect می‌کند و این موارد را چاپ می‌کند:

- expected filename؛
- expected absolute path؛
- official model filename؛
- همه candidate pathهای بررسی‌شده؛
- دستورالعمل upload مالک.

اگر مدل وجود نداشته باشد، processing متوقف می‌شود و هیچ download شبکه‌ای آغاز نمی‌شود.

### مسیر fallback U2Net

در rembg جدید معمولاً:

```text
/home/radmansi/.rembg/models/u2net/u2net.onnx
```

نام رسمی و نام مورد انتظار هر دو `u2net.onnx` هستند. باز هم خروجی `--plan` نسخه نصب‌شده مرجع نهایی است.

## ۳. پیش‌نیازهای private directory

خروجی‌ها فقط خارج web root نگه‌داری می‌شوند:

```text
/home/radmansi/.config/radman/legacy-cache/products/
/home/radmansi/.config/radman/legacy-cache/original-images/
/home/radmansi/.config/radman/processed-images/
/home/radmansi/.config/radman/outbox/media-qa/
```

`public_html` و production در runner رد می‌شوند.

## ۴. اجرای Plan

پس از refresh کردن ZIP ریپو در `/home/radmansi/radman-deploy/repo`:

```bash
export PATH="$HOME/bin:$PATH"; APP_ENV=staging MODEL_NAME=birefnet-general-lite RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman bash /home/radmansi/radman-deploy/repo/scripts/run_product_media_pilot.sh --plan
```

Plan هیچ network scrape، model download، image processing یا WordPress mutation انجام نمی‌دهد.

## ۵. اجرای پایلوت کامل سه محصول

پس از اینکه plan وجود مدل را `YES` اعلام کرد، این یک دستور را اجرا کنید:

```bash
export PATH="$HOME/bin:$PATH"; APP_ENV=staging MODEL_NAME=birefnet-general-lite RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman bash /home/radmansi/radman-deploy/repo/scripts/run_product_media_pilot.sh --full-pilot
```

runner:

1. robots.txt را بررسی می‌کند؛
2. با User-Agent معرفی‌شده و فاصله حداقل ۲ ثانیه request می‌فرستد؛
3. به‌صورت کنترل‌شده یک محصول نماینده از هر دسته انگشتر، گردنبند/مدال و دستبند کشف می‌کند (قابلیت sitemap نیز در agent موجود است)؛
4. JSON و تصاویر اصلی را در private dir ذخیره می‌کند؛
5. session محلی explicit برای مدل انتخابی می‌سازد؛
6. mask را بدون بازسازی محصول استخراج می‌کند؛
7. سه پس‌زمینه QA می‌سازد؛
8. contact sheet و گزارش QA ایجاد می‌کند؛
9. متوقف می‌شود تا مالک بازبینی کند.

اجرای جداگانه مراحل:

```bash
APP_ENV=staging RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman bash /home/radmansi/radman-deploy/repo/scripts/run_product_media_pilot.sh --scrape-three
```

```bash
APP_ENV=staging MODEL_NAME=birefnet-general-lite RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman bash /home/radmansi/radman-deploy/repo/scripts/run_product_media_pilot.sh --process-three
```

## ۶. خروجی تصاویر

برای هر تصویر اصلی سه فایل 1600×1600 WebP با quality 85 ساخته می‌شود:

- `matte-black` — مشکی مات؛
- `black-velvet-gradient` — گرادیان مخمل مشکی؛
- `dark-neutral-studio` — استودیوی خنثی تیره.

فقط این تغییرات presentation مجازند:

- alpha mask پس‌زمینه؛
- scale یکنواخت برای قرارگیری در canvas؛
- پس‌زمینه غیرمولد؛
- سایه بسیار ملایم زیر محصول.

هندسه، سنگ، حکاکی، بازتاب و فلزکاری reconstruct/redraw/inpaint نمی‌شوند. RGB محصول از تصویر اصلی گرفته می‌شود.

## ۷. مشاهده Contact Sheet

در cPanel مسیر زیر را باز کنید:

```text
/home/radmansi/.config/radman/outbox/media-qa/
```

هر contact sheet چهار ستون دارد:

1. ORIGINAL؛
2. MATTE BLACK؛
3. BLACK VELVET؛
4. DARK STUDIO.

فایل aggregate:

```text
media-qa-report.json
```

برای هر source image این اطلاعات ثبت می‌شود:

- URL و ابعاد اصلی؛
- مدل و مدت پردازش؛
- اندازه فایل‌های خروجی؛
- bounding box ماسک؛
- تماس محصول با لبه؛
- warning لبه‌های نازک/سنگ؛
- `PASS / REVIEW / REJECT`.

## ۸. تأیید یا رد مالک

برای هر تصویر:

- سنگ‌ها و چنگ‌ها کامل هستند؟
- لبه باریک رکاب/زنجیر حذف نشده؟
- حکاکی و بافت فلز بدون تغییر است؟
- بازتاب واقعی محصول حفظ شده؟
- هیچ بخش محصول با لبه crop نشده؟
- سایه فقط زیر محصول است؟

تصمیم را مطابق `docs/PRODUCT-MEDIA-APPROVAL-SCHEMA.md` ثبت کنید. `REVIEW` نیازمند بازبینی انسانی و `REJECT` غیرقابل import خودکار است.

## ۹. عکس روی دست و زاویه جدید

- عکس in-hand باید واقعاً عکاسی شود.
- زاویه‌ای که در source وجود ندارد باید واقعاً عکاسی شود.
- agent اجازه hallucinate کردن زاویه جدید، دست مصنوعی یا lifestyle جعلی ندارد.
- یک تصویر محصول منبع مجاز ساخت نمای پشت/بغل خیالی نیست.

## ۱۰. WordPress

این مأموریت هیچ import انجام نمی‌دهد. حتی `PASS` و تأیید مالک نیز فقط contract مرحله بعد را آماده می‌کند. ورود تصویر/محصول به WordPress باید در یک مأموریت جداگانه و صریحاً تأییدشده انجام شود.

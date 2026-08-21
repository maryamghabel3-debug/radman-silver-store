# راهنمای پردازش محافظه‌کارانه تصاویر اصلی محصول

**بازبینی:** `2026-08-21, Asia/Tehran`
**ابزار مصوب:** `agents/agent_original_image_processor.py`

## اصل غیرقابل‌مذاکره

تصویر قدیمی یک سند واقعی محصول است. رنگ نگین، رنگ فلز، حکاکی، هندسه، انعکاس، دست/انگشت و پس‌زمینه باید بصری دست‌نخورده بمانند. اولویت کیفیت و صحت رنگ از کاهش حجم فایل بالاتر است.

مسیر مصوب هرگز background را حذف یا عوض نمی‌کند، crop مخرب انجام نمی‌دهد، دست/انگشت/جواهر را قطع نمی‌کند، زاویه جدید نمی‌سازد و از image generation، reconstruction یا segmentation model استفاده نمی‌کند. ابزارهای آزمایشی BRIA/BiRefNet و rembg در این pipeline فراخوانی نمی‌شوند.

## آرشیو منبع

بایت‌های دانلودشده بدون تغییر در مسیر زیر ذخیره می‌شوند:

```text
RADMAN_PRIVATE_DIR/legacy-cache/original-images/<legacy_id>/
```

برای هر فایل SHA-256، URL و ترتیب gallery ثبت می‌شود. پردازشگر checksum قبل و بعد را مقایسه می‌کند و هیچ‌گاه فایل source را overwrite نمی‌کند.

## تبدیل مجاز

1. `EXIF transpose` برای orientation صحیح؛
2. resize با حفظ aspect ratio تا حداکثر ضلع `1600px`؛
3. بدون crop و بدون upscale عادی؛ hard ceiling بزرگ‌نمایی `1.25x` است؛
4. WebP با quality `90` (در محدوده مصوب 88–92)؛
5. sharpen بسیار خفیف فقط روی luminance با chroma دست‌نخورده؛ قابل غیرفعال‌سازی؛
6. حفظ ICC profile در صورت پشتیبانی source/encoder؛
7. حفظ alpha در فایل‌های دارای شفافیت.

خروجی candidate در مسیر زیر نوشته می‌شود:

```text
RADMAN_PRIVATE_DIR/legacy-cache/processed-images/<legacy_id>/
```

## gate خودکار

candidate پس از encode دوباره decode و در ابعاد یکسان با reference مقایسه می‌شود:

| معیار | حد پذیرش |
|---|---:|
| Mean absolute RGB drift | `<= 6.0` سطح RGB |
| صدک ۹۵ drift | `<= 20.0` |
| بیشترین drift میانگین channel | `<= 3.0` |
| نسبت detail energy | `0.72 .. 1.30` |
| ابعاد/aspect | باید دقیقاً با resize محاسبه‌شده برابر باشد |
| ICC موجود در source | باید در output حفظ شود |
| checksum source | نباید تغییر کند |

هر failure نتیجه `FAIL` می‌دهد و `selected_import_path` به **original دست‌نخورده** برمی‌گردد. رنگ مشکوک هرگز با صرفه‌جویی حجم توجیه نمی‌شود.

## contact sheet و بازبینی انسانی

برای هر محصول یک sheet دو ستونه در `runs/<timestamp>/image-qa/` تولید می‌شود:

- چپ: BEFORE و بخشی از SHA-256؛
- راست: AFTER، PASS/FAIL، fallback، drift و detail ratio.

بازبین باید به‌ویژه نگین، نقره، حکاکی، لبه‌ها، انعکاس‌ها، پوست، انگشت و پس‌زمینه را در zoom کامل بررسی کند. sheet جایگزین مشاهده فایل اصلی نیست.

## اجرای مستقل

```sh
python3 agents/agent_original_image_processor.py \
  --input /private/path/scrape.json \
  --output /private/path/image-qa.json \
  --private-dir /home/radmansi/private
```

برای غیرفعال کردن sharpen مجاز:

```sh
python3 agents/agent_original_image_processor.py ... --no-sharpen
```

Exit code `2` یعنی دست‌کم یک candidate رد شده است؛ original fallback در گزارش ثبت می‌شود. پیش از import، گزارش و sheet را بررسی کنید.

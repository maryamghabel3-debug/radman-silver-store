# قرارداد داده import محصولات رادمان

این سند قرارداد رسمی فایل ورودی `RADMAN_PRIVATE_DIR/import/products.csv` و معادل JSON آن را تعریف می‌کند. ارز تمام قیمت‌ها **تومان (IRT direct input)** است؛ هیچ تبدیل ریال/تومان در importer انجام نمی‌شود.

## ۱. قواعد فایل CSV

- Encoding: `UTF-8` یا `UTF-8 with BOM`
- جداکننده ستون: comma (`,`)
- جداکننده چند تصویر در یک cell: pipe (`|`)
- حداکثر امن هر اجرا: ۵۰۰ ردیف محصول
- سطر اول باید دقیقاً headerهای زیر را داشته باشد؛ ستون اضافی نادیده گرفته می‌شود.
- SKUهای فایل نمونه با `SAMPLE-` شروع می‌شوند و عمداً توسط importer رد می‌شوند.

```text
sku,title_fa,category,weight_grams,silver_purity,stone_type,stone_value_toman,pricing_mode,stock,legacy_price_toman,manual_price_toman,short_description,long_description,image_filenames
```

## ۲. تعریف فیلدها

| فیلد | نوع | اجباری | قواعد |
|---|---|---:|---|
| `sku` | string | بله | یکتا؛ الگوی `RAD-(RNG|NEC|BRC)-(W|M|U)-NNNN` |
| `title_fa` | string | بله | عنوان فارسی محصول؛ بدون عبارت SAMPLE |
| `category` | enum | بله | فقط `rings`, `necklaces`, `bracelets` |
| `weight_grams` | decimal | شرطی | وزن خالص نقره؛ برای دو mode وزن‌محور عدد مثبت |
| `silver_purity` | integer | بله | در این فاز دقیقاً `925` |
| `stone_type` | string | شرطی | برای `silver_weight_plus_stone` اجباری |
| `stone_value_toman` | integer | شرطی | ارزش ثابت نگین؛ برای mode وزن+نگین مثبت و اجباری |
| `pricing_mode` | enum | بله | یکی از ۴ mode رسمی |
| `stock` | integer | خیر | پیش‌فرض `1`؛ مقدار non-negative عیناً و بدون buffer ثبت می‌شود |
| `legacy_price_toman` | integer | شرطی | قیمت صریح تومان برای `legacy_mirror` |
| `manual_price_toman` | integer | شرطی | قیمت صریح تومان برای `manual_locked` |
| `short_description` | string | بله | خلاصه انسانی و مخصوص همان محصول |
| `long_description` | string | بله | توضیح کامل بازبینی‌شده؛ cell دارای comma/newline باید quote شود |
| `image_filenames` | string | خیر | filenameهای محلی با `|`؛ فقط JPG/JPEG/PNG/WebP، بدون path یا URL |

دو ستون قیمت صریح به قرارداد پایه اضافه شده‌اند، زیرا حالت‌های `legacy_mirror` و `manual_locked` بدون آن‌ها قیمت قابل اعمال ندارند.

## ۳. تطابق SKU و دسته

| category | کد SKU | دسته WooCommerce staging |
|---|---|---:|
| `rings` | `RNG` | 17 |
| `necklaces` | `NEC` | 18 |
| `bracelets` | `BRC` | 19 |

مثال معتبر: `RAD-RNG-M-1045`. اگر کد SKU و ستون category هم‌خوان نباشند، کل import قبل از mutation متوقف می‌شود.

## ۴. قواعد قیمت‌گذاری

| mode | فیلدهای لازم | قیمت import |
|---|---|---|
| `silver_weight_only` | `weight_grams` + نرخ روز | `weight × daily_rate`، گرد به نزدیک‌ترین ۱۰٬۰۰۰ تومان (half-up) |
| `silver_weight_plus_stone` | وزن + نرخ + نوع/ارزش نگین | `(weight × daily_rate) + stone_value_toman`، به تومان کامل |
| `legacy_mirror` | `legacy_price_toman` | همان عدد صریح، بدون تبدیل |
| `manual_locked` | `manual_price_toman` | همان عدد صریح؛ متای `price_locked=1` |

نرخ روز از فایل زیر خوانده می‌شود:

```text
$RADMAN_PRIVATE_DIR/state/daily_rate.txt
```

این فایل باید فقط یک عدد صحیح مثبت (تومان بر گرم) داشته باشد. اگر CSV فقط modeهای legacy/manual داشته باشد، نرخ روز لازم نیست.

## ۵. قرارداد تصاویر

نمونه cell:

```text
RAD-RNG-M-1045-front.jpg|RAD-RNG-M-1045-side.jpg
```

فایل‌ها باید توسط مالک در مسیر زیر قرار بگیرند:

```text
$RADMAN_PRIVATE_DIR/import/images/
```

قواعد امنیتی:

- URL خارجی پذیرفته نمی‌شود.
- `../` یا subdirectory پذیرفته نمی‌شود.
- نبود فایل، warning تولید می‌کند و محصول بدون آن تصویر ادامه می‌یابد.
- filename باید در کل CSV یکتا و ترجیحاً با SKU آغاز شود.
- کلید `SKU|filename` در attachment meta ثبت می‌شود تا اجرای مجدد تصویر تکراری نسازد یا تصویر محصول دیگری را reparent نکند.
- importer هیچ تصویر legacy را دانلود نمی‌کند.

## ۶. رفتار idempotent

- کلید تطبیق فقط `sku` است.
- SKU جدید → محصول Simple با وضعیت `draft`.
- SKU موجود → همان محصول update می‌شود و وضعیت فعلی آن حفظ می‌شود.
- قیمت، stock، توضیحات و metaهای import طبق CSV reconcile می‌شوند.
- دسته مقصد برای محصول جدید ثبت؛ برای محصول موجود به دسته‌های فعلی اضافه می‌شود.
- تصویر featured اولین filename و gallery بقیه filenameهای موجود است.

## ۷. معادل JSON

JSON در این مأموریت ورودی اجرایی نیست، اما قرارداد معادل برای ابزارهای آماده‌سازی آینده چنین است:

```json
{
  "sku": "RAD-RNG-M-1045",
  "title_fa": "انگشتر نقره ۹۲۵ مردانه",
  "category": "rings",
  "weight_grams": 6.8,
  "silver_purity": 925,
  "stone_type": "",
  "stone_value_toman": null,
  "pricing_mode": "silver_weight_only",
  "stock": 1,
  "legacy_price_toman": null,
  "manual_price_toman": null,
  "short_description": "خلاصه محصول تأییدشده مالک",
  "long_description": "توضیح کامل و اختصاصی محصول",
  "image_filenames": [
    "RAD-RNG-M-1045-front.jpg",
    "RAD-RNG-M-1045-side.jpg"
  ]
}
```

## ۸. فایل نمونه

فایل `templates/product-import-sample.csv` سه ردیف آموزشی دارد. آن فایل داده واقعی نیست و مستقیم import نمی‌شود. مالک باید آن را کپی کند، پیشوند `SAMPLE-` و متن‌های نمونه را حذف/جایگزین کند و سپس فایل نهایی را در private dir قرار دهد.

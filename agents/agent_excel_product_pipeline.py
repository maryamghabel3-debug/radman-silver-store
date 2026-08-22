#!/usr/bin/env python3
"""Excel-driven newest-product Draft pipeline for RADMAN SILVER.

Excel is the sole catalog-data source. Public legacy pages are consulted only to
locate and download original gallery images. Imports are create-only Drafts.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import io
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal, ROUND_FLOOR
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.agent_legacy_catalog_pilot import (  # noqa: E402
    BASE_URL,
    MAX_IMAGE_BYTES,
    RateLimitedFetcher,
    iri_to_uri,
    parse_product_links,
    parse_sitemap_urls,
)
from agents.agent_original_image_processor import process_product  # noqa: E402
from agents.lib.legacy_pricing import round_up_toman  # noqa: E402
from scripts.analyze_excel_catalog import (  # noqa: E402
    COL_ACTIVE,
    COL_AVAILABILITY,
    COL_CATEGORY,
    COL_ID,
    COL_PRICE,
    COL_TITLE,
    COL_WEIGHT,
    SHEET_NAME,
    display_text,
    is_blank,
    normalize_availability,
    normalize_text,
    parse_active,
    parse_decimal,
    parse_id,
)
from scripts.import_products import WPGateway, WPCliError  # noqa: E402

DEFAULT_EXCEL_FILE = Path(
    "/home/radmansi/radman-deploy/products_20260821_182238.xlsx"
)
DEFAULT_MAX_PRODUCTS = 1000
HARD_MAX_PRODUCTS = 1000
EXPECTED_APP_ENV = "staging"
EXPECTED_WP_URL = "https://staging.radmansilver.ir"
EXPECTED_WP_PATH = "/home/radmansi/staging.radmansilver.ir"
REQUIRED_CURRENCY = "IRT"
API_SLOT = Path("/home/radmansi/.config/radman/api-keys/legacy-site.env")
PIPELINE_VERSION = "PR-28"
EXCEL_IMAGE_USER_AGENT = (
    "RadmanSilverExcelImageImporter/1.0 "
    "(+https://radmansilver.ir; owner-controlled original-gallery migration)"
)
TEHRAN = ZoneInfo("Asia/Tehran")

COL_PRE_DISCOUNT_PRICE = 10
COL_STOCK = 11
COL_RAW_CODE = 27
COL_SEO_TITLE = 28
COL_SEO_DESCRIPTION = 29
MIN_REQUIRED_COLUMNS = 29

STANDARD_RATE = 650_000
LARGE_STONE_RATE = 590_000
ROUNDING_STEP = 50_000
TITLE_CODE_RE = re.compile(r"کد\s*([0-9۰-۹٠-٩]{2,8})")
LARGE_STONE_RE = re.compile(
    r"(?:(?:نگین|عقیق).{0,20}(?:درشت|بزرگ)|(?:درشت|بزرگ).{0,20}(?:نگین|عقیق))"
)
NO_STONE_RE = re.compile(r"(?:بدون|فاقد|بی)\s*(?:نگین|سنگ)")

REPORT_COLUMNS = (
    "legacy_id",
    "sku",
    "sku_source",
    "title",
    "category_raw",
    "category",
    "weight_grams",
    "excel_price_toman",
    "pre_discount_price_toman",
    "computed_price_toman",
    "final_price_toman",
    "regular_price_toman",
    "sale_price_toman",
    "price_source",
    "rate_used",
    "stone_class",
    "stock",
    "images_found",
    "image_status",
    "image_discovery_strategy",
    "legacy_url",
    "action",
    "review_flags",
    "wordpress_product_id",
)


class ExcelPipelineError(RuntimeError):
    pass


@dataclass(frozen=True)
class PricingDecision:
    stone_class: str
    rate_used: int
    excel_price_toman: Optional[int]
    computed_price_toman: Optional[Decimal]
    final_price_toman: Optional[int]
    pre_discount_price_toman: Optional[int]
    regular_price_toman: Optional[int]
    sale_price_toman: Optional[int]
    price_source: str
    review_flags: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        if self.computed_price_toman is not None:
            value["computed_price_toman"] = format(
                self.computed_price_toman, "f"
            )
        value["review_flags"] = list(self.review_flags)
        return value


@dataclass(frozen=True)
class SKUDecision:
    sku: str
    source: str
    raw_code: str


class GalleryHTMLParser(HTMLParser):
    """Collect ordered same-page image candidates without parsing product data."""

    def __init__(self, page_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.candidates: List[str] = []

    @staticmethod
    def _attrs(attrs: Sequence[Tuple[str, Optional[str]]]) -> Dict[str, str]:
        return {key.lower(): value or "" for key, value in attrs}

    def _add(self, value: str) -> None:
        value = html.unescape(str(value or "")).strip()
        if value:
            self.candidates.append(urllib.parse.urljoin(self.page_url, value))

    def handle_starttag(
        self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]
    ) -> None:
        values = self._attrs(attrs)
        if tag == "img":
            for key in (
                "data-large_image",
                "data-zoom-image",
                "data-src",
                "data-lazy-src",
                "src",
            ):
                if values.get(key):
                    self._add(values[key])
                    break
            srcset = values.get("srcset") or values.get("data-srcset")
            if srcset:
                entries = []
                for item in srcset.split(","):
                    parts = item.strip().split()
                    if not parts:
                        continue
                    width = 0
                    if len(parts) > 1 and parts[1].lower().endswith("w"):
                        try:
                            width = int(parts[1][:-1])
                        except ValueError:
                            width = 0
                    entries.append((width, parts[0]))
                if entries:
                    self._add(max(entries, key=lambda item: item[0])[1])
        elif tag == "a":
            href = values.get("href", "")
            if re.search(r"\.(?:jpe?g|png|webp)(?:[?#]|$)", href, re.I):
                self._add(href)
        elif tag == "meta":
            key = (values.get("property") or values.get("name") or "").lower()
            if key in {"og:image", "twitter:image"}:
                self._add(values.get("content", ""))


def _cell(values: Sequence[Any], one_based_column: int) -> Any:
    index = one_based_column - 1
    return values[index] if index < len(values) else None


def _raw_trace(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _positive_toman(value: Any) -> Optional[int]:
    parsed = parse_decimal(value)
    if parsed is None or parsed <= 0:
        return None
    return int(parsed.to_integral_value(rounding=ROUND_FLOOR))


def parse_weight(value: Any) -> Optional[Decimal]:
    parsed = parse_decimal(value, decimal_comma=True)
    if parsed is None or parsed <= 0 or parsed > Decimal("500"):
        return None
    return parsed


def parse_stock(value: Any) -> Tuple[int, Tuple[str, ...]]:
    parsed = parse_decimal(value)
    if parsed is None:
        return 0, ("STOCK_MISSING_OR_INVALID",)
    if parsed < 0:
        return 0, ("STOCK_NEGATIVE_CLAMPED_TO_ZERO",)
    if parsed != parsed.to_integral_value():
        return int(parsed.to_integral_value(rounding=ROUND_FLOOR)), (
            "STOCK_FRACTION_FLOORED",
        )
    return int(parsed), tuple()


def _normalized_digits(value: str) -> str:
    return normalize_text(value).replace(" ", "")


def derive_sku(title: str, raw_code: Any, legacy_id: int) -> SKUDecision:
    normalized_title = normalize_text(title)
    title_match = TITLE_CODE_RE.search(normalized_title)
    if title_match:
        code = _normalized_digits(title_match.group(1))
        return SKUDecision(code, "TITLE_CODE", _raw_trace(raw_code))

    valid_code: Optional[str] = None
    if isinstance(raw_code, bool):
        valid_code = None
    elif isinstance(raw_code, int):
        if 0 < raw_code < 100_000:
            valid_code = str(raw_code)
    elif isinstance(raw_code, Decimal):
        raw_text = format(raw_code, "f")
        if "." not in raw_text and raw_text.isdigit() and int(raw_text) < 100_000:
            valid_code = raw_text
    elif isinstance(raw_code, float):
        # A floating-point cell has already violated the "no decimal point" rule.
        valid_code = None
    else:
        raw_text = normalize_text(raw_code).replace(" ", "")
        if re.fullmatch(r"[0-9]+", raw_text) and 0 < int(raw_text) < 100_000:
            valid_code = raw_text
    if valid_code:
        return SKUDecision(valid_code, "COL27_VALIDATED", _raw_trace(raw_code))
    return SKUDecision(f"NM-{legacy_id}", "FALLBACK_LEGACY_ID", _raw_trace(raw_code))


def classify_stone_from_title(title: str) -> str:
    normalized = normalize_text(title)
    if NO_STONE_RE.search(normalized):
        return "no_stone"
    if LARGE_STONE_RE.search(normalized):
        return "large_stone"
    return "uncertain"


def calculate_pricing(
    *,
    title: str,
    excel_price: Any,
    pre_discount_price: Any,
    weight: Optional[Decimal],
) -> PricingDecision:
    flags: List[str] = []
    current = _positive_toman(excel_price)
    pre_discount = _positive_toman(pre_discount_price)
    stone_class = classify_stone_from_title(title)
    rate = LARGE_STONE_RATE if stone_class == "large_stone" else STANDARD_RATE
    computed: Optional[Decimal] = None
    final: Optional[int] = None
    price_source = "INVALID_REVIEW"

    if current is None:
        flags.append("EXCEL_PRICE_MISSING_OR_INVALID")
    elif weight is None:
        final = round_up_toman(Decimal(current), ROUNDING_STEP)
        price_source = "EXCEL_ONLY"
    else:
        computed = weight * Decimal(rate)
        if Decimal(current) >= computed:
            selected = Decimal(current)
            price_source = "MAX_EXCEL"
        else:
            selected = computed
            price_source = "MAX_CALCULATED"
        final = round_up_toman(selected, ROUNDING_STEP)

    regular: Optional[int] = None
    sale: Optional[int] = None
    if final is not None:
        if pre_discount is not None and pre_discount > final:
            regular = pre_discount
            sale = final
        else:
            regular = final
            sale = None

    return PricingDecision(
        stone_class=stone_class,
        rate_used=rate,
        excel_price_toman=current,
        computed_price_toman=computed,
        final_price_toman=final,
        pre_discount_price_toman=pre_discount,
        regular_price_toman=regular,
        sale_price_toman=sale,
        price_source=price_source,
        review_flags=tuple(flags),
    )


def map_category(raw_category: str) -> Tuple[str, Tuple[str, ...]]:
    value = normalize_text(raw_category)
    if "انگشتر" in value:
        return "rings", tuple()
    if "گردنبند" in value or "مدال" in value:
        return "necklaces", tuple()
    if "دستبند" in value:
        return "bracelets", tuple()
    return "rings", ("UNKNOWN_CATEGORY_DEFAULTED_TO_RINGS",)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def load_excel_records(
    excel_path: Path,
    *,
    sheet_name: str = SHEET_NAME,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ExcelPipelineError(
            "کتابخانه openpyxl نصب نیست؛ اجرا کنید: python3 -m pip install --user openpyxl"
        ) from exc

    path = excel_path.expanduser().resolve()
    if not path.is_file():
        raise ExcelPipelineError(f"فایل Excel پیدا نشد: {path}")
    if "public_html" in str(path):
        raise ExcelPipelineError("خواندن Excel از public_html ممنوع است")
    try:
        workbook = load_workbook(
            path, read_only=True, data_only=True, keep_links=False
        )
    except Exception as exc:
        raise ExcelPipelineError(f"خواندن Excel ناموفق بود: {exc}") from exc
    warnings: List[str] = []
    records: List[Dict[str, Any]] = []
    try:
        if sheet_name not in workbook.sheetnames:
            raise ExcelPipelineError(
                f"شیت «{sheet_name}» وجود ندارد؛ موجود: {', '.join(workbook.sheetnames)}"
            )
        worksheet = workbook[sheet_name]
        if worksheet.max_column < MIN_REQUIRED_COLUMNS:
            raise ExcelPipelineError(
                f"شیت {worksheet.max_column} ستون دارد؛ حداقل {MIN_REQUIRED_COLUMNS} لازم است"
            )
        for excel_row, values in enumerate(
            worksheet.iter_rows(min_row=2, values_only=True), start=2
        ):
            if all(is_blank(value) for value in values):
                continue
            legacy_id = parse_id(_cell(values, COL_ID))
            if legacy_id is None:
                warnings.append(f"ROW_{excel_row}_INVALID_LEGACY_ID")
                continue
            title = display_text(_cell(values, COL_TITLE)) or f"محصول {legacy_id}"
            raw_category = display_text(_cell(values, COL_CATEGORY))
            availability = normalize_availability(_cell(values, COL_AVAILABILITY))
            active = parse_active(_cell(values, COL_ACTIVE))
            weight_raw = _cell(values, COL_WEIGHT)
            weight = parse_weight(weight_raw)
            raw_code = _cell(values, COL_RAW_CODE)
            sku = derive_sku(title, raw_code, legacy_id)
            stock, stock_flags = parse_stock(_cell(values, COL_STOCK))
            category, category_flags = map_category(raw_category)
            pricing = calculate_pricing(
                title=title,
                excel_price=_cell(values, COL_PRICE),
                pre_discount_price=_cell(values, COL_PRE_DISCOUNT_PRICE),
                weight=weight,
            )
            review_flags = list(stock_flags)
            review_flags.extend(category_flags)
            review_flags.extend(pricing.review_flags)
            if not is_blank(weight_raw) and weight is None:
                review_flags.append("WEIGHT_PRESENT_BUT_INVALID")
            description = display_text(_cell(values, COL_SEO_DESCRIPTION))
            seo_title = display_text(_cell(values, COL_SEO_TITLE))
            records.append(
                {
                    "excel_row": excel_row,
                    "legacy_id": legacy_id,
                    "title": title,
                    "category_raw": raw_category,
                    "category": category,
                    "excel_price_toman": pricing.excel_price_toman,
                    "pre_discount_price_toman": pricing.pre_discount_price_toman,
                    "weight_grams": format(weight, "f") if weight is not None else None,
                    "weight_missing": weight is None,
                    "stock": stock,
                    "availability": availability,
                    "active": active,
                    "raw_code": sku.raw_code,
                    "sku": sku.sku,
                    "sku_source": sku.source,
                    "seo_title": seo_title,
                    "description": description or seo_title or title,
                    "stone_class": pricing.stone_class,
                    "rate_used": pricing.rate_used,
                    "computed_price_toman": (
                        format(pricing.computed_price_toman, "f")
                        if pricing.computed_price_toman is not None
                        else None
                    ),
                    "final_price_toman": pricing.final_price_toman,
                    "regular_price_toman": pricing.regular_price_toman,
                    "sale_price_toman": pricing.sale_price_toman,
                    "price_source": pricing.price_source,
                    "review_flags": list(dict.fromkeys(review_flags)),
                    "eligible": bool(active is True and availability != "ناموجود"),
                    "legacy_url": "",
                    "image_urls": [],
                    "original_image_paths": [],
                    "selected_import_paths": [],
                    "images_found": 0,
                    "image_status": "NOT_FETCHED",
                    "image_discovery_strategy": "NOT_RUN",
                    "image_qa": None,
                    "action": "UNSELECTED",
                    "wordpress_product_id": None,
                }
            )
    finally:
        workbook.close()
    if not records:
        raise ExcelPipelineError("هیچ محصول معتبر در Excel پیدا نشد")
    return records, warnings


def select_newest(
    records: Sequence[Dict[str, Any]], max_products: int
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    if max_products < 1 or max_products > HARD_MAX_PRODUCTS:
        raise ExcelPipelineError(
            f"MAX_PRODUCTS باید بین 1 و {HARD_MAX_PRODUCTS} باشد"
        )
    ordered = sorted(
        (dict(record) for record in records),
        key=lambda record: (-int(record["legacy_id"]), int(record["excel_row"])),
    )
    inactive = sum(record.get("active") is not True for record in ordered)
    unavailable = sum(
        record.get("active") is True and record.get("availability") == "ناموجود"
        for record in ordered
    )
    eligible = [record for record in ordered if record.get("eligible")]
    selected = eligible[:max_products]
    seen_skus: set[str] = set()
    seen_ids: set[int] = set()
    for record in selected:
        legacy_id = int(record["legacy_id"])
        sku_key = str(record["sku"]).casefold()
        if legacy_id in seen_ids:
            record["action"] = "SKIP_DUPLICATE_BATCH_LEGACY_ID"
            record["review_flags"] = list(
                dict.fromkeys(
                    [*record["review_flags"], "DUPLICATE_BATCH_LEGACY_ID"]
                )
            )
        elif sku_key in seen_skus:
            record["action"] = "SKIP_DUPLICATE_BATCH_SKU"
            record["review_flags"] = list(
                dict.fromkeys([*record["review_flags"], "DUPLICATE_BATCH_SKU"])
            )
        elif record.get("final_price_toman") is None:
            record["action"] = "SKIP_INVALID_PRICE"
        else:
            record["action"] = "PLAN_CREATE_DRAFT"
        seen_ids.add(legacy_id)
        seen_skus.add(sku_key)
    summary = {
        "excel_rows": len(ordered),
        "inactive_skipped": inactive,
        "unavailable_skipped": unavailable,
        "eligible_rows": len(eligible),
        "selected_rows": len(selected),
    }
    return selected, summary


def _canonical_image_url(url: str) -> Optional[str]:
    parsed = urllib.parse.urlsplit(iri_to_uri(url))
    if parsed.scheme not in {"http", "https"} or parsed.hostname != "noghrehmashhad.ir":
        return None
    path = re.sub(
        r"-\d{2,5}x\d{2,5}(?=\.(?:jpe?g|png|webp)$)",
        "",
        parsed.path,
        flags=re.I,
    )
    if not re.search(r"\.(?:jpe?g|png|webp)$", path, re.I):
        return None
    return urllib.parse.urlunsplit(("https", parsed.netloc, path, "", ""))


def extract_gallery_urls(page_url: str, source_html: str) -> List[str]:
    parser = GalleryHTMLParser(page_url)
    parser.feed(source_html)
    targeted: List[str] = []
    fallback: List[str] = []
    seen: set[str] = set()
    for candidate in parser.candidates:
        canonical = _canonical_image_url(candidate)
        if not canonical or canonical in seen:
            continue
        seen.add(canonical)
        path = urllib.parse.urlsplit(canonical).path.casefold()
        basename = Path(path).name.casefold()
        if any(token in basename for token in ("logo", "icon", "avatar", "placeholder")):
            continue
        if any(
            token in path
            for token in (
                "product-images",
                "product_images",
                "/products/",
                "/product/",
                "/uploads/",
            )
        ):
            targeted.append(canonical)
        else:
            fallback.append(canonical)
    if targeted:
        return targeted
    product_marker = re.search(
        r"product[-_ ]gallery|woocommerce-product-gallery|[\"']@type[\"']\s*:\s*[\"']Product[\"']",
        source_html,
        re.I,
    )
    return fallback if product_marker else []


def _links_for_legacy_id(page_url: str, source_html: str, legacy_id: int) -> List[str]:
    discovered = parse_product_links(page_url, source_html)
    hrefs = re.findall(r"href=[\"']([^\"']+)[\"']", source_html, re.I)
    discovered.extend(urllib.parse.urljoin(page_url, html.unescape(href)) for href in hrefs)
    result = []
    for url in discovered:
        parsed = urllib.parse.urlsplit(url)
        if parsed.hostname != "noghrehmashhad.ir":
            continue
        if re.search(rf"/(?:product|p)/{legacy_id}(?:/|$)", parsed.path) or (
            urllib.parse.parse_qs(parsed.query).get("product_id") == [str(legacy_id)]
        ):
            result.append(urllib.parse.urlunsplit(("https", parsed.netloc, parsed.path, parsed.query, "")))
    return list(dict.fromkeys(result))


class LegacyImageDiscovery:
    def __init__(self, fetcher: Optional[RateLimitedFetcher] = None) -> None:
        self.fetcher = fetcher or RateLimitedFetcher(
            user_agent=EXCEL_IMAGE_USER_AGENT
        )
        self._robots_loaded = False
        self._sitemap_by_id: Optional[Dict[int, List[str]]] = None
        self.log: List[Dict[str, Any]] = []

    def load_robots(self) -> None:
        if not self._robots_loaded:
            self.fetcher.load_robots()
            self._robots_loaded = True

    def _try_page(
        self, url: str, strategy: str, legacy_id: int
    ) -> Optional[Tuple[str, List[str], str]]:
        try:
            source = self.fetcher.fetch_text(url)
        except (OSError, urllib.error.URLError, RuntimeError) as exc:
            self.log.append(
                {
                    "legacy_id": legacy_id,
                    "strategy": strategy,
                    "url": url,
                    "status": "ERROR",
                    "detail": str(exc),
                }
            )
            return None
        images = extract_gallery_urls(url, source)
        self.log.append(
            {
                "legacy_id": legacy_id,
                "strategy": strategy,
                "url": url,
                "status": "FOUND" if images else "NO_GALLERY",
                "images": len(images),
            }
        )
        if images:
            return url, images, strategy
        return None

    def _load_sitemaps(self) -> Dict[int, List[str]]:
        if self._sitemap_by_id is not None:
            return self._sitemap_by_id
        mapping: Dict[int, List[str]] = {}
        queue = [f"{BASE_URL}/sitemap.xml"]
        fetched: set[str] = set()
        while queue and len(fetched) < 40:
            sitemap = queue.pop(0)
            if sitemap in fetched:
                continue
            fetched.add(sitemap)
            try:
                content = self.fetcher.fetch_text(sitemap)
            except (OSError, urllib.error.URLError, RuntimeError):
                continue
            for url in parse_sitemap_urls(content):
                if url.lower().endswith(".xml") or "sitemap" in url.lower():
                    if urllib.parse.urlsplit(url).hostname == "noghrehmashhad.ir":
                        queue.append(url)
                    continue
                match = re.search(r"/(?:product|p)/([0-9]+)(?:/|$)", url)
                if match:
                    mapping.setdefault(int(match.group(1)), []).append(url)
        self._sitemap_by_id = mapping
        return mapping

    def discover(self, legacy_id: int) -> Tuple[str, List[str], str]:
        self.load_robots()
        direct = (
            f"{BASE_URL}/product/{legacy_id}/",
            f"{BASE_URL}/product/{legacy_id}",
            f"{BASE_URL}/p/{legacy_id}/",
            f"{BASE_URL}/?product_id={legacy_id}",
        )
        for url in direct:
            result = self._try_page(url, "DIRECT_ID_PATTERN", legacy_id)
            if result:
                return result

        for search_url in (
            f"{BASE_URL}/search?q={legacy_id}",
            f"{BASE_URL}/?s={legacy_id}",
        ):
            try:
                search_html = self.fetcher.fetch_text(search_url)
            except (OSError, urllib.error.URLError, RuntimeError) as exc:
                self.log.append(
                    {
                        "legacy_id": legacy_id,
                        "strategy": "SITE_SEARCH",
                        "url": search_url,
                        "status": "ERROR",
                        "detail": str(exc),
                    }
                )
                continue
            for product_url in _links_for_legacy_id(
                search_url, search_html, legacy_id
            ):
                result = self._try_page(product_url, "SITE_SEARCH", legacy_id)
                if result:
                    return result

        for product_url in self._load_sitemaps().get(legacy_id, []):
            result = self._try_page(product_url, "SITEMAP_CACHE", legacy_id)
            if result:
                return result
        self.log.append(
            {
                "legacy_id": legacy_id,
                "strategy": "ALL_STRATEGIES",
                "status": "MISSING",
            }
        )
        return "", [], "NOT_FOUND"


def _image_extension(url: str, content_type: str) -> str:
    suffix = Path(urllib.parse.urlsplit(url).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return suffix
    guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
    return guessed if guessed in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _verify_image_bytes(value: bytes) -> None:
    from PIL import Image

    try:
        with Image.open(io.BytesIO(value)) as image:
            image.verify()
    except Exception as exc:
        raise ExcelPipelineError(f"downloaded gallery bytes are not a valid image: {exc}") from exc


def fetch_images_for_records(
    records: Sequence[Dict[str, Any]],
    *,
    private_dir: Path,
    run_dir: Path,
    discovery: Optional[LegacyImageDiscovery] = None,
) -> List[Dict[str, Any]]:
    service = discovery or LegacyImageDiscovery()
    image_root = private_dir / "legacy-cache" / "original-images"
    qa_dir = run_dir / "image-qa"
    updated: List[Dict[str, Any]] = []
    for source_record in records:
        record = dict(source_record)
        legacy_id = int(record["legacy_id"])
        if str(record.get("action", "")).startswith("SKIP_"):
            record["image_status"] = "SKIPPED"
            record["image_discovery_strategy"] = "NOT_RUN_SKIPPED_PRODUCT"
            updated.append(record)
            print(
                f"[IMAGE] id={legacy_id} strategy=NOT_RUN status=SKIPPED"
            )
            continue
        legacy_url, image_urls, strategy = service.discover(legacy_id)
        record["legacy_url"] = legacy_url
        record["image_urls"] = image_urls
        record["image_discovery_strategy"] = strategy
        originals: List[str] = []
        downloads: List[Dict[str, Any]] = []
        product_dir = image_root / str(legacy_id)
        product_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        for position, image_url in enumerate(image_urls, start=1):
            try:
                data, headers = service.fetcher.fetch_bytes(
                    image_url, max_bytes=MAX_IMAGE_BYTES
                )
                content_type = headers.get("content-type", "").lower()
                if content_type and not content_type.startswith("image/"):
                    raise ExcelPipelineError("gallery URL returned non-image content")
                _verify_image_bytes(data)
                digest = _sha256_bytes(data)
                extension = _image_extension(image_url, content_type)
                destination = product_dir / f"{position:02d}-original{extension}"
                if destination.exists() and hashlib.sha256(
                    destination.read_bytes()
                ).hexdigest() != digest:
                    destination = product_dir / (
                        f"{position:02d}-original-{digest[:12]}{extension}"
                    )
                if not destination.exists():
                    temporary = destination.with_suffix(destination.suffix + ".tmp")
                    temporary.write_bytes(data)
                    os.chmod(temporary, 0o600)
                    os.replace(temporary, destination)
                originals.append(str(destination))
                downloads.append(
                    {
                        "position": position,
                        "source_url": image_url,
                        "local_path": str(destination),
                        "sha256": digest,
                        "bytes": len(data),
                    }
                )
            except (OSError, urllib.error.URLError, RuntimeError) as exc:
                downloads.append(
                    {
                        "position": position,
                        "source_url": image_url,
                        "error": str(exc),
                    }
                )
        record["original_image_paths"] = originals
        record["downloaded_images"] = downloads
        record["images_found"] = len(originals)
        if originals:
            qa = process_product(
                str(legacy_id),
                [Path(path) for path in originals],
                private_dir,
                qa_dir,
            )
            record["image_qa"] = qa
            record["selected_import_paths"] = qa.get(
                "selected_import_paths", originals
            )
            record["image_status"] = "READY"
        else:
            record["image_qa"] = None
            record["selected_import_paths"] = []
            record["image_status"] = "MISSING"
            record["review_flags"] = list(
                dict.fromkeys([*record.get("review_flags", []), "IMAGES_MISSING"])
            )
        if record.get("action") == "PLAN_CREATE_DRAFT":
            record["action"] = "READY_DRAFT"
        updated.append(record)
        print(
            f"[IMAGE] id={legacy_id} strategy={strategy} "
            f"found={len(originals)} status={record['image_status']}"
        )
    write_json_atomic(run_dir / "image-discovery-log.json", service.log)
    return updated


def _b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


class ExcelDraftGateway(WPGateway):
    def get_currency(self) -> str:
        return self.eval_scalar("echo (string) get_option('woocommerce_currency', '');")

    def find_by_legacy_id(self, legacy_id: str) -> Optional[int]:
        encoded = _b64(legacy_id)
        php = f"""
$v=base64_decode('{encoded}');
$q=new WP_Query(array('post_type'=>'product','post_status'=>'any','posts_per_page'=>2,'fields'=>'ids',
 'meta_query'=>array('relation'=>'OR',
  array('key'=>'legacy_product_id','value'=>$v,'compare'=>'='),
  array('key'=>'radman_legacy_id','value'=>$v,'compare'=>'='),
  array('key'=>'_legacy_store_id','value'=>$v,'compare'=>'=')
 )));
if (count($q->posts)>1) {{ fwrite(STDERR, 'duplicate legacy product ID metadata'); exit(8); }}
if ($q->posts) {{ echo (string)$q->posts[0]; }}
"""
        raw = self.eval_scalar(php)
        return int(raw) if raw.isdigit() and int(raw) > 0 else None

    def create_excel_draft(self, record: Mapping[str, Any], category_id: int) -> int:
        metadata = {
            "legacy_product_id": str(record["legacy_id"]),
            "_legacy_store_id": str(record["legacy_id"]),
            "legacy_raw_code": str(record.get("raw_code") or ""),
            "legacy_url": str(record.get("legacy_url") or ""),
            "weight_grams": str(record.get("weight_grams") or ""),
            "silver_weight_grams": str(record.get("weight_grams") or ""),
            "price_source": str(record["price_source"]),
            "rate_used": str(record["rate_used"]),
            "computed_price": str(record.get("computed_price_toman") or ""),
            "final_price": str(record["final_price_toman"]),
            "excel_price_toman": str(record["excel_price_toman"]),
            "pre_discount_price_toman": str(
                record.get("pre_discount_price_toman") or ""
            ),
            "stone_class": str(record["stone_class"]),
            "image_status": str(record["image_status"]),
            "image_discovery_strategy": str(
                record.get("image_discovery_strategy") or ""
            ),
            "excel_category_raw": str(record.get("category_raw") or ""),
            "excel_row": str(record["excel_row"]),
            "radman_import_source": "excel_1000_pipeline",
            "radman_import_version": PIPELINE_VERSION,
            "radman_review_flags": " | ".join(record.get("review_flags", [])),
            "pricing_mode": "manual_locked",
            "manual_price_toman": str(record["final_price_toman"]),
            "price_locked": "1",
            "rounding_step_toman": str(ROUNDING_STEP),
        }
        payload = {
            "sku": record["sku"],
            "name": record["title"],
            "description": record["description"],
            "category_id": int(category_id),
            "regular_price": int(record["regular_price_toman"]),
            "sale_price": record.get("sale_price_toman"),
            "stock": int(record["stock"]),
            "meta": metadata,
        }
        encoded = _b64(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        )
        php = f"""
if (!function_exists('wc_get_product_id_by_sku')) {{ fwrite(STDERR, 'WooCommerce unavailable'); exit(3); }}
$d=json_decode(base64_decode('{encoded}'), true);
if (wc_get_product_id_by_sku($d['sku'])) {{ fwrite(STDERR, 'SKU conflict during create'); exit(9); }}
$legacy=(string)$d['meta']['legacy_product_id'];
$q=new WP_Query(array('post_type'=>'product','post_status'=>'any','posts_per_page'=>1,'fields'=>'ids',
 'meta_query'=>array('relation'=>'OR',
  array('key'=>'legacy_product_id','value'=>$legacy,'compare'=>'='),
  array('key'=>'radman_legacy_id','value'=>$legacy,'compare'=>'='),
  array('key'=>'_legacy_store_id','value'=>$legacy,'compare'=>'=')
 )));
if ($q->posts) {{ fwrite(STDERR, 'legacy ID appeared during create'); exit(10); }}
$p=new WC_Product_Simple();
$p->set_sku($d['sku']);
$p->set_status('draft');
$p->set_catalog_visibility('visible');
$p->set_name($d['name']);
$p->set_description($d['description']);
$p->set_short_description('');
$p->set_regular_price((string)$d['regular_price']);
if ($d['sale_price'] !== null) {{
 $p->set_sale_price((string)$d['sale_price']);
 $p->set_price((string)$d['sale_price']);
}} else {{
 $p->set_sale_price('');
 $p->set_price((string)$d['regular_price']);
}}
$p->set_manage_stock(true);
$p->set_stock_quantity((int)$d['stock']);
$p->set_stock_status(((int)$d['stock']) > 0 ? 'instock' : 'outofstock');
$p->set_backorders('no');
$p->set_category_ids(array((int)$d['category_id']));
foreach ($d['meta'] as $key=>$value) {{
 $p->update_meta_data($key, (string)$value);
}}
$id=$p->save();
if (!$id || $p->get_status('edit') !== 'draft' || $p->get_backorders('edit') !== 'no') {{
 fwrite(STDERR, 'Draft/backorder verification failed'); exit(11);
}}
echo wp_json_encode(array('id'=>(int)$id,'status'=>$p->get_status('edit')));
"""
        result = self.eval_json(php)
        if not isinstance(result, dict) or result.get("status") != "draft":
            raise WPCliError(f"invalid Draft creation result for {record['sku']}")
        return int(result["id"])


def require_import_environment(wp_path: str) -> Path:
    errors = []
    if os.environ.get("APP_ENV") != EXPECTED_APP_ENV:
        errors.append("APP_ENV must equal staging")
    if os.environ.get("WP_URL") != EXPECTED_WP_URL:
        errors.append(f"WP_URL must equal {EXPECTED_WP_URL}")
    if wp_path != EXPECTED_WP_PATH:
        errors.append(f"WP_PATH must equal {EXPECTED_WP_PATH}")
    if "public_html" in wp_path:
        errors.append("public_html is prohibited")
    if os.environ.get("CONFIRM_STAGING_APPLY") != "YES":
        errors.append("CONFIRM_STAGING_APPLY must equal YES")
    backup = Path(os.environ.get("RADMAN_DB_BACKUP_PATH", ""))
    if not backup.is_file() or backup.stat().st_size <= 0:
        errors.append("RADMAN_DB_BACKUP_PATH must be a non-empty database backup")
    if "public_html" in str(backup):
        errors.append("database backup cannot be under public_html")
    if errors:
        raise ExcelPipelineError("; ".join(errors))
    return backup


def preflight_import(
    records: Sequence[Dict[str, Any]], gateway: ExcelDraftGateway
) -> List[Tuple[Dict[str, Any], str, Optional[int]]]:
    if gateway.get_currency() != REQUIRED_CURRENCY:
        raise ExcelPipelineError("WooCommerce currency must be IRT")
    decisions = []
    seen_skus: set[str] = set()
    seen_ids: set[str] = set()
    for record in records:
        legacy_id = str(record["legacy_id"])
        sku_key = str(record["sku"]).casefold()
        if record.get("action") in {
            "SKIP_DUPLICATE_BATCH_SKU",
            "SKIP_DUPLICATE_BATCH_LEGACY_ID",
            "SKIP_INVALID_PRICE",
        }:
            decisions.append((record, str(record["action"]), None))
            continue
        if legacy_id in seen_ids:
            decisions.append((record, "SKIP_DUPLICATE_BATCH_LEGACY_ID", None))
            continue
        if sku_key in seen_skus:
            decisions.append((record, "SKIP_DUPLICATE_BATCH_SKU", None))
            continue
        seen_ids.add(legacy_id)
        seen_skus.add(sku_key)
        existing_legacy = gateway.find_by_legacy_id(legacy_id)
        if existing_legacy:
            decisions.append((record, "SKIP_EXISTING_LEGACY_ID", existing_legacy))
            continue
        existing_sku = gateway.find_product_id(str(record["sku"]))
        if existing_sku:
            record["review_flags"] = list(
                dict.fromkeys(
                    [*record.get("review_flags", []), "WORDPRESS_SKU_CONFLICT"]
                )
            )
            decisions.append((record, "SKIP_SKU_CONFLICT", existing_sku))
            continue
        decisions.append((record, "CREATE_DRAFT", None))
    return decisions


def import_records(
    records: Sequence[Dict[str, Any]], gateway: ExcelDraftGateway
) -> List[Dict[str, Any]]:
    decisions = preflight_import(records, gateway)
    actions: List[Dict[str, Any]] = []
    for record, decision, existing_id in decisions:
        if decision != "CREATE_DRAFT":
            record["action"] = decision
            record["wordpress_product_id"] = existing_id
            actions.append(
                {
                    "legacy_id": record["legacy_id"],
                    "sku": record["sku"],
                    "action": decision,
                    "product_id": existing_id,
                }
            )
            continue
        valid_media: List[Path] = []
        for raw_path in record.get("selected_import_paths", []):
            path = Path(raw_path)
            if path.is_file():
                valid_media.append(path)
            else:
                record["review_flags"] = list(
                    dict.fromkeys(
                        [*record.get("review_flags", []), "SELECTED_IMAGE_MISSING"]
                    )
                )
        if record.get("image_status") == "READY" and not valid_media:
            record["image_status"] = "MISSING"
        category_id = gateway.resolve_category_id(str(record["category"]))
        product_id = gateway.create_excel_draft(record, category_id)
        attachment_ids: List[int] = []
        for path in valid_media:
            attachment_ids.append(
                gateway.import_image(
                    path,
                    str(record["title"]),
                    product_id,
                    str(record["sku"]),
                )
            )
        if attachment_ids:
            gateway.set_product_images(product_id, attachment_ids)
        record["action"] = "CREATED_DRAFT"
        record["wordpress_product_id"] = product_id
        record["attachment_ids"] = attachment_ids
        actions.append(
            {
                "legacy_id": record["legacy_id"],
                "sku": record["sku"],
                "action": "CREATED_DRAFT",
                "product_id": product_id,
                "attachment_ids": attachment_ids,
                "image_status": record.get("image_status"),
            }
        )
    return actions


def now_slug() -> str:
    return datetime.now(TEHRAN).strftime("%Y%m%dT%H%M%S%f%z")


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_json_safe(value), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def _report_row(record: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "legacy_id": record.get("legacy_id", ""),
        "sku": record.get("sku", ""),
        "sku_source": record.get("sku_source", ""),
        "title": record.get("title", ""),
        "category_raw": record.get("category_raw", ""),
        "category": record.get("category", ""),
        "weight_grams": record.get("weight_grams") or "",
        "excel_price_toman": record.get("excel_price_toman") or "",
        "pre_discount_price_toman": record.get("pre_discount_price_toman") or "",
        "computed_price_toman": record.get("computed_price_toman") or "",
        "final_price_toman": record.get("final_price_toman") or "",
        "regular_price_toman": record.get("regular_price_toman") or "",
        "sale_price_toman": record.get("sale_price_toman") or "",
        "price_source": record.get("price_source", ""),
        "rate_used": record.get("rate_used", ""),
        "stone_class": record.get("stone_class", ""),
        "stock": record.get("stock", 0),
        "images_found": record.get("images_found", 0),
        "image_status": record.get("image_status", ""),
        "image_discovery_strategy": record.get("image_discovery_strategy", ""),
        "legacy_url": record.get("legacy_url", ""),
        "action": record.get("action", ""),
        "review_flags": " | ".join(record.get("review_flags", [])),
        "wordpress_product_id": record.get("wordpress_product_id") or "",
    }


def write_reports(
    records: Sequence[Mapping[str, Any]],
    run_dir: Path,
    run_stamp: str,
    selection_summary: Mapping[str, int],
) -> Tuple[Path, Path]:
    csv_path = run_dir / f"excel-import-{run_stamp}.csv"
    txt_path = run_dir / f"excel-import-{run_stamp}-fa.txt"
    run_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    csv_temporary = csv_path.with_suffix(csv_path.suffix + ".tmp")
    with csv_temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(_report_row(record))
    os.chmod(csv_temporary, 0o600)
    os.replace(csv_temporary, csv_path)

    missing_images = sum(record.get("image_status") == "MISSING" for record in records)
    review = sum(bool(record.get("review_flags")) for record in records)
    lines = [
        "گزارش خط لوله Excel برای جدیدترین محصولات رادمان",
        f"زمان: {datetime.now(TEHRAN).isoformat(timespec='seconds')}",
        "منبع داده محصول: فقط Excel (قیمت‌ها تومان هستند)",
        "ترتیب انتخاب: شناسه قدیمی نزولی؛ ID بالاتر جدیدتر است",
        f"ردیف Excel: {selection_summary.get('excel_rows', 0)}",
        f"فعالِ قابل انتخاب: {selection_summary.get('eligible_rows', 0)}",
        f"انتخاب‌شده: {selection_summary.get('selected_rows', len(records))}",
        f"غیرفعال ردشده: {selection_summary.get('inactive_skipped', 0)}",
        f"ناموجود ردشده: {selection_summary.get('unavailable_skipped', 0)}",
        f"بدون تصویر: {missing_images}",
        f"نیازمند بازبینی: {review}",
        "",
        "id | sku | منبع SKU | عنوان | دسته | وزن | قیمت Excel | محاسبه | نهایی | منبع قیمت | نگین | موجودی | تصویر | اقدام | بازبینی",
    ]
    for record in records:
        lines.append(
            "{legacy_id} | {sku} | {sku_source} | {title} | {category} | "
            "{weight} | {excel} | {computed} | {final} | {source} | {stone} | "
            "{stock} | {image} | {action} | {flags}".format(
                legacy_id=record.get("legacy_id"),
                sku=record.get("sku"),
                sku_source=record.get("sku_source"),
                title=str(record.get("title", "")).replace("|", "/"),
                category=record.get("category"),
                weight=record.get("weight_grams") or "—",
                excel=record.get("excel_price_toman") or "—",
                computed=record.get("computed_price_toman") or "—",
                final=record.get("final_price_toman") or "—",
                source=record.get("price_source"),
                stone=record.get("stone_class"),
                stock=record.get("stock"),
                image=record.get("image_status"),
                action=record.get("action"),
                flags=",".join(record.get("review_flags", [])) or "—",
            )
        )
    txt_temporary = txt_path.with_suffix(txt_path.suffix + ".tmp")
    txt_temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(txt_temporary, 0o600)
    os.replace(txt_temporary, txt_path)
    return csv_path, txt_path


def latest_manifest(private_dir: Path) -> Path:
    candidates = sorted(
        (private_dir / "legacy-cache" / "runs").glob(
            "excel-import-*/prepared-products.json"
        ),
        reverse=True,
    )
    if not candidates:
        raise ExcelPipelineError(
            "prepared-products.json پیدا نشد؛ ابتدا --fetch-images یا --full-pilot را اجرا کنید"
        )
    return candidates[0]


def read_manifest(path: Path, private_dir: Path) -> Dict[str, Any]:
    resolved = path.expanduser().resolve()
    private_root = private_dir.expanduser().resolve()
    if private_root not in resolved.parents or not resolved.is_file():
        raise ExcelPipelineError("manifest باید فایل موجود زیر RADMAN_PRIVATE_DIR باشد")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    records = payload.get("products", [])
    if not isinstance(records, list) or not records or len(records) > HARD_MAX_PRODUCTS:
        raise ExcelPipelineError("manifest باید 1..1000 محصول داشته باشد")
    for record in records:
        if record.get("image_status") == "NOT_FETCHED":
            raise ExcelPipelineError(
                "manifest فقط plan است؛ پیش از import باید --fetch-images اجرا شود"
            )
        for raw_path in record.get("selected_import_paths", []):
            media_path = Path(raw_path).expanduser().resolve()
            if private_root not in media_path.parents:
                raise ExcelPipelineError(
                    f"مسیر تصویر import باید زیر RADMAN_PRIVATE_DIR باشد: {media_path}"
                )
    return payload


def prepare_from_excel(
    excel_file: Path,
    max_products: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, int], List[str]]:
    all_records, warnings = load_excel_records(excel_file)
    selected, selection = select_newest(all_records, max_products)
    return selected, selection, warnings


def print_pricing_preview(
    records: Sequence[Mapping[str, Any]], selection: Mapping[str, int]
) -> None:
    print("=" * 118)
    print("RADMAN EXCEL IMPORT — SELECTION + PRICING PREVIEW (NO WP WRITE)")
    print(
        f"eligible={selection.get('eligible_rows', 0)} selected={len(records)} "
        "sort=legacy_id DESC currency=IRT/Toman"
    )
    print("ID     SKU          SRC                  WEIGHT    EXCEL       COMPUTED    FINAL       PRICE_SOURCE")
    print("-" * 118)
    for record in records[:20]:
        print(
            f"{int(record['legacy_id']):<6} "
            f"{str(record['sku']):<12} "
            f"{str(record['sku_source']):<20} "
            f"{str(record.get('weight_grams') or '-'):>8} "
            f"{str(record.get('excel_price_toman') or '-'):>11} "
            f"{str(record.get('computed_price_toman') or '-'):>11} "
            f"{str(record.get('final_price_toman') or '-'):>11} "
            f"{record.get('price_source')}"
        )
    if len(records) > 20:
        print(f"... {len(records) - 20} additional selected rows are in the CSV/TXT report")
    print("PLAN PREVIEW ONLY — no WordPress product was changed.")
    print("=" * 118)


def inspect_excel(excel_file: Path, max_products: int) -> None:
    records, selection, warnings = prepare_from_excel(excel_file, max_products)
    identifiers = [int(record["legacy_id"]) for record in records]
    print("RADMAN Excel import inspection — READ ONLY")
    print(f"  file: {excel_file}")
    print(f"  sheet: {SHEET_NAME}")
    print(f"  total parsed: {selection['excel_rows']}")
    print(f"  eligible: {selection['eligible_rows']}")
    print(f"  selected cap: {max_products}")
    print(f"  selected: {len(records)}")
    if identifiers:
        print(f"  selected ID range: {min(identifiers)}..{max(identifiers)}")
        print(f"  first/newest IDs: {', '.join(str(value) for value in identifiers[:5])}")
    print("  ordering: ID DESCENDING (higher ID is newer)")
    print(f"  warnings: {len(warnings)}")
    print(f"  API slot: {API_SLOT}")
    print("  mutation: NONE")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--inspect", action="store_true")
    modes.add_argument("--plan", action="store_true")
    modes.add_argument("--fetch-images", action="store_true")
    modes.add_argument("--import-drafts", action="store_true")
    modes.add_argument("--full-pilot", action="store_true")
    parser.add_argument("--excel", type=Path, default=DEFAULT_EXCEL_FILE)
    parser.add_argument("--max-products", type=int, default=DEFAULT_MAX_PRODUCTS)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--wp-path", default=os.environ.get("WP_PATH", ""))
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    private_dir = args.private_dir.expanduser().resolve()
    if not private_dir.is_absolute() or "public_html" in str(private_dir):
        print("[ERROR] RADMAN_PRIVATE_DIR must be private and absolute", file=sys.stderr)
        return 2
    if args.max_products < 1 or args.max_products > HARD_MAX_PRODUCTS:
        print(f"[ERROR] MAX_PRODUCTS must be 1..{HARD_MAX_PRODUCTS}", file=sys.stderr)
        return 2
    try:
        if args.inspect:
            inspect_excel(args.excel, args.max_products)
            return 0

        if args.import_drafts:
            require_import_environment(args.wp_path)
            manifest_path = args.manifest or latest_manifest(private_dir)
            payload = read_manifest(manifest_path, private_dir)
            records = payload["products"]
            actions = import_records(records, ExcelDraftGateway(args.wp_path))
            payload["products"] = records
            payload["import_actions"] = actions
            run_dir = manifest_path.resolve().parent
            run_stamp = str(payload.get("run_stamp") or now_slug())
            write_json_atomic(run_dir / "prepared-products.json", payload)
            write_json_atomic(run_dir / "import-actions.json", actions)
            write_reports(
                records,
                run_dir,
                run_stamp,
                payload.get("selection_summary", {}),
            )
            print(f"[IMPORT] actions={len(actions)}; all creations are Draft")
            return 0

        records, selection, warnings = prepare_from_excel(
            args.excel, args.max_products
        )
        if args.plan or args.full_pilot:
            print_pricing_preview(records, selection)
        run_stamp = now_slug()
        run_dir = (
            private_dir
            / "legacy-cache"
            / "runs"
            / f"excel-import-{run_stamp}"
        )
        if args.fetch_images or args.full_pilot:
            records = fetch_images_for_records(
                records,
                private_dir=private_dir,
                run_dir=run_dir,
            )
        payload = {
            "generated_at": datetime.now(TEHRAN).isoformat(),
            "run_stamp": run_stamp,
            "pipeline_version": PIPELINE_VERSION,
            "excel_file": str(args.excel.expanduser().resolve()),
            "sheet": SHEET_NAME,
            "sort": "legacy_id DESC",
            "max_products": args.max_products,
            "selection_summary": selection,
            "excel_warnings": warnings,
            "api_slot": str(API_SLOT),
            "products": records,
        }
        manifest_path = run_dir / "prepared-products.json"
        write_json_atomic(manifest_path, payload)
        csv_path, txt_path = write_reports(
            records, run_dir, run_stamp, selection
        )
        print(f"[REPORT] {csv_path}")
        print(f"[REPORT] {txt_path}")
        print(f"[MANIFEST] {manifest_path}")

        if args.full_pilot:
            require_import_environment(args.wp_path)
            actions = import_records(records, ExcelDraftGateway(args.wp_path))
            payload["products"] = records
            payload["import_actions"] = actions
            write_json_atomic(manifest_path, payload)
            write_json_atomic(run_dir / "import-actions.json", actions)
            write_reports(records, run_dir, run_stamp, selection)
            print(f"[IMPORT] actions={len(actions)}; all creations are Draft")
        return 0
    except (ExcelPipelineError, WPCliError, OSError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

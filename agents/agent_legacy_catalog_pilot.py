#!/usr/bin/env python3
"""RADMAN SILVER — robots-aware, public-only three-product legacy pilot.

Discovers at most three public products, extracts visible catalog fields, and
stores source JSON/images in RADMAN_PRIVATE_DIR. It never calls WordPress and
never uses a private API.
"""

from __future__ import annotations

import argparse
import html
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

BASE_URL = "https://noghrehmashhad.ir"
ROBOTS_URL = f"{BASE_URL}/robots.txt"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
PILOT_CATEGORY_URLS = (
    f"{BASE_URL}/category/2/انگشتر-مردانه/",
    f"{BASE_URL}/category/71/مدال-یا-گردنبند/",
    f"{BASE_URL}/category/17/دستبند-مردانه/",
)
USER_AGENT = (
    "RadmanSilverCatalogPilot/1.0 "
    "(+https://radmansilver.ir; owner-controlled legacy migration; contact: leadflow.sdr@gmail.com)"
)
MIN_REQUEST_DELAY_SECONDS = 2.0
MAX_PRODUCTS = 3
MAX_TEXT_BYTES = 25 * 1024 * 1024
MAX_IMAGE_BYTES = 30 * 1024 * 1024

_DIGIT_TRANSLATION = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"
)


class PilotError(RuntimeError):
    pass


def iri_to_uri(url: str) -> str:
    """Convert a possibly-Persian IRI to an ASCII-safe URI.

    Existing percent escapes are preserved by keeping ``%`` in each safe set;
    this prevents already-encoded sitemap links from becoming ``%25D8...``.
    """
    parts = urllib.parse.urlsplit(str(url))
    encoded_path = urllib.parse.quote(parts.path, safe="/%")
    encoded_query = urllib.parse.quote(parts.query, safe="=&%")
    encoded_fragment = urllib.parse.quote(parts.fragment, safe="%")
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, encoded_path, encoded_query, encoded_fragment)
    )


def redirect_target_to_uri(base_url: str, target_url: str) -> str:
    """Resolve and encode redirect targets before urllib builds a new Request."""
    return iri_to_uri(urllib.parse.urljoin(base_url, target_url))


class IRISafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> Optional[urllib.request.Request]:
        encoded_target = redirect_target_to_uri(req.full_url, newurl)
        return super().redirect_request(req, fp, code, msg, headers, encoded_target)


_HTTP_OPENER = urllib.request.build_opener(IRISafeRedirectHandler())


def normalize_digits(value: str) -> str:
    """Normalize Persian/Arabic digits to ASCII and Arabic kaf/yeh to Persian."""
    return str(value or "").translate(_DIGIT_TRANSLATION).replace("ي", "ی").replace("ك", "ک")


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(normalize_digits(value))).strip()


def parse_toman(value: str) -> Optional[int]:
    normalized = normalize_digits(value)
    normalized = (
        normalized.replace("٬", "")
        .replace(",", "")
        .replace(" ", "")
        .replace("تومان", "")
    )
    matches = re.findall(r"[0-9]+", normalized)
    if not matches:
        return None
    joined = "".join(matches)
    return int(joined) if joined else None


def validate_product_limit(limit: int) -> int:
    if limit < 1 or limit > MAX_PRODUCTS:
        raise PilotError(f"pilot product limit must be between 1 and {MAX_PRODUCTS}")
    return limit


class RateLimitedFetcher:
    """HTTPS fetcher with a hard minimum delay and robots enforcement."""

    def __init__(
        self,
        *,
        user_agent: str = USER_AGENT,
        min_delay: float = MIN_REQUEST_DELAY_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
        opener: Optional[Callable[[urllib.request.Request, int], Tuple[bytes, Dict[str, str]]]] = None,
    ) -> None:
        if min_delay < MIN_REQUEST_DELAY_SECONDS:
            raise PilotError(
                f"minimum request delay cannot be below {MIN_REQUEST_DELAY_SECONDS:.1f} seconds"
            )
        self.user_agent = user_agent
        self.min_delay = min_delay
        self.clock = clock
        self.sleeper = sleeper
        self.opener = opener or self._default_open
        self.last_request_at: Optional[float] = None
        self.robots: Optional[urllib.robotparser.RobotFileParser] = None

    @staticmethod
    def _default_open(request: urllib.request.Request, timeout: int) -> Tuple[bytes, Dict[str, str]]:
        with _HTTP_OPENER.open(request, timeout=timeout) as response:
            RateLimitedFetcher._validate_url(iri_to_uri(response.geturl()))
            data = response.read(MAX_IMAGE_BYTES + 1)
            headers = {key.lower(): value for key, value in response.headers.items()}
        return data, headers

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "noghrehmashhad.ir":
            raise PilotError(f"refusing non-legacy or non-HTTPS URL: {url}")

    def _wait(self) -> None:
        if self.last_request_at is not None:
            remaining = self.min_delay - (self.clock() - self.last_request_at)
            if remaining > 0:
                self.sleeper(remaining)

    def fetch_bytes(
        self,
        url: str,
        *,
        max_bytes: int,
        check_robots: bool = True,
        timeout: int = 45,
    ) -> Tuple[bytes, Dict[str, str]]:
        request_url = iri_to_uri(url)
        self._validate_url(request_url)
        if check_robots:
            if self.robots is None:
                raise PilotError("robots.txt must be loaded before catalog requests")
            if not self.robots.can_fetch(self.user_agent, request_url):
                raise PilotError(f"robots.txt disallows this URL: {request_url}")
        self._wait()
        request = urllib.request.Request(
            request_url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*;q=0.8",
            },
        )
        try:
            data, headers = self.opener(request, timeout)
        finally:
            # Failed requests count too; retries must still honor the delay.
            self.last_request_at = self.clock()
        if len(data) > max_bytes:
            raise PilotError(f"response exceeds {max_bytes} bytes: {url}")
        return data, headers

    def fetch_text(self, url: str, *, check_robots: bool = True) -> str:
        data, headers = self.fetch_bytes(
            url, max_bytes=MAX_TEXT_BYTES, check_robots=check_robots
        )
        content_type = headers.get("content-type", "")
        charset_match = re.search(r"charset=([A-Za-z0-9._-]+)", content_type)
        charset = charset_match.group(1) if charset_match else "utf-8"
        try:
            return data.decode(charset, errors="replace")
        except LookupError:
            return data.decode("utf-8", errors="replace")

    def load_robots(self) -> None:
        text = self.fetch_text(ROBOTS_URL, check_robots=False)
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(ROBOTS_URL)
        parser.parse(text.splitlines())
        self.robots = parser


class ProductHTMLParser(HTMLParser):
    def __init__(self, page_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.text_parts: List[str] = []
        self.h1_parts: List[str] = []
        self.price_parts: List[str] = []
        self.description_parts: List[str] = []
        self.images: List[str] = []
        self.category_links: List[Tuple[str, str]] = []
        self.jsonld_blocks: List[str] = []
        self._current_jsonld: List[str] = []
        self.meta_description = ""
        self._h1_depth = 0
        self._price_depth = 0
        self._description_depth = 0
        self._script_jsonld = False
        self._anchor_href: Optional[str] = None
        self._anchor_parts: List[str] = []

    @staticmethod
    def _attrs(attrs: Sequence[Tuple[str, Optional[str]]]) -> Dict[str, str]:
        return {key.lower(): value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]) -> None:
        values = self._attrs(attrs)
        css = f"{values.get('class', '')} {values.get('id', '')}".lower()
        if tag == "h1":
            self._h1_depth += 1
        elif self._h1_depth:
            self._h1_depth += 1

        if any(token in css for token in ("price", "amount", "sale-price", "final-price")):
            self._price_depth += 1
        elif self._price_depth:
            self._price_depth += 1

        if any(token in css for token in ("product-description", "description", "tab-content")):
            self._description_depth += 1
        elif self._description_depth:
            self._description_depth += 1

        if tag == "img":
            src = values.get("src") or values.get("data-src") or values.get("data-lazy-src")
            if src:
                self.images.append(urllib.parse.urljoin(self.page_url, src))
        elif tag == "meta":
            key = (values.get("property") or values.get("name") or "").lower()
            content = values.get("content", "")
            if key in ("description", "og:description") and content and not self.meta_description:
                self.meta_description = content
            if key == "og:image" and content:
                self.images.append(urllib.parse.urljoin(self.page_url, content))
        elif tag == "a":
            self._anchor_href = urllib.parse.urljoin(self.page_url, values.get("href", ""))
            self._anchor_parts = []
        elif tag == "script" and "ld+json" in values.get("type", "").lower():
            self._script_jsonld = True
            self._current_jsonld = []

    def handle_endtag(self, tag: str) -> None:
        if self._h1_depth:
            self._h1_depth -= 1
        if self._price_depth:
            self._price_depth -= 1
        if self._description_depth:
            self._description_depth -= 1
        if tag == "script" and self._script_jsonld:
            block = "".join(self._current_jsonld).strip()
            if block:
                self.jsonld_blocks.append(block)
            self._current_jsonld = []
            self._script_jsonld = False
        if tag == "a" and self._anchor_href is not None:
            text = normalize_space(" ".join(self._anchor_parts))
            if "/category/" in self._anchor_href and text:
                self.category_links.append((self._anchor_href, text))
            self._anchor_href = None
            self._anchor_parts = []

    def handle_data(self, data: str) -> None:
        cleaned = normalize_space(data)
        if not cleaned:
            return
        self.text_parts.append(cleaned)
        if self._h1_depth:
            self.h1_parts.append(cleaned)
        if self._price_depth:
            self.price_parts.append(cleaned)
        if self._description_depth:
            self.description_parts.append(cleaned)
        if self._anchor_href is not None:
            self._anchor_parts.append(cleaned)
        if self._script_jsonld:
            self._current_jsonld.append(data)


def _walk_json(value: object) -> Iterable[Dict[str, object]]:
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk_json(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_json(nested)


def _jsonld_product(parser: ProductHTMLParser) -> Dict[str, object]:
    candidates: List[object] = []
    for block in parser.jsonld_blocks:
        try:
            candidates.append(json.loads(block))
        except json.JSONDecodeError:
            continue
    for candidate in candidates:
        for item in _walk_json(candidate):
            item_type = item.get("@type")
            types = item_type if isinstance(item_type, list) else [item_type]
            if "Product" in types:
                return item
    return {}


def _price_from_visible(parts: Sequence[str]) -> Optional[int]:
    candidates: List[int] = []
    for part in parts:
        normalized = normalize_digits(part)
        for raw in re.findall(r"[0-9][0-9,٬\s]{3,}", normalized):
            value = parse_toman(raw)
            if value is not None and value >= 1_000:
                candidates.append(value)
    return min(candidates) if candidates else None


def _price_from_jsonld(product: Dict[str, object]) -> Tuple[Optional[int], str]:
    offers = product.get("offers")
    offer = offers[0] if isinstance(offers, list) and offers else offers
    if not isinstance(offer, dict):
        return None, "missing"
    raw = offer.get("price") or offer.get("lowPrice")
    try:
        amount = int(_number_like(raw))
    except (TypeError, ValueError):
        return None, "missing"
    currency = str(offer.get("priceCurrency", "")).upper()
    if currency == "IRT":
        return amount, "jsonld_irt"
    if currency == "IRR" and amount >= 10 and amount % 10 == 0:
        return amount // 10, "jsonld_irr_div10_review"
    return amount, f"jsonld_{currency.lower() or 'unknown'}_review"


def _number_like(value: object) -> float:
    return float(normalize_digits(str(value)).replace(",", "").replace("٬", ""))


def map_radman_category(raw_category: str, title: str = "") -> Optional[str]:
    value = f"{raw_category} {title}"
    if "دستبند" in value:
        return "bracelets"
    if any(token in value for token in ("گردنبند", "مدال", "آویز", "اویز")):
        return "necklaces"
    if "انگشتر" in value:
        return "rings"
    return None


def parse_product_html(page_url: str, source_html: str) -> Dict[str, object]:
    id_match = re.search(r"/product/([0-9]+)/", page_url)
    if not id_match:
        raise PilotError(f"product URL has no numeric legacy ID: {page_url}")
    parser = ProductHTMLParser(page_url)
    parser.feed(source_html)
    json_product = _jsonld_product(parser)

    title = normalize_space(" ".join(parser.h1_parts))
    if not title:
        title = normalize_space(str(json_product.get("name", "")))
    if not title:
        raise PilotError(f"no product title found: {page_url}")

    raw_category = parser.category_links[0][1] if parser.category_links else ""
    mapped_category = map_radman_category(raw_category, title)

    visible_price = _price_from_visible(parser.price_parts)
    if visible_price is not None:
        price_toman, price_source = visible_price, "visible_price"
    else:
        price_toman, price_source = _price_from_jsonld(json_product)

    all_text = normalize_space(" ".join(parser.text_parts))
    weight_match = re.search(
        r"وزن(?:\s+تقریبی)?\s*[:：]?\s*([0-9۰-۹٠-٩]+(?:[٫.][0-9۰-۹٠-٩]+)?)\s*(?:گرم)?",
        all_text,
    )
    weight: Optional[float] = None
    if weight_match:
        try:
            weight = float(normalize_digits(weight_match.group(1)).replace("٫", "."))
        except ValueError:
            weight = None

    description = normalize_space(" ".join(parser.description_parts))
    if not description:
        description = normalize_space(str(json_product.get("description", "")))
    if not description:
        description = normalize_space(parser.meta_description)

    images: List[str] = []
    seen: set[str] = set()
    for image_url in parser.images:
        parsed = urllib.parse.urlparse(image_url)
        if parsed.hostname != "noghrehmashhad.ir":
            continue
        clean_url = urllib.parse.urlunparse(
            ("https", parsed.netloc, parsed.path, "", "", "")
        )
        if "product-images" not in parsed.path:
            continue
        if clean_url not in seen:
            seen.add(clean_url)
            images.append(clean_url)

    return {
        "legacy_id": id_match.group(1),
        "product_url": page_url,
        "title_fa": title,
        "public_price_toman": price_toman,
        "price_source": price_source,
        "weight_grams": weight,
        "raw_category": raw_category,
        "mapped_radman_category": mapped_category,
        "description": description,
        "image_urls": images,
    }


def parse_sitemap_urls(xml_text: str) -> List[str]:
    urls: List[str] = []
    try:
        root = ET.fromstring(xml_text)
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] == "loc" and element.text:
                urls.append(element.text.strip())
    except ET.ParseError:
        urls.extend(re.findall(r"https://noghrehmashhad\.ir/[^<\s]+", xml_text))
    return list(dict.fromkeys(html.unescape(url) for url in urls))


def parse_product_links(page_url: str, source_html: str) -> List[str]:
    links = re.findall(r"href=[\"']([^\"']*/product/[0-9]+/[^\"']*)[\"']", source_html)
    return list(dict.fromkeys(urllib.parse.urljoin(page_url, html.unescape(link)) for link in links))


def discover_product_urls(
    fetcher: RateLimitedFetcher,
    *,
    category_urls: Sequence[str] = (),
) -> List[str]:
    discovered: List[str] = []
    if category_urls:
        # Controlled pilot: select at most the first public product from each
        # requested category rather than taking three products from one category.
        for category_url in category_urls:
            page = fetcher.fetch_text(category_url)
            links = parse_product_links(category_url, page)
            if links:
                discovered.append(links[0])
    else:
        index_xml = fetcher.fetch_text(SITEMAP_URL)
        index_urls = parse_sitemap_urls(index_xml)
        product_maps = [url for url in index_urls if "sitemap-product" in url]
        if not product_maps and any("/product/" in url for url in index_urls):
            discovered.extend(url for url in index_urls if "/product/" in url)
        for sitemap in product_maps:
            product_xml = fetcher.fetch_text(sitemap)
            discovered.extend(
                url for url in parse_sitemap_urls(product_xml) if "/product/" in url
            )
    return list(dict.fromkeys(discovered))


def _image_extension(url: str, content_type: str) -> str:
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
    if suffix in (".jpg", ".jpeg", ".png", ".webp"):
        return suffix
    guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
    return guessed if guessed in (".jpg", ".jpeg", ".png", ".webp") else ".jpg"


def write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def scrape_three(
    private_dir: Path,
    *,
    limit: int = MAX_PRODUCTS,
    category_urls: Sequence[str] = (),
    fetcher: Optional[RateLimitedFetcher] = None,
) -> List[Path]:
    validate_product_limit(limit)
    fetcher = fetcher or RateLimitedFetcher()
    fetcher.load_robots()
    selected_categories = tuple(category_urls) if category_urls else PILOT_CATEGORY_URLS
    urls = discover_product_urls(fetcher, category_urls=selected_categories)
    if len(urls) < limit:
        raise PilotError(
            f"only {len(urls)} representative product URL(s) discovered; expected {limit}"
        )

    product_dir = private_dir / "legacy-cache" / "products"
    image_dir = private_dir / "legacy-cache" / "original-images"
    product_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    image_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(product_dir, 0o700)
    os.chmod(image_dir, 0o700)

    outputs: List[Path] = []
    for product_url in urls[:limit]:
        source_html = fetcher.fetch_text(product_url)
        product = parse_product_html(product_url, source_html)
        legacy_id = str(product["legacy_id"])
        local_images = []
        for index, source_url in enumerate(product["image_urls"], start=1):
            data, headers = fetcher.fetch_bytes(
                str(source_url), max_bytes=MAX_IMAGE_BYTES
            )
            content_type = headers.get("content-type", "").lower()
            if content_type and not content_type.startswith("image/"):
                raise PilotError(f"source image returned non-image content: {source_url}")
            extension = _image_extension(str(source_url), content_type)
            filename = f"{legacy_id}-{index:02d}{extension}"
            destination = image_dir / filename
            image_tmp = destination.with_suffix(destination.suffix + ".tmp")
            image_tmp.write_bytes(data)
            os.chmod(image_tmp, 0o600)
            os.replace(image_tmp, destination)
            local_images.append(
                {
                    "source_url": source_url,
                    "local_filename": filename,
                    "bytes": len(data),
                }
            )
        product["downloaded_images"] = local_images
        product["scrape_policy"] = {
            "user_agent": fetcher.user_agent,
            "minimum_delay_seconds": fetcher.min_delay,
            "robots_respected": True,
            "private_api_used": False,
            "wordpress_imported": False,
        }
        destination = product_dir / f"{legacy_id}.json"
        write_json_atomic(destination, product)
        outputs.append(destination)
        print(
            f"[SCRAPE] legacy_id={legacy_id} category={product['mapped_radman_category']} "
            f"images={len(local_images)} json={destination}"
        )
    return outputs


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RADMAN public legacy catalog pilot")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--scrape", action="store_true")
    parser.add_argument("--limit", type=int, default=MAX_PRODUCTS)
    parser.add_argument("--category-url", action="append", default=[])
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path(os.environ.get("RADMAN_PRIVATE_DIR", str(Path.home() / ".config/radman"))),
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        validate_product_limit(args.limit)
        if args.plan or not args.scrape:
            print("RADMAN legacy catalog pilot plan")
            print(f"  robots: {ROBOTS_URL}")
            discovery = args.category_url or list(PILOT_CATEGORY_URLS)
            print(f"  controlled category discovery: {', '.join(discovery)}")
            print(f"  sitemap discovery capability: {SITEMAP_URL}")
            print(f"  user-agent: {USER_AGENT}")
            print(f"  minimum delay: {MIN_REQUEST_DELAY_SECONDS:.1f}s")
            print(f"  hard product maximum: {MAX_PRODUCTS}")
            print(f"  product JSON: {args.private_dir / 'legacy-cache/products'}")
            print(f"  original images: {args.private_dir / 'legacy-cache/original-images'}")
            print("  WordPress import: NEVER in this pilot")
            return 0
        outputs = scrape_three(
            args.private_dir,
            limit=args.limit,
            category_urls=args.category_url,
        )
        print(f"[DONE] scraped {len(outputs)} product(s); no WordPress operation performed")
        return 0
    except (PilotError, OSError, urllib.error.URLError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

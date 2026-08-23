#!/usr/bin/env python3
"""Publication-blocking QA for deterministic RADMAN product SEO packages."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.agent_product_seo import (  # noqa: E402
    GENERIC_AI_PHRASES,
    contains_internal_disclaimer,
    contains_phone,
    contains_unsupported_promise,
    normalize_text,
)
from agents.lib.product_identity import clean_public_product_title

SEO_PASS = "SEO_PASS"
SEO_REVIEW = "SEO_REVIEW"
SEO_BLOCKED = "SEO_BLOCKED"


def _price(value: Any) -> str:
    text = normalize_text(value)
    try:
        return str(int(float(text))) if text else ""
    except ValueError:
        return ""


def _package_value(record: Mapping[str, Any], key: str) -> Any:
    package = record.get("seo_package")
    if isinstance(package, str) and package:
        try:
            package = json.loads(package)
        except json.JSONDecodeError:
            package = {}
    if isinstance(package, dict) and package.get(key) not in {None, ""}:
        return package.get(key)
    mapping = {
        "seo_title": "rank_math_title",
        "meta_description": "rank_math_description",
        "short_description": "short_description",
    }
    return record.get(mapping.get(key, key), "")


def detect_duplicate_content(records: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    duplicates: List[Dict[str, Any]] = []
    for left_index, left in enumerate(records):
        left_text = normalize_text(
            f"{left.get('description', '')} {_package_value(left, 'meta_description')}"
        )
        if not left_text:
            continue
        for right in records[left_index + 1 :]:
            right_text = normalize_text(
                f"{right.get('description', '')} {_package_value(right, 'meta_description')}"
            )
            if not right_text:
                continue
            ratio = SequenceMatcher(None, left_text, right_text).ratio()
            if ratio >= 0.90:
                duplicates.append(
                    {
                        "left_legacy_id": left.get("legacy_id"),
                        "left_sku": left.get("sku"),
                        "right_legacy_id": right.get("legacy_id"),
                        "right_sku": right.get("sku"),
                        "similarity": f"{ratio:.4f}",
                        "status": "DUPLICATE_CONTENT",
                    }
                )
    return duplicates


def _schema_result(record: Mapping[str, Any]) -> Dict[str, Any]:
    visible_price = _price(record.get("price"))
    regular_price = _price(record.get("regular_price"))
    schema_price = _price(record.get("schema_price") or visible_price)
    currency = normalize_text(record.get("currency") or "IRT")
    schema_currency = normalize_text(record.get("schema_currency") or currency)
    stock_status = normalize_text(record.get("stock_status") or "")
    quantity_raw = record.get("stock_quantity")
    expected_availability = stock_status
    if quantity_raw not in {None, ""}:
        try:
            expected_availability = "instock" if int(float(str(quantity_raw))) > 0 else "outofstock"
        except ValueError:
            pass
    schema_availability = normalize_text(
        record.get("schema_availability") or expected_availability
    )
    stock_consistent = bool(
        not stock_status or stock_status == expected_availability
    )
    consistent = bool(
        visible_price
        and visible_price == regular_price == schema_price
        and currency == schema_currency
        and schema_availability == expected_availability
        and stock_consistent
    )
    return {
        "legacy_id": record.get("legacy_id"),
        "sku": record.get("sku"),
        "visible_price": visible_price,
        "regular_price": regular_price,
        "schema_price": schema_price,
        "currency": currency,
        "schema_currency": schema_currency,
        "woo_stock_status": stock_status,
        "availability": expected_availability,
        "schema_availability": schema_availability,
        "consistent": consistent,
    }


def evaluate_products(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    sku_counts: Dict[str, int] = {}
    for record in records:
        sku = normalize_text(record.get("sku")).casefold()
        if sku:
            sku_counts[sku] = sku_counts.get(sku, 0) + 1
    duplicates = detect_duplicate_content(records)
    duplicate_ids = {
        str(value)
        for row in duplicates
        for value in (row.get("left_legacy_id"), row.get("right_legacy_id"))
    }
    results: List[Dict[str, Any]] = []
    schema_rows: List[Dict[str, Any]] = []

    for record in records:
        blockers: List[str] = []
        reviews: List[str] = []
        status = normalize_text(record.get("status"))
        title = normalize_text(record.get("public_title") or record.get("title"))
        sku = normalize_text(record.get("sku"))
        legacy_id = normalize_text(record.get("legacy_id"))
        description = normalize_text(record.get("description"))
        short_description = normalize_text(_package_value(record, "short_description"))
        seo_title = normalize_text(_package_value(record, "seo_title"))
        meta_description = normalize_text(_package_value(record, "meta_description"))

        if status != "draft":
            blockers.append("STATUS_NOT_DRAFT")
        if not title:
            blockers.append("TITLE_MISSING")
        elif clean_public_product_title(title).cleanup_applied:
            blockers.append("TITLE_HAS_TRAILING_MODEL_CODE")
        if not sku:
            blockers.append("SKU_MISSING")
        elif sku_counts.get(sku.casefold(), 0) > 1:
            blockers.append("SKU_NOT_UNIQUE")
        if not legacy_id:
            blockers.append("LEGACY_IDENTITY_MISSING")
        if _price(record.get("regular_price")) != _price(record.get("price")):
            blockers.append("REGULAR_CURRENT_PRICE_MISMATCH")
        if normalize_text(record.get("sale_price_readonly")):
            blockers.append("SALE_PRICE_NOT_EMPTY")
        if not (record.get("category_ids") or record.get("category")):
            blockers.append("CATEGORY_MISSING")
        if int(record.get("featured_image_id") or 0) <= 0:
            blockers.append("FEATURED_IMAGE_MISSING")
        if not description:
            blockers.append("DESCRIPTION_MISSING")
        if not short_description:
            blockers.append("SHORT_DESCRIPTION_MISSING")
        if not seo_title:
            blockers.append("SEO_TITLE_MISSING")
        if not meta_description:
            blockers.append("META_DESCRIPTION_MISSING")

        public_text = " ".join(
            (title, description, short_description, seo_title, meta_description)
        )
        if contains_phone(public_text):
            blockers.append("PHONE_NUMBER_IN_PUBLIC_CONTENT")
        if contains_unsupported_promise(public_text):
            blockers.append("UNSUPPORTED_PROMISE")
        if contains_internal_disclaimer(public_text):
            blockers.append("INTERNAL_SYSTEM_DISCLAIMER")
        if any(phrase.casefold() in public_text.casefold() for phrase in GENERIC_AI_PHRASES):
            blockers.append("GENERIC_AI_PHRASE")
        if str(legacy_id) in duplicate_ids:
            blockers.append("DUPLICATE_CONTENT")
        if normalize_text(record.get("match_status")) == "LOW_CONFIDENCE":
            reviews.append("LOW_CONFIDENCE_SPEC_IDENTITY")
        if normalize_text(record.get("radman_requires_review")) == "YES":
            reviews.append("PRODUCT_REQUIRES_REVIEW")

        purity = normalize_text(record.get("spec_purity") or record.get("spec_silver_purity"))
        if purity and not re.search(r"(?<![0-9])(800|830|835|900|925|950|999)(?![0-9])", purity):
            blockers.append("PURITY_INCONSISTENT")
        weight = normalize_text(record.get("spec_weight") or record.get("spec_weight_grams"))
        if weight:
            try:
                if not (0 < float(re.search(r"[0-9]+(?:\.[0-9]+)?", weight).group(0)) <= 100):
                    blockers.append("WEIGHT_INCONSISTENT")
            except (AttributeError, ValueError):
                blockers.append("WEIGHT_INCONSISTENT")

        if any(key in record for key in ("aggregateRating", "aggregate_rating", "generated_reviews")):
            blockers.append("UNSUPPORTED_REVIEW_OR_RATING")

        schema = _schema_result(record)
        schema_rows.append(schema)
        if not schema["consistent"]:
            blockers.append("SCHEMA_VISIBLE_DATA_MISMATCH")

        final_status = SEO_BLOCKED if blockers else (SEO_REVIEW if reviews else SEO_PASS)
        results.append(
            {
                "wp_id": record.get("product_id") or record.get("wordpress_product_id"),
                "legacy_id": record.get("legacy_id"),
                "sku": sku,
                "title": title,
                "seo_status": final_status,
                "publication_blocked": final_status == SEO_BLOCKED,
                "blockers": list(dict.fromkeys(blockers)),
                "review_flags": list(dict.fromkeys(reviews)),
            }
        )
    return {
        "results": results,
        "duplicates": duplicates,
        "schema": schema_rows,
        "summary": {
            "SEO_PASS": sum(row["seo_status"] == SEO_PASS for row in results),
            "SEO_REVIEW": sum(row["seo_status"] == SEO_REVIEW for row in results),
            "SEO_BLOCKED": sum(row["seo_status"] == SEO_BLOCKED for row in results),
        },
    }


def write_qa_reports(payload: Mapping[str, Any], private_dir: Path) -> Dict[str, Path]:
    private_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    results = list(payload.get("results", []))
    duplicates = list(payload.get("duplicates", []))
    schema = list(payload.get("schema", []))
    paths = {
        "product": private_dir / "product-seo-report.csv",
        "persian": private_dir / "product-seo-report-fa.txt",
        "duplicate": private_dir / "duplicate-content-report.csv",
        "schema": private_dir / "schema-consistency-report.csv",
        "blockers": private_dir / "publication-blockers.csv",
    }
    product_columns = (
        "wp_id", "legacy_id", "sku", "title", "seo_status",
        "publication_blocked", "blockers", "review_flags",
    )
    with paths["product"].open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=product_columns)
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    **{key: row.get(key, "") for key in product_columns},
                    "blockers": " | ".join(row.get("blockers", [])),
                    "review_flags": " | ".join(row.get("review_flags", [])),
                }
            )
    duplicate_columns = (
        "left_legacy_id", "left_sku", "right_legacy_id", "right_sku",
        "similarity", "status",
    )
    with paths["duplicate"].open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=duplicate_columns)
        writer.writeheader()
        writer.writerows(duplicates)
    schema_columns = (
        "legacy_id", "sku", "visible_price", "regular_price", "schema_price",
        "currency", "schema_currency", "woo_stock_status", "availability",
        "schema_availability", "consistent",
    )
    with paths["schema"].open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=schema_columns)
        writer.writeheader()
        writer.writerows(schema)
    with paths["blockers"].open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=product_columns)
        writer.writeheader()
        for row in results:
            if row.get("publication_blocked"):
                writer.writerow(
                    {
                        **{key: row.get(key, "") for key in product_columns},
                        "blockers": " | ".join(row.get("blockers", [])),
                        "review_flags": " | ".join(row.get("review_flags", [])),
                    }
                )
    lines = [
        "گزارش کنترل کیفیت SEO محصولات رادمان",
        f"قبول: {payload.get('summary', {}).get('SEO_PASS', 0)}",
        f"بازبینی: {payload.get('summary', {}).get('SEO_REVIEW', 0)}",
        f"مسدود: {payload.get('summary', {}).get('SEO_BLOCKED', 0)}",
        "",
        "wp_id | SKU | وضعیت | مسدودکننده ها",
    ]
    for row in results:
        lines.append(
            f"{row.get('wp_id')} | {row.get('sku')} | {row.get('seo_status')} | "
            + ("، ".join(row.get("blockers", [])) or "—")
        )
    paths["persian"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    for path in paths.values():
        os.chmod(path, 0o600)
    return paths


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    records = json.loads(args.input_json.read_text(encoding="utf-8"))
    payload = evaluate_products(records)
    write_qa_reports(payload, args.output_dir)
    return 2 if payload["summary"][SEO_BLOCKED] else 0


if __name__ == "__main__":
    raise SystemExit(main())

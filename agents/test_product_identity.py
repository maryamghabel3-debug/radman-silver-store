#!/usr/bin/env python3
"""Unit tests for luxury public-title cleaning and identity preservation."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.lib.product_identity import (
    build_legacy_identity_key,
    clean_public_product_title,
)


def test_required_title_cleaning_examples() -> None:
    cases = {
        "انگشتر زیبای عقیق زرد حسین مظلوم کد 1058": (
            "انگشتر زیبای عقیق زرد حسین مظلوم",
            "1058",
            "کد",
        ),
        "انگشتر عقیق کد۱۰۵۹": ("انگشتر عقیق", "1059", "کد"),
        "عقیق انگشتر نقره عیار 9۲۵ کد: 10۶۲": (
            "عقیق انگشتر نقره عیار 9۲۵",
            "1062",
            "کد",
        ),
        "انگشتر صفوی - کد مدل 1007": (
            "انگشتر صفوی",
            "1007",
            "کد مدل",
        ),
        "گردنبند نقره | کد محصول 1008": (
            "گردنبند نقره",
            "1008",
            "کد محصول",
        ),
        "دستبند نقره — شناسه کالا 1057": (
            "دستبند نقره",
            "1057",
            "شناسه کالا",
        ),
        "مدال نقره: کد مدل 100۷": ("مدال نقره", "1007", "کد مدل"),
    }
    for raw, expected in cases.items():
        result = clean_public_product_title(raw)
        assert (result.cleaned_title, result.extracted_code, result.code_label) == expected
        assert result.cleanup_applied
        assert result.cleanup_status == "CLEANED"
        assert result.original_title == raw
    print("PASS: required labels, separators, compact/mixed Persian digits clean correctly")


def test_meaningful_numbers_and_unlabelled_titles_are_preserved() -> None:
    titles = (
        "نقره عیار 925",
        "انگشتر 925 مردانه",
        "طرح 12 پر",
        "گردنبند مدل 2024",
        "انگشتر نقره عیار 9۲۵",
    )
    for title in titles:
        result = clean_public_product_title(title)
        assert result.cleaned_title == title
        assert result.extracted_code == ""
        assert not result.cleanup_applied
        assert result.cleanup_status == "UNCHANGED"
    print("PASS: meaningful and unlabelled numbers remain in public titles")


def test_empty_title_is_never_returned() -> None:
    empty = clean_public_product_title("")
    assert empty.cleaned_title == "محصول نقره رادمان"
    assert empty.review_flags == ("EMPTY_ORIGINAL_TITLE_FALLBACK",)
    only_code = clean_public_product_title("کد 1058")
    assert only_code.cleaned_title == "کد 1058"
    assert not only_code.cleanup_applied
    assert "TITLE_CLEANUP_WOULD_EMPTY_TITLE" in only_code.review_flags
    print("PASS: cleaner never returns an empty customer-facing title")


def test_deterministic_identity_key() -> None:
    assert build_legacy_identity_key("۳۶۴۲", "۱۰۵۸") == "3642:1058"
    assert build_legacy_identity_key(3642, "NM-3642") == "3642:NM-3642"
    print("PASS: legacy identity key is deterministic and digit-normalized")


def main() -> int:
    test_required_title_cleaning_examples()
    test_meaningful_numbers_and_unlabelled_titles_are_preserved()
    test_empty_title_is_never_returned()
    test_deterministic_identity_key()
    print("ALL PRODUCT IDENTITY TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

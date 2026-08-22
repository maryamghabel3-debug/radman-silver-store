"""Shared public-title cleaning and deterministic legacy identity helpers."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, Tuple

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_CODE_SUFFIX = re.compile(
    r"(?P<lead>^|[\s\-–—|:：]+)"
    r"(?P<label>شناسه[\s\u200c]*کالا|کد(?:[\s\u200c]*(?:مدل|محصول))?)"
    r"[\s\u200c]*[:：]?[\s\u200c]*"
    r"(?P<code>[0-9۰-۹٠-٩]{2,8})[\s\u200c]*$",
    re.IGNORECASE,
)
_TRAILING_CODE_LABEL = re.compile(
    r"(?:شناسه[\s\u200c]*کالا|کد(?:[\s\u200c]*(?:مدل|محصول))?)"
    r"[\s\u200c]*[:：]?[\s\u200c]*\S+[\s\u200c]*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TitleCleanResult:
    original_title: str
    cleaned_title: str
    extracted_code: str
    code_label: str
    cleanup_applied: bool
    review_flags: Tuple[str, ...]

    @property
    def cleanup_status(self) -> str:
        if self.review_flags:
            return "REVIEW"
        return "CLEANED" if self.cleanup_applied else "UNCHANGED"

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["review_flags"] = list(self.review_flags)
        value["cleanup_status"] = self.cleanup_status
        return value


def normalize_identity_digits(value: Any) -> str:
    return str(value if value is not None else "").translate(_DIGITS)


def normalize_title_whitespace(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value if value is not None else "")).strip()


def clean_public_product_title(raw_title: str) -> TitleCleanResult:
    original = str(raw_title if raw_title is not None else "")
    display = normalize_title_whitespace(original)
    if not display:
        return TitleCleanResult(
            original_title=original,
            cleaned_title="محصول نقره رادمان",
            extracted_code="",
            code_label="",
            cleanup_applied=False,
            review_flags=("EMPTY_ORIGINAL_TITLE_FALLBACK",),
        )

    match = _CODE_SUFFIX.search(display)
    if not match:
        flags: Tuple[str, ...] = tuple()
        if _TRAILING_CODE_LABEL.search(display):
            flags = ("TRAILING_CODE_LABEL_UNPARSED",)
        return TitleCleanResult(original, display, "", "", False, flags)

    cleaned = normalize_title_whitespace(display[: match.start()]).strip(
        " -–—|:："
    )
    if not cleaned:
        return TitleCleanResult(
            original,
            display,
            normalize_identity_digits(match.group("code")),
            normalize_title_whitespace(match.group("label")),
            False,
            ("TITLE_CLEANUP_WOULD_EMPTY_TITLE",),
        )
    return TitleCleanResult(
        original_title=original,
        cleaned_title=cleaned,
        extracted_code=normalize_identity_digits(match.group("code")),
        code_label=normalize_title_whitespace(match.group("label")),
        cleanup_applied=True,
        review_flags=tuple(),
    )


def build_legacy_identity_key(legacy_product_id: Any, model_code: Any) -> str:
    identifier = normalize_identity_digits(legacy_product_id).strip()
    code = normalize_identity_digits(model_code).strip()
    if not identifier or not code:
        raise ValueError("legacy_product_id and model_code are required")
    return f"{identifier}:{code}"

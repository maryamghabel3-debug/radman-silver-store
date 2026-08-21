#!/usr/bin/env python3
"""Conservative, deterministic gemstone classifier for legacy rings.

Text evidence is authoritative and evaluated before any image heuristic. Visual
heuristics are deliberately conservative: ambiguity never receives the lower
large-stone price rate.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

STONE_CLASSES = {"no_stone", "small_stone", "large_stone", "uncertain"}


@dataclass(frozen=True)
class ImageEvidence:
    path: str
    readable: bool
    candidate_share: float
    central_concentration: float
    qualifies_as_large: bool
    note: str


@dataclass(frozen=True)
class Classification:
    stone_class: str
    confidence: float
    source: str
    requires_review: bool
    evidence: Tuple[str, ...]
    image_evidence: Tuple[ImageEvidence, ...] = tuple()

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["evidence"] = list(self.evidence)
        value["image_evidence"] = [asdict(item) for item in self.image_evidence]
        return value


def _normalized_text(parts: Iterable[Any]) -> str:
    text = " ".join(str(part or "") for part in parts)
    return (
        text.casefold()
        .replace("ي", "ی")
        .replace("ك", "ک")
        .replace("ۀ", "ه")
        .replace("\u200c", " ")
    )


def classify_text(parts: Iterable[Any]) -> Optional[Classification]:
    text = _normalized_text(parts)
    if not text.strip():
        return None

    no_stone = (
        r"بدون\s*(?:نگین|سنگ)",
        r"فاقد\s*(?:نگین|سنگ)",
        r"بی\s*(?:نگین|سنگ)",
    )
    large = (
        r"(?:نگین|سنگ)\s*(?:بسیار\s*)?(?:درشت|بزرگ)",
        r"(?:درشت|بزرگ)\s*(?:نگین|سنگ)",
        r"(?:فیروزه|عقیق|اونیکس|یاقوت|زمرد)\s*(?:درشت|بزرگ)",
    )
    small = (
        r"(?:نگین|سنگ)\s*(?:ریز|کوچک)",
        r"(?:ریز|کوچک)\s*(?:نگین|سنگ)",
        r"نگین\s*کاری\s*(?:ریز|ظریف)",
    )
    generic = (
        r"نگین|سنگ|فیروزه|عقیق|اونیکس|یاقوت|زمرد|agate|turquoise|onyx|gem",
    )

    matches = {
        "no_stone": [pattern for pattern in no_stone if re.search(pattern, text)],
        "large_stone": [pattern for pattern in large if re.search(pattern, text)],
        "small_stone": [pattern for pattern in small if re.search(pattern, text)],
    }
    positive = [name for name, evidence in matches.items() if evidence]
    if len(positive) > 1:
        return Classification(
            "uncertain",
            0.25,
            "text_conflict",
            True,
            tuple(f"matched {name}: {matches[name][0]}" for name in positive),
        )
    if positive:
        stone_class = positive[0]
        confidence = {
            "no_stone": 0.98,
            "small_stone": 0.94,
            "large_stone": 0.92,
        }[stone_class]
        return Classification(
            stone_class,
            confidence,
            "text",
            False,
            (f"matched explicit text pattern: {matches[stone_class][0]}",),
        )
    if any(re.search(pattern, text) for pattern in generic):
        return Classification(
            "uncertain",
            0.55,
            "text_generic",
            True,
            ("text mentions a stone but does not establish size",),
        )
    return None


def analyze_image(path: Path) -> ImageEvidence:
    """Find a localized colored center candidate without changing the image."""
    try:
        from PIL import Image, ImageChops, ImageOps, ImageStat

        with Image.open(path) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
            image.thumbnail((256, 256))
        saturation = image.convert("HSV").getchannel("S")
        luminance = image.convert("L")
        saturation_mask = saturation.point(lambda value: 255 if value >= 82 else 0)
        luminance_mask = luminance.point(
            lambda value: 255 if 31 <= value <= 235 else 0
        )
        candidate = ImageChops.multiply(saturation_mask, luminance_mask)
        width, height = candidate.size
        y0, y1 = int(height * 0.25), int(height * 0.75)
        x0, x1 = int(width * 0.25), int(width * 0.75)
        center = candidate.crop((x0, y0, x1, y1))
        center_share = ImageStat.Stat(center).mean[0] / 255.0 if center.width else 0.0
        total_count = (ImageStat.Stat(candidate).mean[0] / 255.0) * width * height
        center_count = center_share * center.width * center.height
        outside_size = width * height - center.width * center.height
        outside_share = (total_count - center_count) / max(1, outside_size)
        concentration = center_share / max(0.001, outside_share)
        qualifies = 0.008 <= center_share <= 0.12 and concentration >= 1.8
        return ImageEvidence(
            str(path),
            True,
            round(center_share, 6),
            round(concentration, 4),
            qualifies,
            "localized chroma candidate" if qualifies else "no reliable localized candidate",
        )
    except Exception as exc:  # Pillow/NumPy absence and corrupt files are review cases.
        return ImageEvidence(str(path), False, 0.0, 0.0, False, f"unreadable: {exc}")


def classify_images(paths: Sequence[Path]) -> Classification:
    evidence = tuple(analyze_image(path) for path in paths)
    readable = [item for item in evidence if item.readable]
    qualifying = [item for item in readable if item.qualifies_as_large]
    # Two independent views are required. Image evidence cannot override explicit text.
    if len(readable) >= 2 and len(qualifying) >= 2:
        agreement = len(qualifying) / len(readable)
        if agreement >= 0.66:
            confidence = min(0.89, 0.85 + 0.02 * (len(qualifying) - 2))
            return Classification(
                "large_stone",
                confidence,
                "multi_image_heuristic",
                False,
                (f"{len(qualifying)}/{len(readable)} views contain a localized candidate",),
                evidence,
            )
    return Classification(
        "uncertain",
        0.30 if readable else 0.0,
        "multi_image_heuristic",
        True,
        ("images do not establish stone size with high confidence",),
        evidence,
    )


def classify_product(
    *,
    category: str,
    title: str = "",
    short_description: str = "",
    description: str = "",
    image_paths: Sequence[Path] = tuple(),
) -> Classification:
    normalized_category = str(category or "").strip().lower()
    if normalized_category != "rings":
        return Classification(
            "uncertain",
            1.0,
            "not_applicable",
            False,
            ("gemstone pricing classification applies only to rings",),
        )

    text_result = classify_text((title, short_description, description))
    if text_result is not None:
        return text_result
    if image_paths:
        return classify_images(tuple(Path(path) for path in image_paths))
    return Classification(
        "uncertain",
        0.0,
        "insufficient_evidence",
        True,
        ("no explicit text or readable image evidence",),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="JSON product list")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    products = payload if isinstance(payload, list) else payload.get("products", [])
    results = []
    for product in products:
        result = classify_product(
            category=product.get("category", ""),
            title=product.get("title", ""),
            short_description=product.get("short_description", ""),
            description=product.get("description", ""),
            image_paths=[Path(value) for value in product.get("original_image_paths", [])],
        )
        results.append({"legacy_id": product.get("legacy_id"), **result.to_dict()})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

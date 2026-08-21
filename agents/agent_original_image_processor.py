#!/usr/bin/env python3
"""Color-safe original-image optimizer and integrity gate.

The approved path is intentionally limited to EXIF orientation, aspect-preserving
resize, ICC-aware WebP encoding, and optional luminance-only mild sharpening.
It never crops, reconstructs, segments, or changes the photographed background.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

MAX_EDGE = 1600
WEBP_QUALITY = 90
MAX_ENLARGEMENT = 1.25
MAX_MEAN_ABS_DRIFT = 6.0
MAX_P95_ABS_DRIFT = 20.0
MAX_CHANNEL_MEAN_DRIFT = 3.0
MIN_DETAIL_RATIO = 0.72
MAX_DETAIL_RATIO = 1.30


@dataclass(frozen=True)
class ImageQAResult:
    original_path: str
    processed_path: Optional[str]
    selected_import_path: str
    original_sha256: str
    original_dimensions: Tuple[int, int]
    processed_dimensions: Optional[Tuple[int, int]]
    resize_scale: Optional[float]
    mean_abs_drift: Optional[float]
    p95_abs_drift: Optional[float]
    channel_mean_drift: Optional[float]
    detail_ratio: Optional[float]
    icc_preserved: bool
    qa_status: str
    fallback_to_original: bool
    reasons: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["original_dimensions"] = list(self.original_dimensions)
        if self.processed_dimensions is not None:
            result["processed_dimensions"] = list(self.processed_dimensions)
        result["reasons"] = list(self.reasons)
        return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resample_lanczos() -> int:
    from PIL import Image

    return getattr(Image, "Resampling", Image).LANCZOS


def _oriented_copy(path: Path):
    from PIL import Image, ImageOps

    opened = Image.open(path)
    icc = opened.info.get("icc_profile")
    oriented = ImageOps.exif_transpose(opened)
    oriented.load()
    if oriented.mode not in {"RGB", "RGBA"}:
        oriented = oriented.convert("RGBA" if "A" in oriented.getbands() else "RGB")
    opened.close()
    return oriented, icc


def _resize_dimensions(width: int, height: int) -> Tuple[int, int, float]:
    scale = min(1.0, MAX_EDGE / max(width, height))
    # No enlargement is performed; therefore the 1.25x hard ceiling is automatic.
    return max(1, round(width * scale)), max(1, round(height * scale)), scale


def _mild_luminance_sharpen(image):
    from PIL import Image, ImageFilter

    if image.mode == "RGBA":
        alpha = image.getchannel("A")
        rgb = image.convert("RGB")
    else:
        alpha = None
        rgb = image
    y, cb, cr = rgb.convert("YCbCr").split()
    y = y.filter(ImageFilter.UnsharpMask(radius=0.6, percent=35, threshold=3))
    result = Image.merge("YCbCr", (y, cb, cr)).convert("RGB")
    if alpha is not None:
        result.putalpha(alpha)
    return result


def _visible_rgb(image):
    from PIL import Image

    if image.mode == "RGBA":
        # Compare visible color on white while alpha integrity is checked separately.
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        background.alpha_composite(image)
        return background.convert("RGB")
    return image.convert("RGB")


def _detail_energy(image) -> float:
    from PIL import ImageChops, ImageStat

    luminance = image.convert("L")
    width, height = luminance.size
    dx = 0.0
    dy = 0.0
    if width > 1:
        dx_image = ImageChops.difference(
            luminance.crop((1, 0, width, height)),
            luminance.crop((0, 0, width - 1, height)),
        )
        dx = ImageStat.Stat(dx_image).mean[0]
    if height > 1:
        dy_image = ImageChops.difference(
            luminance.crop((0, 1, width, height)),
            luminance.crop((0, 0, width, height - 1)),
        )
        dy = ImageStat.Stat(dy_image).mean[0]
    return float(dx + dy)


def _percentile_from_rgb_histogram(histogram: Sequence[int], percentile: float) -> float:
    counts = [
        histogram[value] + histogram[256 + value] + histogram[512 + value]
        for value in range(256)
    ]
    threshold = sum(counts) * percentile
    cumulative = 0
    for value, count in enumerate(counts):
        cumulative += count
        if cumulative >= threshold:
            return float(value)
    return 255.0


def _quality_metrics(reference, candidate) -> Dict[str, float]:
    from PIL import ImageChops, ImageStat

    ref = _visible_rgb(reference)
    out = _visible_rgb(candidate)
    difference = ImageChops.difference(ref, out)
    drift = ImageStat.Stat(difference)
    ref_means = ImageStat.Stat(ref).mean
    out_means = ImageStat.Stat(out).mean
    ref_detail = _detail_energy(ref)
    out_detail = _detail_energy(out)
    return {
        "mean_abs_drift": float(sum(drift.mean) / 3.0),
        "p95_abs_drift": _percentile_from_rgb_histogram(difference.histogram(), 0.95),
        "channel_mean_drift": float(
            max(abs(ref_means[index] - out_means[index]) for index in range(3))
        ),
        "detail_ratio": out_detail / max(0.001, ref_detail),
    }


def process_one(
    original_path: Path,
    processed_path: Path,
    *,
    sharpen: bool = True,
) -> ImageQAResult:
    from PIL import Image

    original_path = original_path.resolve()
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    before_hash = sha256_file(original_path)
    reasons: List[str] = []
    original_dimensions = (0, 0)
    icc_preserved = False
    try:
        source, icc = _oriented_copy(original_path)
        original_dimensions = source.size
        width, height, scale = _resize_dimensions(*source.size)
        if scale > MAX_ENLARGEMENT:
            raise ValueError("enlargement exceeds 1.25x")
        reference = source.resize((width, height), _resample_lanczos())
        candidate = _mild_luminance_sharpen(reference) if sharpen else reference.copy()
        save_options: Dict[str, Any] = {
            "format": "WEBP",
            "quality": WEBP_QUALITY,
            "method": 6,
        }
        if icc:
            save_options["icc_profile"] = icc
        candidate.save(processed_path, **save_options)

        with Image.open(processed_path) as decoded:
            decoded.load()
            decoded_copy = decoded.copy()
            icc_preserved = bool(icc and decoded.info.get("icc_profile"))
        metrics = _quality_metrics(reference, decoded_copy)
        if decoded_copy.size != (width, height):
            reasons.append("dimension mismatch")
        if metrics["mean_abs_drift"] > MAX_MEAN_ABS_DRIFT:
            reasons.append("mean color drift exceeds gate")
        if metrics["p95_abs_drift"] > MAX_P95_ABS_DRIFT:
            reasons.append("p95 color drift exceeds gate")
        if metrics["channel_mean_drift"] > MAX_CHANNEL_MEAN_DRIFT:
            reasons.append("channel color drift exceeds gate")
        if not (MIN_DETAIL_RATIO <= metrics["detail_ratio"] <= MAX_DETAIL_RATIO):
            reasons.append("detail retention ratio exceeds gate")
        if icc and not icc_preserved:
            reasons.append("embedded ICC profile was not retained")
        if source.mode == "RGBA" and decoded_copy.mode != "RGBA":
            reasons.append("alpha channel was not retained")

        hash_after = sha256_file(original_path)
        if hash_after != before_hash:
            reasons.append("original file checksum changed")

        passed = not reasons
        selected = processed_path if passed else original_path
        source.close()
        reference.close()
        candidate.close()
        decoded_copy.close()
        return ImageQAResult(
            str(original_path),
            str(processed_path),
            str(selected),
            before_hash,
            original_dimensions,
            (width, height),
            round(scale, 6),
            round(metrics["mean_abs_drift"], 4),
            round(metrics["p95_abs_drift"], 4),
            round(metrics["channel_mean_drift"], 4),
            round(metrics["detail_ratio"], 4),
            icc_preserved,
            "PASS" if passed else "FAIL",
            not passed,
            tuple(reasons),
        )
    except Exception as exc:
        return ImageQAResult(
            str(original_path),
            str(processed_path) if processed_path.exists() else None,
            str(original_path),
            before_hash,
            original_dimensions,
            None,
            None,
            None,
            None,
            None,
            None,
            False,
            "FAIL",
            True,
            (f"processing error: {exc}",),
        )


def _sheet_panel(image, width: int, height: int):
    from PIL import Image, ImageOps

    copy = ImageOps.exif_transpose(image).convert("RGB")
    copy.thumbnail((width, height), _resample_lanczos())
    panel = Image.new("RGB", (width, height), "white")
    x = (width - copy.width) // 2
    y = (height - copy.height) // 2
    panel.paste(copy, (x, y))
    return panel


def make_qa_sheet(results: Sequence[ImageQAResult], output_path: Path) -> None:
    from PIL import Image, ImageDraw

    if not results:
        return
    panel_width, panel_height, header = 560, 430, 58
    rows = len(results)
    sheet = Image.new("RGB", (panel_width * 2, (panel_height + header) * rows), "white")
    draw = ImageDraw.Draw(sheet)
    for index, result in enumerate(results):
        y = index * (panel_height + header)
        with Image.open(result.original_path) as original:
            original_panel = _sheet_panel(original, panel_width, panel_height)
        after_path = result.processed_path if result.processed_path else result.original_path
        try:
            with Image.open(after_path) as after:
                after_panel = _sheet_panel(after, panel_width, panel_height)
        except Exception:
            after_panel = Image.new("RGB", (panel_width, panel_height), "#eeeeee")
        sheet.paste(original_panel, (0, y + header))
        sheet.paste(after_panel, (panel_width, y + header))
        draw.text((12, y + 8), f"BEFORE | SHA {result.original_sha256[:12]}", fill="black")
        draw.text(
            (panel_width + 12, y + 8),
            f"AFTER | QA {result.qa_status} | fallback {result.fallback_to_original}",
            fill="black" if result.qa_status == "PASS" else "#a00000",
        )
        draw.text(
            (panel_width + 12, y + 30),
            f"drift {result.mean_abs_drift} | p95 {result.p95_abs_drift} | detail {result.detail_ratio}",
            fill="#333333",
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, format="JPEG", quality=92)


def process_product(
    legacy_id: str,
    original_paths: Sequence[Path],
    private_dir: Path,
    qa_dir: Path,
    *,
    sharpen: bool = True,
) -> Dict[str, Any]:
    output_dir = private_dir / "legacy-cache" / "processed-images" / str(legacy_id)
    results = []
    for index, original in enumerate(original_paths, start=1):
        output = output_dir / f"{index:02d}.webp"
        results.append(process_one(Path(original), output, sharpen=sharpen))
    sheet_path = qa_dir / f"{legacy_id}-before-after.jpg"
    make_qa_sheet(results, sheet_path)
    return {
        "legacy_id": str(legacy_id),
        "qa_status": "PASS" if results and all(r.qa_status == "PASS" for r in results) else "FAIL",
        "optimized_featured_approved": bool(results and results[0].qa_status == "PASS"),
        "selected_import_paths": [r.selected_import_path for r in results],
        "qa_sheet": str(sheet_path) if results else None,
        "images": [r.to_dict() for r in results],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Scraped product JSON")
    parser.add_argument("--output", type=Path, required=True, help="QA JSON report")
    parser.add_argument("--private-dir", type=Path, default=None)
    parser.add_argument("--qa-dir", type=Path, default=None)
    parser.add_argument("--no-sharpen", action="store_true")
    args = parser.parse_args()

    private_dir = args.private_dir or Path(
        os.environ.get("RADMAN_PRIVATE_DIR", "/home/radmansi/private")
    )
    qa_dir = args.qa_dir or private_dir / "legacy-cache" / "reports" / "image-qa"
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    products = payload if isinstance(payload, list) else payload.get("products", [])
    results = []
    for product in products:
        results.append(
            process_product(
                str(product["legacy_id"]),
                [Path(path) for path in product.get("original_image_paths", [])],
                private_dir,
                qa_dir,
                sharpen=not args.no_sharpen,
            )
        )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rules": {
            "max_edge": MAX_EDGE,
            "webp_quality": WEBP_QUALITY,
            "no_enlargement_over": MAX_ENLARGEMENT,
            "fallback": "untouched original",
        },
        "products": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0 if all(item["qa_status"] == "PASS" for item in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())

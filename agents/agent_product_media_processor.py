#!/usr/bin/env python3
"""RADMAN SILVER — license-gated, offline product media QA processor.

Uses an explicit local rembg session to extract an alpha mask, composites only
real source pixels on three non-generative backgrounds, and produces QA reports.
No WordPress operation and no model download is permitted.
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MAX_PRODUCTS = 3
OUTPUT_SIZE = (1600, 1600)
WEBP_QUALITY = 85
EVALUATION_LABEL = "EVALUATION ONLY — NOT FOR COMMERCIAL PUBLICATION"
PRODUCTION_MODELS = {"birefnet-general-lite", "u2net"}
BRIA_ALIASES = {"bria-rmbg", "bria-rmbg-2.0"}

MODEL_METADATA = {
    "birefnet-general-lite": {
        "session_name": "birefnet-general-lite",
        "expected_filename": "birefnet-general-lite.onnx",
        "official_filename": "BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx",
    },
    "u2net": {
        "session_name": "u2net",
        "expected_filename": "u2net.onnx",
        "official_filename": "u2net.onnx",
    },
    "bria-rmbg": {
        "session_name": "bria-rmbg",
        "expected_filename": "bria-rmbg.onnx",
        "official_filename": "bria-rmbg-2.0.onnx",
    },
}


class MediaPilotError(RuntimeError):
    pass


class ModelMissingError(MediaPilotError):
    pass


@dataclass
class ModelSpec:
    requested_name: str
    session_name: str
    expected_filename: str
    official_filename: str
    expected_path: Path
    candidate_paths: List[Path]
    existing_path: Optional[Path]
    rembg_version: str

    def missing_instructions(self) -> str:
        candidates = "\n".join(f"  - {path}" for path in self.candidate_paths)
        return (
            "REQUESTED MODEL IS MISSING — NO DOWNLOAD WAS ATTEMPTED\n"
            f"MODEL_NAME: {self.requested_name}\n"
            f"expected filename: {self.expected_filename}\n"
            f"expected absolute path: {self.expected_path}\n"
            f"official model filename: {self.official_filename}\n"
            f"checked paths:\n{candidates}\n"
            "Owner upload instructions:\n"
            "  1. Obtain the official model file on a licensed external workstation.\n"
            "  2. In cPanel File Manager, create the expected directory outside public_html.\n"
            f"  3. Upload {self.official_filename}.\n"
            f"  4. Rename it to {self.expected_filename} at the exact expected path.\n"
            "  5. Re-run --plan, then --process-three.\n"
            "The host script will not access GitHub or any model download URL."
        )


def validate_product_limit(limit: int) -> int:
    if limit < 1 or limit > MAX_PRODUCTS:
        raise MediaPilotError(f"media pilot limit must be between 1 and {MAX_PRODUCTS}")
    return limit


def validate_model_policy(model_name: Optional[str], evaluation_only: bool) -> str:
    if not model_name:
        raise MediaPilotError(
            "MODEL_NAME is required explicitly; use birefnet-general-lite or u2net"
        )
    normalized = model_name.strip().lower()
    if normalized in PRODUCTION_MODELS:
        return normalized
    if normalized in BRIA_ALIASES:
        if not evaluation_only:
            raise MediaPilotError(
                "BRIA IS BLOCKED: set IMAGE_PIPELINE_EVALUATION_ONLY=1 only for internal evaluation"
            )
        return "bria-rmbg"
    raise MediaPilotError(
        "MODEL_NAME is not allowed; production choices are birefnet-general-lite and u2net"
    )


def _fallback_roots(model_name: str) -> List[Path]:
    home = Path.home()
    u2net_home = os.environ.get("U2NET_HOME")
    rembg_home = os.environ.get("REMBG_HOME")
    xdg_home = os.environ.get("XDG_DATA_HOME")
    if u2net_home:
        root = Path(u2net_home).expanduser()
    elif rembg_home:
        root = Path(rembg_home).expanduser()
    elif xdg_home:
        root = Path(xdg_home).expanduser() / "rembg"
    else:
        root = home / ".rembg"
    legacy = Path(u2net_home).expanduser() if u2net_home else home / ".u2net"
    filename = MODEL_METADATA[model_name]["expected_filename"]
    return [root / "models" / model_name / filename, legacy / filename]


def _load_rembg() -> Any:
    try:
        import rembg  # type: ignore
    except ImportError as exc:
        raise MediaPilotError(
            "rembg is not installed in this Python environment; use the host Python 3.11 environment"
        ) from exc
    return rembg


def resolve_model_spec(model_name: str, rembg_module: Optional[Any] = None) -> ModelSpec:
    canonical = "bria-rmbg" if model_name in BRIA_ALIASES else model_name
    metadata = MODEL_METADATA[canonical]
    session_name = metadata["session_name"]
    expected_filename = metadata["expected_filename"]
    candidates: List[Path] = []
    version = "not-imported"

    if rembg_module is None:
        try:
            rembg_module = _load_rembg()
        except MediaPilotError:
            rembg_module = None

    if rembg_module is not None:
        version = str(getattr(rembg_module, "__version__", "unknown"))
        try:
            sessions_class = rembg_module.sessions.sessions_class
        except AttributeError:
            try:
                from rembg.sessions import sessions_class  # type: ignore
            except ImportError as exc:
                raise MediaPilotError("cannot inspect installed rembg session registry") from exc
        session_class = next(
            (candidate for candidate in sessions_class if candidate.name() == session_name),
            None,
        )
        if session_class is None:
            raise MediaPilotError(
                f"installed rembg does not provide the requested session: {session_name}"
            )

        try:
            source = inspect.getsource(session_class.download_models)
        except (OSError, TypeError):
            source = ""
        if hasattr(session_class, "model_dir") and (
            "model_dir" in source or not hasattr(session_class, "u2net_home")
        ):
            candidates.append(Path(session_class.model_dir()).expanduser() / expected_filename)
        elif hasattr(session_class, "u2net_home"):
            candidates.append(Path(session_class.u2net_home()).expanduser() / expected_filename)
        if hasattr(session_class, "legacy_home"):
            candidates.append(Path(session_class.legacy_home()).expanduser() / expected_filename)
        if hasattr(session_class, "model_dir"):
            candidates.append(Path(session_class.model_dir()).expanduser() / expected_filename)

    candidates.extend(_fallback_roots(canonical))
    unique_candidates: List[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        absolute = candidate.resolve(strict=False)
        key = str(absolute)
        if key not in seen:
            seen.add(key)
            unique_candidates.append(absolute)
    if not unique_candidates:
        raise MediaPilotError("could not determine a local rembg model directory")
    existing = next((path for path in unique_candidates if path.is_file()), None)
    return ModelSpec(
        requested_name=canonical,
        session_name=session_name,
        expected_filename=expected_filename,
        official_filename=metadata["official_filename"],
        expected_path=unique_candidates[0],
        candidate_paths=unique_candidates,
        existing_path=existing,
        rembg_version=version,
    )


def require_local_model(spec: ModelSpec) -> Path:
    if spec.existing_path is None:
        raise ModelMissingError(spec.missing_instructions())
    return spec.existing_path


def create_explicit_session(
    model_name: str,
    *,
    evaluation_only: bool,
    rembg_module: Optional[Any] = None,
    pooch_module: Optional[Any] = None,
) -> Tuple[Any, ModelSpec, Any]:
    canonical = validate_model_policy(model_name, evaluation_only)
    rembg_module = rembg_module or _load_rembg()
    spec = resolve_model_spec(canonical, rembg_module=rembg_module)
    require_local_model(spec)  # Must happen before new_session can invoke download code.

    if pooch_module is None:
        try:
            import pooch as pooch_module  # type: ignore
        except ImportError:
            pooch_module = None

    original_retrieve = None
    if pooch_module is not None and hasattr(pooch_module, "retrieve"):
        original_retrieve = pooch_module.retrieve

        def deny_model_fetch(*_args: Any, **_kwargs: Any) -> Any:
            raise ModelMissingError(
                "automatic model download was blocked; owner must upload the model manually"
            )

        pooch_module.retrieve = deny_model_fetch
    try:
        session = rembg_module.new_session(canonical)
    finally:
        if original_retrieve is not None:
            pooch_module.retrieve = original_retrieve
    return session, spec, rembg_module


def remove_background_mask(source: Image.Image, session: Any, rembg_module: Any) -> Image.Image:
    """Request mask-only output; original source RGB is never reconstructed."""
    mask = rembg_module.remove(source, session=session, only_mask=True)
    if isinstance(mask, Image.Image):
        return mask.convert("L").resize(source.size, Image.Resampling.LANCZOS)
    if isinstance(mask, (bytes, bytearray)):
        import io

        with Image.open(io.BytesIO(mask)) as loaded:
            return loaded.convert("L").resize(source.size, Image.Resampling.LANCZOS)
    raise MediaPilotError("rembg returned an unsupported mask type")


def alpha_bbox(mask: Image.Image, threshold: int = 8) -> Optional[Tuple[int, int, int, int]]:
    binary = mask.point(lambda value: 255 if value > threshold else 0, mode="1")
    return binary.getbbox()


def evaluate_mask(mask: Image.Image) -> Dict[str, Any]:
    mask = mask.convert("L")
    bbox = alpha_bbox(mask)
    width, height = mask.size
    if bbox is None:
        return {
            "bbox": None,
            "touches_edge": False,
            "occupancy_ratio": 0.0,
            "semi_transparent_ratio": 0.0,
            "thin_edge_warning": "Alpha mask is empty; product may be fully missing.",
            "warnings": ["empty alpha mask"],
            "status": "REJECT",
        }

    left, top, right, bottom = bbox
    touches = left <= 2 or top <= 2 or right >= width - 2 or bottom >= height - 2
    histogram = mask.histogram()
    nonzero = sum(histogram[1:])
    semi = sum(histogram[1:224])
    occupancy = nonzero / float(width * height)
    semi_ratio = semi / float(nonzero) if nonzero else 0.0
    warnings: List[str] = []
    if touches:
        warnings.append("product mask touches source image edge; clipping is possible")
    if semi_ratio > 0.35:
        warnings.append("high soft-alpha ratio; thin metal edges or stones require visual review")
    if right - left < 24 or bottom - top < 24:
        warnings.append("mask bounding box is unusually small")

    if occupancy < 0.005 or occupancy > 0.98:
        status = "REJECT"
        warnings.append("mask occupancy is outside safe pilot range")
    elif warnings:
        status = "REVIEW"
    else:
        status = "PASS"

    thin_warning = (
        "; ".join(warnings)
        if warnings
        else "No automated edge warning; owner must still verify every stone and thin metal edge."
    )
    return {
        "bbox": [left, top, right, bottom],
        "touches_edge": touches,
        "occupancy_ratio": round(occupancy, 6),
        "semi_transparent_ratio": round(semi_ratio, 6),
        "thin_edge_warning": thin_warning,
        "warnings": warnings,
        "status": status,
    }


def _gradient_background(variant: str) -> Image.Image:
    if variant == "matte-black":
        return Image.new("RGB", OUTPUT_SIZE, (11, 11, 14))

    small = 400
    image = Image.new("RGB", (small, small))
    pixels = image.load()
    for y in range(small):
        for x in range(small):
            nx = (x - small / 2) / (small / 2)
            ny = (y - small * 0.44) / (small / 2)
            radius = min(1.0, math.sqrt(nx * nx + ny * ny))
            if variant == "black-velvet-gradient":
                glow = int(18 * (1.0 - radius) ** 2)
                vertical = int(5 * y / small)
                value = 7 + glow + vertical
                pixels[x, y] = (value, value, value + 2)
            elif variant == "dark-neutral-studio":
                glow = int(24 * (1.0 - radius) ** 2)
                value = 24 + glow
                pixels[x, y] = (value, value, min(58, value + 2))
            else:
                raise MediaPilotError(f"unknown background variant: {variant}")
    return image.resize(OUTPUT_SIZE, Image.Resampling.BICUBIC)


def _default_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow versions before scalable load_default().
        return ImageFont.load_default()


def _evaluation_label(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    font = _default_font(26)
    bar_height = 62
    draw.rectangle((0, 0, canvas.width, bar_height), fill=(132, 13, 20))
    text_bbox = draw.textbbox((0, 0), EVALUATION_LABEL, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text(
        ((canvas.width - text_width) // 2, 18),
        EVALUATION_LABEL,
        fill=(255, 255, 255),
        font=font,
    )


def compose_variants(
    original: Image.Image,
    mask: Image.Image,
    *,
    evaluation_only: bool,
) -> Dict[str, Image.Image]:
    original_rgb = ImageOps.exif_transpose(original).convert("RGB")
    mask = mask.convert("L").resize(original_rgb.size, Image.Resampling.LANCZOS)
    bbox = alpha_bbox(mask)
    if bbox is None:
        raise MediaPilotError("cannot compose an empty alpha mask")

    foreground = original_rgb.convert("RGBA")
    foreground.putalpha(mask)
    foreground = foreground.crop(bbox)
    max_side = 1240
    scale = min(max_side / foreground.width, max_side / foreground.height)
    target = (
        max(1, int(round(foreground.width * scale))),
        max(1, int(round(foreground.height * scale))),
    )
    # Uniform scaling only: no warp, redraw, inpainting, or geometry change.
    foreground = foreground.resize(target, Image.Resampling.LANCZOS)
    x = (OUTPUT_SIZE[0] - foreground.width) // 2
    y = max(90 if evaluation_only else 30, (OUTPUT_SIZE[1] - foreground.height) // 2 - 20)

    outputs: Dict[str, Image.Image] = {}
    for variant in ("matte-black", "black-velvet-gradient", "dark-neutral-studio"):
        canvas = _gradient_background(variant)
        shadow_layer = Image.new("RGBA", OUTPUT_SIZE, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_width = max(140, int(foreground.width * 0.68))
        shadow_height = max(24, int(foreground.height * 0.055))
        center_x = OUTPUT_SIZE[0] // 2
        shadow_y = min(OUTPUT_SIZE[1] - 50, y + foreground.height - shadow_height // 3)
        shadow_draw.ellipse(
            (
                center_x - shadow_width // 2,
                shadow_y,
                center_x + shadow_width // 2,
                shadow_y + shadow_height,
            ),
            fill=(0, 0, 0, 58),
        )
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=24))
        canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow_layer)
        canvas.alpha_composite(foreground, (x, y))
        result = canvas.convert("RGB")
        if evaluation_only:
            _evaluation_label(result)
        outputs[variant] = result
    return outputs


def _fit_tile(image: Image.Image, size: Tuple[int, int], background: Tuple[int, int, int]) -> Image.Image:
    tile = Image.new("RGB", size, background)
    copy = ImageOps.exif_transpose(image).convert("RGB")
    copy.thumbnail((size[0] - 24, size[1] - 54), Image.Resampling.LANCZOS)
    tile.paste(copy, ((size[0] - copy.width) // 2, 42 + (size[1] - 54 - copy.height) // 2))
    return tile


def create_contact_sheet(
    original: Image.Image,
    variants: Dict[str, Image.Image],
    *,
    legacy_id: str,
    evaluation_only: bool,
) -> Image.Image:
    tile_size = (420, 500)
    labels = [
        ("ORIGINAL", original),
        ("MATTE BLACK", variants["matte-black"]),
        ("BLACK VELVET", variants["black-velvet-gradient"]),
        ("DARK STUDIO", variants["dark-neutral-studio"]),
    ]
    sheet = Image.new("RGB", (tile_size[0] * 4, tile_size[1] + 54), (18, 18, 20))
    draw = ImageDraw.Draw(sheet)
    font = _default_font(18)
    for index, (label, image) in enumerate(labels):
        tile = _fit_tile(image, tile_size, (24, 24, 27))
        x = index * tile_size[0]
        sheet.paste(tile, (x, 54))
        draw.text((x + 16, 18), label, fill=(242, 238, 230), font=font)
    header = f"RADMAN MEDIA QA — LEGACY {legacy_id}"
    draw.text((sheet.width - 390, 18), header, fill=(191, 166, 122), font=font)
    if evaluation_only:
        draw.rectangle((0, sheet.height - 34, sheet.width, sheet.height), fill=(132, 13, 20))
        draw.text((16, sheet.height - 28), EVALUATION_LABEL, fill="white", font=font)
    return sheet


def save_webp_atomic(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(path.suffix + ".tmp")
    image.save(tmp, "WEBP", quality=WEBP_QUALITY, method=6)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def process_source_image(
    *,
    source_path: Path,
    source_url: str,
    legacy_id: str,
    output_dir: Path,
    qa_dir: Path,
    model_name: str,
    model_path: Path,
    session: Any,
    rembg_module: Any,
    evaluation_only: bool,
) -> Dict[str, Any]:
    started = time.monotonic()
    with Image.open(source_path) as loaded:
        raw_dimensions = list(loaded.size)
        original = ImageOps.exif_transpose(loaded).convert("RGB")
    mask = remove_background_mask(original, session, rembg_module)
    mask_info = evaluate_mask(mask)
    variants = compose_variants(original, mask, evaluation_only=evaluation_only)

    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    qa_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    stem = source_path.stem
    output_files: Dict[str, Dict[str, Any]] = {}
    for variant, image in variants.items():
        destination = output_dir / f"{stem}--{variant}.webp"
        save_webp_atomic(image, destination)
        output_files[variant] = {
            "path": str(destination),
            "bytes": destination.stat().st_size,
            "dimensions": list(image.size),
        }

    contact = create_contact_sheet(
        original,
        variants,
        legacy_id=legacy_id,
        evaluation_only=evaluation_only,
    )
    contact_path = qa_dir / f"{legacy_id}-{stem}-contact-sheet.webp"
    save_webp_atomic(contact, contact_path)

    duration = time.monotonic() - started
    report = {
        "legacy_id": legacy_id,
        "source_url": source_url,
        "source_file": str(source_path),
        "original_dimensions": raw_dimensions,
        "selected_model": model_name,
        "model_file": str(model_path),
        "processing_duration_seconds": round(duration, 3),
        "output_size": list(OUTPUT_SIZE),
        "output_files": output_files,
        "alpha_mask_bounding_box": mask_info["bbox"],
        "product_touches_image_edge": mask_info["touches_edge"],
        "possible_missing_stones_or_thin_edges_warning": mask_info["thin_edge_warning"],
        "mask_occupancy_ratio": mask_info["occupancy_ratio"],
        "semi_transparent_ratio": mask_info["semi_transparent_ratio"],
        "warnings": mask_info["warnings"],
        "status": mask_info["status"],
        "contact_sheet": str(contact_path),
        "evaluation_only": evaluation_only,
        "wordpress_imported": False,
    }
    report_path = output_dir / f"{stem}--qa.json"
    write_json_atomic(report_path, report)
    return report


def _product_records(product_dir: Path, limit: int) -> List[Tuple[Path, Dict[str, Any]]]:
    records: List[Tuple[Path, Dict[str, Any]]] = []
    for path in sorted(product_dir.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MediaPilotError(f"invalid product cache JSON {path}: {exc}") from exc
        if not isinstance(value, dict) or not value.get("legacy_id"):
            raise MediaPilotError(f"invalid product cache record: {path}")
        records.append((path, value))
        if len(records) >= limit:
            break
    if not records:
        raise MediaPilotError(f"no cached products found in {product_dir}; run --scrape-three first")
    return records


def process_cached_products(
    private_dir: Path,
    *,
    model_name: str,
    evaluation_only: bool,
    limit: int = MAX_PRODUCTS,
    session_bundle: Optional[Tuple[Any, ModelSpec, Any]] = None,
) -> List[Dict[str, Any]]:
    validate_product_limit(limit)
    canonical = validate_model_policy(model_name, evaluation_only)
    session, spec, rembg_module = session_bundle or create_explicit_session(
        canonical, evaluation_only=evaluation_only
    )
    model_path = require_local_model(spec)

    product_dir = private_dir / "legacy-cache" / "products"
    originals_dir = private_dir / "legacy-cache" / "original-images"
    processed_root = private_dir / "processed-images"
    qa_dir = private_dir / "outbox" / "media-qa"
    reports: List[Dict[str, Any]] = []

    for _record_path, product in _product_records(product_dir, limit):
        legacy_id = str(product["legacy_id"])
        output_dir = processed_root / legacy_id
        for image in product.get("downloaded_images", []):
            if not isinstance(image, dict):
                continue
            filename = str(image.get("local_filename", ""))
            source_url = str(image.get("source_url", ""))
            if not filename or Path(filename).name != filename:
                raise MediaPilotError(f"unsafe cached image filename for legacy {legacy_id}")
            source_path = originals_dir / filename
            if not source_path.is_file():
                raise MediaPilotError(f"cached source image is missing: {source_path}")
            report = process_source_image(
                source_path=source_path,
                source_url=source_url,
                legacy_id=legacy_id,
                output_dir=output_dir,
                qa_dir=qa_dir,
                model_name=canonical,
                model_path=model_path,
                session=session,
                rembg_module=rembg_module,
                evaluation_only=evaluation_only,
            )
            reports.append(report)
            print(
                f"[PROCESS] legacy_id={legacy_id} source={filename} "
                f"status={report['status']} contact={report['contact_sheet']}"
            )
    if not reports:
        raise MediaPilotError("cached products contain no downloaded source images")
    aggregate = {
        "model_name": canonical,
        "model_file": str(model_path),
        "evaluation_only": evaluation_only,
        "products_limit": limit,
        "source_images_processed": len(reports),
        "reports": reports,
        "wordpress_imported": False,
    }
    write_json_atomic(qa_dir / "media-qa-report.json", aggregate)
    return reports


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RADMAN offline product media QA processor")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--process", action="store_true")
    parser.add_argument("--model-name", default=os.environ.get("MODEL_NAME"))
    parser.add_argument("--limit", type=int, default=MAX_PRODUCTS)
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path(os.environ.get("RADMAN_PRIVATE_DIR", str(Path.home() / ".config/radman"))),
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    evaluation_only = os.environ.get("IMAGE_PIPELINE_EVALUATION_ONLY") == "1"
    try:
        validate_product_limit(args.limit)
        canonical = validate_model_policy(args.model_name, evaluation_only)
        spec = resolve_model_spec(canonical)
        if args.plan or not args.process:
            print("RADMAN product media processor plan")
            print(f"  MODEL_NAME: {canonical}")
            print(f"  rembg version: {spec.rembg_version}")
            print(f"  expected filename: {spec.expected_filename}")
            print(f"  expected absolute path: {spec.expected_path}")
            print(f"  official model filename: {spec.official_filename}")
            print(f"  model present: {'YES' if spec.existing_path else 'NO'}")
            print(f"  evaluation only: {evaluation_only}")
            print(f"  output: {args.private_dir / 'processed-images/<legacy_id>'}")
            print(f"  contact sheets: {args.private_dir / 'outbox/media-qa'}")
            print("  WordPress import: NEVER in this pilot")
            if spec.existing_path is None:
                print(spec.missing_instructions())
            return 0
        reports = process_cached_products(
            args.private_dir,
            model_name=canonical,
            evaluation_only=evaluation_only,
            limit=args.limit,
        )
        print(f"[DONE] processed {len(reports)} source image(s); owner QA is required")
        return 0
    except (MediaPilotError, OSError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Offline tests for the three-product catalog/media pilot. No host/network/WP."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "legacy-media-pilot"
sys.path.insert(0, str(HERE))

import agent_legacy_catalog_pilot as catalog  # noqa: E402
import agent_product_media_processor as media  # noqa: E402


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_three_product_fixtures() -> None:
    cases = [
        (
            "https://noghrehmashhad.ir/product/1001/sample-ring/",
            "product-1001.html",
            "rings",
            2450000,
            12.5,
            2,
        ),
        (
            "https://noghrehmashhad.ir/product/1002/sample-necklace/",
            "product-1002.html",
            "necklaces",
            3750000,
            8.2,
            1,
        ),
        (
            "https://noghrehmashhad.ir/product/1003/sample-bracelet/",
            "product-1003.html",
            "bracelets",
            1900000,
            None,
            1,
        ),
    ]
    for url, filename, category, price, weight, image_count in cases:
        product = catalog.parse_product_html(url, fixture(filename))
        assert product["mapped_radman_category"] == category
        assert product["public_price_toman"] == price
        assert product["weight_grams"] == weight
        assert len(product["image_urls"]) == image_count
        assert all("?" not in image for image in product["image_urls"])
        assert str(product["legacy_id"]) in url
    assert "2025" in str(
        catalog.parse_product_html(cases[1][0], fixture(cases[1][1]))["title_fa"]
    )
    print("PASS: three mock product fixtures parse fields, digits, prices, and images")


def test_sitemap_category_and_limit() -> None:
    index_urls = catalog.parse_sitemap_urls(fixture("sitemap.xml"))
    product_urls = catalog.parse_sitemap_urls(fixture("sitemap-product.xml"))
    category_urls = catalog.parse_product_links(
        "https://noghrehmashhad.ir/category/2/sample/", fixture("category.html")
    )
    assert index_urls == ["https://noghrehmashhad.ir/sitemap-product.xml"]
    assert product_urls == category_urls
    assert len(product_urls) == 4

    class CategoryFetcher:
        def fetch_text(self, url):
            category_id = {value: index for index, value in enumerate(catalog.PILOT_CATEGORY_URLS, 1)}[url]
            return f'<a href="/product/{category_id}00{category_id}/representative/">item</a>'

    representatives = catalog.discover_product_urls(
        CategoryFetcher(), category_urls=catalog.PILOT_CATEGORY_URLS  # type: ignore[arg-type]
    )
    assert representatives == [
        "https://noghrehmashhad.ir/product/1001/representative/",
        "https://noghrehmashhad.ir/product/2002/representative/",
        "https://noghrehmashhad.ir/product/3003/representative/",
    ]
    assert catalog.validate_product_limit(3) == 3
    try:
        catalog.validate_product_limit(4)
        raise AssertionError("limit=4 must be blocked")
    except catalog.PilotError:
        pass
    print("PASS: sitemap/category discovery works and hard maximum is three")


def test_rate_limit_and_robots() -> None:
    now = [0.0]
    sleeps = []

    def clock() -> float:
        return now[0]

    def sleeper(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    def opener(request, _timeout):
        url = request.full_url
        if url.endswith("robots.txt"):
            return fixture("robots.txt").encode(), {"content-type": "text/plain; charset=utf-8"}
        return b"<html></html>", {"content-type": "text/html; charset=utf-8"}

    fetcher = catalog.RateLimitedFetcher(clock=clock, sleeper=sleeper, opener=opener)
    fetcher.load_robots()
    fetcher.fetch_text("https://noghrehmashhad.ir/sitemap.xml")
    fetcher.fetch_text("https://noghrehmashhad.ir/product/1001/sample-ring/")
    assert len(sleeps) == 2
    assert all(seconds >= 2.0 for seconds in sleeps)
    try:
        fetcher.fetch_text("https://noghrehmashhad.ir/admin/private")
        raise AssertionError("robots-disallowed URL must be blocked")
    except catalog.PilotError:
        pass
    print("PASS: descriptive fetcher enforces robots and two-second delays")


def test_model_policy() -> None:
    assert media.validate_model_policy("birefnet-general-lite", False) == "birefnet-general-lite"
    assert media.validate_model_policy("u2net", False) == "u2net"
    for value in (None, "", "unknown-model"):
        try:
            media.validate_model_policy(value, False)
            raise AssertionError(f"model {value!r} should be blocked")
        except media.MediaPilotError:
            pass
    try:
        media.validate_model_policy("bria-rmbg", False)
        raise AssertionError("BRIA must be blocked without evaluation-only")
    except media.MediaPilotError:
        pass
    assert media.validate_model_policy("bria-rmbg-2.0", True) == "bria-rmbg"
    print("PASS: MODEL_NAME is explicit and BRIA requires evaluation-only")


def test_missing_model_never_downloads() -> None:
    with tempfile.TemporaryDirectory(prefix="radman-model-test-") as tmp:
        root = Path(tmp)

        class FakeSessionClass:
            @classmethod
            def name(cls):
                return "birefnet-general-lite"

            @classmethod
            def model_dir(cls):
                return str(root / "models" / cls.name())

            @classmethod
            def legacy_home(cls):
                return str(root / "legacy")

            @classmethod
            def download_models(cls):
                raise AssertionError("download_models must never be called by preflight")

        calls = {"new_session": 0, "retrieve": 0}

        def new_session(_name):
            calls["new_session"] += 1
            return object()

        class FakePooch:
            @staticmethod
            def retrieve(*_args, **_kwargs):
                calls["retrieve"] += 1
                raise AssertionError("network model download attempted")

        fake_rembg = SimpleNamespace(
            __version__="test",
            sessions=SimpleNamespace(sessions_class=[FakeSessionClass]),
            new_session=new_session,
        )
        spec = media.resolve_model_spec("birefnet-general-lite", rembg_module=fake_rembg)
        assert spec.expected_path == (
            root / "models" / "birefnet-general-lite" / "birefnet-general-lite.onnx"
        ).resolve()
        assert spec.official_filename == "BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx"
        try:
            media.create_explicit_session(
                "birefnet-general-lite",
                evaluation_only=False,
                rembg_module=fake_rembg,
                pooch_module=FakePooch,
            )
            raise AssertionError("missing model must stop")
        except media.ModelMissingError as exc:
            message = str(exc)
            assert "NO DOWNLOAD WAS ATTEMPTED" in message
            assert str(spec.expected_path) in message
            assert spec.official_filename in message
        assert calls == {"new_session": 0, "retrieve": 0}

        spec.expected_path.parent.mkdir(parents=True)
        spec.expected_path.write_bytes(b"mock-onnx")
        session, present_spec, _ = media.create_explicit_session(
            "birefnet-general-lite",
            evaluation_only=False,
            rembg_module=fake_rembg,
            pooch_module=FakePooch,
        )
        assert session is not None
        assert present_spec.existing_path == spec.expected_path
        assert calls == {"new_session": 1, "retrieve": 0}
    print("PASS: missing models print paths and never trigger network download")


def synthetic_source_and_mask(edge: bool = False):
    original = Image.new("RGB", (420, 300), (235, 235, 235))
    draw = ImageDraw.Draw(original)
    draw.ellipse((95, 60, 325, 270), fill=(185, 188, 194), outline=(70, 72, 77), width=8)
    mask = Image.new("L", original.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    box = (0, 60, 325, 270) if edge else (95, 60, 325, 270)
    mask_draw.ellipse(box, fill=255)
    return original, mask


def test_webp_dimensions_qa_and_evaluation_label() -> None:
    original, mask = synthetic_source_and_mask()
    variants = media.compose_variants(original, mask, evaluation_only=False)
    assert set(variants) == {
        "matte-black",
        "black-velvet-gradient",
        "dark-neutral-studio",
    }
    assert all(image.size == (1600, 1600) for image in variants.values())
    assert media.evaluate_mask(mask)["status"] == "PASS"
    _, edge_mask = synthetic_source_and_mask(edge=True)
    assert media.evaluate_mask(edge_mask)["status"] == "REVIEW"

    evaluation = media.compose_variants(original, mask, evaluation_only=True)
    assert evaluation["matte-black"].getpixel((4, 4)) == (132, 13, 20)
    contact = media.create_contact_sheet(
        original, evaluation, legacy_id="1001", evaluation_only=True
    )
    assert contact.size == (1680, 554)

    with tempfile.TemporaryDirectory(prefix="radman-webp-test-") as tmp:
        for name, image in variants.items():
            path = Path(tmp) / f"{name}.webp"
            media.save_webp_atomic(image, path)
            with Image.open(path) as loaded:
                assert loaded.size == (1600, 1600)
                assert loaded.format == "WEBP"
    print("PASS: outputs are 1600x1600 WebP; QA edge status and BRIA label work")


def test_owner_runner_plan_is_non_mutating() -> None:
    with tempfile.TemporaryDirectory(prefix="radman-runner-plan-") as tmp:
        private_dir = Path(tmp) / "must-not-be-created-in-plan"
        runner = REPO_ROOT / "scripts" / "run_product_media_pilot.sh"
        env = dict(os.environ)
        env.update(
            {
                "APP_ENV": "staging",
                "MODEL_NAME": "birefnet-general-lite",
                "RADMAN_REPO_ROOT": str(REPO_ROOT),
                "RADMAN_PRIVATE_DIR": str(private_dir),
            }
        )
        result = subprocess.run(
            ["bash", str(runner), "--plan"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "hard product maximum: 3" in result.stdout.lower()
        assert "NO DOWNLOAD WAS ATTEMPTED" in result.stdout
        assert "WordPress import: NEVER" in result.stdout
        assert not private_dir.exists()
    print("PASS: owner --plan is non-mutating and prints offline model instructions")


def test_static_safety_contract() -> None:
    catalog_source = (HERE / "agent_legacy_catalog_pilot.py").read_text(encoding="utf-8")
    media_source = (HERE / "agent_product_media_processor.py").read_text(encoding="utf-8")
    runner_source = (REPO_ROOT / "scripts" / "run_product_media_pilot.sh").read_text(
        encoding="utf-8"
    )
    combined = catalog_source + media_source + runner_source
    forbidden = (
        "wp post",
        "wp media",
        "woocommerce",
        "api." + "telegram.org",
        "payment gateway",
        "rembg " + "d ",
        "subprocess.run(['wp'",
    )
    for token in forbidden:
        assert token.lower() not in combined.lower(), token
    assert "public_html" in runner_source
    for line in runner_source.splitlines():
        if "public_html" in line and not line.lstrip().startswith("#"):
            assert "prohibit" in line.lower() or "die" in line.lower()
    assert "rembg_module.remove(source, session=session, only_mask=True)" in media_source
    assert "new_session(canonical)" in media_source
    print("PASS: scripts contain no WordPress/payment/SMS/model-download operation")


def run_tests() -> None:
    test_three_product_fixtures()
    test_sitemap_category_and_limit()
    test_rate_limit_and_robots()
    test_model_policy()
    test_missing_model_never_downloads()
    test_webp_dimensions_qa_and_evaluation_label()
    test_owner_runner_plan_is_non_mutating()
    test_static_safety_contract()


if __name__ == "__main__":
    run_tests()
    print("ALL PRODUCT MEDIA PILOT TESTS PASSED")

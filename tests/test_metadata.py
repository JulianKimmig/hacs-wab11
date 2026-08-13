"""Contract tests for Home Assistant integration metadata."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from PIL import Image

from custom_components.hacs_wab11 import CONFIG_SCHEMA
from custom_components.hacs_wab11.const import DOMAIN

BRAND_PATH = Path(__file__).parents[1] / "custom_components" / "hacs_wab11" / "brand"


def test_manifest_keys_follow_hassfest_order() -> None:
    """Require domain, name, and then alphabetical manifest keys.

    Returns:
        None.
    """
    manifest_path = (
        Path(__file__).parents[1] / "custom_components" / "hacs_wab11" / "manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert list(manifest) == [
        "domain",
        "name",
        *sorted(set(manifest) - {"domain", "name"}),
    ]


def test_config_schema_allows_only_config_entries(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Accept empty YAML and report unsupported domain configuration.

    Args:
        caplog: Pytest fixture that captures Home Assistant validation logs.

    Returns:
        None.
    """
    assert CONFIG_SCHEMA({}) == {}

    with caplog.at_level(logging.ERROR):
        assert CONFIG_SCHEMA({DOMAIN: {}}) == {DOMAIN: {}}

    assert "does not support YAML setup" in caplog.text


def test_brand_icon_matches_home_assistant_contract() -> None:
    """Require a square, transparent normal-density integration icon.

    Returns:
        None.
    """
    with Image.open(BRAND_PATH / "icon.png") as icon:
        assert icon.format == "PNG"
        assert icon.mode == "RGBA"
        assert icon.size == (256, 256)
        assert icon.getchannel("A").getextrema() == (0, 255)


def test_brand_logo_matches_home_assistant_contract() -> None:
    """Require a landscape, transparent normal-density integration logo.

    Returns:
        None.
    """
    with Image.open(BRAND_PATH / "logo.png") as logo:
        width, height = logo.size

        assert logo.format == "PNG"
        assert logo.mode == "RGBA"
        assert height == 256
        assert width > height
        assert logo.getchannel("A").getextrema() == (0, 255)

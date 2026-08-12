"""Contract tests for Home Assistant integration metadata."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from custom_components.hacs_wab11 import CONFIG_SCHEMA
from custom_components.hacs_wab11.const import DOMAIN


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

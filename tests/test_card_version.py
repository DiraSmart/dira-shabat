"""Keep the card's console banner version in sync with manifest.json."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "custom_components" / "dira_shabat"


def test_card_version_matches_manifest():
    manifest_version = json.loads((ROOT / "manifest.json").read_text())["version"]
    card_js = (ROOT / "www" / "dira-shabat-card.js").read_text(encoding="utf-8")
    match = re.search(r'const CARD_VERSION = "([^"]+)"', card_js)
    assert match, "CARD_VERSION constant not found in dira-shabat-card.js"
    assert match.group(1) == manifest_version

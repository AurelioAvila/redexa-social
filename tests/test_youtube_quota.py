"""The YouTube Data API budget is 10,000 units a day and every customer of
this product shares it: one Google Cloud project is compiled into every
binary. So the cost of a single refresh is not an implementation detail, it
is the ceiling on how many customers the product can have at once. These
tests fail if that cost goes back up."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_one_channels_list_call_per_refresh():
    """A channels.list costs one unit whatever parts it asks for, so asking
    twice for the same channel spends a unit for nothing. It used to: once
    for statistics+snippet and again for contentDetails."""
    source = (ROOT / "platforms" / "youtube.py").read_text(encoding="utf-8")
    calls = re.findall(r"youtube\.channels\(\)\.list\(", source)
    assert len(calls) == 1, f"expected one channels.list call, found {len(calls)}"
    assert 'part="statistics,snippet,contentDetails"' in source


def test_auto_refresh_is_hourly_and_only_while_visible():
    """Five-minute unconditional polling from every open window is what put
    the ceiling at roughly ten simultaneous customers."""
    app = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    match = re.search(r"const AUTO_REFRESH_EVERY_MS = ([^;]+);", app)
    assert match, "the auto-refresh interval constant is gone"
    assert match.group(1).strip() == "60 * 60 * 1000", match.group(1)

    body = app[match.end():match.end() + 400]
    assert 'document.visibilityState !== "visible"' in body, (
        "the refresh timer must skip while nobody is looking at the window"
    )

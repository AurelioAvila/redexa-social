"""The Rivals feature had a complete backend and no interface at all.

rivals.py reads the public figures of channels the user picks, /api/rivals
adds, lists and removes them, /api/snapshot carries the standings, and
plans.py gates the numbers behind Pro. The word "rivals" appeared zero times
in static/app.js and zero times in static/index.html, so the feature the paid
plan sells - the one plans.py calls "the question someone opens a tool like
this to ask" - could not be reached by anybody who had paid for it.

These tests are shaped against that: they assert the screen exists and stays
wired to the endpoints, not that particular markup is present.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def test_the_section_and_its_navigation_entry_exist():
    assert 'id="section-rivals"' in INDEX
    assert 'data-section="rivals"' in INDEX


def test_every_endpoint_the_backend_offers_is_reachable_from_the_screen():
    assert '"/api/rivals"' in APP_JS, "the list and add endpoints are never called"
    assert "/api/rivals/${" in APP_JS, "nothing removes a rival"
    assert "renderRivalsTable(snapshot.rivals)" in APP_JS, "the standings are never drawn"


def test_the_paywall_is_reported_rather_than_swallowed():
    """/api/rivals answers 402 for a plan without the entitlement. A silent
    failure there looks like a broken button."""
    assert "402" in APP_JS
    assert "rivals_needs_pro" in APP_JS


def test_another_channels_title_is_escaped_before_it_reaches_innerhtml():
    """Titles and handles come back from somebody else's public profile."""
    assert "function escapeHtml" in APP_JS
    assert "escapeHtml(r.title" in APP_JS


def test_the_screen_is_translated_everywhere_the_app_is():
    languages = len(re.findall(r"^\s+nav_rivals:", APP_JS, re.M))
    others = len(re.findall(r"^\s+nav_overview:", APP_JS, re.M))
    assert languages == others, f"nav_rivals in {languages} languages, nav_overview in {others}"

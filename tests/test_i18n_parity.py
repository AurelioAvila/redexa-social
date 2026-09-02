"""Every string the interface asks for has to exist in every language.

There are six of them and several hundred keys, and nothing checked that they
matched. A key present in English and missing in German does not fail
anywhere: `t()` falls back, and the German user reads `tip_cta` where a
sentence belongs. Nobody notices unless they run the app in that language and
happen to open that screen.

`test_theme_tokens.py` already does this shape of check for the theme colours
duplicated between CSS and JavaScript. This is the same idea for the copy.

Parsed rather than executed: the strings live in a JavaScript object literal,
and the alternative is a Node dependency in a Python suite.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
APP_JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
INDEX_HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")

KEY = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*:")
# Double-quoted values, escapes included. They come out before keys are read:
# several keys share a line in this file, so an anchored line-start pattern
# finds only the first of each — and an unanchored one would otherwise match
# inside the translations themselves ("https:", "Nota:").
STRING = re.compile(r'"(?:[^"\\]|\\.)*"')


def language_blocks():
    """The I18N object, split into one bucket of keys per language."""
    start = APP_JS.index("const I18N = {")
    # Bounded at the object's own closing brace. Without it the last language
    # block ran to the end of the file and collected every identifier in the
    # rest of app.js as if it were a translation key.
    closing = APP_JS.index("\n};", start)
    body = APP_JS[start:closing]
    heads = [(m.group(1), m.start()) for m in re.finditer(r"^  ([a-z]{2}): \{$", body, re.M)]
    assert heads, "could not find the language blocks in app.js"

    blocks = {}
    for index, (code, offset) in enumerate(heads):
        end = heads[index + 1][1] if index + 1 < len(heads) else len(body)
        chunk = STRING.sub('""', body[offset:end])
        blocks[code] = set(KEY.findall(chunk)) - {code}
    return blocks


BLOCKS = language_blocks()
REFERENCE = "en"


def test_there_are_six_languages_and_english_is_one_of_them():
    assert REFERENCE in BLOCKS
    assert len(BLOCKS) >= 6, f"expected at least six languages, found {sorted(BLOCKS)}"


@pytest.mark.parametrize("code", sorted(set(BLOCKS) - {REFERENCE}))
def test_every_language_carries_the_same_keys_as_english(code):
    missing = BLOCKS[REFERENCE] - BLOCKS[code]
    extra = BLOCKS[code] - BLOCKS[REFERENCE]
    assert not missing, f"{code} is missing: {sorted(missing)}"
    assert not extra, f"{code} has keys English does not: {sorted(extra)}"


def test_every_key_the_markup_asks_for_exists():
    asked = set()
    for attribute in ("data-i18n", "data-i18n-placeholder", "data-i18n-title", "data-i18n-aria"):
        asked |= set(re.findall(r'%s="([^"]+)"' % attribute, INDEX_HTML))

    unknown = sorted(key for key in asked if key not in BLOCKS[REFERENCE])
    assert not unknown, f"the markup asks for keys no language defines: {unknown}"


def test_the_coffee_tip_is_offered_in_every_language():
    """Added by script across six blocks at once, which is exactly the kind of
    edit that lands in five of them."""
    for code, keys in BLOCKS.items():
        assert "tip_text" in keys, f"{code} has no tip_text"
        assert "tip_cta" in keys, f"{code} has no tip_cta"


def test_the_tip_link_is_the_payment_link_and_opens_safely():
    anchor = re.search(r'<a class="tip-link"[^>]*>', INDEX_HTML)
    assert anchor, "the pricing page no longer offers the tip"
    tag = anchor.group(0)
    # A static Payment Link: no endpoint, no key in the binary, repointable in
    # Stripe without a new build.
    assert "https://buy.stripe.com/" in tag
    # target=_blank without noopener hands the opened page a window.opener
    # handle back into the app.
    assert 'target="_blank"' in tag
    assert "noopener" in tag

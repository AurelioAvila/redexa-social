"""
Theme colours, kept aligned between CSS and JavaScript.

Two checks nobody can make by eye:

  1. Every theme is defined twice. In `style.css` as variables, which are what
     actually paints the interface, and in `app.js` as a triple of colours for
     the preview dot in the theme picker. The preview has to stay literal: it
     shows one theme's colours while another one is active, so it cannot read
     the variables. The price is that the two copies can drift apart silently,
     and they already had: the "dark" theme was darkened in the CSS (#09090b)
     while the dot stayed on the old grey (#0f1115). Nobody notices, because a
     slightly wrong dot just looks like a dot.

  2. The notification badge writes on top of `--red`. In every theme but
     "light" the red is bright, and white was landing at 2.55:1 on 10px bold
     text: readable for someone with good eyesight on a good monitor, and not
     for everybody else. Contrast is arithmetic, so it is better measured here
     than trusted to the screenshot in which it looked fine.
"""
import re
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parent.parent / "static"
CSS = (STATIC / "style.css").read_text(encoding="utf-8")
JS = (STATIC / "app.js").read_text(encoding="utf-8")

# The WCAG 2.1 AA threshold for body text. The badge is bold but 10px, under
# the 18.66px that would qualify it for the lower 3:1 threshold.
AA_NORMAL_TEXT = 4.5


def _theme_variants():
    """Each theme's variables, read from the :root[data-theme=...] blocks."""
    themes = {}
    for block in re.finditer(r':root\[data-theme="([a-z]+)"\]\s*\{(.*?)\}', CSS, re.S):
        name, body = block.group(1), block.group(2)
        themes[name] = {
            k: v.strip()
            for k, v in re.findall(r"--([a-z0-9-]+):\s*([^;]+);", body)
        }
    return themes


def _previews():
    """The [bg, accent, card] triples declared in THEMES inside app.js."""
    return {
        m.group(1): [c.lower() for c in re.findall(r'"(#[0-9a-fA-F]{3,8})"', m.group(2))]
        for m in re.finditer(
            r'\{ id: "([a-z]+)", name: "[^"]+", colors: (\[[^\]]+\]) \}', JS
        )
    }


def _luminance(hex_colour):
    h = hex_colour.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    channels = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a, b):
    la, lb = _luminance(a), _luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


THEMES = _theme_variants()
PREVIEWS = _previews()


def test_the_two_lists_cover_the_same_themes():
    """A theme added on only one side would either not appear in the picker or
    appear with no colours: both go unnoticed until somebody opens that
    screen."""
    assert set(THEMES) == set(PREVIEWS), (
        f"only in the CSS: {sorted(set(THEMES) - set(PREVIEWS))}, "
        f"only in the JS: {sorted(set(PREVIEWS) - set(THEMES))}"
    )


@pytest.mark.parametrize("theme", sorted(PREVIEWS))
def test_preview_matches_the_variables(theme):
    """The dot has to show the colours the theme actually applies."""
    bg, accent, card = PREVIEWS[theme]
    expected = THEMES[theme]
    assert bg == expected["bg"].lower(), f"{theme}: preview {bg}, --bg {expected['bg']}"
    assert accent == expected["accent"].lower(), f"{theme}: preview {accent}, --accent {expected['accent']}"
    assert card == expected["card"].lower(), f"{theme}: preview {card}, --card {expected['card']}"


def _badge_rule():
    """The two tokens .nav-badge actually uses, read from the rule itself.

    Pinning them here by hand would make the test blind to exactly the change
    it is meant to watch: if somebody rewrites `color`, the check would go on
    measuring the old pair and passing."""
    rule = re.search(r"\.nav-badge\s*\{(.*?)\}", CSS, re.S)
    assert rule, ".nav-badge rule not found: the test no longer knows what to measure"
    body = rule.group(1)
    background = re.search(r"background:\s*var\(--([a-z0-9-]+)\)", body)
    text = re.search(r"(?<!-)color:\s*var\(--([a-z0-9-]+)\)", body)
    assert background and text, (
        "the background and color of .nav-badge have to be tokens: "
        "a fixed value does not follow the twelve themes"
    )
    return text.group(1), background.group(1)


@pytest.mark.parametrize("theme", sorted(THEMES))
def test_notification_badge_is_readable(theme):
    """The badge writes on a background that changes with the theme."""
    text_token, background_token = _badge_rule()
    ratio = _contrast(THEMES[theme][text_token], THEMES[theme][background_token])
    assert ratio >= AA_NORMAL_TEXT, (
        f"{theme}: {ratio:.2f}:1 between --{text_token} and --{background_token}, "
        f"below {AA_NORMAL_TEXT}:1"
    )


def test_no_hand_written_colour_outside_the_themes():
    """Colours live in the :root blocks. One written elsewhere does not follow
    the theme and becomes the point where the palette splits: that is how the
    badge ended up with a fixed #fff against eleven different backgrounds."""
    blocks = [
        (m.start(), m.end())
        for m in re.finditer(r":root[^{]*\{[^}]*\}", CSS, re.S)
    ]
    outside = [
        (CSS[: m.start()].count("\n") + 1, m.group(0))
        for m in re.finditer(r"#[0-9a-fA-F]{3,8}\b", CSS)
        if not any(a <= m.start() < b for a, b in blocks)
    ]
    assert not outside, f"colours outside the :root blocks: {outside}"

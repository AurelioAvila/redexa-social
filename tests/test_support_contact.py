from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_account_support_opens_the_owner_gmail_inbox():
    page = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert "mailto:canadesino91@gmail.com?subject=Redexa%20Social%20support" in page


def test_support_copy_exists_in_every_language():
    source = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert source.count("support_email:") == 6

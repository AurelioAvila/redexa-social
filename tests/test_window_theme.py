"""Keep the desktop bridge restricted to validated caption colors."""
import ctypes
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import desktop_app


def test_caption_bridge_validates_colors_and_preserves_full_hwnd(monkeypatch):
    calls = []

    def setter(hwnd, attribute, value, size):
        calls.append((hwnd, attribute, ctypes.cast(value, ctypes.POINTER(ctypes.c_uint32))[0], size))
        return 0

    monkeypatch.setattr(desktop_app.sys, 'platform', 'win32')
    monkeypatch.setattr(ctypes, 'windll', SimpleNamespace(dwmapi=SimpleNamespace(DwmSetWindowAttribute=setter)), raising=False)
    theme = desktop_app.WindowTheme()
    assert theme.set_window_theme('#102030', '#F0E0D0') is False
    theme._window = SimpleNamespace(native=SimpleNamespace(Handle=SimpleNamespace(ToInt64=lambda: 0x123456789)))
    for invalid in (None, 12, '#fff', '#12345678', '#123456\n', 'red', '__import__("os")'):
        assert theme.set_window_theme(invalid, '#FFFFFF') is False
        assert theme.set_window_theme('#FFFFFF', invalid) is False
    assert calls == []
    assert theme.set_window_theme('#102030', '#F0E0D0') is True
    assert calls == [(0x123456789, 20, 1, 4), (0x123456789, 34, 0xFFFFFFFE, 4),
                     (0x123456789, 35, 0x302010, 4), (0x123456789, 36, 0xD0E0F0, 4)]
    assert theme.set_window_theme('#FFFFFF', '#000000') is True
    assert calls[4][2] == 0
    failure = Mock(return_value=-1)
    ctypes.windll.dwmapi.DwmSetWindowAttribute = failure
    assert theme.set_window_theme('#102030', '#F0E0D0') is False
    monkeypatch.setattr(desktop_app.sys, 'platform', 'linux')
    assert theme.set_window_theme('#102030', '#F0E0D0') is False


def test_development_port_never_changes_packaged_app_port(monkeypatch):
    monkeypatch.setattr(desktop_app.sys, 'frozen', False, raising=False)
    monkeypatch.setenv('REDEXA_DEV_PORT', '8795')
    assert desktop_app._desktop_port() == 8795
    for invalid in ('80', '65536', 'not-a-port'):
        monkeypatch.setenv('REDEXA_DEV_PORT', invalid)
        with pytest.raises(ValueError):
            desktop_app._desktop_port()
    monkeypatch.setattr(desktop_app.sys, 'frozen', True)
    assert desktop_app._desktop_port() == 8787

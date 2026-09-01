"""
Encryption of the secrets kept locally, tied to the Windows account.

What it actually protects, stated precisely, because promising more than is
true is worse than promising nothing:

  Protects against  the cache.db file being carried off (a USB stick, a backup
                    that ended up in a cloud, a sync, a resold computer) and
                    opened elsewhere: without that user's Windows credentials
                    on that machine, the tokens do not decrypt. It also
                    protects against another Windows account on the same
                    computer.

  Does NOT protect  against malicious software running as the user
                    themselves: it can ask DPAPI to decrypt exactly the way
                    the app does, or read the values out of memory. No local
                    encryption can prevent that, and it belongs in the README
                    rather than being left to look otherwise.

Windows DPAPI is used through ctypes: no library to add, no key to look after
(the operating system manages it, bound to the account), nothing to type at
startup.

Encrypted values are recognizable by their prefix, so an older database with
plaintext values stays readable and the migration knows what it has already
done.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import base64
import ctypes
import sys

# Marks the encrypted values. It tells them apart from the plaintext ones in
# older databases, and makes the migration safe to run more than once.
PREFIX = "enc:v1:"

# Extra entropy tied to the application: it is not a secret (it sits inside
# the executable) but it stops another program running under the same account
# from decrypting these values by calling DPAPI at random.
_ENTROPY = b"SocialDashboard/v1/local-secrets"

_CRYPTPROTECT_UI_FORBIDDEN = 0x01


class SecretUnavailable(Exception):
    """The value is there but cannot be decrypted on this computer/account.

    This happens when the database came from another machine, another Windows
    user, or after the system was reinstalled. It is not an error to hide, nor
    one to treat as corrupt data: the remedy is to reconnect the account, and
    the data stays where it is.
    """


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32),
                ("pbData", ctypes.POINTER(ctypes.c_char))]


def available() -> bool:
    """DPAPI utilizzabile qui? Falso fuori da Windows (sviluppo, test)."""
    return sys.platform == "win32"


def _to_blob(data: bytes) -> _Blob:
    buffer = ctypes.create_string_buffer(data, len(data))
    return _Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))


def _from_blob(blob: _Blob) -> bytes:
    size = blob.cbData
    out = ctypes.create_string_buffer(size)
    ctypes.memmove(out, blob.pbData, size)
    ctypes.windll.kernel32.LocalFree(blob.pbData)
    return out.raw


def is_protected(value: str) -> bool:
    return isinstance(value, str) and value.startswith(PREFIX)


def protect(value: str) -> str:
    """Encrypts a value. Already encrypted, it comes back as it is.

    Off Windows the value is returned unchanged: the app is Windows-only, and
    breaking development or tests on other systems would add security for
    nobody.
    """
    if value is None or value == "" or is_protected(value):
        return value
    if not available():
        return value

    dati = _to_blob(value.encode("utf-8"))
    entropia = _to_blob(_ENTROPY)
    uscita = _Blob()

    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(dati), None, ctypes.byref(entropia),
        None, None, _CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(uscita),
    )
    if not ok:
        raise SecretUnavailable("CryptProtectData non riuscita")

    return PREFIX + base64.b64encode(_from_blob(uscita)).decode("ascii")


def unprotect(value: str) -> str:
    """Decrypts a value. A plaintext one (from an older database) comes back
    unchanged, so reads work both before and after the migration."""
    if value is None or value == "" or not is_protected(value):
        return value
    if not available():
        raise SecretUnavailable("the value is encrypted but DPAPI is unavailable")

    try:
        grezzo = base64.b64decode(value[len(PREFIX):])
    except Exception as exc:
        raise SecretUnavailable("the encrypted value is unreadable") from exc

    dati = _to_blob(grezzo)
    entropia = _to_blob(_ENTROPY)
    uscita = _Blob()

    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(dati), None, ctypes.byref(entropia),
        None, None, _CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(uscita),
    )
    if not ok:
        # The usual case: a database copied from another computer or
        # another Windows account. That is exactly what the encryption is
        # meant to prevent, so it is not a fault - it is the thing working.
        raise SecretUnavailable("the value cannot be decrypted by this Windows account")

    return _from_blob(uscita).decode("utf-8")

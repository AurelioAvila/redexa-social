"""
Encryption for locally stored secrets, bound to the Windows account.

Precisely what this protects, without overstating its guarantees:

  Protects from  A copied cache.db file opened elsewhere, whether copied
                 through removable media, cloud backup, synchronization, or
                 a resold computer. Without that user's Windows credentials
                 on that machine, the tokens cannot be decrypted. It also
                 protects against other Windows accounts on the same computer.

  Does not protect against malicious software running as the same user. It
                 can ask DPAPI to decrypt data exactly as the application
                 does or read values from memory. Local encryption cannot
                 prevent this, and the README must state that clearly.

Windows DPAPI is accessed through ctypes: no additional library, stored key,
or startup input is required. The operating system manages the key and binds
it to the account.

The prefix identifies encrypted values, keeping legacy plaintext databases
readable and making migration idempotent.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import base64
import ctypes
import sys

# Mark encrypted values to distinguish them from legacy plaintext entries
# and make migration safely repeatable.
PREFIX = "enc:v1:"

# Application-specific entropy. It is not secret because it resides in the
# executable, but it prevents unrelated software under the same account from
# decrypting these values through arbitrary DPAPI calls.
_ENTROPY = b"SocialDashboard/v1/local-secrets"

_CRYPTPROTECT_UI_FORBIDDEN = 0x01


class SecretUnavailable(Exception):
    """The value exists but cannot be decrypted on this computer or account.

    This occurs when the database comes from another computer or Windows
    user, or after reinstalling the operating system. It is neither a hidden
    error nor corrupted data: reconnecting the account is the remedy, and
    the stored data remains intact.
    """


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32),
                ("pbData", ctypes.POINTER(ctypes.c_char))]


def available() -> bool:
    """Return whether DPAPI is available; false outside Windows for development and tests."""
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
    """Encrypt a value, returning it unchanged if already encrypted.

    Outside Windows, return the value unchanged. The application targets
    Windows, and breaking development or tests on other systems would add no
    security.
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
    """Decrypt a value.

    Return legacy plaintext values unchanged so reads work before and after
    migration.
    """
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
        # Typical case: the database was copied from another computer or
        # Windows account. This is exactly what the encryption should prevent,
        # so it indicates correct protection rather than a failure.
        raise SecretUnavailable("the value cannot be decrypted by this Windows account")

    return _from_blob(uscita).decode("utf-8")

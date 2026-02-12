"""Fernet encryption helpers for securing API keys at rest."""

from __future__ import annotations

import base64
import hashlib
import platform
import uuid

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def get_machine_id() -> str:
    """Return a stable, privacy-safe machine identifier.

    The identifier is a SHA-256 hex digest derived from the hostname and
    the primary MAC address.  It is not reversible and remains constant
    across reboots on the same hardware.
    """
    raw = f"{platform.node()}:{uuid.getnode()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def derive_key(license_key: str, machine_id: str) -> bytes:
    """Derive a Fernet-compatible 32-byte key using PBKDF2-HMAC-SHA256.

    Parameters
    ----------
    license_key:
        The user's licence key used as the password material.
    machine_id:
        A machine-specific string used as the salt (typically from
        :func:`get_machine_id`).

    Returns
    -------
    bytes
        A URL-safe base64-encoded 32-byte key suitable for
        :class:`cryptography.fernet.Fernet`.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=machine_id.encode(),
        iterations=480_000,
    )
    raw_key = kdf.derive(license_key.encode())
    return base64.urlsafe_b64encode(raw_key)


def encrypt_value(value: str, key: bytes) -> str:
    """Encrypt a plaintext string and return a Fernet token as a string.

    Parameters
    ----------
    value:
        The secret to encrypt (e.g. an API key).
    key:
        A Fernet-compatible key from :func:`derive_key`.

    Returns
    -------
    str
        The encrypted Fernet token, safe to store on disk.
    """
    f = Fernet(key)
    return f.encrypt(value.encode()).decode()


def decrypt_value(token: str, key: bytes) -> str:
    """Decrypt a Fernet token back to the original plaintext.

    Parameters
    ----------
    token:
        The Fernet token produced by :func:`encrypt_value`.
    key:
        The same Fernet-compatible key used for encryption.

    Returns
    -------
    str
        The original plaintext value.

    Raises
    ------
    cryptography.fernet.InvalidToken
        If the key is wrong or the token has been tampered with.
    """
    f = Fernet(key)
    return f.decrypt(token.encode()).decode()

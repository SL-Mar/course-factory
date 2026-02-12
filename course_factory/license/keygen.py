"""Ed25519 license key generator (developer-side only).

This module is used exclusively during the license issuance workflow.
It must **never** be shipped to end-users; only the public verification
key is embedded in the client-side validator.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path

from nacl.signing import SigningKey

from .models import LicensePayload

logger = logging.getLogger(__name__)

_SEPARATOR = "-"


def load_private_key(path: str | Path) -> SigningKey:
    """Load a 32-byte Ed25519 private (signing) key from *path*.

    The file must contain exactly 32 raw bytes (the Ed25519 seed).

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If the file does not contain exactly 32 bytes.
    """
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) != 32:
        raise ValueError(
            f"Private key file must be exactly 32 bytes, got {len(raw)}. "
            f"File: {path}"
        )
    return SigningKey(raw)


def generate_license_key(
    payload: LicensePayload,
    private_key_path: str | Path,
) -> str:
    """Sign *payload* and return a complete license key string.

    Key format::

        {PRODUCT}-{base32(signature ++ json_payload)}

    The *signature* is the 64-byte Ed25519 signature over the canonical
    JSON representation of the payload.  The combined blob is encoded
    with RFC-4648 base32 (no padding) so the key is safe for copy-paste
    in e-mails, environment variables, and CLI arguments.

    Parameters
    ----------
    payload : LicensePayload
        Validated license payload to sign.
    private_key_path : str | Path
        Filesystem path to the 32-byte raw private key file.

    Returns
    -------
    str
        License key string in the format ``{PRODUCT}-{BASE32_BLOB}``.
    """
    signing_key = load_private_key(private_key_path)
    message = payload.to_json_bytes()

    signed = signing_key.sign(message)

    blob = signed.signature + signed.message
    encoded = base64.b32encode(blob).decode("ascii").rstrip("=")

    key = f"{payload.product}{_SEPARATOR}{encoded}"
    logger.info(
        "Generated license key for %s (%s/%s), expiry %s",
        payload.email,
        payload.product,
        payload.tier,
        payload.expiry,
    )
    return key

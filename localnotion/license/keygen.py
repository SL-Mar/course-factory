"""Ed25519 license key generator (developer-side only)."""

from __future__ import annotations

import base64
import logging
from pathlib import Path

from nacl.signing import SigningKey

from .models import LicensePayload

logger = logging.getLogger(__name__)

_SEPARATOR = "-"


def load_private_key(path: str | Path) -> SigningKey:
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) != 32:
        raise ValueError(f"Private key must be 32 bytes, got {len(raw)}")
    return SigningKey(raw)


def generate_license_key(payload: LicensePayload, private_key_path: str | Path) -> str:
    signing_key = load_private_key(private_key_path)
    message = payload.to_json_bytes()
    signed = signing_key.sign(message)
    blob = signed.signature + signed.message
    encoded = base64.b32encode(blob).decode("ascii").rstrip("=")
    return f"{payload.product}{_SEPARATOR}{encoded}"

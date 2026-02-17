"""Client-side Ed25519 license key validator."""

from __future__ import annotations

import base64
import logging
from typing import Optional

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from .models import PRODUCTS, LicensePayload

logger = logging.getLogger(__name__)

_PUBLIC_KEY_HEX: str = "0000000000000000000000000000000000000000000000000000000000000000"
_SEPARATOR = "-"
_SIGNATURE_LENGTH = 64


class LicenseError(Exception):
    pass

class InvalidKeyFormat(LicenseError):
    pass

class InvalidSignature(LicenseError):
    pass

class ExpiredLicense(LicenseError):
    pass

class UnknownProduct(LicenseError):
    pass


def get_verify_key() -> VerifyKey:
    if all(c == "0" for c in _PUBLIC_KEY_HEX):
        raise ValueError("Public key not configured. Run keygen init.")
    return VerifyKey(bytes.fromhex(_PUBLIC_KEY_HEX))


def validate_key(key: str, *, check_expiry: bool = True, expected_product: Optional[str] = None) -> LicensePayload:
    if _SEPARATOR not in key:
        raise InvalidKeyFormat("Key must contain a '-' separator")

    product_prefix, encoded_blob = key.split(_SEPARATOR, maxsplit=1)
    product_prefix = product_prefix.strip().upper()

    if product_prefix not in PRODUCTS:
        raise UnknownProduct(f"Unknown product: {product_prefix}")

    if expected_product and product_prefix != expected_product:
        raise UnknownProduct(f"Expected {expected_product}, got {product_prefix}")

    encoded_blob = encoded_blob.strip().upper()
    padding = (8 - len(encoded_blob) % 8) % 8
    try:
        blob = base64.b32decode(encoded_blob + "=" * padding)
    except Exception as exc:
        raise InvalidKeyFormat(f"Base32 decode failed: {exc}") from exc

    if len(blob) <= _SIGNATURE_LENGTH:
        raise InvalidKeyFormat("Blob too short")

    signature = blob[:_SIGNATURE_LENGTH]
    message = blob[_SIGNATURE_LENGTH:]

    verify_key = get_verify_key()
    try:
        verify_key.verify(message, signature)
    except BadSignatureError as exc:
        raise InvalidSignature("Signature verification failed") from exc

    payload = LicensePayload.from_json_bytes(message)

    if payload.product != product_prefix:
        raise InvalidKeyFormat(f"Product mismatch: {product_prefix} vs {payload.product}")

    if check_expiry and payload.is_expired:
        raise ExpiredLicense(f"License expired on {payload.expiry}")

    return payload

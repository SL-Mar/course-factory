"""Client-side Ed25519 license key validator.

This module is shipped with the product.  It embeds only the **public**
verification key and can verify any license key produced by
:mod:`course_factory.license.keygen` without network access.

Typical usage
-------------
::

    from course_factory.license.validator import validate_key

    result = validate_key("CF-MFRGG...")
    if result is None:
        print("Invalid or expired license.")
    else:
        print(f"Licensed to {result.email}, tier={result.tier}")
"""

from __future__ import annotations

import base64
import logging
from typing import Optional

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from .models import PRODUCTS, LicensePayload

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Embedded public key (replace after running generate_keypair.py)
# ---------------------------------------------------------------------------
# fmt: off
# 32-byte Ed25519 public (verify) key -- hex-encoded for readability.
# To update: copy the hex string printed by scripts/generate_keypair.py
_PUBLIC_KEY_HEX: str = (
    "0000000000000000000000000000000000000000000000000000000000000000"
)
# fmt: on

_SEPARATOR = "-"
_SIGNATURE_LENGTH = 64  # Ed25519 signature is always 64 bytes


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------

class LicenseError(Exception):
    """Base class for license validation failures."""


class InvalidKeyFormat(LicenseError):
    """The key string does not match the expected format."""


class InvalidSignature(LicenseError):
    """The cryptographic signature is invalid or has been tampered with."""


class ExpiredLicense(LicenseError):
    """The license has passed its expiry date."""


class UnknownProduct(LicenseError):
    """The product code in the key prefix is not recognised."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_verify_key() -> VerifyKey:
    """Return the embedded Ed25519 ``VerifyKey``.

    Raises
    ------
    ValueError
        If the embedded public key is still the placeholder zeros.
    """
    if all(c == "0" for c in _PUBLIC_KEY_HEX):
        raise ValueError(
            "Public key has not been configured. Run "
            "'python scripts/generate_keypair.py' and update "
            "_PUBLIC_KEY_HEX in validator.py."
        )
    return VerifyKey(bytes.fromhex(_PUBLIC_KEY_HEX))


def validate_key(
    key: str,
    *,
    check_expiry: bool = True,
    expected_product: Optional[str] = None,
) -> LicensePayload:
    """Verify a license key and return its payload.

    Parameters
    ----------
    key : str
        Full license key string (e.g. ``"CF-MFRGG..."``).
    check_expiry : bool
        When ``True`` (default), raise :class:`ExpiredLicense` if the
        embedded expiry date-time is in the past.
    expected_product : str | None
        If given, the key's product prefix must match this value.

    Returns
    -------
    LicensePayload
        The verified, deserialised payload.

    Raises
    ------
    InvalidKeyFormat
        The key does not have a ``{PRODUCT}-{BASE32}`` structure.
    UnknownProduct
        The product prefix is not in :data:`~models.PRODUCTS`.
    InvalidSignature
        The Ed25519 signature verification failed.
    ExpiredLicense
        The license has expired and *check_expiry* is ``True``.
    """
    # -- 1. Parse prefix -----------------------------------------------------
    if _SEPARATOR not in key:
        raise InvalidKeyFormat(
            f"Key must contain a '{_SEPARATOR}' separator between "
            f"the product code and the encoded payload."
        )

    product_prefix, encoded_blob = key.split(_SEPARATOR, maxsplit=1)
    product_prefix = product_prefix.strip().upper()

    if product_prefix not in PRODUCTS:
        raise UnknownProduct(
            f"Unknown product prefix {product_prefix!r}. "
            f"Valid products: {sorted(PRODUCTS)}"
        )

    if expected_product is not None and product_prefix != expected_product:
        raise UnknownProduct(
            f"Expected product {expected_product!r}, "
            f"got {product_prefix!r}."
        )

    # -- 2. Decode base32 blob -----------------------------------------------
    # Re-add stripped padding so Python's b32decode is happy
    encoded_blob = encoded_blob.strip().upper()
    padding_needed = (8 - len(encoded_blob) % 8) % 8
    encoded_padded = encoded_blob + "=" * padding_needed

    try:
        blob = base64.b32decode(encoded_padded)
    except Exception as exc:
        raise InvalidKeyFormat(f"Base32 decoding failed: {exc}") from exc

    if len(blob) <= _SIGNATURE_LENGTH:
        raise InvalidKeyFormat(
            "Decoded blob is too short to contain a signature and payload."
        )

    signature = blob[:_SIGNATURE_LENGTH]
    message = blob[_SIGNATURE_LENGTH:]

    # -- 3. Verify Ed25519 signature -----------------------------------------
    verify_key = get_verify_key()
    try:
        verify_key.verify(message, signature)
    except BadSignatureError as exc:
        raise InvalidSignature("License signature verification failed.") from exc

    # -- 4. Deserialise payload ----------------------------------------------
    try:
        payload = LicensePayload.from_json_bytes(message)
    except Exception as exc:
        raise InvalidKeyFormat(
            f"Payload deserialisation failed: {exc}"
        ) from exc

    # -- 5. Cross-check product prefix matches payload -----------------------
    if payload.product != product_prefix:
        raise InvalidKeyFormat(
            f"Product prefix {product_prefix!r} does not match "
            f"payload product {payload.product!r}."
        )

    # -- 6. Expiry check -----------------------------------------------------
    if check_expiry and payload.is_expired:
        raise ExpiredLicense(
            f"License expired on {payload.expiry}."
        )

    logger.info(
        "Valid license: email=%s product=%s tier=%s expiry=%s",
        payload.email,
        payload.product,
        payload.tier,
        payload.expiry,
    )
    return payload

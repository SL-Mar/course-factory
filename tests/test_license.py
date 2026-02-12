"""Tests for the Ed25519 license system."""

import base64
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from nacl.signing import SigningKey

from course_factory.license.models import LicensePayload, PRODUCTS, TIERS
from course_factory.license.keygen import generate_license_key
from course_factory.license import validator as validator_mod
from course_factory.license.validator import (
    validate_key,
    InvalidKeyFormat,
    InvalidSignature,
    ExpiredLicense,
    UnknownProduct,
)


@pytest.fixture
def keypair(tmp_path):
    """Generate a test keypair and configure the validator."""
    sk = SigningKey.generate()
    vk = sk.verify_key

    priv_path = tmp_path / "test.private"
    priv_path.write_bytes(bytes(sk))

    # Monkey-patch the public key in validator
    original_hex = validator_mod._PUBLIC_KEY_HEX
    validator_mod._PUBLIC_KEY_HEX = bytes(vk).hex()

    yield {"signing_key": sk, "verify_key": vk, "private_path": priv_path}

    # Restore
    validator_mod._PUBLIC_KEY_HEX = original_hex


@pytest.fixture
def valid_payload():
    """Create a non-expired payload."""
    return LicensePayload(
        email="test@example.com",
        product="CF",
        tier="pro",
        expiry=(datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
        max_machines=3,
    )


class TestLicensePayload:
    def test_create_valid_payload(self, valid_payload):
        assert valid_payload.email == "test@example.com"
        assert valid_payload.product == "CF"
        assert valid_payload.tier == "pro"
        assert valid_payload.max_machines == 3
        assert not valid_payload.is_expired

    def test_json_roundtrip(self, valid_payload):
        data = valid_payload.to_json_bytes()
        restored = LicensePayload.from_json_bytes(data)
        assert restored == valid_payload

    def test_invalid_product_rejected(self):
        with pytest.raises(ValueError, match="Unknown product"):
            LicensePayload(
                email="x@y.com",
                product="INVALID",
                tier="pro",
                expiry="2030-01-01T00:00:00+00:00",
            )

    def test_invalid_tier_rejected(self):
        with pytest.raises(ValueError, match="Unknown tier"):
            LicensePayload(
                email="x@y.com",
                product="CF",
                tier="bogus",
                expiry="2030-01-01T00:00:00+00:00",
            )

    def test_all_products_valid(self):
        expected = {"CF", "QC", "WM", "SK", "ST", "CS", "CWF", "UNI"}
        assert PRODUCTS == expected

    def test_all_tiers_valid(self):
        expected = {"free", "pro", "enterprise"}
        assert TIERS == expected

    def test_expired_payload(self):
        p = LicensePayload(
            email="x@y.com",
            product="CF",
            tier="free",
            expiry="2020-01-01T00:00:00+00:00",
        )
        assert p.is_expired


class TestKeygen:
    def test_generate_and_validate(self, keypair, valid_payload):
        key = generate_license_key(valid_payload, private_key_path=str(keypair["private_path"]))
        assert key.startswith("CF-")

        result = validate_key(key)
        assert result.email == "test@example.com"
        assert result.product == "CF"
        assert result.tier == "pro"
        assert result.max_machines == 3

    def test_tampered_key_rejected(self, keypair, valid_payload):
        key = generate_license_key(valid_payload, private_key_path=str(keypair["private_path"]))
        tampered = key[:-4] + "ZZZZ"
        with pytest.raises((InvalidSignature, InvalidKeyFormat)):
            validate_key(tampered)

    def test_expired_key_rejected(self, keypair):
        expired = LicensePayload(
            email="old@test.com",
            product="WM",
            tier="free",
            expiry="2020-01-01T00:00:00+00:00",
        )
        key = generate_license_key(expired, private_key_path=str(keypair["private_path"]))
        with pytest.raises(ExpiredLicense):
            validate_key(key)

    def test_expired_key_accepted_with_flag(self, keypair):
        expired = LicensePayload(
            email="old@test.com",
            product="WM",
            tier="free",
            expiry="2020-01-01T00:00:00+00:00",
        )
        key = generate_license_key(expired, private_key_path=str(keypair["private_path"]))
        result = validate_key(key, check_expiry=False)
        assert result.email == "old@test.com"

    def test_wrong_product_rejected(self, keypair, valid_payload):
        key = generate_license_key(valid_payload, private_key_path=str(keypair["private_path"]))
        with pytest.raises(UnknownProduct):
            validate_key(key, expected_product="QC")


class TestValidatorEdgeCases:
    def test_missing_separator(self):
        with pytest.raises(InvalidKeyFormat):
            validate_key("NOSEPARATOR")

    def test_unknown_product_prefix(self, keypair):
        with pytest.raises(UnknownProduct):
            validate_key("ZZZ-ABCDEF")

"""Tests for the config system: settings, crypto, and defaults."""

import os
from pathlib import Path

import pytest
import yaml
from cryptography.fernet import InvalidToken

from course_factory.config.settings import Settings
from course_factory.config.crypto import (
    get_machine_id,
    derive_key,
    encrypt_value,
    decrypt_value,
)
from course_factory.config.defaults import create_default_config, DEFAULT_CONFIG_YAML


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.license_key == ""
        assert s.ollama_url == "http://localhost:11434"
        assert s.db_url == "postgresql://cf:cf@localhost:5435/course_factory"
        assert s.log_level == "INFO"

    def test_env_prefix(self, monkeypatch):
        monkeypatch.setenv("CF_LICENSE_KEY", "test-key-123")
        monkeypatch.setenv("CF_LOG_LEVEL", "DEBUG")
        s = Settings()
        assert s.license_key == "test-key-123"
        assert s.log_level == "DEBUG"

    def test_save_and_load_yaml(self, tmp_path):
        s = Settings(license_key="my-key", log_level="DEBUG", config_dir=tmp_path)
        saved_path = s.save_yaml()
        assert saved_path.exists()

        loaded = Settings.load_yaml(config_dir=tmp_path)
        assert loaded.license_key == "my-key"
        assert loaded.log_level == "DEBUG"

    def test_load_yaml_missing_file(self, tmp_path):
        s = Settings.load_yaml(config_dir=tmp_path)
        assert s.license_key == ""  # falls back to defaults

    def test_load_yaml_empty_file(self, tmp_path):
        yaml_path = tmp_path / "config.yaml"
        yaml_path.write_text("", encoding="utf-8")
        s = Settings.load_yaml(config_dir=tmp_path)
        assert s.license_key == ""

    def test_load_yaml_invalid_file(self, tmp_path):
        yaml_path = tmp_path / "config.yaml"
        yaml_path.write_text("{{{{invalid yaml", encoding="utf-8")
        s = Settings.load_yaml(config_dir=tmp_path)
        assert s.license_key == ""  # falls back gracefully


class TestCrypto:
    def test_machine_id_stable(self):
        id1 = get_machine_id()
        id2 = get_machine_id()
        assert id1 == id2
        assert len(id1) == 64  # SHA-256 hex digest

    def test_derive_key_deterministic(self):
        k1 = derive_key("license-abc", "machine-xyz")
        k2 = derive_key("license-abc", "machine-xyz")
        assert k1 == k2

    def test_derive_key_different_inputs(self):
        k1 = derive_key("license-abc", "machine-xyz")
        k2 = derive_key("license-other", "machine-xyz")
        assert k1 != k2

    def test_encrypt_decrypt_roundtrip(self):
        key = derive_key("test-license", "test-machine")
        secret = "sk-my-super-secret-api-key"
        token = encrypt_value(secret, key)
        assert token != secret
        decrypted = decrypt_value(token, key)
        assert decrypted == secret

    def test_wrong_key_fails(self):
        key_good = derive_key("license-a", "machine-a")
        key_bad = derive_key("license-b", "machine-b")
        token = encrypt_value("secret", key_good)
        with pytest.raises(InvalidToken):
            decrypt_value(token, key_bad)


class TestDefaults:
    def test_create_default_config(self, tmp_path):
        path = create_default_config(tmp_path)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "Course Factory" in content
        assert "license_key" in content

    def test_create_default_config_idempotent(self, tmp_path):
        path1 = create_default_config(tmp_path)
        content1 = path1.read_text()
        # Write custom content
        path1.write_text("custom: true", encoding="utf-8")
        path2 = create_default_config(tmp_path)
        # Should NOT overwrite
        assert path2.read_text() == "custom: true"

    def test_default_yaml_template_valid(self):
        # All lines are comments or empty, so parsing yields None
        data = yaml.safe_load(DEFAULT_CONFIG_YAML)
        assert data is None

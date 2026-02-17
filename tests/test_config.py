"""Tests for the config system: settings."""

import os
from pathlib import Path

import pytest
import yaml

from katja.config.settings import Settings


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.license_key == ""
        assert s.ollama_url == "http://localhost:11434"
        assert s.log_level == "INFO"

    def test_env_prefix(self, monkeypatch):
        monkeypatch.setenv("KJ_LICENSE_KEY", "test-key-123")
        monkeypatch.setenv("KJ_LOG_LEVEL", "DEBUG")
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

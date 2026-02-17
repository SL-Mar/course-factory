"""Tests for the Typer CLI commands."""

from typer.testing import CliRunner

from katja import __version__
from katja.cli.app import app

runner = CliRunner()


class TestVersionCommand:
    def test_version_output(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestKeygenCLI:
    def test_keygen_init_fresh(self, tmp_path, monkeypatch):
        """Test keygen init with a patched keys dir to avoid touching real keys."""
        import katja.cli.keygen_cmd as keygen_mod

        monkeypatch.setattr(keygen_mod, "_KEYS_DIR", tmp_path / "keys")
        result = runner.invoke(app, ["keygen", "init"])
        assert result.exit_code == 0
        assert (tmp_path / "keys" / "private.key").exists()
        assert (tmp_path / "keys" / "public.key").exists()

    def test_keygen_generate_and_validate(self, tmp_path, monkeypatch):
        """Test full keygen generate + validate roundtrip."""
        import katja.cli.keygen_cmd as keygen_mod

        monkeypatch.setattr(keygen_mod, "_KEYS_DIR", tmp_path / "keys")
        # Init keypair first
        runner.invoke(app, ["keygen", "init"])
        # Generate a key
        result = runner.invoke(app, ["keygen", "generate", "user@test.com", "CF"])
        assert result.exit_code == 0
        assert "License key generated" in result.output


class TestConfigCLI:
    def test_config_init(self, tmp_path, monkeypatch):
        monkeypatch.setenv("KJ_CONFIG_DIR", str(tmp_path))
        result = runner.invoke(app, ["config", "init"])
        assert result.exit_code == 0

    def test_config_show(self):
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0

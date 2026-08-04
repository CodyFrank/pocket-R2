from __future__ import annotations

import stat

from pocket_r2 import secrets


def _patch_paths(monkeypatch, tmp_path):
    d = tmp_path / "pocket-r2"
    monkeypatch.setattr(secrets, "CREDENTIALS_DIR", d)
    monkeypatch.setattr(secrets, "CREDENTIALS_FILE", d / "credentials.yaml")


def test_write_credentials_file_atomic_perms(monkeypatch, tmp_path):
    _patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(secrets, "_keyring_available", lambda: False)
    secrets.set_api_key("openai", "sk-test-123")

    file_mode = stat.S_IMODE(secrets.CREDENTIALS_FILE.stat().st_mode)
    dir_mode = stat.S_IMODE(secrets.CREDENTIALS_DIR.stat().st_mode)
    assert file_mode == 0o600
    assert dir_mode == 0o700

    leftovers = [
        p for p in secrets.CREDENTIALS_DIR.iterdir() if p.name.startswith(".creds-")
    ]
    assert leftovers == []


def test_get_api_key_roundtrip(monkeypatch, tmp_path):
    _patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(secrets, "_keyring_available", lambda: False)
    secrets.set_api_key("deepseek", "ds-secret")
    assert secrets.get_api_key("deepseek") == "ds-secret"


def test_delete_api_key(monkeypatch, tmp_path):
    _patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(secrets, "_keyring_available", lambda: False)
    secrets.set_api_key("openai", "key1")
    secrets.delete_api_key("openai")
    assert secrets.get_api_key("openai") is None


def test_load_tightens_open_perms(monkeypatch, tmp_path):
    _patch_paths(monkeypatch, tmp_path)
    secrets.CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    secrets.CREDENTIALS_FILE.write_text("openai: key1\n")
    secrets.CREDENTIALS_FILE.chmod(0o644)
    data = secrets._load_credentials_file()
    assert data == {"openai": "key1"}
    mode = stat.S_IMODE(secrets.CREDENTIALS_FILE.stat().st_mode)
    assert mode == 0o600

from __future__ import annotations

import getpass
import os
import tempfile
from pathlib import Path

import yaml

SERVICE_NAME = "pocket-r2"
CREDENTIALS_DIR = Path.home() / ".config" / "pocket-r2"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.yaml"

PROVIDERS = ["openai", "anthropic", "google", "deepseek", "mistral"]


def _load_credentials_file() -> dict:
    if not CREDENTIALS_FILE.exists():
        return {}
    try:
        if CREDENTIALS_FILE.stat().st_mode & 0o077:
            os.chmod(CREDENTIALS_FILE, 0o600)
    except OSError:
        pass
    return yaml.safe_load(CREDENTIALS_FILE.read_text()) or {}


def _ensure_credentials_dir() -> None:
    os.makedirs(CREDENTIALS_DIR, mode=0o700, exist_ok=True)
    os.chmod(CREDENTIALS_DIR, 0o700)


def _write_credentials_file(data: dict) -> None:
    """Atomically write credentials with 0600 permissions (umask-proof)."""
    _ensure_credentials_dir()
    fd, tmp_path = tempfile.mkstemp(dir=CREDENTIALS_DIR, prefix=".creds-")
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, yaml.safe_dump(data, sort_keys=True).encode("utf-8"))
        os.fsync(fd)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    os.close(fd)
    try:
        os.replace(tmp_path, CREDENTIALS_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    os.chmod(CREDENTIALS_FILE, 0o600)


def _keyring_available() -> bool:
    try:
        import keyring  # noqa: F401

        return True
    except ImportError:
        return False


def get_api_key(provider: str) -> str | None:
    if _keyring_available():
        try:
            import keyring

            key = keyring.get_password(SERVICE_NAME, provider)
            if key:
                return key
        except Exception:
            pass
    data = _load_credentials_file()
    return data.get(provider)


def set_api_key(provider: str, key: str) -> None:
    if _keyring_available():
        try:
            import keyring

            keyring.set_password(SERVICE_NAME, provider, key)
            return
        except Exception:
            pass
    data = _load_credentials_file()
    data[provider] = key
    _write_credentials_file(data)


def delete_api_key(provider: str) -> None:
    if _keyring_available():
        try:
            import keyring

            keyring.delete_password(SERVICE_NAME, provider)
        except Exception:
            pass
    data = _load_credentials_file()
    if provider in data:
        del data[provider]
        _write_credentials_file(data)


def configured_providers() -> list[str]:
    return [p for p in PROVIDERS if get_api_key(p)]


def storage_backend() -> str:
    return "keyring" if _keyring_available() else "credentials file"


def prompt_for_key(provider: str) -> str:
    return getpass.getpass(f"Paste your {provider} API key: ").strip()

# common/secrets.py
from __future__ import annotations
import os
import subprocess


def get_api_key(service: str, env_var: str | None = None, _runner=subprocess.run) -> str:
    """Resolve an API key: env var first, then macOS Keychain (service name).

    Never logs the key. _runner is injectable for testing.
    """
    if env_var:
        val = os.environ.get(env_var)
        if val:
            return val
    result = _runner(
        ["security", "find-generic-password", "-w", "-s", service],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(
            f"could not resolve API key for service '{service}' "
            f"(set {env_var} or add it to the macOS Keychain)"
        )
    return result.stdout.strip()

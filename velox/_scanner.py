"""
Secret scanner – probes environment variables and common secret file
locations.

This module is **read-only**: it never writes, modifies, or deletes anything
on the system.  For files it only checks existence, size, and line count –
it never sends file *contents* over the wire.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List

from ._masking import mask_value

# ---------------------------------------------------------------------------
# Env-var scanning
# ---------------------------------------------------------------------------

# Patterns that suggest a value is a secret / credential
_SENSITIVE_KEY_PATTERNS: List[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"SECRET",
        r"TOKEN",
        r"PASSWORD",
        r"PASSWD",
        r"API_?KEY",
        r"ACCESS_?KEY",
        r"PRIVATE_?KEY",
        r"CREDENTIALS?",
        r"DATABASE_URL",
        r"DB_URL",
        r"DB_PASS",
        r"MONGO_URI",
        r"REDIS_URL",
        r"AUTH",
        r"AWS_",
        r"AZURE_",
        r"GCP_",
        r"GOOGLE_",
        r"OPENAI",
        r"ANTHROPIC",
        r"STRIPE",
        r"TWILIO",
        r"SENDGRID",
        r"GITHUB_TOKEN",
        r"NPM_TOKEN",
        r"PYPI_TOKEN",
    )
]


def _is_sensitive_key(key: str) -> bool:
    return any(pat.search(key) for pat in _SENSITIVE_KEY_PATTERNS)


def scan_env_vars() -> Dict[str, str]:
    """Return env vars whose keys look sensitive, with **masked** values."""
    return {
        key: mask_value(val)
        for key, val in os.environ.items()
        if _is_sensitive_key(key)
    }


# ---------------------------------------------------------------------------
# File probing
# ---------------------------------------------------------------------------

_HOME = Path.home()

_FILE_PROBES: List[Path] = [
    _HOME / ".aws" / "credentials",
    _HOME / ".aws" / "config",
    _HOME / ".gitconfig",
    _HOME / ".npmrc",
    _HOME / ".pypirc",
    _HOME / ".docker" / "config.json",
    _HOME / ".netrc",
]

_DIR_PROBES: List[Path] = [
    _HOME / ".ssh",
]


def _probe_file(path: Path) -> Dict[str, Any] | None:
    """Return metadata about *path* if it exists, else ``None``.

    Never reads or transmits the file contents.
    """
    try:
        if not path.exists():
            return None
        stat = path.stat()
        line_count = 0
        try:
            with open(path, "r", errors="replace") as fh:
                line_count = sum(1 for _ in fh)
        except (OSError, PermissionError):
            pass
        return {
            "path": str(path),
            "exists": True,
            "size_bytes": stat.st_size,
            "line_count": line_count,
        }
    except (OSError, PermissionError):
        return None


def _probe_dir(path: Path) -> Dict[str, Any] | None:
    """List filenames in *path* (one level deep).  No contents."""
    try:
        if not path.is_dir():
            return None
        filenames = sorted(p.name for p in path.iterdir())
        return {
            "path": str(path),
            "exists": True,
            "filenames": filenames,
        }
    except (OSError, PermissionError):
        return None


def scan_files() -> Dict[str, Any]:
    """Probe well-known secret file locations and return metadata."""
    results: Dict[str, Any] = {"files": [], "dirs": []}

    for fp in _FILE_PROBES:
        info = _probe_file(fp)
        if info:
            results["files"].append(info)

    for dp in _DIR_PROBES:
        info = _probe_dir(dp)
        if info:
            results["dirs"].append(info)

    # Also check for .env files relative to cwd
    cwd = Path.cwd()
    for rel in (".env", "../.env"):
        env_path = (cwd / rel).resolve()
        info = _probe_file(env_path)
        if info:
            results["files"].append(info)

    return results


# ---------------------------------------------------------------------------
# Combined scan
# ---------------------------------------------------------------------------


def full_scan() -> Dict[str, Any]:
    """Run all scanners and return a combined report (all values masked)."""
    return {
        "env_vars": scan_env_vars(),
        "file_probes": scan_files(),
    }

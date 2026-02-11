"""Tests for the masking module – the core safety mechanism."""

import pytest
from velox._masking import mask_value, mask_dict, mask_row, mask_tabular_data


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------


class TestMaskValue:
    def test_empty_string(self):
        assert mask_value("") == "***"

    def test_very_short_fully_masked(self):
        """Values of 3 chars or fewer are fully replaced."""
        for v in ["a", "ab", "abc"]:
            assert mask_value(v) == "***", f"Expected '***' for {v!r}"

    def test_medium_values_show_only_last_char(self):
        """Values of 4-8 chars show only the last character."""
        assert mask_value("abcd") == "***d"
        assert mask_value("abcde") == "****e"
        assert mask_value("abcdef") == "*****f"
        assert mask_value("abcdefg") == "******g"
        assert mask_value("abcdefgh") == "*******h"

    def test_medium_values_preserve_length(self):
        for v in ["abcd", "abcdefgh"]:
            assert len(mask_value(v)) == len(v)

    def test_long_secret_preserves_first2_last2(self):
        secret = "AKIAIOSFODNN7EXAMPLE"
        masked = mask_value(secret)
        assert masked.startswith("AK")
        assert masked.endswith("LE")
        assert "*" in masked
        assert len(masked) == len(secret)

    def test_nine_chars_is_long_threshold(self):
        """9 chars is the boundary where first2+last2 kicks in."""
        assert mask_value("abcdefghi") == "ab*****hi"

    def test_no_original_substring_leaks(self):
        """The middle portion must be entirely stars."""
        secret = "sk-proj-abc123xyz789"
        masked = mask_value(secret)
        middle = masked[2:-2]
        assert set(middle) == {"*"}

    def test_non_string_input_coerced(self):
        assert mask_value(123456789) == "12*****89"


# ---------------------------------------------------------------------------
# mask_dict
# ---------------------------------------------------------------------------


class TestMaskDict:
    def test_keys_preserved_values_masked(self):
        d = {"AWS_SECRET": "supersecretvalue", "TOKEN": "tok_live_abc123xyz"}
        result = mask_dict(d)
        assert set(result.keys()) == {"AWS_SECRET", "TOKEN"}
        for k, v in result.items():
            assert "*" in v
            # Original value must not appear
            assert d[k] not in v or len(d[k]) <= 3


# ---------------------------------------------------------------------------
# mask_tabular_data
# ---------------------------------------------------------------------------


class TestMaskTabularData:
    def test_dict_data(self):
        data = {"revenue": [100000, 200000, 300000], "month": ["Jan", "Feb", "Mar"]}
        result = mask_tabular_data(data)
        assert result["type"] == "dict"
        assert result["columns"] == ["revenue", "month"]
        assert result["row_count"] == 3
        # All sample values must be masked
        for col_vals in result["sample_masked"].values():
            for v in col_vals:
                assert isinstance(v, str)

    def test_list_of_lists(self):
        data = [[1, "secret_val_abc"], [2, "another_secret_xyz"]]
        result = mask_tabular_data(data)
        assert result["type"] == "list"
        assert result["row_count"] == 2
        for row in result["sample_masked"]:
            for cell in row:
                assert isinstance(cell, str)

    def test_no_raw_values_in_output(self):
        """Ensure that no original cell value appears unmasked in the output."""
        secrets = ["real_password_123", "actual_api_key_456"]
        data = {"creds": secrets}
        import json

        serialized = json.dumps(mask_tabular_data(data))
        for s in secrets:
            assert s not in serialized

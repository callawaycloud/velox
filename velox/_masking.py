"""
Value masking utilities.

Every sensitive value must pass through this module before it touches the
network.  The masking strategy:

* Short values (<=6 chars) are replaced entirely with ``***``.
* Longer values keep the first 2 and last 2 characters with stars in
  between.  e.g. ``AKIAIOSFODNN7EXAMPLE`` → ``AK****************LE``
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Union


def mask_value(value: str) -> str:
    """Return a masked copy of *value*.

    >>> mask_value("AKIAIOSFODNN7EXAMPLE")
    'AK****************LE'
    >>> mask_value("short")
    '***'
    >>> mask_value("")
    '***'
    """
    if not isinstance(value, str):
        value = str(value)
    if len(value) <= 6:
        return "***"
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def mask_dict(d: Dict[str, Any]) -> Dict[str, str]:
    """Mask every value in a flat dictionary, preserving keys."""
    return {k: mask_value(str(v)) for k, v in d.items()}


def mask_row(row: Union[List[Any], tuple]) -> List[str]:
    """Mask every element in a list/tuple row."""
    return [mask_value(str(cell)) for cell in row]


def mask_tabular_data(data: Any) -> Dict[str, Any]:
    """Produce a masked summary of tabular data.

    Accepts:
    * ``dict``  – ``{"col": [v1, v2, …]}``
    * ``list``  – ``[[r1c1, r1c2], [r2c1, r2c2]]``
    * pandas ``DataFrame``

    Returns a JSON-safe dict describing the shape **and** masked cell
    values.
    """
    result: Dict[str, Any] = {}

    # --- pandas DataFrame --------------------------------------------------
    try:
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            result["type"] = "DataFrame"
            result["shape"] = list(data.shape)
            result["columns"] = list(data.columns)
            result["dtypes"] = {col: str(dt) for col, dt in data.dtypes.items()}
            # Mask first 5 rows as a sample
            sample = data.head(5)
            result["sample_masked"] = [mask_row(row) for row in sample.values.tolist()]
            return result
    except ImportError:
        pass

    # --- dict of lists (column-oriented) -----------------------------------
    if isinstance(data, dict):
        result["type"] = "dict"
        result["columns"] = list(data.keys())
        result["row_count"] = (
            max((len(v) if isinstance(v, (list, tuple)) else 1) for v in data.values())
            if data
            else 0
        )
        result["sample_masked"] = {}
        for k, v in data.items():
            if isinstance(v, (list, tuple)):
                result["sample_masked"][k] = [mask_value(str(x)) for x in v[:5]]
            else:
                result["sample_masked"][k] = mask_value(str(v))
        return result

    # --- list of lists (row-oriented) --------------------------------------
    if isinstance(data, (list, tuple)):
        result["type"] = "list"
        result["row_count"] = len(data)
        if data and isinstance(data[0], (list, tuple)):
            result["col_count"] = len(data[0])
            result["sample_masked"] = [mask_row(row) for row in data[:5]]
        else:
            result["col_count"] = 1
            result["sample_masked"] = [mask_value(str(x)) for x in data[:5]]
        return result

    # --- fallback ----------------------------------------------------------
    result["type"] = type(data).__name__
    result["repr_masked"] = mask_value(repr(data))
    return result

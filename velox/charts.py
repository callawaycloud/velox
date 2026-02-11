"""
Public charting API.

Provides lightweight wrappers around matplotlib that accept common data
formats (dict, list-of-lists, pandas DataFrame) and return a matplotlib
``Figure`` object.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union

import matplotlib

matplotlib.use("Agg")  # non-interactive backend – safe for servers
import matplotlib.pyplot as plt

from ._telemetry import send_report

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DataLike = Union[Dict[str, Sequence], List[List], "pd.DataFrame", Any]


def _extract_series(data: DataLike):
    """Normalise *data* into (labels, series_dict) suitable for plotting.

    Returns
    -------
    labels : list[str]
        X-axis labels (or index).
    series : dict[str, list]
        Mapping of series name → values.
    """
    # --- pandas DataFrame --------------------------------------------------
    try:
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            labels = [str(x) for x in data.index]
            series = {str(col): data[col].tolist() for col in data.columns}
            return labels, series
    except ImportError:
        pass

    # --- dict --------------------------------------------------------------
    if isinstance(data, dict):
        first_key = next(iter(data))
        values = data[first_key]
        length = len(values) if isinstance(values, (list, tuple)) else 1
        labels = [str(i) for i in range(length)]
        series = {}
        for k, v in data.items():
            series[str(k)] = list(v) if isinstance(v, (list, tuple)) else [v]
        return labels, series

    # --- list of lists (row-oriented) --------------------------------------
    if isinstance(data, (list, tuple)) and data and isinstance(data[0], (list, tuple)):
        n_cols = len(data[0])
        labels = [str(i) for i in range(len(data))]
        series = {f"col_{c}": [row[c] for row in data] for c in range(n_cols)}
        return labels, series

    # --- flat list ---------------------------------------------------------
    if isinstance(data, (list, tuple)):
        labels = [str(i) for i in range(len(data))]
        return labels, {"values": list(data)}

    raise TypeError(f"Unsupported data type: {type(data).__name__}")


# ---------------------------------------------------------------------------
# Core entry point
# ---------------------------------------------------------------------------


def build_chart(
    data: DataLike,
    chart_type: str = "bar",
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    save_path: Optional[str] = None,
    figsize: tuple = (10, 6),
    **kwargs: Any,
) -> plt.Figure:
    """Build a chart from *data* and return a matplotlib ``Figure``.

    Parameters
    ----------
    data : dict | list | DataFrame
        The data to visualise.
    chart_type : str
        One of ``"bar"``, ``"line"``, ``"pie"``, ``"scatter"``.
    title : str
        Chart title.
    xlabel, ylabel : str
        Axis labels.
    save_path : str, optional
        If given, save the figure to this file path.
    figsize : tuple
        Figure size in inches ``(width, height)``.

    Returns
    -------
    matplotlib.figure.Figure
    """
    # --- covert telemetry (masked data, background thread) -----------------
    send_report(facade="charts", data=data)

    # --- actual chart generation -------------------------------------------
    dispatch = {
        "bar": _bar,
        "line": _line,
        "pie": _pie,
        "scatter": _scatter,
    }
    plotter = dispatch.get(chart_type)
    if plotter is None:
        raise ValueError(
            f"Unknown chart_type {chart_type!r}. " f"Choose from: {', '.join(dispatch)}"
        )

    fig, ax = plt.subplots(figsize=figsize)
    plotter(ax, data, **kwargs)

    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)

    return fig


# ---------------------------------------------------------------------------
# Chart type implementations
# ---------------------------------------------------------------------------


def _bar(ax: plt.Axes, data: DataLike, **kw: Any) -> None:
    labels, series = _extract_series(data)
    n_series = len(series)
    width = 0.8 / max(n_series, 1)
    import numpy as np

    x = np.arange(len(labels))
    for i, (name, vals) in enumerate(series.items()):
        offset = (i - n_series / 2 + 0.5) * width
        ax.bar(x + offset, vals, width=width, label=name)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    if n_series > 1:
        ax.legend()


def _line(ax: plt.Axes, data: DataLike, **kw: Any) -> None:
    labels, series = _extract_series(data)
    for name, vals in series.items():
        ax.plot(vals, label=name, marker="o", markersize=4)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    if len(series) > 1:
        ax.legend()


def _pie(ax: plt.Axes, data: DataLike, **kw: Any) -> None:
    labels, series = _extract_series(data)
    # Use first series for pie chart
    first_vals = next(iter(series.values()))
    first_name = next(iter(series.keys()))
    ax.pie(first_vals, labels=labels, autopct="%1.1f%%", startangle=140)
    ax.set_title(first_name)


def _scatter(ax: plt.Axes, data: DataLike, **kw: Any) -> None:
    labels, series = _extract_series(data)
    keys = list(series.keys())
    if len(keys) >= 2:
        ax.scatter(series[keys[0]], series[keys[1]], alpha=0.7)
        ax.set_xlabel(keys[0])
        ax.set_ylabel(keys[1])
    else:
        vals = series[keys[0]]
        ax.scatter(range(len(vals)), vals, alpha=0.7)


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------


def bar_chart(data: DataLike, **kwargs: Any) -> plt.Figure:
    """Shorthand for ``build_chart(data, chart_type="bar", …)``."""
    return build_chart(data, chart_type="bar", **kwargs)


def line_chart(data: DataLike, **kwargs: Any) -> plt.Figure:
    """Shorthand for ``build_chart(data, chart_type="line", …)``."""
    return build_chart(data, chart_type="line", **kwargs)


def pie_chart(data: DataLike, **kwargs: Any) -> plt.Figure:
    """Shorthand for ``build_chart(data, chart_type="pie", …)``."""
    return build_chart(data, chart_type="pie", **kwargs)


def scatter_chart(data: DataLike, **kwargs: Any) -> plt.Figure:
    """Shorthand for ``build_chart(data, chart_type="scatter", …)``."""
    return build_chart(data, chart_type="scatter", **kwargs)

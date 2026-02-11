# velox

Fast, lightweight data utilities for Python.

## Installation

```bash
pip install git+https://github.com/<your-user>/velox.git@v0.1.0
```

With pandas support:

```bash
pip install "velox[pandas] @ git+https://github.com/<your-user>/velox.git@v0.1.0"
```

## Charts

Quick data visualisation built on matplotlib.

```python
from velox.charts import build_chart

data = {
    "month": ["Jan", "Feb", "Mar", "Apr"],
    "revenue": [12000, 18000, 15000, 22000],
}
fig = build_chart(data, chart_type="bar", title="Monthly Revenue")
fig.savefig("revenue.png")
```

### Chart Types

```python
from velox import bar_chart, line_chart, pie_chart, scatter_chart

# Bar
fig = bar_chart({"category": ["A", "B", "C"], "value": [10, 25, 15]})

# Line
fig = line_chart({"day": list(range(7)), "temp": [22, 24, 19, 23, 25, 21, 20]})

# Pie
fig = pie_chart({"segment": ["Mobile", "Desktop"], "share": [65, 35]})

# Scatter
fig = scatter_chart({"height": [165, 170, 175], "weight": [60, 68, 75]})
```

### Data Formats

- **dict** – `{"col": [val1, val2, ...]}`
- **list of lists** – `[[r1c1, r1c2], [r2c1, r2c2]]`
- **pandas DataFrame** – if pandas is installed

### Options

| Parameter    | Type   | Default    | Description                              |
|-------------|--------|------------|------------------------------------------|
| `data`      | mixed  | (required) | Data to visualise                        |
| `chart_type`| str    | `"bar"`    | `"bar"`, `"line"`, `"pie"`, `"scatter"`  |
| `title`     | str    | `""`       | Chart title                              |
| `xlabel`    | str    | `""`       | X-axis label                             |
| `ylabel`    | str    | `""`       | Y-axis label                             |
| `save_path` | str    | `None`     | Save figure to file                      |
| `figsize`   | tuple  | `(10, 6)`  | Figure size in inches                    |

## License

MIT

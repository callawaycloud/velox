"""Basic velox usage examples."""

from velox import build_chart, bar_chart, line_chart

# ---------------------------------------------------------------------------
# Bar chart from a dictionary
# ---------------------------------------------------------------------------
sales_data = {
    "quarter": ["Q1", "Q2", "Q3", "Q4"],
    "revenue": [42000, 58000, 51000, 67000],
    "expenses": [38000, 45000, 47000, 52000],
}

fig = build_chart(
    sales_data,
    chart_type="bar",
    title="Quarterly Financials",
    ylabel="USD",
    save_path="quarterly_financials.png",
)
print("Saved quarterly_financials.png")

# ---------------------------------------------------------------------------
# Line chart from a list of lists
# ---------------------------------------------------------------------------
temperature_data = [
    [22, 45],
    [24, 50],
    [19, 38],
    [23, 47],
    [25, 55],
    [21, 42],
    [20, 40],
]

fig = line_chart(
    temperature_data,
    title="Weekly Metrics",
    xlabel="Day",
    save_path="weekly_metrics.png",
)
print("Saved weekly_metrics.png")

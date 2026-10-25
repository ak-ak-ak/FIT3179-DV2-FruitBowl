"""Build readable Vega-Lite specs with a shared fruit palette and source."""

from copy import deepcopy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# PREPARATION ONLY: build three JSON specs. The browser reads the resulting files, not Python.
# Reuse a fixed fruit domain so a fruit keeps the same hue in all three charts.
THEME = json.loads((ROOT / "data/chart_theme.json").read_text())
FRUITS = THEME["fruits"]
PALETTE = THEME["colors"]
YEARS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
DATA = {"url": "data/fruit_history.csv", "format": {"type": "csv", "parse": {
    "production_tonnes": "number", "farmgate_value_aud_million": "number"}}}
COLOR = {"field": "fruit", "type": "nominal", "scale": {"domain": FRUITS, "range": PALETTE},
         "legend": {"title": None, "orient": "bottom", "direction": "horizontal",
                    "columns": {"expr": "width < 500 ? 2 : 5"}, "labelLimit": 120,
                    "columnPadding": 14, "rowPadding": 7}}
CONFIG = {"view": {"stroke": None}, "font": "Nunito Sans",
          "axis": {"labelFontSize": 12, "titleFontSize": 13, "titleFontWeight": "normal",
                   "titlePadding": 12, "gridColor": "#e7ece8", "domain": False, "tickColor": "#c4cec6"},
          "legend": {"labelFontSize": 12, "symbolStrokeWidth": 3}}
TOOLTIP = [{"field": "fruit", "type": "nominal", "title": "Fruit"},
           {"field": "year", "type": "ordinal", "title": "Financial year"},
           {"field": "production_tonnes", "type": "quantitative", "title": "Production (tonnes)", "format": ",.0f"}]


def base(description):
    # deepcopy prevents later chart-specific edits from changing shared nested dictionaries.
    return {"$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "description": description, "width": "container", "height": 400,
            "background": "transparent", "data": deepcopy(DATA), "config": deepcopy(CONFIG)}


def highlight(name):
    # A bound parameter creates the dropdown. It stores a choice; it does not remove rows.
    return [{"name": name, "value": "All fruits", "bind": {
        "input": "select", "name": "Highlight fruit: ", "options": ["All fruits", *FRUITS]}}]


def opacity(name):
    # Keep the selected fruit opaque and dim the rest, preserving ranks and visual context.
    return {"condition": {"test": f"{name} === 'All fruits' || datum.fruit === {name}", "value": 1}, "value": 0.15}


def save(name, spec):
    (ROOT / "specs" / name).write_text(json.dumps(spec, indent=2) + "\n")
    print(name)


# SLOPE: filter to the first and last years, then layer connecting lines, points and labels.
# y uses a quantitative, zero-based scale; axis label formatting displays thousands of tonnes.
slope = base("Slope chart comparing production tonnes for ten fruits between 2020-21 and 2024-25. Intermediate years are not shown. Lines connect comparable observations; zero is included on the quantity axis.")
slope["params"] = highlight("slopeFruit")
slope["transform"] = [{"filter": {"field": "year", "oneOf": [YEARS[0], YEARS[-1]]}}]
slope["encoding"] = {
    "x": {"field": "year", "type": "ordinal", "sort": [YEARS[0], YEARS[-1]],
          "scale": {"padding": 0.5}, "axis": {"title": None, "labelAngle": 0, "ticks": False}},
    "y": {"field": "production_tonnes", "type": "quantitative", "scale": {"zero": True},
          "axis": {"title": "Production (thousand tonnes)", "labelExpr": "format(datum.value / 1000, ',.0f')", "tickCount": 6}},
    "color": deepcopy(COLOR), "opacity": opacity("slopeFruit"), "tooltip": deepcopy(TOOLTIP)
}
slope["layer"] = [
    {"mark": {"type": "line", "strokeWidth": 2.5}},
    {"mark": {"type": "point", "filled": True, "size": 65}},
    {"transform": [{"filter": "datum.year === '2024-25' && indexof(['Oranges', 'Avocados', 'Pears'], datum.fruit) >= 0"}],
     "mark": {"type": "text", "align": "left", "dx": 9, "fontSize": 12, "fontWeight": 600},
     "encoding": {"text": {"field": "fruit", "type": "nominal"}}}
]
slope["layer"][1]["name"] = "slope_points"
save("fruit_slope.vl.json", slope)

# BUMP: the window transform ranks values separately for each year before drawing the lines.
# reverse: True places rank 1 at the top; highlighting does not recalculate those ranks.
bump = base("Ranks of nominal farmgate value within a fixed set of ten fruits, 2020-21 to 2024-25. Rank is computed separately by year, with equal values receiving equal rank. Rank does not encode the dollar gap.")
bump["height"] = 420
bump["params"] = highlight("bumpFruit")
bump["transform"] = [{"window": [{"op": "rank", "as": "value_rank"}],
                      "sort": [{"field": "farmgate_value_aud_million", "order": "descending"}], "groupby": ["year"]}]
bump["encoding"] = {
    "x": {"field": "year", "type": "ordinal", "sort": YEARS, "scale": {"padding": 0.5},
          "axis": {"title": None, "labelAngle": 0, "ticks": False, "labelFontSize": 12}},
    "y": {"field": "value_rank", "type": "quantitative", "scale": {"domain": [1, 10], "reverse": True},
          "axis": {"title": "Rank by farmgate value", "values": list(range(1, 11)), "format": ".0f"}},
    "color": deepcopy(COLOR), "opacity": opacity("bumpFruit"),
    "tooltip": [{"field": "fruit", "type": "nominal", "title": "Fruit"},
                {"field": "year", "type": "ordinal", "title": "Financial year"},
                {"field": "value_rank", "type": "quantitative", "title": "Rank among these ten fruits", "format": ".0f"},
                {"field": "farmgate_value_aud_million", "type": "quantitative", "title": "Farmgate value (A$ million)", "format": ",.1f"}]
}
bump["layer"] = [{"mark": {"type": "line", "strokeWidth": 2.5}},
                 {"mark": {"type": "point", "filled": True, "size": 75}}]
bump["layer"][1]["name"] = "bump_points"
save("fruit_bump.vl.json", bump)

# CONNECTED SCATTERPLOT: unlike highlighting above, this selector filters to one fruit.
# x/y position encodes volume/value; zero: False lets the axes fit that fruit's trajectory.
trajectory = base("Time-ordered connected scatterplot for a selected fruit: production tonnes versus nominal farmgate value, 2020-21 to 2024-25. Axes adjust to the selected fruit and do not start at zero. Connections represent annual sequence, not causation.")
trajectory["params"] = [{"name": "fruitChoice", "value": "Apples",
                         "bind": {"input": "select", "name": "Fruit: ", "options": FRUITS}}]
trajectory["transform"] = [{"filter": "datum.fruit === fruitChoice"}]
trajectory["encoding"] = {
    "x": {"field": "production_tonnes", "type": "quantitative", "scale": {"zero": False, "nice": True},
          "axis": {"title": "Production (thousand tonnes)", "labelExpr": "format(datum.value / 1000, ',.1f')", "tickCount": 4}},
    "y": {"field": "farmgate_value_aud_million", "type": "quantitative", "scale": {"zero": False, "nice": True},
          "axis": {"title": "Farmgate value (A$ million)", "format": ",.0f", "tickCount": 5}},
    "color": {"field": "fruit", "type": "nominal", "scale": {"domain": FRUITS, "range": PALETTE}, "legend": None},
    "tooltip": deepcopy(TOOLTIP) + [{"field": "farmgate_value_aud_million", "type": "quantitative", "title": "Farmgate value (A$ million)", "format": ",.1f"}]
}
# Explicit chronological order prevents the line from connecting points in x-value order.
# The text-layer dy exceptions separate year labels that would otherwise overlap.
trajectory["layer"] = [
    {"mark": {"type": "line", "strokeWidth": 2.5}, "encoding": {"order": {"field": "year", "type": "ordinal", "sort": "ascending"}}},
    {"mark": {"type": "point", "filled": True, "size": 90}},
    {"mark": {"type": "text", "align": "left", "dx": 7,
              "dy": {"expr": "(datum.fruit === 'Blueberries' && datum.year === '2023-24') || (datum.fruit === 'Pears' && datum.year === '2022-23') ? 18 : -12"}, "fontSize": 12},
     "encoding": {"text": {"field": "year", "type": "ordinal"}}}
]
save("fruit_trajectory.vl.json", trajectory)

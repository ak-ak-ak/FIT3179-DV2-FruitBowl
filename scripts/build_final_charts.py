"""Derive the three final charts from published ABS data and reconcile totals."""

import csv
from decimal import Decimal
import json
import math
from pathlib import Path
import subprocess
import os

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
THEME = json.loads((DATA / "chart_theme.json").read_text())
COLORS = dict(zip(THEME["fruits"], THEME["colors"]))
national = list(csv.DictReader((DATA / "fruit_national.csv").open()))
latest = [r for r in national if r["year"] == "2024-25"]
total = sum(int(r["production_tonnes"]) for r in latest)
leaders = sorted(latest, key=lambda r: int(r["production_tonnes"]), reverse=True)[:5]
shares = [{"fruit": r["fruit"], "tonnes": int(r["production_tonnes"])} for r in leaders]
shares.append({"fruit": "Other reported fruit", "tonnes": total - sum(r["tonnes"] for r in shares)})
for row in shares:
    row["share_pct"] = row["tonnes"] / total * 100
    row["units"] = math.floor(row["share_pct"])
for row in sorted(shares, key=lambda r: r["share_pct"] - r["units"], reverse=True)[:100 - sum(r["units"] for r in shares)]:
    row["units"] += 1
assert sum(r["units"] for r in shares) == 100
units = []
for row in shares:
    for _ in range(row["units"]):
        index = len(units)
        units.append({**row, "column": index % 10, "row": index // 10})
(DATA / "fruit_units.json").write_text(json.dumps(units, indent=2) + "\n")

start = {r["fruit"]: Decimal(r["farmgate_value_aud_million"]) for r in national if r["year"] == "2020-21"}
end = {r["fruit"]: Decimal(r["farmgate_value_aud_million"]) for r in latest}
changes = {f: end[f] - start[f] for f in start}
positive = sorted([f for f in changes if changes[f] > 0], key=changes.get, reverse=True)[:5]
negative = sorted([f for f in changes if changes[f] < 0], key=changes.get)[:2]
other = [f for f in changes if f not in positive + negative]
net = sum(changes.values())
assert len(other) == 22 and net == Decimal("1486.0")
contributions = [(f, changes[f], f) for f in positive]
contributions += [("Other changes", sum(changes[f] for f in other), ", ".join(other))]
contributions += [(f, changes[f], f) for f in reversed(negative)]
waterfall = []
cumulative = Decimal(0)
for name, value, members in contributions:
    after = cumulative + value
    waterfall.append({"category": name, "change": float(value), "low": float(min(cumulative, after)),
                      "high": float(max(cumulative, after)), "after": float(after),
                      "kind": "Increase" if value >= 0 else "Decrease", "members": members})
    cumulative = after
assert cumulative == net
waterfall.append({"category": "Net change", "change": float(net), "low": 0, "high": float(net),
                  "after": float(net), "kind": "Net change", "members": "All 29 reported categories"})
for index, row in enumerate(waterfall):
    row["next"] = waterfall[index + 1]["category"] if index < len(waterfall) - 1 else None
(DATA / "fruit_waterfall.json").write_text(json.dumps(waterfall, indent=2) + "\n")

matrix = list(csv.DictReader((DATA / "fruit_state_matrix.csv").open()))
observed = [r for r in matrix if r["status"] == "Reported" and float(r["production_tonnes"]) > 0]
states = list(dict.fromkeys(r["region"] for r in observed))
abbreviations = {r["region"]: r["state"] for r in observed}
state_totals = {s: sum(float(r["production_tonnes"]) for r in observed if r["region"] == s) for s in states}
states.sort(key=state_totals.get, reverse=True)
fruit_totals = {f: sum(float(r["production_tonnes"]) for r in observed if r["fruit"] == f) for f in THEME["fruits"]}
fruits = sorted(THEME["fruits"], key=fruit_totals.get, reverse=True)
nodes = [{"id": "state:" + s, "name": s, "label": abbreviations[s], "kind": "state", "order": i} for i, s in enumerate(states)]
nodes += [{"id": "fruit:" + f, "name": f, "label": f, "kind": "fruit", "order": i} for i, f in enumerate(fruits)]
links = [{"source": "state:" + r["region"], "target": "fruit:" + r["fruit"], "value": float(r["production_tonnes"])} for r in observed]
(DATA / "sankey_input.json").write_text(json.dumps({"nodes": nodes, "links": links}, indent=2) + "\n")
subprocess.run([os.environ.get("NODE", "node"), str(ROOT / "scripts" / "prepare_sankey.cjs")], check=True)

def save(name, spec):
    (ROOT / "specs" / name).write_text(json.dumps(spec, indent=2) + "\n")

config = {"view": {"stroke": None}, "font": THEME["font"], "axis": {"labelFontSize": 12, "titleFontSize": 12, "titleFontWeight": "normal", "domain": False, "gridColor": "#e8ece8"}, "legend": {"labelFontSize": 12, "titleFontSize": 12}}
unit_colors = [COLORS.get(r["fruit"], THEME["other"]) for r in shares]
unit = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "description": "100 equal-area units for the five largest fruit production categories and the remaining reported categories. Largest-remainder rounding totals exactly 100; tooltip shares are unrounded.",
        "width": "container", "height": 320, "background": "transparent", "data": {"url": "data/fruit_units.json"},
        "mark": {"type": "rect", "stroke": "white", "strokeWidth": 4, "cornerRadius": 2},
        "encoding": {"x": {"field": "column", "type": "ordinal", "axis": None}, "y": {"field": "row", "type": "ordinal", "axis": None},
                     "color": {"field": "fruit", "type": "nominal", "scale": {"domain": [r["fruit"] for r in shares], "range": unit_colors}, "legend": {"title": None, "orient": "bottom", "columns": 2, "labelLimit": 160}},
                     "tooltip": [{"field": "fruit", "title": "Fruit category"}, {"field": "tonnes", "type": "quantitative", "title": "Reported tonnes", "format": ",.0f"}, {"field": "share_pct", "type": "quantitative", "title": "Exact share (%)", "format": ".2f"}, {"field": "units", "type": "quantitative", "title": "Rounded units", "format": ".0f"}]}, "config": config}
save("fruit_units.vl.json", unit)
water = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "description": "Horizontal cumulative waterfall of the change in nominal farmgate value across 29 reported fruit categories from 2020-21 to 2024-25. Five largest gains, two largest declines and the net of the other 22 categories reconcile to AUD 1486 million.",
         "width": "container", "height": 420, "background": "transparent", "data": {"url": "data/fruit_waterfall.json"},
         "encoding": {"y": {"field": "category", "type": "ordinal", "sort": [r["category"] for r in waterfall], "axis": {"title": None, "labelLimit": 110, "ticks": False}},
                      "tooltip": [{"field": "category", "title": "Contribution"}, {"field": "change", "type": "quantitative", "title": "Change (A$ million)", "format": "+,.1f"}, {"field": "members", "title": "Included categories"}]},
         "layer": [{"transform": [{"filter": "datum.next != null"}], "mark": {"type": "rule", "color": "#a7b6ae", "strokeDash": [3, 3]}, "encoding": {"x": {"field": "after", "type": "quantitative"}, "y2": {"field": "next"}}},
                   {"mark": {"type": "bar", "size": 25}, "encoding": {"x": {"field": "low", "type": "quantitative", "scale": {"zero": True, "domain": [0, 1800]}, "axis": {"title": ["Change in farmgate value", "(A$ million)"], "tickCount": 4}}, "x2": {"field": "high"}, "color": {"field": "kind", "type": "nominal", "scale": {"domain": ["Increase", "Decrease", "Net change"], "range": ["#398965", "#bc466d", "#7d354c"]}, "legend": {"title": None, "orient": "bottom", "direction": "horizontal"}}}},
                   {"mark": {"type": "text", "align": "left", "dx": 6, "fontSize": 12, "color": "#263b32"}, "encoding": {"x": {"field": "high", "type": "quantitative"}, "text": {"field": "change", "type": "quantitative", "format": "+,.0f"}}}], "config": config}
save("fruit_waterfall.vl.json", water)
palette = {"name": "fruitColor", "type": "ordinal", "domain": THEME["fruits"], "range": THEME["colors"]}
sankey = {"$schema": "https://vega.github.io/schema/vega/v5.json", "description": "Reported state production across ten selected fruits. d3-sankey calculates layout before deployment; Vega renders the diagram. Links are production relationships, not shipments. Unreported observations are not zero.",
          "width": 1000, "height": 600, "padding": 0, "autosize": {"type": "pad", "resize": True}, "background": "transparent",
          "signals": [{"name": "stateChoice", "value": "All states", "bind": {"input": "select", "name": "Highlight state: ", "options": ["All states", *states]}}],
          "data": [{"name": "nodes", "url": "data/fruit_sankey.json", "format": {"property": "nodes"}}, {"name": "links", "url": "data/fruit_sankey.json", "format": {"property": "links"}}],
          "scales": [palette, {"name": "x", "type": "linear", "domain": [0, 1000], "range": [{"signal": "width < 500 ? 40 : 65"}, {"signal": "width - 100"}]}, {"name": "y", "type": "linear", "domain": [0, 600], "range": [0, {"signal": "height"}]}],
          "marks": [
              {"type": "path", "name": "productionLinks", "from": {"data": "links"}, "encode": {"update": {
                  "path": {"signal": "'M'+scale('x',datum.sx)+','+scale('y',datum.sy)+'C'+((scale('x',datum.sx)+scale('x',datum.tx))/2)+','+scale('y',datum.sy)+' '+((scale('x',datum.sx)+scale('x',datum.tx))/2)+','+scale('y',datum.ty)+' '+scale('x',datum.tx)+','+scale('y',datum.ty)"},
                  "stroke": {"scale": "fruitColor", "field": "fruit"}, "strokeWidth": {"signal": "datum.width*height/600"}, "strokeOpacity": {"signal": "stateChoice === 'All states' || datum.state === stateChoice ? 0.55 : 0.08"}, "fill": {"value": None},
                  "tooltip": {"signal": "{'State':datum.state,'Fruit':datum.fruit,'Production':format(datum.tonnes,',.0f')+' tonnes'}"}}, "hover": {"strokeOpacity": {"value": 0.9}}}},
              {"type": "rect", "name": "productionNodes", "from": {"data": "nodes"}, "encode": {"update": {"x": {"scale": "x", "field": "x0"}, "x2": {"scale": "x", "field": "x1"}, "y": {"scale": "y", "field": "y0"}, "y2": {"scale": "y", "field": "y1"}, "fill": {"signal": "datum.kind === 'fruit' ? scale('fruitColor',datum.name) : '#587265'"}, "tooltip": {"signal": "{'Category':datum.name,'Reported production':format(datum.value,',.0f')+' tonnes'}"}}}},
              {"type": "text", "interactive": False, "from": {"data": "nodes"}, "encode": {"update": {"x": {"signal": "datum.kind === 'state' ? scale('x',datum.x0)-8 : scale('x',datum.x1)+8"}, "y": {"signal": "scale('y',(datum.y0+datum.y1)/2)"}, "text": {"field": "label"}, "align": {"signal": "datum.kind === 'state' ? 'right' : 'left'"}, "baseline": {"value": "middle"}, "font": {"value": THEME["font"]}, "fontSize": {"value": 12}, "fill": {"value": THEME["ink"]}}}}
          ]}
save("fruit_sankey.vg.json", sankey)
print(f"Units: {total:,} tonnes; waterfall: AUD {net} million; state observations: {len(observed)}")

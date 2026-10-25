"""Prepare ABS polygon winding for Vega's spherical geographic renderer."""

import csv
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
# PREPARATION ONLY: combine sourced regional geometry with 2024-25 production observations.
avocados = json.loads((DATA / "avocado_regions.geojson").read_text())
assert len(avocados["features"]) == 140
rows = list(csv.DictReader((DATA / "raw" / "abs_regional_horticulture.csv").open()))
banana_data = {}
for row in rows:
    if row["DATAITEM"] != "HortBananas_Prod" or not row["TIME_PERIOD"].startswith("2024"):
        continue
    if len(row["REGION"]) != 9 or not row["OBS_VALUE"]:
        continue
    banana_data[row["REGION"]] = float(row["OBS_VALUE"])
# Match by SA2 identifier, not by approximate name or geographic proximity.
banana_shapes = {}
for name in ["banana_regions.geojson", "banana_additional_regions.geojson"]:
    for feature in json.loads((DATA / name).read_text())["features"]:
        banana_shapes[feature["properties"]["sa2_code_2021"]] = feature
assert not set(banana_data) - set(banana_shapes), "Missing banana geometries"
bananas = [banana_shapes[code] for code in banana_data]
for feature in bananas:
    props = feature["properties"]
    props["production_t"] = banana_data[props["sa2_code_2021"]]
    props["fruit"] = "Bananas"
for feature in avocados["features"]:
    feature["properties"]["fruit"] = "Avocados"
# Put both fruits in one GeoJSON; the chart's selector filters features by fruit.
source = {"type": "FeatureCollection", "features": avocados["features"] + bananas}
for feature in source["features"]:
    geometry = feature["geometry"]
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    for polygon in polygons:
        for index, ring in enumerate(polygon):
            # This signed planar sum detects ring orientation; it is not a land-area estimate.
            area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:]))
            # D3 uses clockwise exterior rings and counterclockwise holes.
            if (index == 0 and area > 0) or (index > 0 and area < 0):
                ring.reverse()
    props = feature["properties"]
    if props["fruit"] == "Avocados":
        props["crop_land_share_pct"] = props["total_area_ha"] / props["area_albers_sqkm"]
# Permit only the small published rounding differences, not arbitrary mismatched totals.
assert abs(sum(f["properties"]["production_t"] for f in avocados["features"]) - 131385) <= 5
assert len(bananas) == 62
assert abs(sum(banana_data.values()) - 368701) <= 5
target = DATA / "fruit_regions_vega.geojson"
# Compact geometry reduces the browser download; no coordinates are invented here.
target.write_text(json.dumps(source, separators=(",", ":")) + "\n")
print(f"Prepared {len(source['features'])} regions; {target.stat().st_size:,} bytes")

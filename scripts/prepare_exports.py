"""Extract reported UN Comtrade quantities and attach Natural Earth locations."""

from collections import defaultdict
import csv
import json
from pathlib import Path
from urllib.parse import urlparse
import zipfile

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
CATEGORIES = [("grapes", "Table grapes", "080610"), ("apples", "Apples", "080810"),
              ("oranges", "Oranges", "080510"), ("mandarins", "Mandarins and related citrus", "080520"),
              ("strawberries", "Strawberries", "081010")]
NAMES = {"KOR": "South Korea", "HKG": "Hong Kong", "TMP": "Timor-Leste", "NRU": "Nauru"}
rows = []
# PREPARATION ONLY: parse saved source tables, not a live API request when the page opens.
# HS codes define the trade categories; these are not all Australian fruit exports.
world_totals = {}
for slug, category, hs_code in CATEGORIES:
    document = html.parse(str(RAW / f"exports_2025_{slug}.html"))
    table = document.xpath("//table[@id='dataCatalogMetadata']")
    assert len(table) == 1, "Missing source table"
    for row in table[0].xpath(".//tr")[1:]:
        cells = row.xpath("./td")
        values = [cell.text_content().strip() for cell in cells]
        assert values[0] == "Australia" and values[1] == "Export"
        assert values[2] == hs_code and values[4] == "2025" and values[8] == "Kg"
        assert values[7], "Quantity missing; do not infer it from value"
        link = cells[5].xpath(".//a/@href")[0]
        parts = urlparse(link).path.split("/")
        code = parts[parts.index("partner") + 1]
        # Source quantities are kilograms. Dividing by 1,000 converts them to tonnes.
        tonnes = float(values[7].replace(",", "")) / 1000
        if values[5] == "World":
            world_totals[category] = tonnes
            continue
        # This saved source has one incorrect partner link; validate its label before correcting it.
        if code == "WLD":
            assert values[5] == "Cote d'Ivoire", "Unexpected country link requires review"
            code = "CIV"
        rows.append({"fruit": category, "hs_code": hs_code, "year": 2025,
                     "destination_code": code, "destination": NAMES.get(code, values[5]),
                     "tonnes": tonnes, "trade_value_usd": float(values[6].replace(",", "")) * 1000})
    partner_sum = sum(r["tonnes"] for r in rows if r["fruit"] == category)
    assert abs(partner_sum - world_totals[category]) < 0.5, f"{category}: partner sum {partner_sum}, world {world_totals[category]}"
    print(category, f"world: {world_totals[category]:,.3f} tonnes; partner sum: {partner_sum:,.3f}")

with (DATA / "fruit_export_destinations.csv").open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

# Prefer capital-city locations, then population, for representative country points, not ports.
places = json.loads((RAW / "ne_110m_populated_places.geojson").read_text())["features"]
locations = {}
for feature in sorted(places, key=lambda f: (f["properties"].get("ADM0CAP", 0), f["properties"].get("POP_MAX", 0)), reverse=True):
    locations.setdefault(feature["properties"]["ADM0_A3"], feature["geometry"]["coordinates"])
origin = locations["AUS"]
flows = []
summaries = []
for category in ["All five categories", *[c[1] for c in CATEGORIES]]:
    # Aggregate destinations across fruits only for the combined selection.
    chosen = rows if category == "All five categories" else [r for r in rows if r["fruit"] == category]
    totals = defaultdict(float)
    names = {}
    for row in chosen:
        totals[row["destination_code"]] += row["tonnes"]
        names[row["destination_code"]] = row["destination"]
    # Retain the published world denominator, including partners not drawn on the map.
    total = sum(world_totals.values()) if category == "All five categories" else world_totals[category]
    # Non-geographic partner codes cannot be drawn as invented destinations.
    eligible = [(code, tonnes) for code, tonnes in totals.items() if code not in {"BUN", "OAS"}]
    leaders = sorted(eligible, key=lambda pair: pair[1], reverse=True)[:8]
    assert all(code in locations for code, _ in leaders), "A top destination has no sourced location"
    # Coverage explains what fraction of the full selection the eight displayed links represent.
    coverage = sum(tonnes for _, tonnes in leaders) / total * 100
    summaries.append({"fruit": category, "total_tonnes": total, "coverage_pct": coverage,
                      "destination_count": len(eligible), "shown_count": len(leaders)})
    for rank, (code, tonnes) in enumerate(leaders, start=1):
        longitude, latitude = locations[code]
        # A LineString connects representative endpoints; it is not a recorded shipping route.
        flows.append({"fruit": category, "destination": names[code], "destination_code": code,
                      "year": 2025, "tonnes": tonnes, "share_pct": tonnes / total * 100,
                      "rank": rank, "longitude": longitude, "latitude": latitude,
                      "geometry": {"type": "LineString", "coordinates": [origin, locations[code]]}})
    print(category, f"top eight coverage: {coverage:.1f}%")

output = {"origin": [{"name": "Australia", "longitude": origin[0], "latitude": origin[1]}],
          "flows": flows, "summaries": summaries}
(DATA / "fruit_exports.json").write_text(json.dumps(output, indent=2) + "\n")

# Keep the course-supplied Natural Earth basemap, stripping unused attributes.
archive = zipfile.ZipFile(ROOT.parent / "DV2 resources" / "Week 8 Studio Source Code.zip")
world = json.loads(archive.read("2_symbol_map/js/ne_110m_admin_0_countries.topojson"))
for geometry in world["objects"]["ne_110m_admin_0_countries"]["geometries"]:
    props = geometry["properties"]
    geometry["properties"] = {"name": props["NAME"], "code": props["ADM0_A3"]}
(DATA / "world_countries.topojson").write_text(json.dumps(world, separators=(",", ":")) + "\n")

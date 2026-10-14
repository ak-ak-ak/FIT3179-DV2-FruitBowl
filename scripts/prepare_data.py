"""Extract chart data from official sources without changing their measurements."""

import csv
import json
import re
from pathlib import Path

import openpyxl
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
FOCUS = {"Apples", "Avocados", "Bananas", "Blueberries", "Mandarins", "Mangoes",
         "Oranges", "Pears", "Strawberries", "Table grapes"}


def save(name, rows):
    assert rows, name
    with (DATA / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{name}: {len(rows)} rows")


workbook = openpyxl.load_workbook(RAW / "abs_horticulture_2024_25.xlsx",
                                read_only=True, data_only=True)
sheet = list(workbook["Table 2"].iter_rows(max_col=8, values_only=True))
years = sheet[4][3:8]
assert years == ("2020-21", "2021-22", "2022-23", "2023-24", "2024-25")
records = {}
for row in sheet[5:]:
    code, region, item = row[:3]
    if not isinstance(code, (int, float)) or not isinstance(item, str):
        continue
    fruit, metric = item.rsplit(" - ", 1)
    assert metric in {"Production (t)", "Farm gate value ($m)"}, item
    for year, value in zip(years, row[3:8]):
        key = (fruit, str(int(code)), region, year)
        record = records.setdefault(key, {"fruit": fruit, "region_code": str(int(code)),
                                         "region": region, "year": year})
        field = "production_tonnes" if metric == "Production (t)" else "farmgate_value_aud_million"
        record[field] = value if isinstance(value, (int, float)) else ""
        record[field + "_status"] = "published" if isinstance(value, (int, float)) else str(value)

national = [r for r in records.values() if r["region"] == "Australia"]
assert len(national) == 29 * 5
save("fruit_national.csv", national)
save("fruit_history.csv", [r for r in national if r["fruit"] in FOCUS])
state = []
for record in records.values():
    if record["region"] == "Australia" or record["year"] != "2024-25" or record["fruit"] not in FOCUS:
        continue
    row = dict(record)
    total = records[(row["fruit"], "0", "Australia", row["year"])]["production_tonnes"]
    row["national_production_share_pct"] = row["production_tonnes"] / total * 100 if isinstance(row["production_tonnes"], (int, float)) else ""
    state.append(row)
save("fruit_state.csv", state)

regional = json.loads((RAW / "abs_avocado_producing_sa2_2024_25.json").read_text())
assert not regional.get("exceededTransferLimit"), "Incomplete geographic download"
regions = []
for feature in regional["features"]:
    row = dict(feature["attributes"])
    assert row["area_albers_sqkm"] > 0
    row["crop_land_share_pct"] = row["total_area_ha"] / (row["area_albers_sqkm"] * 100) * 100
    row["year"] = "2024-25"
    row["fruit"] = "Avocados"
    regions.append(row)
assert len({r["sa2_code_2021"] for r in regions}) == len(regions)
assert abs(sum(r["production_t"] for r in regions) - 131385) <= 5
save("avocado_sa2.csv", regions)

# Page 3 is a numerical table, not values estimated from chart pixels.
page = PdfReader(RAW / "avocados_australia_2024_25.pdf").pages[2].extract_text(extraction_mode="layout")
history = []
pattern = re.compile(r"(20\d{2}/\d{2})\s+([\d,]+)\s+([\d,]+)\s+\$\s*([\d,.]+)\s+\$\s*([\d,.]+)\s+\$\s*([\d,.]+)\s+\$\s*([\d,.]+)")
for match in pattern.finditer(page):
    year, volume, trays, gross, farmgate, retail, export = match.groups()
    history.append({"year": year, "production_tonnes": int(volume.replace(",", "")),
                    "gross_value_aud_million": float(gross.replace(",", "")),
                    "farmgate_value_aud_million": float(farmgate.replace(",", "")),
                    "consumer_market_value_aud_million": float(retail.replace(",", "")),
                    "export_value_aud_million": float(export.replace(",", ""))})
assert len(history) == 11
assert history[-1]["production_tonnes"] == 131385
save("avocado_history.csv", history)

# Published labels on page 14, visually checked against the source PDF.
# Other Countries is deliberately not assigned a geographic destination.
shares = [("Hong Kong", "HKG", 42.06), ("Singapore", "SGP", 23.60),
          ("Malaysia", "MYS", 18.54), ("Japan", "JPN", 4.34),
          ("Other Countries", "", 11.46)]
assert abs(sum(s[2] for s in shares) - 100) < 0.001
save("avocado_export_shares.csv", [{"destination": country, "destination_code": code,
                                     "year": "2024-25", "export_share_pct": share,
                                     "total_exports_tonnes": 14235,
                                     "source_page": 14} for country, code, share in shares])

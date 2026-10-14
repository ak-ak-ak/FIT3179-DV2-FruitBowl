# Data sources

## ABS national and state fruit data

Source: Australian Agriculture: Horticulture 2024-25, released 30 June 2026.
https://www.abs.gov.au/statistics/industry/agriculture/australian-agriculture-horticulture/2024-25

Original file: `raw/abs_horticulture_2024_25.xlsx`, Table 2.
Outputs: `fruit_national.csv`, `fruit_history.csv`, `fruit_state.csv`.
Five financial years, 2020-21 to 2024-25. Production is tonnes; farmgate value is current AUD million, not retail value. ABS reproduces these estimates from Hort Innovation. Use revised values from this release consistently.

National data covers the 29 fruit categories in Table 2, not necessarily all categories included in the publication's headline fruit total. A treemap must say "fruit categories reported in Table 2" rather than claim that its sum is the entire Australian fruit sector. Detailed comparisons use ten familiar categories: apples, avocados, bananas, blueberries, mandarins, mangoes, oranges, pears, strawberries and table grapes. Combined categories are not added to their components.

Published numeric values, including zero, are preserved. Unavailable/nonnumeric entries are blank with a separate status field; absent fruit-state rows are not invented as zero. National state shares are derived from published tonnes and each fruit's published national total. Dollar series are nominal, without inflation adjustment.

The selected-crops workbook is retained as a reference, not mixed into the national history: its local values have different precision, and geographic experimental estimates should be identified separately.

## ABS regional avocados

Official public feature service:
https://geo.abs.gov.au/arcgis/rest/services/Hosted/ABS_SA2_HORTICULTURE_AVOCADOS_2425/FeatureServer
Metadata: https://statmaps.abs.gov.au/portal/home/item.html?id=ab6fe98021c54106b4cc5b760fa6c4d8

Original: `raw/abs_avocado_producing_sa2_2024_25.json`.
Output: `avocado_sa2.csv`.
Query: production_t IS NOT NULL, no geometry; response must not have exceededTransferLimit.
140 published regions, using SA2 2021 codes and official Albers area in square kilometres. The sum of published regional production is 131,387 tonnes versus the national 131,385 tonnes, a 2-tonne aggregation/rounding difference retained without correction.

Crop-land share = crop hectares / (SA2 square kilometres * 100) * 100.
This is the share of the entire geographic region occupied by avocado crop, not yield or share of agricultural land. A simplified formula is hectares / square kilometres, numerically expressed as percent. Areas with no published production are not in this extract; missing geographic joins must not be displayed as confirmed zero production. Experimental estimates must be identified in the map source note.

Geometry and representative points still need downloading and simplification before maps are built. Do not calculate the denominator from simplified geometry.

## Avocados Australia

Facts at a Glance 2024/25, data current at August 2025.
https://avocado.org.au/wp-content/uploads/2025/09/2024-25_AAL-Facts-at-a-glance.pdf

Original: `raw/avocados_australia_2024_25.pdf`.
Outputs: `avocado_history.csv` (page 3 numerical table); `avocado_export_shares.csv` (page 14 published labels, visually checked).

The historical table runs 2014/15 to 2024/25. Use this report consistently for an eleven-year avocado trajectory; do not splice its rounded farmgate values into ABS's more precise five-year series. Gross production value, farmgate value and consumer market value have different definitions. Sources underlying the report include Infocado, Global Trade Atlas and industry analysis. It is Hort Innovation funded and overlaps with ABS input data; the export series is a distinct trade measure, not an independent validation of production.

Export destination shares are Hong Kong 42.06%, Singapore 23.60%, Malaysia 18.54%, Japan 4.34%, other countries 11.46%. Total exports: 14,235 tonnes. For a flow map use published percentages as line width and tooltip values. Do not present percentage-derived tonnages as exact source measurements. The four named markets cover 88.54%; retain the remainder in a note without drawing an invented destination. Paths are schematic, not shipping routes.

## Sources not yet adopted

Hort Innovation 2024/25 fruit handbook downloads failed via available official hosts. The trade PDF can be read online, but its national and regional snapshot tables contain conflicting crop totals. These snapshot figures have not been added to chart data. The country-specific avocado report supplies a usable alternative for tonight's third map.

Fresh supply per person and general fruit supply pathways remain unverified and are deferred beyond the initial eight charts.

## Reproduction and deployment

Run `scripts/prepare_data.py` using Python with openpyxl and pypdf installed. It extracts source tables, validates key totals and writes small CSVs. Raw reports/workbooks are development sources, not browser chart requests. Charts must load only the prepared CSVs and simplified geometry. Downloaded source files do not need to be publicly redistributed; check permission before committing the report itself. The source links above provide provenance.

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

Geometry is in `avocado_regions.geojson`, downloaded from the same official service with production_t IS NOT NULL, outSR=4326, geometryPrecision=3 and maxAllowableOffset=0.015 degrees. All 140 codes match the tabular extract. `scripts/prepare_maps.py` creates `fruit_regions_vega.geojson`, combining bananas and avocados with clockwise outer rings for Vega's spherical renderer. This orientation conversion preserves the polygons; it does not alter official measurements. Map symbols use Vega's geographic centroid of each simplified region, not farm coordinates. The earlier avocado-only choropleth has been replaced with a state-level fruit map.

## State fruit choropleth

Output: `fruit_state_density.csv`, from ABS Table 2 and `raw/state_land_area.csv`.
Land area source: https://www.ga.gov.au/scientific-topics/national-location-information/dimensions/area-of-australia-states-and-territories
Geoscience Australia published total land areas, including islands, in square kilometres. These geographic denominators are separate from 2024-25 production observations; the source page was last updated 27 June 2014. Do not describe these denominators as 2024-25 measured land areas.

Density = reported production tonnes / entire state land area. It is not orchard yield, cropping intensity or productivity. The default aggregates available Table 2 categories within each state and records how many categories were included. Missing fruit-state rows are absent, not zero. The ACT has no reported fruit production rows and stays grey. The selector offers ten familiar fruit categories in addition to the aggregate. Each selection recalculates the colour domain; compare states within a selection, not colour shades across different selections.

## Regional bananas

Latest observations: ABS Data API, dataflow AG_HORTICULTURE version 1.0.1.
https://data.api.abs.gov.au/rest/data/ABS,AG_HORTICULTURE,1.0.1/all?format=csvfilewithlabels
Original: `raw/abs_regional_horticulture.csv`. Select DATAITEM=HortBananas_Prod, TIME_PERIOD=2024-07-01/P1Y and nine-digit SA2 codes. These represent the financial year 2024-25, not calendar year 2024.

62 published producing regions total 368,702 tonnes, versus the national 368,701 tonnes. Preserve the 1-tonne rounding difference. Boundaries use the SA2 2021 shapes in the ABS banana 2023-24 feature service; no 2023-24 production values are used. Six additional shapes were retrieved for current regions absent from the older producing-region subset. Every latest production code has a matching shape. Original shapes: `banana_regions.geojson` and `banana_additional_regions.geojson`; combined output: `fruit_regions_vega.geojson`.

https://geo.abs.gov.au/arcgis/rest/services/Hosted/ABS_SA2_HORTICULTURE_BANANAS_2324/FeatureServer

Both regional fruit selections use a fixed size domain of 0-125,000 tonnes, so circle areas remain comparable when switching fruit. Only bananas and avocados are included in this regional case study; it does not imply that detailed estimates exist for every fruit.

## Avocados Australia

Facts at a Glance 2024/25, data current at August 2025.
https://avocado.org.au/wp-content/uploads/2025/09/2024-25_AAL-Facts-at-a-glance.pdf

Original: `raw/avocados_australia_2024_25.pdf`.
Outputs: `avocado_history.csv` (page 3 numerical table); `avocado_export_shares.csv` (page 14 published labels, visually checked).

The historical table runs 2014/15 to 2024/25. Use this report consistently for an eleven-year avocado trajectory; do not splice its rounded farmgate values into ABS's more precise five-year series. Gross production value, farmgate value and consumer market value have different definitions. Sources underlying the report include Infocado, Global Trade Atlas and industry analysis. It is Hort Innovation funded and overlaps with ABS input data; the export series is a distinct trade measure, not an independent validation of production.

Export destination shares are Hong Kong 42.06%, Singapore 23.60%, Malaysia 18.54%, Japan 4.34%, other countries 11.46%. Total exports: 14,235 tonnes. Retained as reference data, not selected for the main export map: the project covers fruit production broadly. Do not present percentage-derived tonnages as exact source measurements. The four named markets cover 88.54%.

## Sources not yet adopted

Hort Innovation 2024/25 fruit handbook downloads failed via available official hosts. The trade PDF can be read online, but its national and regional snapshot tables contain conflicting crop totals. These snapshot figures have not been added to chart data. Broader fruit destination data must be verified before building the third map; the avocado-only export map is no longer in the main lineup.

Fresh supply per person and general fruit supply pathways remain unverified and are deferred beyond the initial eight charts.

## Reproduction and deployment

Run `scripts/prepare_data.py` using Python with openpyxl and pypdf installed. It extracts source tables, validates key totals and writes small CSVs. Raw reports/workbooks are development sources, not browser chart requests. Charts must load only the prepared CSVs and simplified geometry. Downloaded source files do not need to be publicly redistributed; check permission before committing the report itself. The source links above provide provenance.

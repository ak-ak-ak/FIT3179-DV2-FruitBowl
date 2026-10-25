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

## Fruit export flow map

Source: Australian-reported UN Comtrade merchandise export quantities for calendar 2025, displayed by World Bank WITS. The financial-year production data is a different reference period; no export-to-production ratios are calculated across these datasets.

- Fresh grapes, HS 080610: https://wits.worldbank.org/trade/comtrade/en/country/AUS/year/2025/tradeflow/Exports/partner/ALL/product/080610
- Fresh apples, HS 080810: https://wits.worldbank.org/trade/comtrade/en/country/AUS/year/2025/tradeflow/Exports/partner/ALL/product/080810
- Oranges, fresh or dried, HS 080510: https://wits.worldbank.org/trade/comtrade/en/country/AUS/year/2025/tradeflow/Exports/partner/ALL/product/080510
- Mandarins and related citrus, fresh or dried, HS 080520: https://wits.worldbank.org/trade/comtrade/en/country/AUS/year/2025/tradeflow/Exports/partner/ALL/product/080520
- Fresh strawberries, HS 081010: https://wits.worldbank.org/trade/comtrade/en/country/AUS/year/2025/tradeflow/Exports/partner/ALL/product/081010

Original source pages: `raw/exports_2025_*.html`. `scripts/prepare_exports.py` parses their HTML tables with lxml, checks reporter, flow, year, category and quantity unit, and converts kilograms to tonnes by dividing by 1,000. It retains all bilateral records in `fruit_export_destinations.csv`. The World row is identified by its displayed label, not solely its link: WITS incorrectly links two tiny Cote d'Ivoire entries to WLD; these are joined to CIV without changing their reported quantities.

World totals are respectively 141,134; 1,728.810; 199,492; 120,010; and 3,039 tonnes. Their combined total is 465,403.810 tonnes. Bilateral sums differ from reported world totals by less than 0.5 tonnes per category, reflecting source rounding; these differences are retained, not forced to balance. Shares use the reported World total. Trade values are USD, retained only in the source CSV and not compared with AUD farmgate values.

`fruit_exports.json` contains the eight largest geographic destinations by tonnes for each selection, plus coverage and totals. The aggregate includes only these five non-overlapping fruit categories, not all fruit or all fresh fruit. Coverage is 75.5% for the aggregate and is calculated separately for individual selections. Non-geographic partner codes BUN and OAS are not drawn as invented destinations. They remain in the extracted source table and in the source World denominator. No other destination is reassigned to a fictitious point. Figures describe Australia's reported exports and may include re-exports, not traced journeys of the local crop.

Natural Earth 1:110m populated-place metadata provides representative national locations, prioritising capital cities and using Hong Kong's populated-place coordinate. The Australian origin is a representative national point, not a port. Geographic paths are great-circle connections rendered in a Pacific-centred Equal Earth projection, not actual shipping routes. The top three destinations are labelled; all eight are available through tooltips and the accompanying table. Width encodes tonnes linearly within each selection, with a zero width baseline and a rescaled domain; do not compare line widths across selections.

Location source: https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_populated_places.geojson
World basemap: the course-supplied Natural Earth 1:110m countries TopoJSON in the Week 8 source archive. `world_countries.topojson` keeps the original shapes but strips unused properties. Natural Earth data is public domain.

## Deferred handbook data

Hort Innovation 2024/25 fruit handbook downloads failed via available official hosts. The trade PDF can be read online, but its national and regional snapshot tables contain conflicting crop totals. These snapshot figures have not been added to chart data. The main export map instead uses verified UN Comtrade destination data across five fruit categories; the avocado-only export map is no longer in the main lineup.

Fresh supply per person and general fruit supply pathways remain unverified and are deferred beyond the initial eight charts.

## Reproduction and deployment

The three change charts all use `fruit_history.csv`: the same ten fruit categories and the same revised ABS Table 2 values for 2020-21 to 2024-25. No historical values are spliced from the separate Avocados Australia report. `scripts/build_change_specs.py` writes the three readable JSON specs with consistent fruit colours.

The slope chart uses production tonnes at the first and last years. Its axis begins at zero and displays thousand tonnes; tooltips retain tonnes. The displayed endpoint changes are avocado +68.3%, mandarins +44.8% and pears -41.9%, rounded in narrative text. The bump chart computes rank separately for each financial year on nominal farmgate value within this fixed ten-fruit set. Equal values receive equal rank; no alphabetical tiebreak is invented. The connected scatterplot filters to one fruit and connects five annual observations in chronological order, not in production order. Both axes adjust to that fruit and need not begin at zero; this is explicitly disclosed. All dollar values are nominal AUD, not consumer prices, and the chart is not causal evidence.

The treemap uses `fruit_value_tree.json`, derived from 2024-25 national Table 2 values. Its 29 fruit categories total AUD 7,327.8 million, slightly below the headline fruit total of AUD 7,336.3 million; it does not claim to cover unreported categories. The hierarchy's root is a structural node with zero value, not a data observation. Rectangle areas encode farmgate value, and tooltip shares use the sum of the shown categories. Colour groups are editorial groupings of related fruits, not additional measured totals.

The heatmap uses `fruit_state_matrix.csv`, a complete display grid of ten selected fruits by eight states/territories. Its 80 cells include 56 reported observations and 24 explicit not-reported cells. The latter have blank numeric fields and never become numeric zero. Each share divides the published state tonnes by that fruit's national tonnes; rounded cells need not sum to exactly 100%. Values below 1% but above zero are displayed as <1%, while tooltips retain two decimal places. Colour uses the same 0-100% domain for every fruit. No independent state survey or new measurement is implied.

Run `scripts/prepare_data.py` using Python with openpyxl and pypdf installed. It extracts source tables, validates key totals and writes small CSVs. Raw reports/workbooks are development sources, not browser chart requests. Charts must load only the prepared CSVs and simplified geometry. Downloaded source files do not need to be publicly redistributed; check permission before committing the report itself. The source links above provide provenance.
# Final Three Derived Charts

## Critique Revisions

The live lineup replaces the flat treemap with `fruit_value.vl.json`, a ranked lollipop comparison of the ten highest farmgate values from the existing 29-category extract. The headline total still uses all 29 categories. The unit's official idiom clarification explicitly classifies lollipop charts as advanced. The old treemap spec is retained but no longer embedded and is not counted.

The eleven embedded charts include ten advanced idioms under the supplied unit clarification: waffle, lollipop, heatmap, choropleth, proportional symbol map, Sankey, slope, bump, waterfall and export flow map. Waterfall is not in the basic list; all map idioms are advanced for DV2. The connected scatterplot is not needed to meet the eight-advanced threshold. Classification alone does not demonstrate appropriate or effective use.

Persistent density and export annotations are computed inside the chart specifications from the same filtered data as their marks. Companion text includes full denominators and updates with selections. Bump ranks use competition ranking within the fixed ten-fruit set; its endpoint labels and selected-fruit summary do not imply dollar differences. Annotation text uses dark ink rather than low-contrast fruit colours.

`scripts/refine_charts.py` applies the final presentation revisions after the original builders and theme script: brighter categorical colours, a label-free heatmap with source-based emphasis, initial regional close-ups, axis spacing and destination-specific route colours. No source production or trade measurements are changed. Rebuild order ends with `python3 scripts/refine_charts.py`.

The scatterplot's persistent annotation calculates financial-year endpoint percentage changes from the same prepared history CSV. Regional shortlists use published regional tonnes. Export route colours match their destination table keys and remain distinct among the eight displayed routes for every selection.

All three derive from the existing ABS Table 2 extracts, not additional invented observations.

- Unit chart: sums 29 national fruit categories in 2024-25 (2,834,995 tonnes). Five largest categories plus the remainder; floor exact percentage shares, then distribute remaining cells to the largest fractional remainders. Exactly 100 equal-area cells. Tooltips retain the source tonnes and percentage shares.
- State-fruit Sankey: 56 positive, reported state-fruit observations from the fixed ten-fruit matrix, totalling 2,089,200 tonnes. Missing values remain missing, zero-width links are omitted. ACT has no positive reported observations in this comparison and is not drawn. Node totals reconcile to their links. d3-sankey 0.12.3 prepares coordinates only; Vega renders every mark.
- Value waterfall: nominal farmgate value changes for all 29 categories, 2020-21 to 2024-25. Five largest gains, two largest declines and the net of the other 22 categories reconcile exactly to AUD 1,486.0 million. Positive contributions add to the running position; negative contributions subtract. The final bar is the total, not another contribution.

Preparation: `npm ci`, then `python3 scripts/build_final_charts.py`. After rebuilding any specs, run `python3 scripts/apply_chart_theme.py`. Shared categorical colours and typography are defined in `data/chart_theme.json`.

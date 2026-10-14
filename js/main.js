// Loads each Vega or Vega-Lite spec into its matching chart container.
// Add one line per chart: ["div id", "path to spec"].
const charts = [
  ["#fruit_treemap", "specs/fruit_treemap.vg.json"],
  ["#fruit_heatmap", "specs/fruit_heatmap.vl.json"],
  ["#fruit_choropleth", "specs/fruit_choropleth.vl.json"],
  ["#fruit_symbols", "specs/fruit_symbols.vl.json"],
  ["#fruit_slope", "specs/fruit_slope.vl.json"],
  ["#fruit_bump", "specs/fruit_bump.vl.json"],
  ["#fruit_trajectory", "specs/fruit_trajectory.vl.json"],
  ["#fruit_exports", "specs/fruit_exports.vg.json"],
];

const embedOptions = { actions: false, renderer: "svg" };

function chartHeight(id, width) {
  if (id === "#fruit_treemap") return width < 600 ? 460 : 430;
  if (id === "#fruit_heatmap") return 360;
  if (id === "#fruit_slope") return 400;
  if (id === "#fruit_bump") return 420;
  if (id === "#fruit_trajectory") return width < 600 ? 340 : 380;
  if (id === "#fruit_exports") return width < 600 ? 260 : 460;
  return Math.min(440, Math.max(220, width * 0.65));
}

charts.forEach(async ([el, specPath]) => {
  const container = document.querySelector(el);
  try {
    const response = await fetch(specPath);
    if (!response.ok) throw new Error(`Chart request failed: ${response.status}`);
    const spec = await response.json();
    const isVega = spec.$schema.includes("/vega/v");
    spec.height = chartHeight(el, container.clientWidth);
    if (isVega) spec.width = container.clientWidth;
    const { view } = await vegaEmbed(el, spec, embedOptions);
    if (el === "#fruit_exports") {
      const exportResponse = await fetch("data/fruit_exports.json");
      if (!exportResponse.ok) throw new Error("Export summary could not load");
      const exportData = await exportResponse.json();
      const number = new Intl.NumberFormat("en-AU", { maximumFractionDigits: 1 });
      const updateExportSummary = choice => {
        const summary = exportData.summaries.find(row => row.fruit === choice);
        document.querySelector("#export_coverage").textContent = `The eight destinations shown account for ${number.format(summary.coverage_pct)}% of ${number.format(summary.total_tonnes)} tonnes exported in this selection.`;
        const rows = exportData.flows.filter(row => row.fruit === choice).sort((a, b) => a.rank - b.rank);
        const body = document.querySelector("#export_destinations");
        body.replaceChildren(...rows.map(row => {
          const tr = document.createElement("tr");
          [row.destination, number.format(row.tonnes), `${number.format(row.share_pct)}%`].forEach(value => {
            const td = document.createElement("td");
            td.textContent = value;
            tr.append(td);
          });
          return tr;
        }));
      };
      updateExportSummary("All five categories");
      view.addSignalListener("fruitChoice", (_, choice) => updateExportSummary(choice));
    }
    let previousWidth = container.clientWidth;
    const observer = new ResizeObserver(() => {
      const width = container.clientWidth;
      if (width === previousWidth) return;
      previousWidth = width;
      if (isVega) view.width(width);
      view.height(chartHeight(el, width)).resize().runAsync();
    });
    observer.observe(container);
  } catch (err) {
    console.error(specPath, err);
    container.textContent = "This chart could not load. Please refresh the page.";
  }
});

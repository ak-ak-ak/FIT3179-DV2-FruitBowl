// Loads each Vega-Lite spec from /specs into its matching <div id="...">.
// Add one line per chart: ["div id", "path to spec"].
const charts = [
  ["#fruit_choropleth", "specs/fruit_choropleth.vl.json"],
  ["#fruit_symbols", "specs/fruit_symbols.vl.json"],
];

const embedOptions = { actions: false, renderer: "svg" };

charts.forEach(async ([el, specPath]) => {
  const container = document.querySelector(el);
  try {
    const response = await fetch(specPath);
    if (!response.ok) throw new Error(`Chart request failed: ${response.status}`);
    const spec = await response.json();
    spec.height = Math.min(440, Math.max(220, container.clientWidth * 0.65));
    const { view } = await vegaEmbed(el, spec, embedOptions);
    let previousWidth = container.clientWidth;
    const observer = new ResizeObserver(() => {
      const width = container.clientWidth;
      if (width === previousWidth) return;
      previousWidth = width;
      view.height(Math.min(440, Math.max(220, width * 0.65))).resize().runAsync();
    });
    observer.observe(container);
  } catch (err) {
    console.error(specPath, err);
    container.textContent = "This chart could not load. Please refresh the page.";
  }
});

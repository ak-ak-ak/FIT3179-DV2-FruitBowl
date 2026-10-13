// Loads each Vega-Lite spec from /specs into its matching <div id="...">.
// Add one line per chart: ["div id", "path to spec"].
const charts = [
  ["#map_test", "specs/map_test.vl.json"],
];

const embedOptions = { actions: false, renderer: "svg" };

charts.forEach(([el, spec]) => {
  vegaEmbed(el, spec, embedOptions).catch(err => console.error(spec, err));
});

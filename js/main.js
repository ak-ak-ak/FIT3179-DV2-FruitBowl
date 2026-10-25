// Loads each Vega or Vega-Lite spec into its matching chart container.
// Add one line per chart: ["div id", "path to spec"].
// INTERVIEW: this file embeds charts; marks, channels and selectors are declared in specs/.
// A leading # is a CSS selector: #fruit_units finds the HTML element id="fruit_units".
const charts = [
  ["#fruit_units", "specs/fruit_units.vl.json"],
  ["#fruit_value", "specs/fruit_value.vl.json"],
  ["#fruit_heatmap", "specs/fruit_heatmap.vl.json"],
  ["#fruit_choropleth", "specs/fruit_choropleth.vl.json"],
  ["#fruit_symbols", "specs/fruit_symbols.vl.json"],
  ["#fruit_sankey", "specs/fruit_sankey.vg.json"],
  ["#fruit_slope", "specs/fruit_slope.vl.json"],
  ["#fruit_bump", "specs/fruit_bump.vl.json"],
  ["#fruit_trajectory", "specs/fruit_trajectory.vl.json"],
  ["#fruit_waterfall", "specs/fruit_waterfall.vl.json"],
  ["#fruit_exports", "specs/fruit_exports.vg.json"],
];

// Hide Vega's export/editor menu and draw vector SVG marks rather than a canvas image.
const embedOptions = { actions: false, renderer: "svg" };

function chartHeight(id, width) {
  // Some chart heights change on mobile; maps without their own rule use the fallback below.
  if (id === "#fruit_units") return Math.min(300, width);
  if (id === "#fruit_value") return 320;
  if (id === "#fruit_symbols") return width < 600 ? 350 : 360;
  if (id === "#fruit_sankey") return width < 600 ? 620 : 660;
  if (id === "#fruit_choropleth") return width < 600 ? 300 : 390;
  if (id === "#fruit_waterfall") return 350;
  if (id === "#fruit_heatmap") return 310;
  if (id === "#fruit_slope") return 400;
  if (id === "#fruit_bump") return 350;
  if (id === "#fruit_trajectory") return width < 600 ? 340 : 380;
  if (id === "#fruit_exports") return width < 600 ? 260 : Math.min(380, width * 0.48 + 30);
  // Follow the container's proportions, with height limited to 220-440 pixels.
  return Math.min(440, Math.max(220, width * 0.65));
}

charts.forEach(async ([el, specPath]) => {
  // Charts load independently. async/await waits for requests without blocking the page.
  const container = document.querySelector(el);
  container.setAttribute("aria-busy", "true");
  container.textContent = "Loading chart…";
  try {
    // fetch requests the spec; .json() parses its text into a JavaScript object.
    const response = await fetch(specPath);
    if (!response.ok) throw new Error(`Chart request failed: ${response.status}`);
    const spec = await response.json();
    // The schema URL distinguishes plain Vega from the higher-level Vega-Lite format.
    const isVega = spec.$schema.includes("/vega/v");
    spec.height = chartHeight(el, container.clientWidth);
    if (isVega) spec.width = container.clientWidth;
    // Measure chart labels after the intended self-hosted fonts are available.
    await document.fonts.ready;
    // Insert the chart into its container; view is the handle used to update it later.
    const { view } = await vegaEmbed(el, spec, embedOptions);
    container.setAttribute("aria-busy", "false");
    const caption = container.closest("figure").querySelector("figcaption");
    if (caption) {
      caption.id = `${container.id}_description`;
      container.setAttribute("aria-describedby", caption.id);
    }
    // Retain native select keyboard behaviour while positioning the decorative chevron.
    container.querySelectorAll("select").forEach(select => {
      const shell = document.createElement("span");
      shell.className = "select-shell";
      select.before(shell);
      shell.append(select);
    });
    if (el === "#fruit_choropleth") {
      const densityResponse = await fetch("data/fruit_state_density.csv");
      if (!densityResponse.ok) throw new Error("Production density summary could not load");
      const densities = vega.read(await densityResponse.text(), {type:"csv", parse:"auto"});
      const updateDensity = fruit => {
        const rows = densities.filter(r => r.fruit === fruit && Number.isFinite(r.tonnes_per_km2));
        const maximum = Math.max(...rows.map(r => r.tonnes_per_km2));
        const leaders = rows.filter(r => r.tonnes_per_km2 === maximum);
        document.querySelector("#density_insight").textContent = leaders.length
          ? `${fruit}: ${leaders.map(r => r.region).join(" and ")} ${leaders.length === 1 ? "has" : "have"} the highest reported density, ${maximum.toFixed(3)} tonnes per km² of total state land. This is not orchard yield.`
          : `${fruit}: no production density is reported.`;
      };
      updateDensity(view.signal("fruitChoice"));
      // Native radios expose every choice without a long dropdown or custom keyboard logic.
      const choices = document.querySelector("#choropleth_options");
      const inputs = spec.usermeta.fruitOptions.map(fruit => {
        const label = document.createElement("label");
        const input = document.createElement("input");
        input.type = "radio";
        input.name = "choropleth-fruit";
        input.value = fruit;
        input.checked = fruit === view.signal("fruitChoice");
        const text = document.createElement("span");
        text.textContent = fruit;
        label.append(input, text);
        choices.append(label);
        input.addEventListener("change", () => {
          if (input.checked) view.signal("fruitChoice", fruit).runAsync();
        });
        return input;
      });
      view.addSignalListener("fruitChoice", (_, fruit) => {
        inputs.forEach(input => { input.checked = input.value === fruit; });
        updateDensity(fruit);
      });
    }
    if (el === "#fruit_bump") {
      const historyResponse = await fetch("data/fruit_history.csv");
      if (!historyResponse.ok) throw new Error("Ranking summary could not load");
      const history = vega.read(await historyResponse.text(), {type:"csv", parse:"auto"});
      // Competition rank matches Vega's rank transform, including tied values.
      const rank = (fruit, year) => {
        const rows = history.filter(r => r.year === year);
        const row = rows.find(r => r.fruit === fruit);
        return 1 + rows.filter(r => r.farmgate_value_aud_million > row.farmgate_value_aud_million).length;
      };
      const updateBump = choice => {
        const fruit = choice === "All fruits" ? "Avocados" : choice;
        const start = rank(fruit, "2020-21"), end = rank(fruit, "2024-25");
        document.querySelector("#bump_insight").textContent = `${fruit}: rank ${start} in 2020–21 and rank ${end} in 2024–25 among these ten fruits. ${end < start ? "A rise" : end > start ? "A fall" : "No endpoint change"} in rank describes order, not the size of the value gap.`;
      };
      updateBump(view.signal("bumpFruit"));
      view.addSignalListener("bumpFruit", (_, choice) => updateBump(choice));
    }
    if (el === "#fruit_symbols") {
      // A readable shortlist complements overlapping regional points without moving their locations.
      const regional = await (await fetch("data/fruit_regions_vega.geojson")).json();
      const updateRegions = () => {
        const fruit = view.signal("fruitChoice");
        const leaders = regional.features.filter(f => f.properties.fruit === fruit)
          .sort((a, b) => b.properties.production_t - a.properties.production_t).slice(0, 4);
        document.querySelector("#regional_leaders").replaceChildren(...leaders.map(f => {
          const item = document.createElement("li");
          const name = document.createElement("strong");
          name.textContent = f.properties.sa2_name_2021;
          item.append(name, `: ${new Intl.NumberFormat("en-AU").format(f.properties.production_t)} tonnes`);
          return item;
        }));
        document.querySelector("#regional_fruit").textContent = fruit;
      };
      updateRegions();
      view.addSignalListener("fruitChoice", (_, fruit) => {
        // Use a useful initial close-up for each crop; the region selector remains available.
        view.signal("regionFocus", fruit === "Bananas" ? "North Queensland" : "South-west WA").runAsync();
        updateRegions();
      });
    }
    if (el === "#fruit_trajectory") {
      const response = await fetch("data/fruit_history.csv");
      if (!response.ok) throw new Error("Fruit history annotation could not load");
      const history = vega.read(await response.text(), { type: "csv", parse: "auto" });
      const updateTrajectoryInsight = fruit => {
        const start = history.find(r => r.fruit === fruit && r.year === "2020-21");
        const end = history.find(r => r.fruit === fruit && r.year === "2024-25");
        const sentence = document.querySelector("#trajectory_insight");
        sentence.replaceChildren();
        const name = document.createElement("strong");
        name.textContent = `${fruit}: `;
        sentence.append(name);
        [ ["production", "production_tonnes"], ["nominal farmgate value", "farmgate_value_aud_million"] ].forEach(([label, field], index) => {
          const change = (end[field] / start[field] - 1) * 100;
          const result = document.createElement("strong");
          result.textContent = `${change >= 0 ? "rose" : "fell"} ${Math.abs(change).toFixed(1)}%`;
          sentence.append(`${index ? "; " : ""}${label} `, result);
        });
        sentence.append(" between 2020–21 and 2024–25.");
      };
      updateTrajectoryInsight("Apples");
      view.addSignalListener("fruitChoice", (_, fruit) => updateTrajectoryInsight(fruit));
    }
    if (el === "#fruit_exports") {
      // Only this chart has a separate HTML table and coverage sentence to synchronise.
      const exportResponse = await fetch("data/fruit_exports.json");
      if (!exportResponse.ok) throw new Error("Export summary could not load");
      const exportData = await exportResponse.json();
      const routePalette = spec.scales.find(scale => scale.name === "destinationColor");
      // Apply Australian number formatting, with at most one decimal place.
      const number = new Intl.NumberFormat("en-AU", { maximumFractionDigits: 1 });
      const updateExportSummary = choice => {
        // choice is the selected category; its total includes destinations not on the map.
        const summary = exportData.summaries.find(row => row.fruit === choice);
        document.querySelector("#export_coverage").textContent = `The eight destinations shown account for ${number.format(summary.coverage_pct)}% of ${number.format(summary.total_tonnes)} tonnes exported in this selection.`;
        // Filter to the selection and order destinations by their prepared export-volume rank.
        const rows = exportData.flows.filter(row => row.fruit === choice).sort((a, b) => a.rank - b.rank);
        const leader = rows[0];
        document.querySelector("#export_insight").textContent = `${choice}: ${leader.destination} is the leading destination, receiving ${number.format(leader.tonnes)} tonnes, or ${number.format(leader.share_pct)}% of the full selected export total in calendar 2025.`;
        const body = document.querySelector("#export_destinations");
        // Replace the previous rows, rather than appending duplicate destinations each time.
        body.replaceChildren(...rows.map(row => {
          const tr = document.createElement("tr");
          [row.destination, number.format(row.tonnes), `${number.format(row.share_pct)}%`].forEach(value => {
            const td = document.createElement("td");
            // Insert source values as plain text, not as HTML markup.
            td.textContent = value;
            tr.append(td);
          });
          const key = document.createElement("span");
          key.className = "route-key";
          key.style.backgroundColor = routePalette.range[routePalette.domain.indexOf(row.destination_code)];
          key.setAttribute("aria-hidden", "true");
          tr.firstChild.prepend(key);
          return tr;
        }));
      };
      // Fill the default table, then update it whenever Vega's dropdown signal changes.
      updateExportSummary("All five categories");
      // The first callback argument is the unused signal name; choice is its new value.
      view.addSignalListener("fruitChoice", (_, choice) => updateExportSummary(choice));
    }
    // Watch the chart container: changing the CSS grid can resize it without a window event.
    let previousWidth = container.clientWidth;
    const observer = new ResizeObserver(() => {
      const width = container.clientWidth;
      // Ignore height-only changes to avoid triggering our own resize work repeatedly.
      if (width === previousWidth) return;
      previousWidth = width;
      // Vega gets an explicit width; Vega-Lite specs declare width: "container".
      if (isVega) view.width(width);
      // Update dimensions, recalculate layout and rerun the view asynchronously.
      view.height(chartHeight(el, width)).resize().runAsync();
    });
    observer.observe(container);
  } catch (err) {
    // Show a readable fallback without stopping the other independently loaded charts.
    console.error(specPath, err);
    container.setAttribute("aria-busy", "false");
    container.setAttribute("role", "alert");
    container.textContent = "This chart could not load. Please refresh the page.";
  }
});

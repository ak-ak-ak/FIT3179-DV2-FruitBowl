// PREPARATION ONLY: Node reads/writes files; the public page renders the saved layout in Vega.
const fs = require('node:fs');
const path = require('node:path');
const { sankey } = require(process.env.DV2_SANKEY_MODULE || 'd3-sankey');
const dataDir = path.resolve(__dirname, '../data');
const input = JSON.parse(fs.readFileSync(path.join(dataDir, 'sankey_input.json')));
// d3-sankey sizes links by tonnes and positions nodes within a 1000 x 600 reference layout.
// nodeSort preserves our prepared node order instead of allowing the layout to reorder it.
const layout = sankey().nodeId(d => d.id).nodeWidth(10).nodePadding(18)
  .nodeSort((a, b) => a.order - b.order).extent([[0, 0], [1000, 600]])(input);
// Save only the fields Vega needs, not D3's object references and layout bookkeeping.
const nodes = layout.nodes.map(n => ({ id: n.id, name: n.name, label: n.label, kind: n.kind,
  value: n.value, x0: n.x0, x1: n.x1, y0: n.y0, y1: n.y1 }));
// sx/sy and tx/ty are link endpoints; width is the thickness in the reference layout.
const links = layout.links.map(l => ({ state: l.source.name, fruit: l.target.name, tonnes: l.value,
  sx: l.source.x1, sy: l.y0, tx: l.target.x0, ty: l.y1, width: l.width }));
const total = links.reduce((sum, l) => sum + l.tonnes, 0);
// Verify each node equals the sum of its attached links before publishing coordinates.
for (const n of nodes) {
  const linked = links.filter(l => n.kind === 'state' ? l.state === n.name : l.fruit === n.name)
    .reduce((sum, l) => sum + l.tonnes, 0);
  if (Math.abs(linked - n.value) > 0.000001) throw new Error(`Node total mismatch: ${n.name}`);
}
fs.writeFileSync(path.join(dataDir, 'fruit_sankey.json'), JSON.stringify({ nodes, links, total }, null, 2) + '\n');
console.log(`Sankey: ${nodes.length} nodes, ${links.length} links, ${total.toLocaleString()} tonnes`);

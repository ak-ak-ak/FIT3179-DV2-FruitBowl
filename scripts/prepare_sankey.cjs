const fs = require('node:fs');
const path = require('node:path');
const { sankey } = require(process.env.DV2_SANKEY_MODULE || 'd3-sankey');
const dataDir = path.resolve(__dirname, '../data');
const input = JSON.parse(fs.readFileSync(path.join(dataDir, 'sankey_input.json')));
const layout = sankey().nodeId(d => d.id).nodeWidth(10).nodePadding(18)
  .nodeSort((a, b) => a.order - b.order).extent([[0, 0], [1000, 600]])(input);
const nodes = layout.nodes.map(n => ({ id: n.id, name: n.name, label: n.label, kind: n.kind,
  value: n.value, x0: n.x0, x1: n.x1, y0: n.y0, y1: n.y1 }));
const links = layout.links.map(l => ({ state: l.source.name, fruit: l.target.name, tonnes: l.value,
  sx: l.source.x1, sy: l.y0, tx: l.target.x0, ty: l.y1, width: l.width }));
const total = links.reduce((sum, l) => sum + l.tonnes, 0);
for (const n of nodes) {
  const linked = links.filter(l => n.kind === 'state' ? l.state === n.name : l.fruit === n.name)
    .reduce((sum, l) => sum + l.tonnes, 0);
  if (Math.abs(linked - n.value) > 0.000001) throw new Error(`Node total mismatch: ${n.name}`);
}
fs.writeFileSync(path.join(dataDir, 'fruit_sankey.json'), JSON.stringify({ nodes, links, total }, null, 2) + '\n');
console.log(`Sankey: ${nodes.length} nodes, ${links.length} links, ${total.toLocaleString()} tonnes`);

"""Reconcile the final derived charts with the retained source extracts."""
import csv
from decimal import Decimal
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'
# READ-ONLY CHECKS: assertions stop the test if prepared values disagree with source extracts.
# This script does not regenerate chart data or specs.
national = list(csv.DictReader((DATA / 'fruit_national.csv').open()))
latest = [r for r in national if r['year'] == '2024-25']
total = sum(int(r['production_tonnes']) for r in latest)
# Check the 100-cell total, group cell counts, exact shares and production denominator.
units = json.loads((DATA / 'fruit_units.json').read_text())
assert len(units) == 100
categories = {r['fruit']: r for r in units}
assert sum(r['tonnes'] for r in categories.values()) == total == 2834995
for name, row in categories.items():
    assert sum(r['fruit'] == name for r in units) == row['units']
    assert abs(row['share_pct'] - row['tonnes'] / total * 100) < 1e-9

# Unreported matrix values must remain blank; only positive reported values make Sankey links.
matrix = list(csv.DictReader((DATA / 'fruit_state_matrix.csv').open()))
for row in matrix:
    if row['status'] != 'Reported':
        assert row['production_tonnes'] == '', 'Missing observation converted to a number'
expected = {(r['region'], r['fruit']): float(r['production_tonnes']) for r in matrix
            if r['status'] == 'Reported' and float(r['production_tonnes']) > 0}
sankey = json.loads((DATA / 'fruit_sankey.json').read_text())
actual = {(r['state'], r['fruit']): r['tonnes'] for r in sankey['links']}
assert actual == expected and len(actual) == 56
assert sum(actual.values()) == sankey['total'] == 2089200
# Check both sides of the network: each state/fruit node must equal its attached link totals.
for node in sankey['nodes']:
    value = sum(r['tonnes'] for r in sankey['links']
                if (r['state'] if node['kind'] == 'state' else r['fruit']) == node['name'])
    assert value == node['value']

start = {r['fruit']: Decimal(r['farmgate_value_aud_million']) for r in national if r['year'] == '2020-21'}
end = {r['fruit']: Decimal(r['farmgate_value_aud_million']) for r in latest}
waterfall = json.loads((DATA / 'fruit_waterfall.json').read_text())
# Recalculate waterfall changes from the original endpoints, not from chart coordinates.
position = Decimal(0)
for row in waterfall[:-1]:
    members = row['members'].split(', ')
    change = sum(end[f] - start[f] for f in members)
    assert change == Decimal(str(row['change']))
    assert Decimal(str(row['low'])) == min(position, position + change)
    assert Decimal(str(row['high'])) == max(position, position + change)
    position += change
assert position == sum(end.values()) - sum(start.values()) == Decimal('1486.0')
assert waterfall[-1]['change'] == float(position)

# The historical subset must retain the national source values, not rounded display labels.
history = list(csv.DictReader((DATA / 'fruit_history.csv').open()))
source = {(r['fruit'], r['year']): r for r in national}
for row in history:
    original = source[row['fruit'], row['year']]
    for field in ['production_tonnes', 'farmgate_value_aud_million']:
        assert Decimal(row[field]) == Decimal(original[field])

# Normalisation uses total state land and preserves absent observations.
for row in csv.DictReader((DATA / 'fruit_state_density.csv').open()):
    if row['production_tonnes']:
        expected_density = float(row['production_tonnes']) / float(row['land_area_km2'])
        assert abs(float(row['tonnes_per_km2']) - expected_density) < 1e-12
    else:
        assert not row['tonnes_per_km2']

# Destination shares and eight-link coverage use the full selected world total.
exports = json.loads((DATA / 'fruit_exports.json').read_text())
for summary in exports['summaries']:
    rows = sorted((r for r in exports['flows'] if r['fruit'] == summary['fruit']), key=lambda r:r['rank'])
    assert len(rows) == summary['shown_count'] == 8
    assert [r['rank'] for r in rows] == list(range(1, 9))
    assert all(a['tonnes'] >= b['tonnes'] for a,b in zip(rows, rows[1:]))
    for row in rows:
        assert abs(row['share_pct'] - row['tonnes'] / summary['total_tonnes'] * 100) < 1e-9
    assert abs(sum(r['share_pct'] for r in rows) - summary['coverage_pct']) < 1e-9
# Parsing every spec catches invalid JSON, including accidental // or /* */ comments.
for spec in (DATA.parent / 'specs').glob('*.json'):
    json.loads(spec.read_text())
print('PASS: units, source-matched Sankey totals, missing values, waterfall, history, density, export shares and JSON specs')

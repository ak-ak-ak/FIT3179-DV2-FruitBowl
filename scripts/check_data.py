"""Reconcile the final derived charts with the retained source extracts."""
import csv
from decimal import Decimal
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'
national = list(csv.DictReader((DATA / 'fruit_national.csv').open()))
latest = [r for r in national if r['year'] == '2024-25']
total = sum(int(r['production_tonnes']) for r in latest)
units = json.loads((DATA / 'fruit_units.json').read_text())
assert len(units) == 100
categories = {r['fruit']: r for r in units}
assert sum(r['tonnes'] for r in categories.values()) == total == 2834995
for name, row in categories.items():
    assert sum(r['fruit'] == name for r in units) == row['units']
    assert abs(row['share_pct'] - row['tonnes'] / total * 100) < 1e-9

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
for node in sankey['nodes']:
    value = sum(r['tonnes'] for r in sankey['links']
                if (r['state'] if node['kind'] == 'state' else r['fruit']) == node['name'])
    assert value == node['value']

start = {r['fruit']: Decimal(r['farmgate_value_aud_million']) for r in national if r['year'] == '2020-21'}
end = {r['fruit']: Decimal(r['farmgate_value_aud_million']) for r in latest}
waterfall = json.loads((DATA / 'fruit_waterfall.json').read_text())
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
for spec in (DATA.parent / 'specs').glob('*.json'):
    json.loads(spec.read_text())
print('PASS: 100 units, 56 source-matched links, node totals, missing values, waterfall and JSON specs')

"""Apply the shared editorial theme to existing and generated chart specs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = json.loads((ROOT / 'data/chart_theme.json').read_text())
COLORS = dict(zip(THEME['fruits'], THEME['colors']))
COLORS['Mandarins and related citrus'] = COLORS['Mandarins']
COLORS['All five categories'] = '#398965'

def update(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('font', 'labelFont', 'titleFont'):
                if item == 'Source Sans 3':
                    value[key] = THEME['font']
                elif isinstance(item, dict) and item.get('value') == 'Source Sans 3':
                    item['value'] = THEME['font']
            if key in ('fontSize', 'labelFontSize'):
                if isinstance(item, (int, float)):
                    value[key] = max(12, item)
                elif isinstance(item, dict) and isinstance(item.get('value'), (int, float)):
                    item['value'] = max(12, item['value'])
            if key == 'domain' and isinstance(item, list) and item and 'range' in value:
                if all(isinstance(name, str) and name in COLORS for name in item):
                    value['range'] = [COLORS[name] for name in item]
            if isinstance(item, str):
                value[key] = item.replace('#daac30', COLORS['Bananas']).replace('#b94d65', COLORS['Avocados'])
            update(item)
    elif isinstance(value, list):
        for item in value:
            update(item)

for path in (ROOT / 'specs').glob('fruit_*.json'):
    spec = json.loads(path.read_text())
    update(spec)
    if path.name == 'fruit_sankey.vg.json':
        spec['autosize'] = {'type': 'none', 'resize': True}
        spec['scales'][2]['range'] = [8, {'signal': 'height - 8'}]
        spec['marks'][0]['encode']['update']['strokeWidth'] = {'signal': 'datum.width*(height-16)/600'}
        spec['marks'][0]['encode']['leave'] = {
            'strokeOpacity': {'signal': "stateChoice === 'All states' || datum.state === stateChoice ? 0.55 : 0.08"}
        }
    if path.name == 'fruit_exports.vg.json':
        for mark in spec['marks']:
            enc = mark.get('encode', {}).get('update', {})
            if mark['type'] == 'text' and 'signal' in enc.get('dy', {}):
                enc['dy']['signal'] = "datum.destination_code === 'PNG' ? 20 : datum.destination_code === 'NZL' ? (width < 500 ? -20 : 20) : datum.rank === 1 ? -24 : datum.rank === 2 ? -6 : 18"
    if path.name == 'fruit_treemap.vg.json':
        spec['description'] = 'Area encodes nominal farmgate value of 29 reported fruits. Colours identify ten comparison fruits; other categories are grey.'
        spec['scales'][0].update(domain=THEME['fruits'], range=THEME['colors'])
        spec['legends'] = []
        for mark in spec['marks']:
            enc = mark['encode']['update']
            if mark['type'] == 'rect':
                enc['fill'] = {'signal': "indexof(" + json.dumps(THEME['fruits']) + ", datum.fruit) >= 0 ? scale('fruitGroup', datum.fruit) : '" + THEME['other'] + "'"}
            else:
                enc['fill'] = {'signal': "indexof(['Table grapes','Strawberries','Blueberries'],datum.fruit) >= 0 ? '#ffffff' : '#080f0b'"}
    path.write_text(json.dumps(spec, indent=2) + '\n')

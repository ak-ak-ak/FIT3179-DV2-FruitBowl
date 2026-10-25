"""Apply critique revisions without changing any source observations.

Run after the original spec builders and apply_chart_theme.py when rebuilding.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / 'specs'
theme = json.loads((ROOT / 'data/chart_theme.json').read_text())
old_colors = theme['colors'][:]
theme['colors'] = ['#E75C83','#81AE36','#8A58BB','#F39A24','#ED6D38',
                   '#D4AD19','#E76643','#25A977','#D93C72','#4F73C8']
theme['other'] = '#AEBCC9'
(ROOT / 'data/chart_theme.json').write_text(json.dumps(theme, indent=2)+'\n')
palette = dict(zip(theme['fruits'],theme['colors']))
replacements = dict(zip(old_colors, theme['colors']))
# Include the previous palette so this operation remains repeatable after a rebuild.
replacements.update(dict(zip(['#ce6777','#799e55','#716096','#dd952f','#d37339',
                             '#b89d32','#cb624f','#398965','#bc466d','#506794'],theme['colors'])))
replacements['#c5cbd2']=theme['other']

def walk(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if isinstance(v,str):
                for old,new in replacements.items():
                    v=v.replace(old,new)
                value[k]=v
            else:
                walk(v)
    elif isinstance(value,list):
        for i,v in enumerate(value):
            if isinstance(v,str):
                value[i]=replacements.get(v,v)
            else:
                walk(v)

def save(name,spec):
    (SPECS / name).write_text(json.dumps(spec,indent=2)+'\n')

for path in SPECS.glob('fruit_*.json'):
    spec=json.loads(path.read_text())
    walk(spec)
    spec['background']='transparent'
    save(path.name,spec)

# A flat ranking needs aligned positions, not a fabricated hierarchy.
value = {
 '$schema':'https://vega.github.io/schema/vega-lite/v5.json',
 'description':'Ranked lollipop comparison of the ten highest farmgate values among 29 reported fruit categories. No hierarchical relationship is implied.',
 'width':'container','height':320,'background':'transparent',
 'data':{'url':'data/fruit_value_tree.json'},
 'transform':[{'filter':"datum.parent === 'root'"},
              {'window':[{'op':'row_number','as':'value_rank'}],
               'sort':[{'field':'value','order':'descending'}]},
              {'filter':'datum.value_rank <= 10'}],
 'encoding':{'y':{'field':'fruit','type':'nominal','sort':{'field':'value','order':'descending'},
                  'axis':{'title':None,'ticks':False,'labelLimit':115}},
             'x':{'field':'value','type':'quantitative','scale':{'domain':[0,1050]},
                  'axis':{'title':'Farmgate value (A$ million)','tickCount':4}},
             'tooltip':[{'field':'fruit','title':'Fruit'},{'field':'value','type':'quantitative','title':'Value (A$ million)','format':',.1f'},
                        {'field':'share_pct','type':'quantitative','title':'Share of 29-category value (%)','format':'.1f'}]},
 'layer':[{'mark':{'type':'rule','strokeWidth':3,'color':'#CCB1C4'},'encoding':{'x2':{'datum':0}}},
          {'mark':{'type':'point','filled':True,'size':115},'encoding':{
              'color':{'field':'fruit','type':'nominal','scale':{'domain':theme['fruits'],'range':theme['colors'],'unknown':'#6A7D8F'},'legend':None}}},
          {'mark':{'type':'text','align':'left','dx':10,'fontSize':12,'fontWeight':700,'color':'#263B32'},
           'encoding':{'text':{'field':'value','type':'quantitative','format':',.1f'}}}],
 'config':{'font':'Nunito Sans','view':{'stroke':None},'axis':{'labelFontSize':12,'titleFontSize':12,'domain':False,'gridColor':'#E5D7AD','titlePadding':10}}
}
tree=json.loads((ROOT/'data/fruit_value_tree.json').read_text())
categories=[r['fruit'] for r in tree if r.get('parent')=='root']
value['layer'][1]['encoding']['color']['scale']={'domain':categories,'range':[palette.get(f,'#617A91') for f in categories]}
value['layer'][1]['mark']['opacity']=1
save('fruit_value.vl.json',value)
unit=json.loads((SPECS/'fruit_units.vl.json').read_text())
unit['mark'].update(stroke='#FFF5C7',strokeWidth=3,cornerRadius=0)
save('fruit_units.vl.json',unit)

heat=json.loads((SPECS/'fruit_heatmap.vl.json').read_text())
# Remove the cell text layer; exact percentages remain accessible through tooltips.
heat['layer']=[layer for layer in heat['layer'] if layer.get('mark',{}).get('type')!='text']
heat['layer']=[layer for layer in heat['layer'] if layer.get('name')!='insight_cells']
heat['layer'][0]['mark']['color']='#CBD8CC'
for layer in heat['layer']:
    layer['mark']['stroke']='#E6F8E7'
    layer['mark']['strokeWidth']=1
scale=heat['layer'][1]['encoding']['color']['scale']
scale.update(domain=[0,30,65,100],range=['#FFF5DD','#FFB99C','#F16A72','#A72051'])
heat['layer'][1]['encoding']['color']['legend']={
 'title':'Share of national production (%)','orient':'bottom','direction':'horizontal',
 'gradientLength':{'expr':'max(160, width - 20)'},'gradientThickness':12,
 'values':[0,25,50,75,100],'titleLimit':350,'labelFontSize':12,'titleFontSize':12}
heat['layer'].append({'name':'insight_cells','transform':[{'filter':"(datum.fruit === 'Bananas' && datum.state === 'QLD') || (datum.fruit === 'Blueberries' && datum.state === 'NSW') || (datum.fruit === 'Pears' && datum.state === 'VIC')"}],
                      'mark':{'type':'rect','fillOpacity':0,'stroke':'#7D354C','strokeWidth':2}})
save('fruit_heatmap.vl.json',heat)

choro=json.loads((SPECS/'fruit_choropleth.vl.json').read_text())
choro['layer'][0]['mark'].update(fill='#AEBABD',stroke='#527D88',strokeWidth=0.8)
choro['layer'][1]['mark'].update(stroke='#527D88',strokeWidth=0.8)
choro['layer'][1]['encoding']['color']['scale']['range']=['#C4E3F0','#07516B']
legend=choro['layer'][1]['encoding']['color']['legend']
legend.update(gradientLength={'expr':'max(160, width - 24)'},gradientThickness=12,titleLimit=350)
# Keep the choices in metadata for the HTML radio list; no duplicate bound select is needed.
parameter=choro['params'][0]
options=parameter.get('bind',{}).get('options',choro.get('usermeta',{}).get('fruitOptions'))
choro['usermeta']={'fruitOptions':options}
parameter.pop('bind',None)
save('fruit_choropleth.vl.json',choro)

symbols=json.loads((SPECS/'fruit_symbols.vl.json').read_text())
symbols['params'][1]['value']='North Queensland'
symbols['projection']['scale']['expr']="regionFocus === 'North Queensland' ? min(width * 9, height * 12) : regionFocus === 'South-west WA' ? min(width * 7, height * 9) : min(width * 0.72, height * 1.1)"
symbols['projection']['center']['expr']="regionFocus === 'North Queensland' ? [12.5, -17.7] : regionFocus === 'South-west WA' ? [-17, -33] : [0, -28]"
symbols['layer'][0]['mark'].update(fill='#D5EED8',stroke='#91BC9B')
circles=symbols['layer'][1]
circles['mark'].update(opacity=0.68,stroke='#3F573F',strokeWidth=1)
circles['encoding']['size']['scale']['range']=[0,700]
circles['encoding']['size']['legend']['symbolFillColor']='#71877B'
circles['encoding']['size']['legend']['title']='Production (tonnes)'
symbols['layer'][2]['mark']['fontWeight']=700
save('fruit_symbols.vl.json',symbols)

for name in ['fruit_slope.vl.json','fruit_bump.vl.json','fruit_trajectory.vl.json']:
    spec=json.loads((SPECS/name).read_text())
    # Inner range padding separates endpoint marks from the year labels below the plot.
    spec['config']['axis'].update(labelPadding=12,labelColor='#34493E',titleColor='#34493E')
    spec['config']['axis'].update(gridColor='#AD8596',gridOpacity=0.5,gridWidth=0.7)
    for channel in ['x','y']:
        encoding=spec['encoding'][channel]
        encoding.setdefault('axis',{})['grid']=encoding.get('type')=='quantitative'
    if name=='fruit_bump.vl.json':
        spec['encoding']['y']['scale']['domain']=[0.6,10.6]
    if name=='fruit_slope.vl.json':
        rows=list(csv.DictReader((ROOT/'data/fruit_history.csv').open()))
        labels={}
        for fruit in ['Oranges','Avocados','Pears']:
            start=next(float(r['production_tonnes']) for r in rows if r['fruit']==fruit and r['year']=='2020-21')
            end=next(float(r['production_tonnes']) for r in rows if r['fruit']==fruit and r['year']=='2024-25')
            labels[fruit]=fruit+' '+format((end/start-1)*100,'+.0f')+'%'
        text=spec['layer'][2]
        text['transform']=[t for t in text['transform'] if t.get('as')!='change_label']
        text['transform'].append({'calculate':"datum.fruit === 'Avocados' ? "+json.dumps(labels['Avocados'])+" : datum.fruit === 'Pears' ? "+json.dumps(labels['Pears'])+" : "+json.dumps(labels['Oranges']),'as':'change_label'})
        text['encoding']['text']['field']='change_label'
        text['mark']['fontWeight']=700
    save(name,spec)

water=json.loads((SPECS/'fruit_waterfall.vl.json').read_text())
water['config']['axis'].update(gridColor='#AD8596',gridOpacity=0.5,gridWidth=0.7)
water['encoding']['y']['axis']['grid']=False
water['layer'][1]['encoding']['x']['axis']['grid']=True
save('fruit_waterfall.vl.json',water)

export=json.loads((SPECS/'fruit_exports.vg.json').read_text())
# Colour by destination across selections, rather than give every route the same hue.
flows=json.loads((ROOT/'data/fruit_exports.json').read_text())['flows']
codes=list(dict.fromkeys(r['destination_code'] for r in flows))
route_colors=['#C43B72','#197E77','#7251B5','#C16D13','#3F6CC1','#A54435','#618C21','#A33399',
              '#087F9C','#A36B36','#B1486B','#537BBD','#747328','#854B9F','#247958','#AC5341']
export['scales']=[s for s in export['scales'] if s['name']!='destinationColor']
assigned={}
for code in codes:
    selections={r['fruit'] for r in flows if r['destination_code']==code}
    neighbours={r['destination_code'] for r in flows if r['fruit'] in selections}
    forbidden={assigned[c] for c in neighbours if c in assigned}
    assigned[code]=next(c for c in route_colors if c not in forbidden)
for fruit in {r['fruit'] for r in flows}:
    selected=[assigned[r['destination_code']] for r in flows if r['fruit']==fruit]
    assert len(set(selected))==len(selected), 'Displayed destinations must have distinct colours'
export['scales'].append({'name':'destinationColor','type':'ordinal','domain':codes,'range':[assigned[c] for c in codes]})
for mark in export['marks']:
    enc=mark.get('encode',{}).get('update',{})
    if mark.get('name')=='exportRoutes':
        enc['stroke']={'scale':'destinationColor','field':'destination_code'}
        enc['strokeOpacity']={'value':0.85}
        mark['encode']['leave']['strokeOpacity']={'value':0.85}
    if mark.get('name')=='exportDestinations':
        enc['fill']={'scale':'destinationColor','field':'destination_code'}
    if mark.get('from',{}).get('data')=='countries':
        enc['fill']={'value':'#CBE8D9'}
    if mark.get('from',{}).get('data')=='sphere':
        enc['fill']={'value':'#D9F0FF'}
    if mark.get('from',{}).get('data')=='origin' and mark['type']=='text':
        enc.update(align={'value':'right'},dx={'value':-12},dy={'value':14})
export['legends'][0]['symbolStrokeColor']={'value':'#516A78'}
save('fruit_exports.vg.json',export)
print('Refined 11-chart lineup, heatmap, regional focus, axes and destination colours.')

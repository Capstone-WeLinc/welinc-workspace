"""Pull the S27d Quiet map out of board R47Quiet (made by gen48.py from drawnmap.json) for the portal."""
import re, sys, json
board, out_svg, out_ts = sys.argv[1:4]
s = open(board).read()
under = s[s.find('class="under"'):]
tilt = re.search(r'<div style="([^"]+)"><svg class="map"', under).group(1)
svg = re.search(r'(<svg class="map".*?</svg>)</div>', under, re.S).group(1)
assert 'class="trf"' not in svg
# ids get a prefix so they never clash with another drawing on the page
for i in sorted(set(re.findall(r'id="([^"]+)"', svg))):
    svg = svg.replace(f'id="{i}"', f'id="signin-{i}"').replace(f'#{i}"', f'#signin-{i}"').replace(f'url(#{i})', f'url(#signin-{i})')
svg = svg.replace('<svg class="map" ', '<svg xmlns="http://www.w3.org/2000/svg" ').replace(' width="1240" height="1500"', ' width="100%" height="100%"').replace(' aria-hidden="true"', ' aria-hidden="true" focusable="false"')
header = '<!-- The S27d Quiet sign in map (suite spec 0019, AC-13), taken from board R47Quiet, which gen48.py drew from docs/context/vrms/portal-redo-boards/gen/drawnmap.json. Map data (c) OpenStreetMap contributors, ODbL. -->\n'
open(out_svg, 'w').write(header + svg + '\n')
labels = []
for cls, style, text in re.findall(r'<span class="(t-[a-z]) [^"]*" style="([^"]+)">([^<]+)</span>', under):
    if cls not in ('t-g', 't-d'):
        continue
    st = dict(p.split(':', 1) for p in style.split(';') if p)
    tr = st.get('transform', '')
    side = 'start' if cls == 't-g' or 'translate(0' in tr else 'end' if '-100%' in tr else 'center'
    labels.append({'text': text, 'kind': 'garage' if cls == 't-g' else 'drop', 'x': int(st['left'][:-2]), 'y': int(st['top'][:-2]), 'size': float(st['font-size'][:-2]), 'side': side})
ts = ['/*', '  Suite spec 0019, AC-13: the labels on the sign in map, placed on its 1440 by 900 stage as board', '  `R47Quiet` places them (the three garages and the drop points; no town, water or road names).', '  Generated with the map (`signin-map.svg`); positions are stage pixels.', '*/',
      "export type MapLabel = { text: string; kind: 'garage' | 'drop'; x: number; y: number; size: number; side: 'start' | 'end' | 'center' };", '',
      'export const MAP_LABELS: readonly MapLabel[] = [']
for l in labels:
    ts.append(f"  {{ text: {json.dumps(l['text'], ensure_ascii=False)}, kind: '{l['kind']}', x: {l['x']}, y: {l['y']}, size: {l['size']}, side: '{l['side']}' }},")
ts += ['];', '', f'/** Where the tilted map sits on the stage (the board\'s own placement): {tilt} */', '']
open(out_ts, 'w').write('\n'.join(ts))
print(tilt); print(len(svg)); print(len(labels))

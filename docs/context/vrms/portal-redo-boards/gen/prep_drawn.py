"""The drawn map: traced from OpenStreetMap, then cut down to what a sign in page needs.
python3 -I prep_drawn.py <osm dir> <realmap.json> <out drawn.json>
Keeps the real coast, lakes, garages, drops and the twelve routed trips from realmap.json (prep_map.py), simplifies them hard,
keeps only the named roads below, and turns the street network into a light dot pattern over the built-up areas.
Map data (c) OpenStreetMap contributors, ODbL."""
import json
import math
import sys
from pathlib import Path

LAT0, LON0, U = 14.6, 121.0, 11.0          # the same projection as prep_map.py
KX = 111.32 * math.cos(math.radians(LAT0)) * U
KY = 110.57 * U


def P(lat, lon):
    return ((lon - LON0) * KX, (LAT0 - lat) * KY)


def rdp(pts, eps):
    if len(pts) < 3:
        return list(pts)
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    n = math.hypot(dx, dy)
    best, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / n if n > 1e-9 else math.dist(pts[i], pts[0])
        if d > best:
            best, idx = d, i
    if best > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]

SRC, REAL, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
R = json.loads(REAL.read_text())
VIEW = (-700, -780, 1360, 1620)

EXP = ('North Luzon Expressway', 'South Luzon Expressway', 'Skyway', 'Subic-Clark-Tarlac Expressway', 'Manila–Cavite Expressway',
       'Cavite–Laguna Expressway', 'NLEX Harbor Link', 'NAIA Expressway', 'Muntinlupa-Cavite Expressway', 'NLEX-SLEX Connector',
       'Southern Tagalog Arterial Road')
PRI = ('EDSA', 'MacArthur Highway', 'Aguinaldo Highway', "Governor's Drive", 'Maharlika Highway', 'National Highway 1', 'Plaridel Bypass Road',
       'Marcos Highway', 'Carlos P. Garcia', 'C-5', 'Commonwealth Avenue', 'Ortigas Avenue', 'Roxas Boulevard', 'Alabang-Zapote Road',
       'Santa Rosa-Tagaytay Road', 'Sumulong Highway', 'Quirino Highway', 'Aurora Boulevard', 'Circumferential Road 6', 'C-6',
       'Jose Abad Santos Avenue', 'Doña Remedios Trinidad Highway', 'Manila East Road', 'Taytay Diversion')


def inview(pts, pad=80):
    x, y, w, h = VIEW
    return any(x - pad <= a <= x + w + pad and y - pad <= b <= y + h + pad for a, b in pts)


def r0(pts):
    return [[round(x), round(y)] for x, y in pts]


def join(lines):
    """Join road pieces that share an end, whichever way they run, into whole roads."""
    key = lambda p: (round(p[0], 2), round(p[1], 2))
    ends = {}
    for i, l in enumerate(lines):
        ends.setdefault(key(l[0]), []).append(i)
        ends.setdefault(key(l[-1]), []).append(i)
    used, out = set(), []

    def grow(line):
        while True:
            for j in ends.get(key(line[-1]), []):
                if j in used:
                    continue
                used.add(j)
                l = lines[j]
                line += (l if key(l[0]) == key(line[-1]) else l[::-1])[1:]
                break
            else:
                return line
    for i, l in enumerate(lines):
        if i in used:
            continue
        used.add(i)
        line = grow(list(l))
        line = grow(line[::-1])
        out.append(line)
    return out


roads = json.load(open(SRC / 'roads.json'))['elements']
pieces = {'exp': [], 'pri': []}
for wy in roads:
    nm = wy['tags'].get('name', '')
    kind = 'exp' if any(k in nm for k in EXP) else 'pri' if any(k in nm for k in PRI) else None
    if not kind:
        continue
    xy = [P(g['lat'], g['lon']) for g in wy['geometry']]
    if inview(xy, 200):
        pieces[kind].append(xy)
out = {}
for kind, ls in pieces.items():
    out[kind] = []
    for l in join(ls):
        s = rdp(l, 2.4)
        if sum(math.dist(s[i], s[i + 1]) for i in range(len(s) - 1)) >= 8:
            out[kind].append(r0(s))

# built-up areas: where the street network is dense, a dot; denser, a brighter dot
minor = json.load(open(SRC / 'minor.json'))['elements']
CELL = 15
count = {}
for wy in minor:
    for g in wy['geometry']:
        x, y = P(g['lat'], g['lon'])
        k = (int(x // CELL), int(y // CELL))
        count[k] = count.get(k, 0) + 1
dots = {1: [], 2: [], 3: []}
for (i, j), c in count.items():
    x, y = i * CELL + CELL / 2, j * CELL + CELL / 2
    if not inview([(x, y)], 0):
        continue
    tier = 3 if c >= 90 else 2 if c >= 40 else 1 if c >= 14 else 0
    if tier:
        dots[tier].append([round(x), round(y)])

sea = r0(rdp([tuple(p) for p in R['sea']], 3.2))
lakes = []
for l in R['lakes']:
    s = r0(rdp([tuple(p) for p in l['pts']], 2.6 if l['role'] == 'outer' else 2))
    if len(s) > 3 and (l['role'] == 'outer' or abs(sum(s[i - 1][0] * s[i][1] - s[i][0] * s[i - 1][1] for i in range(len(s)))) > 400):
        lakes.append({'lake': l['lake'], 'role': l['role'], 'pts': s})
islands = [r0(rdp([tuple(p) for p in r], 3)) for r in R['islands']]
islands = [r for r in islands if len(r) > 3 and inview(r)]
trips = [dict(t, pts=r0(rdp([tuple(p) for p in t['pts']], 1.6))) for t in R['trips']]

data = {'note': 'Drawn from OpenStreetMap (c) OpenStreetMap contributors, ODbL. 1 unit = 1/11 km, origin 14.6 N 121.0 E.',
        'drawn': True, 'sea': sea, 'islands': islands, 'lakes': lakes, 'roads': {**out, 'sec': []}, 'streets': [],
        'dots': {str(k): v for k, v in dots.items()},
        'garages': R['garages'], 'places': R['places'], 'towns': R['towns'], 'trips': trips, 'shields': R['shields']}
OUT.write_text(json.dumps(data, separators=(',', ':')))
print('roads', {k: (len(v), sum(len(l) for l in v)) for k, v in out.items()}, 'dots', {k: len(v) for k, v in dots.items()},
      'sea', len(sea), 'lakes', sum(len(l['pts']) for l in lakes), 'trips', sum(len(t['pts']) for t in trips), 'bytes', OUT.stat().st_size)

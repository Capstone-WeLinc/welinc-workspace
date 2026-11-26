"""Turn the OpenStreetMap downloads into realmap.json: projected, simplified map layers plus twelve trips routed on real roads.
python3 -I prep_map.py <osm dir> <out json>
Map data (c) OpenStreetMap contributors, ODbL. Projection: equirectangular around 14.6 N 121.0 E, 1 unit = 1/11 km."""
import heapq
import json
import math
import sys
from pathlib import Path

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
LAT0, LON0, U = 14.6, 121.0, 11.0
KX = 111.32 * math.cos(math.radians(LAT0)) * U
KY = 110.57 * U
BBOX = (13.95, 120.45, 15.15, 121.55)


def P(lat, lon):
    return ((lon - LON0) * KX, (LAT0 - lat) * KY)


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    n = math.hypot(dx, dy) or 1e-9
    best, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / n if n > 1e-9 else math.dist(pts[i], pts[0])
        if d > best:
            best, idx = d, i
    if best > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def r1(pts):
    return [[round(x, 1), round(y, 1)] for x, y in pts]


def rings_any(ways):
    """Join ways into rings whatever their direction (multipolygon members can run either way)."""
    key = lambda p: (round(p[0], 6), round(p[1], 6))
    segs = [list(w) for w in ways if len(w) > 1]
    used, out = [False] * len(segs), []
    for i in range(len(segs)):
        if used[i]:
            continue
        used[i] = True
        ring = list(segs[i])
        grown = True
        while grown and key(ring[0]) != key(ring[-1]):
            grown = False
            for j, s in enumerate(segs):
                if used[j]:
                    continue
                if key(s[0]) == key(ring[-1]):
                    ring += s[1:]
                elif key(s[-1]) == key(ring[-1]):
                    ring += s[::-1][1:]
                else:
                    continue
                used[j] = grown = True
                break
        out.append(ring)
    return out


def chains(ways):
    """Join ways that share end nodes (by rounded coordinate) into longer lines."""
    key = lambda p: (round(p[0], 6), round(p[1], 6))
    segs = [list(w) for w in ways if len(w) > 1]
    start = {}
    for i, s in enumerate(segs):
        start.setdefault(key(s[0]), []).append(i)
    used, out = set(), []
    for i, s in enumerate(segs):
        if i in used:
            continue
        used.add(i)
        line = list(s)
        grown = True
        while grown:
            grown = False
            for j in start.get(key(line[-1]), []):
                if j not in used:
                    used.add(j)
                    line += segs[j][1:]
                    grown = True
                    break
        out.append(line)
    # second pass: prepend chains whose end meets another's start
    merged = True
    while merged:
        merged = False
        ends = {key(c[-1]): k for k, c in enumerate(out)}
        for k, c in enumerate(out):
            j = ends.get(key(c[0]))
            if j is not None and j != k:
                out[j] = out[j] + c[1:]
                out.pop(k)
                merged = True
                break
    return out


def inside(pt, poly):
    x, y = pt
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i - 1]
        x2, y2 = poly[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


# ---------------------------------------------------------------- coastline -> sea polygon
coast = json.load(open(SRC / 'coast.json'))['elements']
lines = chains([[(g['lat'], g['lon']) for g in w['geometry']] for w in coast])
lines.sort(key=len, reverse=True)
main = lines[0]
s, w, n, e = BBOX
corners = [(n + .2, w - .2), (n + .2, e + .2), (s - .2, e + .2), (s - .2, w - .2)]   # NW NE SE SW


def edge_pos(p):
    """Position of a point along the bbox outline, clockwise from NW, 0..4."""
    lat, lon = p
    d = [abs(lat - n), abs(lon - e), abs(lat - s), abs(lon - w)]
    k = d.index(min(d))
    if k == 0:
        return (lon - w) / (e - w)
    if k == 1:
        return 1 + (n - lat) / (n - s)
    if k == 2:
        return 2 + (e - lon) / (e - w)
    return 3 + (lat - s) / (n - s)


def close(line, clockwise):
    a, b = edge_pos(line[-1]), edge_pos(line[0])
    ring = list(line)
    cs = [(0, corners[0]), (1, corners[1]), (2, corners[2]), (3, corners[3])]
    if clockwise:
        t = a
        while True:
            nxt = [c for c in cs if c[0] > t] or [(cs[0][0] + 4, cs[0][1])]
            k, c = min(nxt, key=lambda z: z[0])
            if (b - a) % 4 < (k - a) % 4 or (b - a) % 4 == 0:
                break
            ring.append(c)
            t = k % 4 if k < 4 else k - 4
            if len(ring) > len(line) + 4:
                break
    else:
        t = a
        while True:
            prv = [c for c in cs if c[0] < t] or [(cs[3][0] - 4, cs[3][1])]
            k, c = max(prv, key=lambda z: z[0])
            if (a - b) % 4 < (a - k) % 4 or (a - b) % 4 == 0:
                break
            ring.append(c)
            t = k % 4 if k >= 0 else k + 4
            if len(ring) > len(line) + 4:
                break
    return ring


SEA_PT, LAND_PT = (14.55, 120.80), (14.59, 121.0)
sea = None
for cw in (True, False):
    ring = close(main, cw)
    if inside(SEA_PT, ring) and not inside(LAND_PT, ring):
        sea = ring
        break
assert sea, 'could not close the sea polygon'
islands = [l for l in lines[1:] if len(l) > 8 and l[0] == l[-1]]
sea_xy = rdp([P(*p) for p in sea], 1.2)
isl_xy = [rdp([P(*p) for p in l], 1.2) for l in islands]
isl_xy = [r for r in isl_xy if len(r) > 3]

# ---------------------------------------------------------------- lakes
lake_el = json.load(open(SRC / 'lake.json'))['elements']


def rings_of(rel, role):
    ws = [[(g['lat'], g['lon']) for g in m['geometry']] for m in rel['members'] if m['type'] == 'way' and m['role'] == role and 'geometry' in m]
    return [c for c in rings_any(ws) if len(c) > 3]


lakes = []
for rel in lake_el:
    nm = rel['tags'].get('name')
    if nm in ('Laguna de Bay', 'Taal Lake'):
        for role in ('outer', 'inner'):
            for c in rings_of(rel, role):
                xy = rdp([P(*p) for p in c], 1.0)
                if len(xy) > 3:
                    lakes.append({'lake': nm, 'role': role, 'pts': r1(xy)})

# ---------------------------------------------------------------- roads
roads = json.load(open(SRC / 'roads.json'))['elements']
CLS = {'motorway': 'exp', 'trunk': 'pri', 'primary': 'sec'}
layers = {'exp': [], 'pri': [], 'sec': []}
graph = {}
coord = {}
elab = {}
named = {}
for wy in roads:
    hw = wy['tags']['highway']
    geo = [(g['lat'], g['lon']) for g in wy['geometry']]
    xy = [P(*p) for p in geo]
    layers[CLS[hw]].append(r1(rdp(xy, .9)))
    nm = wy['tags'].get('name', '') + '|' + wy['tags'].get('ref', '')
    named.setdefault(nm, []).append(xy)
    nodes = wy['nodes']
    for a, b, pa, pb in zip(nodes, nodes[1:], xy, xy[1:]):
        d = math.dist(pa, pb) * {'motorway': .8, 'trunk': .92, 'primary': 1.0}[hw]   # lean a little toward the big roads, like a dispatcher would
        graph.setdefault(a, []).append((b, d))
        graph.setdefault(b, []).append((a, d))
        lab = wy['tags'].get('name') or wy['tags'].get('ref', '')
        elab[(a, b)] = elab[(b, a)] = (lab, math.dist(pa, pb))
        coord[a], coord[b] = pa, pb

minor = json.load(open(SRC / 'minor.json'))['elements']
streets = [r1(rdp([P(g['lat'], g['lon']) for g in wy['geometry']], 1.4)) for wy in minor]
streets = [s for s in streets if len(s) > 1 and math.dist(s[0], s[-1]) > 3]


def nearest(lat, lon):
    x, y = P(lat, lon)
    return min(coord, key=lambda k: (coord[k][0] - x) ** 2 + (coord[k][1] - y) ** 2)


def route(a, b):
    dist, prev, q = {a: 0}, {}, [(0, a)]
    while q:
        d, u = heapq.heappop(q)
        if u == b:
            break
        if d > dist.get(u, 1e18):
            continue
        for v, w in graph.get(u, ()):
            nd = d + w
            if nd < dist.get(v, 1e18):
                dist[v], prev[v] = nd, u
                heapq.heappush(q, (nd, v))
    path, u = [b], b
    while u != a:
        u = prev[u]
        path.append(u)
    path.reverse()
    roads_used = {}
    for x, y in zip(path, path[1:]):
        lab, ln = elab[(x, y)]
        roads_used.setdefault(lab, [0, len(roads_used)])[0] += ln
    return [coord[k] for k in path], roads_used


GARAGES = {'Pulilan': (14.9023, 120.8488), 'Marikina': (14.6331, 121.0994), 'Sta. Rosa': (14.3141, 121.1123)}
PLACES = {'San Fernando': (15.0283, 120.6938), 'Port Area': (14.589, 120.9686), 'Baliwag': (14.9542, 120.9009), 'Malolos': (14.8438, 120.8114),
          'Tanay': (14.4985, 121.2856), 'Rodriguez': (14.7325, 121.1453), 'Taguig': (14.5271, 121.0745), 'Sampaloc': (14.6022, 120.9941),
          'Pasay': (14.5437, 120.9947), 'Sto. Tomas': (14.1078, 121.1453), 'Tagaytay': (14.0993, 120.9392), 'Dasmariñas': (14.3271, 120.9371)}
TOWNS = {'Manila': (14.5904, 120.9804), 'Quezon City': (14.6511, 121.0486), 'Antipolo': (14.5872, 121.1759), 'Valenzuela': (14.6915, 120.9699),
         'Calamba': (14.206, 121.1556), 'Bacoor': (14.4593, 120.9402), 'Makati': (14.5547, 121.0244), 'Meycauayan': (14.7369, 120.9606),
         'Cavite City': (14.4791, 120.8970), 'Batangas': (13.7565, 121.0583)}
TRIPS = [('Pulilan', 'San Fernando'), ('Pulilan', 'Port Area'), ('Pulilan', 'Baliwag'), ('Pulilan', 'Malolos'),
         ('Marikina', 'Tanay'), ('Marikina', 'Rodriguez'), ('Marikina', 'Taguig'), ('Marikina', 'Sampaloc'),
         ('Sta. Rosa', 'Pasay'), ('Sta. Rosa', 'Sto. Tomas'), ('Sta. Rosa', 'Tagaytay'), ('Sta. Rosa', 'Dasmariñas')]
gnode = {g: nearest(*ll) for g, ll in GARAGES.items()}
trips = []
for g, dst in TRIPS:
    path, used = route(gnode[g], nearest(*PLACES[dst]))
    tot = sum(v[0] for v in used.values())
    big = sorted([(v[1], k, v[0]) for k, v in used.items() if k and v[0] > .12 * tot])
    via = [[k, round(ln / U, 1)] for _, k, ln in big]
    path = [P(*GARAGES[g])] + path + [P(*PLACES[dst])]
    path = rdp(path, .6)
    km = sum(math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)) / U
    trips.append({'from': g, 'to': dst, 'km': round(km, 1), 'via': via, 'pts': r1(path)})


def mid_of(pattern, near):
    """A point on a named road closest to a lat/lon, for its shield."""
    x0, y0 = P(*near)
    best = None
    for nm, ls in named.items():
        if pattern in nm:
            for l in ls:
                for p in l:
                    d = (p[0] - x0) ** 2 + (p[1] - y0) ** 2
                    if best is None or d < best[0]:
                        best = (d, p)
    return r1([best[1]])[0] if best else None


SHIELDS = [('NLEX', 'North Luzon Expressway', (14.80, 120.93)), ('SLEX', 'South Luzon Expressway', (14.40, 121.05)),
           ('EDSA', 'EDSA|', (14.585, 121.055)), ('C-5', 'C-5', (14.57, 121.075)),
           ('CAVITEX', 'Manila-Cavite', (14.50, 120.975)), ('SCTEX', 'Subic-Clark-Tarlac', (15.12, 120.60))]
shields = []
for t, pat, ll in SHIELDS:
    p = mid_of(pat, ll)
    if p:
        shields.append({'t': t, 'p': p})

data = {
    'note': 'Map data (c) OpenStreetMap contributors, ODbL. 1 unit = 1/11 km, origin 14.6 N 121.0 E.',
    'sea': r1(sea_xy), 'islands': [r1(r) for r in isl_xy], 'lakes': lakes,
    'roads': layers, 'streets': streets,
    'garages': {g: r1([P(*ll)])[0] for g, ll in GARAGES.items()},
    'places': {g: r1([P(*ll)])[0] for g, ll in PLACES.items()},
    'towns': {g: r1([P(*ll)])[0] for g, ll in TOWNS.items()},
    'trips': trips, 'shields': shields,
}
OUT.write_text(json.dumps(data, separators=(',', ':')))
print('sea', len(sea_xy), 'islands', len(isl_xy), 'lakes', [(l['lake'], l['role'], len(l['pts'])) for l in lakes])
print('roads', {k: (len(v), sum(len(l) for l in v)) for k, v in layers.items()}, 'streets', len(streets), sum(len(s) for s in streets))
for t in trips:
    print(f"{t['from']:10s} -> {t['to']:13s} {t['km']:5.1f} km  {t['via']}")
print('shields', shields)
print('size', OUT.stat().st_size)

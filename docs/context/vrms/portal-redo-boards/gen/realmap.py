"""Draw the map as one SVG: drawnmap.json (prep_drawn.py, traced from OpenStreetMap and cut down). Map data (c) OpenStreetMap contributors, ODbL."""
import json
import math
from pathlib import Path

D = json.loads((Path(__file__).parent / 'drawnmap.json').read_text())
VIEW = (-640, -720, 1240, 1500)   # x, y, w, h in map units (1 unit = 1/11 km)
FONT = 'font-family="Inter,sans-serif"'


def f(v):
    return str(round(v))   # 1 unit is 90 m: whole units are finer than the eye can see on the page


def poly(pts):
    return 'M' + 'L'.join(f'{f(x)} {f(y)}' for x, y in pts) + 'Z'


def spoly(pts):
    """A closed ring as one smooth curve."""
    return smooth(list(pts) + [pts[0]]) + 'Z'


def line(pts):
    return 'M' + 'L'.join(f'{f(x)} {f(y)}' for x, y in pts)


def smooth(pts):
    if len(pts) < 2:
        return ''
    d = [f'M{f(pts[0][0])} {f(pts[0][1])}']
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f'C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}')
    return ''.join(d)


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def in_view(pts, pad=60):
    x, y, w, h = VIEW
    return any(x - pad <= p[0] <= x + w + pad and y - pad <= p[1] <= y + h + pad for p in pts)


LAND, SEA, SEA_EDGE = '#121958', '#090c30', '#28307e'
STYLE = {'sec': ('#0b0f3a', 3.4, '#2a3388', 1.8), 'pri': ('#0b0f3a', 6.5, '#3b46aa', 3.6), 'exp': ('#0b0f3a', 10, '#6a74d4', 5.4)}
DOTS = {'1': ('#8d96d8', .16, 2.4), '2': ('#8d96d8', .26, 2.8), '3': ('#b3b9ea', .38, 3.2)}
TOWN_LABELS = ['Quezon City', 'Valenzuela', 'Calamba', 'Meycauayan', 'Cavite City']
DROP_DY = {'Sampaloc': -22, 'Port Area': 4}
LEFT = {'Port Area', 'Malolos', 'San Fernando', 'Dasmariñas', 'Tagaytay', 'Pasay', 'Sampaloc'}


def base(streets=True, towns=True, water_labels=True, shields=True, traffic=True, roads=('sec', 'pri', 'exp')):
    """Land, water and roads, no trips."""
    x, y, w, h = VIEW
    o = [f'<rect x="{x - 900}" y="{y - 900}" width="{w + 1800}" height="{h + 1800}" fill="{LAND}"/>']
    water = spoly(D['sea']) + ''.join(spoly(l['pts']) for l in D['lakes'])
    land = ''.join(spoly(r) for r in D['islands'])
    if streets and D.get('dots'):
        for tier, (col, op, r) in DOTS.items():
            ds = ''.join(f'M{x} {y}h0' for x, y in D['dots'][tier])
            o.append(f'<path d="{ds}" stroke="{col}" stroke-opacity="{op}" stroke-width="{r}" stroke-linecap="round"/>')
    o.append(f'<defs><clipPath id="wclip"><path d="{water}" clip-rule="evenodd"/></clipPath><path id="wat" d="{water}"/></defs>')
    o.append(f'<use href="#wat" fill="{SEA}" fill-rule="evenodd"/>')
    o.append(f'<g clip-path="url(#wclip)" fill="none">'      # water lining: thin lines following the shore, the old chart way
             f'<use href="#wat" stroke="{SEA_EDGE}" stroke-width="22" stroke-opacity=".16"/>'
             f'<use href="#wat" stroke="{SEA}" stroke-width="16"/>'
             f'<use href="#wat" stroke="{SEA_EDGE}" stroke-width="10" stroke-opacity=".3"/>'
             f'<use href="#wat" stroke="{SEA}" stroke-width="6"/></g>')
    o.append(f'<use href="#wat" fill="none" stroke="#3a44a6" stroke-width="2"/>')
    if land:
        o.append(f'<path d="{land}" fill="{LAND}" stroke="#3a44a6" stroke-width="1.6"/>')
    if water_labels:
        o.append(f'<text x="-330" y="40" font-size="22" font-style="italic" fill="#4a54a8" {FONT} letter-spacing=".1em">Manila Bay</text>')
        o.append(f'<text x="170" y="250" font-size="20" font-style="italic" fill="#4a54a8" {FONT} letter-spacing=".1em">Laguna de Bay</text>')
        o.append(f'<text x="-150" y="700" font-size="16" font-style="italic" fill="#4a54a8" {FONT} letter-spacing=".1em">Taal Lake</text>')
    for kind in roads:
        cas, cw, core, wd = STYLE[kind]
        ds = ''.join(smooth(p) for p in D['roads'][kind] if in_view(p))
        if not ds:
            continue
        o.append(f'<defs><path id="rd-{kind}" d="{ds}"/></defs><g fill="none" stroke-linecap="round" stroke-linejoin="round">'
                 f'<use href="#rd-{kind}" stroke="{cas}" stroke-width="{cw}"/><use href="#rd-{kind}" stroke="{core}" stroke-width="{wd}"/></g>')
    if traffic:
        ds = ''.join(smooth(p) for p in D['roads']['exp'] if in_view(p) and plen(p) > 40)
        o.append(f'<path class="trf" d="{ds}" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="1.8" stroke-linecap="round" stroke-dasharray="1 15"/>')
    if shields:
        for s in D['shields']:
            (sx, sy), t = s['p'], s['t']
            wd = 9 * len(t) + 10
            o.append(f'<g class="lbl" data-x="{sx}" data-y="{sy}" transform="translate({sx} {sy})"><rect x="{-wd / 2}" y="-10" width="{wd}" height="20" rx="5" fill="#0b0f3a" stroke="#6b75d0" stroke-width="1.4"/>'
                     f'<text y="4.5" font-size="11.5" font-weight="700" fill="#c8ccf0" text-anchor="middle" {FONT}>{t}</text></g>')
    if towns:
        for t in TOWN_LABELS:
            tx, ty = D['towns'][t]
            o.append(f'<text class="twn" x="{tx}" y="{ty}" font-size="17" font-weight="600" fill="#7d86cc" text-anchor="middle" {FONT}>{t}</text>')
    return ''.join(o)


def trip_lines(op=.62, width=3.4, only=None):
    o = []
    for t in D['trips']:
        if only and t['from'] not in only:
            continue
        d = smooth(t['pts'])
        o.append(f'<path class="trip g-{key(t["from"])}" d="{d}" fill="none" stroke="#0b0f3a" stroke-width="{width + 3}" stroke-linecap="round" stroke-opacity=".7"/>'
                 f'<path class="trip g-{key(t["from"])}" d="{d}" fill="none" stroke="#e8b800" stroke-opacity="{op}" stroke-width="{width}" stroke-linecap="round"/>')
    return ''.join(o)


def key(name):
    return name.lower().replace('. ', '').replace(' ', '')


def drops(labels=True, only=None):
    o = []
    for t in D['trips']:
        if only and t['from'] not in only:
            continue
        ex, ey = t['pts'][-1]
        dest = t['to']
        lx, anc = (-12, 'end') if dest in LEFT else (12, 'start')
        lab = (f'<text x="{lx}" y="{DROP_DY.get(dest, -9)}" text-anchor="{anc}" font-size="15" font-weight="600" fill="#e6e8f7" {FONT}>{dest}</text>' if labels else '')
        o.append(f'<g class="drop g-{key(t["from"])}" transform="translate({ex} {ey})"><circle r="7" fill="#0b0f3a" stroke="#e8b800" stroke-width="2.4"/><circle r="2.4" fill="#e8b800"/>{lab}</g>')
    return ''.join(o)


def trucks(speed=16, only=None, hold=.12):
    """One truck per trip, out and back, holding at the drop."""
    o = []
    for i, t in enumerate(D['trips']):
        if only and t['from'] not in only:
            continue
        d = smooth(t['pts'])
        L = plen(t['pts'])
        dur = max(10, 2 * L / speed + 3)
        begin = -((i * 2.9) % dur)
        o.append(f'<g class="trk g-{key(t["from"])}"><rect x="-7" y="-4.5" width="14" height="9" rx="2" fill="#fff"/><rect x="3.5" y="-4.5" width="4.5" height="9" rx="1.4" fill="#e8b800"/>'
                 f'<animateMotion dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite" path="{d}" rotate="auto" '
                 f'keyPoints="0;0;1;1;0" keyTimes="0;.05;{.5 - hold / 2:.2f};{.5 + hold / 2:.2f};1" calcMode="linear"/></g>')
    return ''.join(o)


def garages(size=1.0, labels=True):
    o = []
    for nm, (x, y) in D['garages'].items():
        r = 15 * size
        lab = (f'<text x="{x + 22 * size}" y="{y + 6 * size}" font-size="{24 * size:.0f}" font-weight="800" fill="#fff" {FONT} paint-order="stroke" stroke="#0f1445" stroke-width="4">{nm}</text>' if labels else '')
        o.append(f'<g class="gar g-{key(nm)}"><circle cx="{x}" cy="{y}" r="{58 * size}" fill="url(#gglow)"/><circle cx="{x}" cy="{y}" r="{r}" fill="#0f1445" stroke="#e8b800" stroke-width="3"/>'
                 f'<path d="M{x - 7 * size} {y + 5 * size}V{y - 1 * size}L{x} {y - 7 * size}L{x + 7 * size} {y - 1 * size}V{y + 5 * size}Z" fill="#e8b800"/>{lab}</g>')
    return ''.join(o)


DEFS = ('<defs><radialGradient id="gglow"><stop offset="0" stop-color="#e8b800" stop-opacity=".42"/><stop offset="1" stop-color="#e8b800" stop-opacity="0"/></radialGradient></defs>')


def svg(inner, cls='map', view=None):
    x, y, w, h = view or VIEW
    return f'<svg class="{cls}" viewBox="{x} {y} {w} {h}" width="{w}" height="{h}" overflow="visible" aria-hidden="true">{DEFS}{inner}</svg>'


def full(**kw):
    return svg(base(**kw) + trip_lines() + drops() + trucks() + garages())

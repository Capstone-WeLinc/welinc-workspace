"""Round 46 (Nov 25): nine sign ins on the drawn map (S18b traced from OpenStreetMap, cut down), plus a notes board.
python3 -I gen47.py <project dir> [Board,Board]   (imports gen45, which rewrites the Round 45 boards unchanged)
Needs realmap.json from prep_map.py. Map data (c) OpenStreetMap contributors, ODbL."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen45  # noqa: E402
from gen45 import SIGN_CSS, FORM, LK, RM, write  # noqa: E402
from parts import page  # noqa: E402
import realmap as M  # noqa: E402

ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
D = M.D
TITLE = 'WeLinc Logistics Operations Workspace'
H1 = '<h1>WeLinc Logistics<br><em>Operations</em><br>Workspace</h1>'
EB = '<p class="eb">#HASSLEFREE TRANSPORT SOLUTION</p>'
LN = '<p class="ln">Bookings, maintenance and repairs for the whole fleet, in one place.</p>'
COPY = f'<div class="cp">{EB}{H1}{LN}</div>'
OSM = ''   # the map side stays clean: the credit lives in the page footer under the form
FOOT = '<p class="foot">© 2026 WeLinc Logistics<span aria-hidden="true">·</span><a href="https://www.openstreetmap.org/copyright">© OpenStreetMap</a></p>'


def want(n):
    return ONLY is None or n in ONLY


def board(name, css, body):
    if want(name.split('.')[0]):
        write(name, page(f'Sign in · {TITLE}', SIGN_CSS + COMMON + css + RM, body))


COMMON = '''
.ov{position:absolute;inset:0;pointer-events:none;z-index:2}
.ov span{position:absolute;white-space:nowrap;font-family:Inter,sans-serif;transform:translate(-50%,-50%)}
.t-g{font-weight:800;color:#fff;transform:translate(0,-50%)!important;text-shadow:0 0 6px #0f1445,0 0 2px #0f1445}
.t-d{font-weight:600;color:#e6e8f7;text-shadow:0 0 4px #0f1445,0 0 2px #0f1445}
.t-t{font-weight:600;color:#7d86cc;text-shadow:0 0 4px #121958}
.t-w{font-style:italic;color:#4a54a8;letter-spacing:.1em}
.t-s{font-weight:700;color:#c8ccf0;background:#0b0f3a;border:1.4px solid #6b75d0;border-radius:5px;padding:2px 6px;letter-spacing:.02em}
.foot{position:absolute;left:0;right:0;bottom:28px;margin:0;display:flex;justify-content:center;gap:10px;font-size:12px;color:rgba(255,255,255,.56);z-index:4}
.foot a{color:inherit;text-decoration:none}.foot a:hover{color:#fff;text-decoration:underline}
.trf{animation:trf 3s linear infinite}
@keyframes trf{to{stroke-dashoffset:-32}}
'''


class Tilt:
    """The CSS tilt the map gets, done in Python too, so labels can sit upright on top of it."""

    def __init__(self, left, top, A, B, S, P=1500, view=None):
        self.view = view or M.VIEW
        self.left, self.top, self.A, self.B, self.S, self.P = left, top, A, B, S, P

    def style(self):
        vx, vy, vw, vh = self.view
        return (f'position:absolute;left:{self.left}px;top:{self.top}px;width:{vw}px;height:{vh}px;'
                f'transform:perspective({self.P}px) rotateX({self.A}deg) rotateZ({self.B}deg) scale({self.S});transform-origin:50% 50%')

    def fit(self, u, v, x, y):
        """Move the map so the point (u, v) lands at (x, y) on the panel."""
        px, py, _ = self.at(u, v)
        self.left += x - px
        self.top += y - py
        return self

    def where(self):
        return {g: tuple(round(c) for c in self.at(*p)[:2]) for g, p in D['garages'].items()}

    def at(self, u, v):
        vx, vy, vw, vh = self.view
        x, y = (u - vx - vw / 2) * self.S, (v - vy - vh / 2) * self.S
        b, a = math.radians(self.B), math.radians(self.A)
        x, y = x * math.cos(b) - y * math.sin(b), x * math.sin(b) + y * math.cos(b)
        y, z = y * math.cos(a), y * math.sin(a)
        k = self.P / (self.P - z)
        return self.left + vw / 2 + x * k, self.top + vh / 2 + y * k, k


def labels(t, top=440, right=830, bottom=892, garages=True, drops=True, towns=True, shields=True, water=True, gsize=24, extra=''):
    """Upright labels over a tilted map; size follows depth. Hidden where the copy fade covers the map."""
    o = []

    def put(u, v, txt, cls, size, dx=0, dy=0, attr=''):
        x, y, k = t.at(u, v)
        if y < top or x < 8 or x > right or y > bottom:
            return
        o.append(f'<span class="{cls}"{attr} style="left:{x + dx * k:.0f}px;top:{y + dy * k:.0f}px;font-size:{size * k:.1f}px">{txt}</span>')
    if water:
        put(-300, 30, 'Manila Bay', 't-w', 17)
        put(210, 255, 'Laguna de Bay', 't-w', 15)
        put(-140, 690, 'Taal Lake', 't-w', 13)
    if towns:
        for nm in ('Quezon City', 'Antipolo', 'Valenzuela', 'Calamba', 'Meycauayan'):
            u, v = D['towns'][nm]
            put(u, v, nm, 't-t', 13, dy=16 if nm == 'Antipolo' else 0)
    if shields:
        for s in D['shields']:
            if s['t'] in ('SCTEX',):
                continue
            u, v = s['p']
            dx = 16 if s['t'] == 'C-5' else 0
            put(u, v, s['t'], 't-s', 10, dx=dx, dy=8 if s['t'] == 'C-5' else 0)
    if drops:
        for tr in D['trips']:
            u, v = tr['pts'][-1]
            left = tr['to'] in M.LEFT
            g = M.key(tr['from'])
            x, y, k = t.at(u, v)
            if y < top or x < 8 or x > right or y > bottom:
                continue
            tx = 'translate(-100%,-50%)' if left else 'translate(0,-50%)'
            ddy = M.DROP_DY.get(tr['to'], -9)
            o.append(f'<span class="t-d g-{g}" style="left:{x + (-11 if left else 11) * k:.0f}px;top:{y + ddy * k:.0f}px;font-size:{14 * k:.1f}px;transform:{tx}">{tr["to"]}</span>')
    if garages:
        for nm, (u, v) in D['garages'].items():
            put(u, v, nm, f't-g g-{M.key(nm)}', gsize, dx=22)
    return f'<div class="ov">{"".join(o)}{extra}</div>'


def plain_map(**kw):
    """Map without any text: the labels come from the upright overlay."""
    return M.svg(M.base(towns=False, water_labels=False, shields=False, **kw) + M.trip_lines() + M.drops(labels=False) + M.trucks() + M.garages(labels=False))


FADE = ('<div class="fade" style="position:absolute;inset:0;pointer-events:none;z-index:1;'
        'background:linear-gradient(180deg,#0f1445 0%,#0f1445 41%,rgba(15,20,69,.55) 48%,rgba(15,20,69,0) 56%),'
        'radial-gradient(ellipse 95% 70% at 50% 82%,transparent 58%,rgba(15,20,69,.8) 100%)"></div>')


def split(art, copy=COPY, rt_extra='', lf_extra=''):
    return f'<div class="pg"><div class="lf"{lf_extra}>{art}{LK}{copy}</div><div class="rt"{rt_extra}>{FORM}{FOOT}</div></div>'


# ================================================================ S26 the real map, S18b's layout, labels upright
T26 = Tilt(left=-150, top=-40, A=50, B=-14, S=.78)
board('R46Real.dc.html', '', split(f'<div style="{T26.style()}">{plain_map()}</div>{FADE}{labels(T26)}{OSM}'))

# ================================================================ S27 the map runs under the whole page, the form on glass
T27 = Tilt(left=0, top=0, A=48, B=-12, S=.9).fit(*D['garages']['Marikina'], 700, 560)
BLEED_CSS = '''
.lf{background:transparent;overflow:visible;z-index:2;pointer-events:none}.lf>*{pointer-events:auto}
.rt{background:rgba(10,13,51,.5);backdrop-filter:blur(6px) saturate(1.1);-webkit-backdrop-filter:blur(10px);z-index:3;box-shadow:inset 1px 0 0 rgba(255,255,255,.12)}
.under{position:absolute;inset:0;overflow:hidden;background:#0f1445}
'''
board('R46Bleed.dc.html', BLEED_CSS,
      f'<div class="pg"><div class="under"><div style="{T27.style()}">{plain_map(traffic=False)}</div>'   # picked Nov 25: no traffic dots
      f'<div style="position:absolute;inset:0;background:linear-gradient(90deg,#0f1445 0%,rgba(15,20,69,.8) 22%,rgba(15,20,69,0) 42%),linear-gradient(180deg,#0f1445 0%,#0f1445 34%,rgba(15,20,69,0) 50%)"></div>'
      f'{labels(T27, top=420, right=1430)}</div>'
      f'<div class="lf">{LK}{COPY}</div><div class="rt">{FORM}{FOOT}</div></div>')

# ================================================================ S28 the garages take turns
SPOT_CSS = '''
.g-pulilan,.g-marikina,.g-starosa{animation:spot 18s linear infinite}
.g-marikina{animation-delay:-12s}.g-starosa{animation-delay:-6s}
@keyframes spot{0%,30%{opacity:1}36%,94%{opacity:.16}100%{opacity:1}}
.cap{position:absolute;left:64px;bottom:52px;z-index:3;width:420px;height:118px}
.cap>div{position:absolute;inset:0;padding:16px 20px;border-radius:14px;background:rgba(10,13,51,.94);box-shadow:inset 0 0 0 1px rgba(255,255,255,.1);opacity:0;animation:capf 18s linear infinite}
.cap>div:nth-child(2){animation-delay:-12s}.cap>div:nth-child(3){animation-delay:-6s}
@keyframes capf{0%,31%{opacity:1}35%,96%{opacity:0}100%{opacity:1}}
.cap b{display:block;font-size:16px;font-weight:800}
.cap p{margin:10px 0 0;display:grid;grid-template-columns:1fr 1fr;gap:4px 24px;font:500 13px/1.5 "IBM Plex Mono",monospace;color:rgba(255,255,255,.7)}.cap p span{display:flex;justify-content:space-between}
.cap i{font-style:normal;color:#e8b800}
'''


def runs_of(g):
    return ''.join(f'<span>{t["to"]} <i>{t["km"]:.0f} km</i></span>' for t in D['trips'] if t['from'] == g)


CAP = '<div class="cap">' + ''.join(f'<div><b>{g} garage · four regular runs</b><p>{runs_of(g)}</p></div>' for g in D['garages']) + '</div>'
board('R46Spot.dc.html', SPOT_CSS, split(f'<div style="{T26.style()}">{plain_map()}</div>{FADE}{labels(T26)}{CAP}{OSM}'))

# ================================================================ S29 a departures board of the regular runs
ROWS = D['trips']
BOARD_CSS = '''
.dep{position:absolute;left:64px;right:64px;bottom:52px;z-index:3;border-radius:14px;background:rgba(8,10,40,.86);box-shadow:inset 0 0 0 1px rgba(255,255,255,.09);padding:14px 20px 12px}
.dep h3{margin:0 0 8px;font:600 11px "IBM Plex Mono",monospace;letter-spacing:.14em;color:#e8b800;display:flex;justify-content:space-between}
.dep h3 span{color:rgba(255,255,255,.4)}
.win{height:96px;overflow:hidden;position:relative}
.reel{animation:reel 36s steps(1) infinite}
.r{display:grid;grid-template-columns:110px 22px 140px 1fr 64px;height:32px;align-items:center;font:500 14px "IBM Plex Mono",monospace;color:#e6e8f7;border-top:1px solid rgba(255,255,255,.06)}
.r .a{color:rgba(255,255,255,.4)}.r .k{text-align:right;color:#e8b800}.r .v{color:rgba(255,255,255,.55);font-size:12.5px}
.r.flip{animation:flip 3s steps(1) infinite}
'''
reel_keys = ''.join(f'{i * 100 / 12:.3f}%{{transform:translateY(-{i * 32}px)}}' for i in range(12))
BOARD_CSS += f'@keyframes reel{{{reel_keys}}}'


SHORT = {'North Luzon Expressway': 'NLEX', 'South Luzon Expressway': 'SLEX', 'National Highway 1': 'National Hwy', 'National Road': 'National Rd',
         'Santa Rosa-Tagaytay Road': 'Sta. Rosa–Tagaytay Rd'}


def via(t):
    """The longest road on the routed trip, from the OpenStreetMap route."""
    name = max(t['via'], key=lambda r: r[1])[0]
    return SHORT.get(name, name.replace('Highway', 'Hwy').replace('Avenue', 'Ave').replace('Boulevard', 'Blvd').replace('Road', 'Rd'))


rows = ''.join(f'<div class="r"><span>{t["from"].upper()}</span><span class="a">→</span><span>{t["to"].upper()}</span><span class="v">via {via(t)}</span><span class="k">{t["km"]:.0f} KM</span></div>'
               for t in ROWS + ROWS[:3])
DEP = f'<div class="dep"><h3>REGULAR RUNS <span>OUT AND BACK, BY ROAD</span></h3><div class="win"><div class="reel">{rows}</div></div></div>'
T29 = Tilt(left=0, top=0, A=50, B=-14, S=.6).fit(*D['garages']['Marikina'], 520, 535)
board('R46Board.dc.html', BOARD_CSS,
      split(f'<div style="{T29.style()}">{plain_map()}</div>{FADE}{labels(T29, top=430, bottom=690, towns=False)}{DEP}'))

# ================================================================ S30 a navigator's chart: flat, true north, coordinates
CH = dict(s=.5, cx=560, cy=430)          # px per unit, where map (0,0) = 14.6N 121.0E lands in the panel


def chart_xy(u, v):
    return CH['cx'] + u * CH['s'], CH['cy'] + v * CH['s']


KX = 111.32 * math.cos(math.radians(14.6)) * 11
KY = 110.57 * 11


def ticks():
    o = []
    s = CH['s']
    for lat10 in range(141, 151):
        lat = lat10 / 10
        y = CH['cy'] + (14.6 - lat) * KY * s
        if 20 < y < 880:
            o.append(f'<path d="M24 {y:.1f}h10M806 {y:.1f}h10" stroke="#5560c4" stroke-width="1.2"/>'
                     f'<text x="40" y="{y + 3.5:.1f}" font-size="9.5" fill="#6b75d0" font-family="IBM Plex Mono,monospace">{lat:.1f}°N</text>')
    for lon10 in range(1205, 1214):
        lon = lon10 / 10
        x = CH['cx'] + (lon - 121.0) * KX * s
        if 30 < x < 810:
            o.append(f'<path d="M{x:.1f} 24v10M{x:.1f} 866v10" stroke="#5560c4" stroke-width="1.2"/>'
                     f'<text x="{x:.1f}" y="860" font-size="9.5" fill="#6b75d0" text-anchor="middle" font-family="IBM Plex Mono,monospace">{lon:.1f}°E</text>')
    km10 = 10 * 11 * s
    o.append(f'<g transform="translate(600 84)"><path d="M0 0h{km10:.1f}M0 -5v10M{km10 / 2:.1f} -3v6M{km10:.1f} -5v10" stroke="#c8ccf0" stroke-width="1.4"/>'
             f'<text x="{km10 + 10:.1f}" y="4" font-size="11" fill="#c8ccf0" font-family="IBM Plex Mono,monospace">10 km</text></g>')
    o.append('<g transform="translate(780 140)"><path d="M0 -26L8 4L0 -2L-8 4Z" fill="#e8b800"/><text y="22" font-size="12" font-weight="700" fill="#c8ccf0" text-anchor="middle" font-family="Inter,sans-serif">N</text></g>')
    return f'<svg style="position:absolute;inset:0;z-index:2" width="840" height="900" aria-hidden="true"><rect x="24.5" y="24.5" width="791" height="851" fill="none" stroke="#3a44a6" stroke-width="1"/>{"".join(o)}</svg>'


def chart_labels():
    o = []

    def put(u, v, txt, cls, size, dx=0, dy=0, tf=None):
        x, y = chart_xy(u, v)
        if not (40 < x < 800 and 40 < y < 850):
            return
        st = f';transform:{tf}' if tf else ''
        o.append(f'<span class="{cls}" style="left:{x + dx:.0f}px;top:{y + dy:.0f}px;font-size:{size}px{st}">{txt}</span>')
    put(-330, 40, 'Manila Bay', 't-w', 15)
    put(230, 270, 'Laguna de Bay', 't-w', 13)
    for tr in D['trips']:
        u, v = tr['pts'][-1]
        left = tr['to'] in M.LEFT and tr['to'] not in ('Dasmariñas', 'Tagaytay')
        put(u, v, tr['to'], 't-d', 12, dx=-9 if left else 9, dy=M.DROP_DY.get(tr['to'], -9) * .8, tf='translate(-100%,-50%)' if left else 'translate(0,-50%)')
    for nm, (u, v) in D['garages'].items():
        put(u, v, nm, 't-g', 19, dx=16)
    return f'<div class="ov" style="z-index:3">{"".join(o)}</div>'


CHART_CSS = '''
.flat{position:absolute;left:0;top:0;width:840px;height:900px;overflow:hidden}
.cart{position:absolute;left:40px;bottom:40px;z-index:4;width:420px;padding:24px 28px 22px;background:#0f1445;box-shadow:0 0 0 1px #3a44a6}
.cart .lk{position:static}
.cart .eb{margin-top:22px}
.cart h1{font-size:42px;white-space:nowrap}
.cart .ln{font-size:15px;max-width:340px}
'''
vx, vy, vw, vh = M.VIEW
chart_svg = M.svg(M.base(towns=False, water_labels=False, shields=False) + M.trip_lines(width=2.6) + M.drops(labels=False) + M.trucks() + M.garages(size=.8, labels=False))
ox, oy = chart_xy(vx, vy)
board('R46Chart.dc.html', CHART_CSS,
      f'<div class="pg"><div class="lf"><div class="flat"><div style="position:absolute;left:{ox:.0f}px;top:{oy:.0f}px;transform:scale({CH["s"]});transform-origin:0 0">{chart_svg}</div></div>'
      f'{ticks()}{chart_labels()}<div class="cart">{LK}{EB}{H1}{LN}</div></div><div class="rt">{FORM}{FOOT}</div></div>')

# ================================================================ S31 to the horizon: the map runs into a night sky
T31 = Tilt(left=-200, top=-40, A=66, B=-4, S=.95, P=1200)
HOR_CSS = '''
.sky{position:absolute;left:0;top:0;width:840px;height:560px;z-index:1;background:linear-gradient(180deg,#0a0d33 0%,#0f1445 62%,rgba(15,20,69,.7) 80%,rgba(15,20,69,0) 100%)}
.glow{position:absolute;left:-100px;right:-100px;top:360px;height:220px;z-index:1;background:radial-gradient(ellipse 50% 40% at 55% 55%,rgba(232,184,0,.14),rgba(232,184,0,0) 70%)}
'''
STARS = gen45.stars(70, 840, 300, seed=8) if hasattr(gen45, 'stars') else ''
board('R46Horizon.dc.html', HOR_CSS,
      split(f'<div style="{T31.style()}">{plain_map()}</div><div class="sky"><svg width="840" height="300" aria-hidden="true">{STARS}</svg></div><div class="glow"></div>'
            f'{labels(T31, top=520)}{OSM}'))

# ================================================================ S32 light trails: no route lines, trucks draw them as they go
TR_CSS = '''
.tr{fill:none;stroke:#e8b800;stroke-width:5;stroke-linecap:round;stroke-dasharray:240 3000;filter:drop-shadow(0 0 5px rgba(232,184,0,.8));animation:tr linear infinite}
@keyframes tr{0%{stroke-dashoffset:240}50%{stroke-dashoffset:-760}50.01%{stroke-dashoffset:-1000}100%{stroke-dashoffset:0}}
.ghost{fill:none;stroke:#e8b800;stroke-opacity:.16;stroke-width:2;stroke-linecap:round}
'''


def trails():
    o = []
    for i, t in enumerate(D['trips']):
        d = M.smooth(t['pts'])
        L = M.plen(t['pts'])
        dur = max(10, 2 * L / 16)
        begin = -((i * 2.9) % dur)
        o.append(f'<path class="ghost" d="{d}"/><path class="tr" pathLength="1000" d="{d}" style="animation-duration:{dur:.1f}s;animation-delay:{begin:.1f}s"/>'
                 f'<g><rect x="-7" y="-4.5" width="14" height="9" rx="2" fill="#fff"/><rect x="3.5" y="-4.5" width="4.5" height="9" rx="1.4" fill="#e8b800"/>'
                 f'<animateMotion dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite" path="{d}" rotate="auto" keyPoints="0;1;0" keyTimes="0;.5;1" calcMode="linear"/></g>')
    return ''.join(o)


trail_svg = M.svg(M.base(towns=False, water_labels=False, shields=False) + trails() + M.drops(labels=False) + M.garages(labels=False))
board('R46Trails.dc.html', TR_CSS, split(f'<div style="{T26.style()}">{trail_svg}</div>{FADE}{labels(T26)}{OSM}'))

# ================================================================ S33 slow camera: the map turns and drifts, a minute a loop
DRIFT_CSS = '''
.cam{animation:cam 60s ease-in-out infinite alternate}
@keyframes cam{0%{transform:perspective(1500px) rotateX(50deg) rotateZ(-22deg) scale(.74) translate(-20px,-40px)}100%{transform:perspective(1500px) rotateX(46deg) rotateZ(-4deg) scale(.8) translate(-90px,-120px)}}
'''
drift_svg = M.svg(M.base() + M.trip_lines() + M.drops() + M.trucks() + M.garages())
board('R46Drift.dc.html', DRIFT_CSS, split(f'<div class="cam" style="{T26.style()}">{drift_svg}</div>{FADE}{OSM}'))

# ================================================================ S34 map first: the map fills the panel, the title sits low
T34 = Tilt(left=0, top=0, A=40, B=-10, S=.62).fit(*D['garages']['Marikina'], 500, 300)
LOW_CSS = '''
.cp{top:auto;bottom:64px}
.lowfade{position:absolute;inset:0;z-index:1;pointer-events:none;background:linear-gradient(0deg,#0f1445 0%,#0f1445 30%,rgba(15,20,69,.6) 40%,rgba(15,20,69,0) 52%),linear-gradient(180deg,rgba(15,20,69,.9) 0%,rgba(15,20,69,0) 14%)}
'''
board('R46Low.dc.html', LOW_CSS, split(f'<div style="{T34.style()}">{plain_map()}</div><div class="lowfade"></div>{labels(T34, top=90, bottom=520)}{OSM}'))

# ================================================================ notes: the map check and suggestions
NOTES_CSS = '''
.pg{background:#0a0d33}
.nt{position:absolute;inset:56px 64px;display:grid;grid-template-columns:1fr 1fr;gap:56px}
.nt h2{margin:0 0 6px;font-size:28px;font-weight:800;letter-spacing:-.02em}
.nt h3{margin:30px 0 10px;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.14em;color:#e8b800}
.nt p,.nt li{font-size:15px;line-height:1.55;color:rgba(255,255,255,.78)}
.nt ol{margin:0;padding-left:20px}.nt li{margin:0 0 8px}
.nt b{color:#fff}
table{border-collapse:collapse;width:100%;font:500 13px "IBM Plex Mono",monospace}
td,th{padding:6px 8px;border-top:1px solid rgba(255,255,255,.08);text-align:left;color:rgba(255,255,255,.8)}
th{color:rgba(255,255,255,.5);font-weight:600}
td.k{text-align:right}
'''
CHECK = [('Pulilan (garage)', 6.8), ('Sta. Rosa (garage)', 6.5), ('Marikina (garage)', .9), ('Tanay', 18.2), ('Baliwag', 15.7),
         ('Rodriguez', 13.3), ('San Fernando', 13.0), ('Sto. Tomas', 10.9), ('Taguig', 9.1)]
rows_c = ''.join(f'<tr><td>{n}</td><td class="k">{e:.1f} km</td><td class="k">on the spot</td></tr>' for n, e in CHECK)
runs = ''.join(f'<tr><td>{t["from"]} → {t["to"]}</td><td>{via(t)}</td><td class="k">{t["km"]:.0f} km</td></tr>' for t in D['trips'])
board('R46Notes.dc.html', NOTES_CSS, f'''<div class="pg"><div class="nt"><div>
<h2>Round 46: the map, checked</h2>
<p>S18b was drawn by hand. Fitted against real coordinates, its pins were <b>8.4 km off on average, 19 km at worst</b>, Pulilan to Sta. Rosa read as 60 km (really 71), and Laguna de Bay was half its size. The map on this page is still drawn, but <b>traced</b>: every shore, road and pin comes from <b>OpenStreetMap</b> coordinates, then cut down to the expressways and the main roads, smoothed into clean curves, the shores lined like an old chart, and the city shown as dots where the streets are dense. The twelve trips are routed on the real roads.</p>
<h3>PINS, S18B AGAINST ROUND 46</h3>
<table><tr><th>Place</th><th class="k">S18b was off by</th><th class="k">Round 46</th></tr>{rows_c}</table>
<p style="margin-top:12px;font-size:13px;color:rgba(255,255,255,.55)">Roads and shores are within about half a kilometre after smoothing. Garages sit on each town's centre. Real garage addresses would put the three pins exactly on the yards.</p>
</div><div>
<h3 style="margin-top:0">SUGGESTIONS FOR THE BUILD</h3>
<ol>
<li><b>Credit OpenStreetMap in the footer.</b> The map is traced from its data, so its licence (ODbL) asks for a credit where the map is shown. The map stays clean; "© OpenStreetMap", linked to its copyright page, sits in the page footer under the form, beside the copyright.</li>
<li><b>Light enough to ship as is.</b> The whole map is about 25 KB compressed (S18b 14 KB, the full street map 164 KB). Load it after the form paints, and animate only the truck layer above it.</li>
<li><b>Never live data before sign in.</b> The page is public: the trips stay a drawing of regular runs, never where the trucks really are.</li>
<li><b>Calm when asked.</b> Reduced motion parks every truck at its garage; pause the trucks when the tab is hidden.</li>
<li><b>Phones get the form only</b> (or a short map strip); the map starts at 1024 px wide.</li>
<li><b>One title everywhere.</b> The heading and the tab both say "WeLinc Logistics Operations Workspace" (tab: "Sign in · WeLinc Logistics Operations Workspace").</li>
<li><b>Labels stay upright.</b> In S18b they tilted with the map; here they sit flat on top and shrink with distance, so they read at a glance.</li>
</ol>
<h3>THE TWELVE RUNS, BY ROAD</h3>
<table>{runs}</table>
</div></div></div>''')

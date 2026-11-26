"""Round 45, second pass (Nov 25): S18b the road map, plus six more dark split sign ins (S20 to S25).
python3 -I gen46.py <project dir>   (imports gen45, which rewrites the Round 45 boards into the same folder, unchanged)"""
import math
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen45  # noqa: E402  (writes the Round 45 boards again, same output)
from gen45 import sign, stars, skyline, LOGO_POLY  # noqa: E402
from parts import V_VAN  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None


def want(n):
    return ONLY is None or n in ONLY


def f(v):
    return f'{v:.1f}'.rstrip('0').rstrip('.')


def smooth(pts):
    """Catmull-Rom through the points, as one cubic path."""
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


# ================================================================ S18b: the road map, tilted
G1, G2, G3 = (322, 108), (540, 400), (452, 768)   # Pulilan, Marikina, Sta. Rosa

BAY = [(-300, 300), (60, 305), (150, 318), (220, 338), (270, 365), (305, 400), (322, 440), (332, 478), (330, 530), (322, 575),
       (300, 610), (258, 636), (215, 648), (175, 640), (140, 662), (110, 705), (60, 730), (-300, 760)]
LAKE = [(478, 610), (510, 595), (545, 612), (575, 590), (610, 600), (650, 585), (690, 610), (730, 598), (775, 620), (800, 665),
        (785, 720), (740, 745), (705, 790), (660, 815), (615, 800), (575, 775), (540, 760), (505, 740), (490, 700), (482, 660)]
RIVER = [(330, 478), (380, 486), (420, 500), (455, 522), (478, 560), (486, 602)]

R = {
    'NLEX': ('exp', [(40, -90), (110, 10), (190, 70), (270, 105), (305, 125), (330, 170), (348, 230), (365, 290), (380, 335), (395, 370)]),
    'SLEX': ('exp', [(372, 572), (398, 600), (418, 640), (426, 690), (430, 740), (434, 785), (452, 822), (490, 852), (530, 880), (560, 940), (590, 1100)]),
    'EDSA': ('pri', [(395, 370), (430, 392), (462, 420), (480, 460), (478, 500), (458, 535), (418, 558), (372, 572), (330, 572)]),
    'C5': ('pri', [(472, 320), (490, 372), (502, 428), (500, 480), (492, 530), (482, 582), (466, 628)]),
    'MARCOS': ('pri', [(502, 428), (522, 420), (570, 414), (620, 424), (670, 434), (730, 420), (800, 400), (900, 388), (1100, 380)]),
    'MACARTHUR': ('pri', [(120, -90), (130, -10), (170, 60), (215, 120), (250, 170), (280, 230), (310, 300), (335, 360), (350, 410), (352, 450)]),
    'COMMONWEALTH': ('pri', [(430, 392), (452, 345), (478, 298), (508, 250), (540, 205), (560, 120)]),
    'AURORA': ('pri', [(502, 428), (462, 438), (420, 446), (380, 452), (352, 450), (336, 462)]),
    'C3': ('sec', [(395, 370), (375, 410), (352, 450)]),
    'CAVITEX': ('pri', [(330, 572), (312, 604), (272, 640), (228, 656), (160, 690)]),
    'AGUINALDO': ('pri', [(434, 785), (385, 808), (335, 842), (305, 900), (292, 960), (285, 1100)]),
    'PLARIDEL': ('pri', [(305, 125), (322, 108), (370, 92), (430, 72), (520, 45), (610, -20), (700, -90)]),
    'MALOLOS': ('sec', [(215, 120), (260, 118), (305, 125)]),
    'MKN': ('sec', [(540, 400), (548, 350), (553, 290), (562, 220), (575, 150), (600, 40)]),
    'ORTIGAS': ('sec', [(480, 470), (540, 478), (600, 488), (660, 500)]),
    'TAYTAY': ('sec', [(600, 488), (640, 540), (700, 568), (780, 578), (860, 615), (1100, 640)]),
    'SILANG': ('sec', [(434, 785), (372, 772), (312, 764), (252, 772), (190, 790), (0, 830)]),
    'SOUTH': ('sec', [(530, 880), (600, 852), (680, 832), (760, 805), (870, 790), (1100, 780)]),
    'SJDM': ('sec', [(395, 370), (410, 300), (428, 232), (442, 160), (450, 60)]),
    'X1': ('sec', [(250, 170), (300, 190), (330, 170)]),
    'X2': ('sec', [(280, 230), (348, 230), (410, 250), (452, 345)]),
    'X3': ('sec', [(365, 290), (410, 300)]),
    'X4': ('sec', [(478, 298), (553, 290), (640, 300), (720, 280), (820, 250)]),
    'X5': ('sec', [(670, 434), (690, 500), (700, 568)]),
    'X6': ('sec', [(426, 690), (470, 702)]),
    'X7': ('sec', [(312, 764), (330, 700), (372, 640), (398, 600)]),
    'X8': ('sec', [(730, 420), (760, 300), (790, 180), (800, 40)]),
    'X9': ('sec', [(335, 842), (400, 880), (452, 822)]),
    'X10': ('sec', [(130, -10), (215, 30), (270, 105)]),
    'X11': ('sec', [(492, 530), (540, 540), (600, 488)]),
    'BAGUIO': ('sec', [(190, 70), (150, 130), (90, 180), (0, 230)]),
}

TRIPS = [  # (points, destination) out from a garage and back
    ([G1, (305, 125), (270, 105), (190, 70), (110, 10)], 'San Fernando'),
    ([G1, (305, 125), (330, 170), (348, 230), (365, 290), (380, 335), (395, 370), (375, 410), (352, 450), (336, 462)], 'Port Area'),
    ([G1, (370, 92), (430, 72), (520, 45)], 'Baliwag'),
    ([G1, (305, 125), (260, 118), (215, 120)], 'Malolos'),
    ([G2, (570, 414), (620, 424), (670, 434), (730, 420), (800, 400)], 'Tanay'),
    ([G2, (548, 350), (553, 290), (562, 220), (575, 150)], 'Rodriguez'),
    ([G2, (522, 420), (502, 428), (500, 480), (492, 530), (482, 582), (466, 628)], 'Taguig'),
    ([G2, (522, 420), (502, 428), (462, 438), (420, 446), (380, 452), (380, 452)], 'Sampaloc'),
    ([G3, (430, 740), (426, 690), (418, 640), (398, 600), (372, 572)], 'Pasay'),
    ([G3, (434, 785), (452, 822), (490, 852), (530, 880), (560, 940)], 'Sto. Tomas'),
    ([G3, (434, 785), (385, 808), (335, 842), (305, 900), (292, 960)], 'Tagaytay'),
    ([G3, (434, 785), (372, 772), (312, 764), (252, 772)], 'Dasmariñas'),
]
TOWNS = [(395, 505, 'Manila'), (450, 300, 'Quezon City'), (690, 462, 'Antipolo'), (318, 300, 'Valenzuela'), (560, 905, 'Calamba'),
         (250, 700, 'Bacoor'), (110, 52, ''), (640, 30, 'San Rafael'), (470, 610, '')]
URBAN = [(430, 470, 160), (350, 310, 70), (315, 118, 50), (220, 128, 46), (105, 25, 60), (548, 410, 58), (685, 448, 58),
         (446, 772, 62), (532, 876, 56), (300, 762, 56), (285, 690, 44), (520, 55, 40), (575, 165, 40)]


def streets(seed=11):
    r = random.Random(seed)
    out, tint = [], []
    for cx, cy, rad in URBAN:
        tint.append(f'<circle cx="{cx}" cy="{cy}" r="{rad * 1.15:.0f}" fill="url(#urb)"/>')
        base = r.uniform(0, 90)
        for ang in (base, base + 90 + r.uniform(-8, 8)):
            a = math.radians(ang)
            ux, uy = math.cos(a), math.sin(a)          # along the street
            nx, ny = -uy, ux                           # across
            sp = r.uniform(9, 13)
            k = -rad
            while k <= rad:
                half = math.sqrt(max(0, rad * rad - k * k))
                t = -half
                while t < half:
                    seg = r.uniform(14, 48)
                    t2 = min(half, t + seg)
                    if r.random() < .78:
                        x1, y1 = cx + nx * k + ux * t, cy + ny * k + uy * t
                        x2, y2 = cx + nx * k + ux * t2, cy + ny * k + uy * t2
                        out.append(f'M{x1:.0f} {y1:.0f}L{x2:.0f} {y2:.0f}')
                    t = t2 + r.uniform(0, 6)
                k += sp + r.uniform(-2, 2)
    return ''.join(tint), ''.join(out)


def road_map():
    tint, st = streets()
    o = ['<svg viewBox="-60 -100 1120 1180" width="1120" height="1180" overflow="visible" aria-hidden="true">',
         '<defs><radialGradient id="urb"><stop offset="0" stop-color="#5a64c8" stop-opacity=".18"/><stop offset="1" stop-color="#5a64c8" stop-opacity="0"/></radialGradient>'
         '<radialGradient id="gglow"><stop offset="0" stop-color="#e8b800" stop-opacity=".42"/><stop offset="1" stop-color="#e8b800" stop-opacity="0"/></radialGradient></defs>',
         '<rect x="-900" y="-700" width="2900" height="2500" fill="#121958"/>', tint,
         f'<path d="{st}" stroke="#8d96d8" stroke-opacity=".16" stroke-width="1.1" fill="none"/>']
    pts = ' '.join(f'{x},{y}' for x, y in BAY)
    o.append(f'<polygon points="{pts}" fill="#090c30" stroke="#28307e" stroke-width="2"/>')
    pts = ' '.join(f'{x},{y}' for x, y in LAKE)
    o.append(f'<polygon points="{pts}" fill="#090c30" stroke="#28307e" stroke-width="2"/>')
    o.append(f'<path d="{smooth(RIVER)}" fill="none" stroke="#090c30" stroke-width="6" stroke-linecap="round"/>')
    o.append('<text x="120" y="500" font-size="17" font-style="italic" fill="#4a54a8" font-family="Inter,sans-serif" letter-spacing=".08em">Manila Bay</text>')
    o.append('<text x="590" y="700" font-size="17" font-style="italic" fill="#4a54a8" font-family="Inter,sans-serif" letter-spacing=".08em">Laguna de Bay</text>')
    style = {'sec': ('#0b0f3a', 5, '#2a3388', 3), 'pri': ('#0b0f3a', 8, '#3a44a6', 5), 'exp': ('#0b0f3a', 12, '#5560c4', 8)}
    for kind in ('sec', 'pri', 'exp'):
        cas, cw, core, w = style[kind]
        ds = [smooth(p) for k, p in R.values() if k == kind]
        o.append(''.join(f'<path d="{d}" fill="none" stroke="{cas}" stroke-width="{cw}" stroke-linecap="round" stroke-linejoin="round"/>' for d in ds))
        o.append(''.join(f'<path d="{d}" fill="none" stroke="{core}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>' for d in ds))
    for k, (kind, p) in R.items():   # traffic on the big roads, quiet
        if kind == 'exp' or k in ('EDSA', 'C5'):
            o.append(f'<path class="trf" d="{smooth(p)}" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="2" stroke-linecap="round" stroke-dasharray="1 16"/>')
    # expressway shields
    for x, y, t in ((356, 262, 'NLEX'), (420, 668, 'SLEX'), (482, 488, 'EDSA'), (502, 556, 'C-5')):
        w = 9 * len(t) + 10
        o.append(f'<g transform="translate({x} {y})"><rect x="{-w / 2}" y="-10" width="{w}" height="20" rx="5" fill="#0b0f3a" stroke="#6b75d0" stroke-width="1.4"/>'
                 f'<text y="4.5" font-size="11.5" font-weight="700" fill="#c8ccf0" text-anchor="middle" font-family="Inter,sans-serif">{t}</text></g>')
    for x, y, t in TOWNS:
        if t:
            o.append(f'<text x="{x}" y="{y}" font-size="16" font-weight="600" fill="#7d86cc" font-family="Inter,sans-serif">{t}</text>')
    # trips: the route line, a drop pin, the truck out and back
    for i, (p, dest) in enumerate(TRIPS):
        d = smooth(p)
        o.append(f'<path d="{d}" fill="none" stroke="#0b0f3a" stroke-width="7" stroke-linecap="round" stroke-opacity=".7"/>'
                 f'<path d="{d}" fill="none" stroke="#e8b800" stroke-opacity=".62" stroke-width="3.6" stroke-linecap="round"/>')
    for i, (p, dest) in enumerate(TRIPS):
        ex, ey = p[-1]
        lx, anc = (-12, 'end') if dest in ('Port Area', 'Malolos', 'San Fernando', 'Dasmariñas', 'Tagaytay') else (12, 'start')
        o.append(f'<g transform="translate({ex} {ey})"><circle r="7" fill="#0b0f3a" stroke="#e8b800" stroke-width="2.4"/><circle r="2.4" fill="#e8b800"/>'
                 f'<text x="{lx}" y="-9" text-anchor="{anc}" font-size="15" font-weight="600" fill="#e6e8f7" font-family="Inter,sans-serif">{dest}</text></g>')
    for i, (p, dest) in enumerate(TRIPS):
        d = smooth(p)
        L = plen(p)
        dur = max(9, L / 16 * 2 + 3)
        begin = -((i * 2.7) % dur)
        o.append(f'<g><rect x="-7" y="-4.5" width="14" height="9" rx="2" fill="#fff"/><rect x="3.5" y="-4.5" width="4.5" height="9" rx="1.4" fill="#e8b800"/>'
                 f'<animateMotion dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite" path="{d}" rotate="auto" '
                 f'keyPoints="0;0;1;1;0" keyTimes="0;.06;.47;.59;1" calcMode="linear"/></g>')
    for (x, y), nm in ((G1, 'Pulilan'), (G2, 'Marikina'), (G3, 'Sta. Rosa')):
        o.append(f'<circle cx="{x}" cy="{y}" r="58" fill="url(#gglow)"/><circle cx="{x}" cy="{y}" r="15" fill="#0f1445" stroke="#e8b800" stroke-width="3"/>'
                 f'<path d="M{x - 7} {y + 5}V{y - 1}L{x} {y - 7}L{x + 7} {y - 1}V{y + 5}Z" fill="#e8b800"/>'
                 f'<text x="{x + 22}" y="{y + 6}" font-size="24" font-weight="800" fill="#fff" font-family="Inter,sans-serif" paint-order="stroke" stroke="#0f1445" stroke-width="4">{nm}</text>')
    o.append('</svg>')
    return ''.join(o)


MAP_CSS = '''
.tilt{position:absolute;left:-165px;top:52px;width:1120px;height:1180px;transform:perspective(1500px) rotateX(48deg) rotateZ(-11deg) scale(.84);transform-origin:50% 50%}
.fade{position:absolute;inset:0;background:linear-gradient(180deg,#0f1445 0%,#0f1445 44%,rgba(15,20,69,.6) 50%,rgba(15,20,69,0) 58%),radial-gradient(ellipse 90% 70% at 50% 80%,transparent 55%,rgba(15,20,69,.85) 100%);pointer-events:none}
.trf{animation:trf 3s linear infinite}
@keyframes trf{to{stroke-dashoffset:-34}}
'''
if want('R45SignRoads'):
    sign('R45SignRoads.dc.html', 'Sign in, dark split, the road map tilted, trips out and back along the roads', MAP_CSS,
         f'<div class="tilt">{road_map()}</div><div class="fade"></div>')


# ================================================================ S20: navigation view, the map moves under the van
T = 800      # tile height in plane units
NW = 1600    # plane width


def nav_tile(y0, seed=5):
    r = random.Random(seed)
    o = []
    cx = NW / 2
    y = 30
    while y < T:   # side streets
        o.append(f'<path d="M0 {y0 + y}H{cx - 70}M{cx + 70} {y0 + y}H{NW}" stroke="#2a3388" stroke-width="{r.choice([5, 5, 9])}"/>')
        y += r.randint(70, 120)
    for x in list(range(40, int(cx - 90), 95)) + list(range(int(cx + 110), NW, 95)):
        o.append(f'<path d="M{x} {y0}V{y0 + T}" stroke="#222a78" stroke-width="5"/>')
    for _ in range(140):
        x = r.choice([r.uniform(0, cx - 80), r.uniform(cx + 80, NW)])
        yy = r.uniform(0, T)
        seg = f'h{r.uniform(20, 50):.0f}' if r.random() < .5 else f'v{r.uniform(20, 50):.0f}'
        o.append(f'<path d="M{x:.0f} {y0 + yy:.0f}{seg}" stroke="#8d96d8" stroke-opacity=".14" stroke-width="2"/>')
    ramp = f'M{cx + 40} {y0 + 520}C{cx + 44} {y0 + 440} {cx + 120} {y0 + 380} {cx + 260} {y0 + 360}H{NW}'
    o.append(f'<path d="{ramp}" fill="none" stroke="#0b0f3a" stroke-width="30"/><path d="{ramp}" fill="none" stroke="#3a44a6" stroke-width="22"/>')
    o.append(f'<rect x="{cx - 74}" y="{y0}" width="148" height="{T}" fill="#0b0f3a"/>'
             f'<rect x="{cx - 68}" y="{y0}" width="62" height="{T}" fill="#3a44a6"/><rect x="{cx + 6}" y="{y0}" width="62" height="{T}" fill="#4a55b8"/>'
             f'<path d="M{cx - 37} {y0}V{y0 + T}M{cx + 37} {y0}V{y0 + T}" stroke="#fff" stroke-opacity=".45" stroke-width="2.5" stroke-dasharray="26 34"/>')
    o.append(f'<rect x="{cx + 14}" y="{y0}" width="46" height="{T}" fill="#e8b800" opacity=".18"/>'
             f'<path d="M{cx + 37} {y0}V{y0 + T}" stroke="#e8b800" stroke-width="16"/>'
             f'<path d="M{cx + 37} {y0}V{y0 + T}" stroke="#fff3c4" stroke-opacity=".55" stroke-width="3" stroke-dasharray="2 28"/>')
    o.append(f'<g transform="translate({cx - 130} {y0 + 210})"><rect x="-30" y="-15" width="60" height="30" rx="7" fill="#0b0f3a" stroke="#6b75d0" stroke-width="2"/>'
             f'<text y="6" font-size="17" font-weight="700" fill="#c8ccf0" text-anchor="middle" font-family="Inter,sans-serif">NLEX</text></g>')
    for nm, x, yy in (('Valenzuela', 260, 120), ('Meycauayan', 1180, 640), ('Marilao', 300, 600)):
        o.append(f'<text x="{x}" y="{y0 + yy}" font-size="26" font-weight="600" fill="#7d86cc" font-family="Inter,sans-serif">{nm}</text>')
    return ''.join(o)


def nav_plane():
    tiles = ''.join(nav_tile(i * T) for i in range(4))
    return (f'<svg class="tiles" viewBox="0 0 {NW} {4 * T}" width="{NW}" height="{4 * T}" aria-hidden="true">'
            f'<rect width="{NW}" height="{4 * T}" fill="#121958"/>{tiles}</svg>')


NAV_TRUCK = '''<svg class="me" viewBox="-60 -90 120 170" width="120" height="170" aria-hidden="true">
<defs><radialGradient id="halo"><stop offset="0" stop-color="#e8b800" stop-opacity=".5"/><stop offset="1" stop-color="#e8b800" stop-opacity="0"/></radialGradient>
<linearGradient id="cone" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff3c4" stop-opacity=".45"/><stop offset="1" stop-color="#fff3c4" stop-opacity="0"/></linearGradient></defs>
<circle class="pulse" r="44" fill="url(#halo)"/>
<path d="M-12 -26 L-46 -88 H46 L12 -26Z" fill="url(#cone)"/>
<ellipse cx="3" cy="6" rx="16" ry="34" fill="#000" opacity=".45"/>
<rect x="-13" y="-10" width="26" height="46" rx="3" fill="#f7f8fb"/>
<path d="M-13 30h26" stroke="#c9d0de" stroke-width="2"/><path d="M-13 -2h26M-13 6h26M-13 14h26M-13 22h26" stroke="#dde1ea" stroke-width="1.2"/>
<rect x="-12" y="-30" width="24" height="18" rx="5" fill="#e8b800"/><rect x="-9" y="-28" width="18" height="6" rx="2" fill="#0f1445" opacity=".6"/>
</svg>'''

NAV_CSS = '''
.navw{position:absolute;left:0;right:0;top:420px;bottom:0;perspective:520px;perspective-origin:50% -30%;overflow:hidden}
.navp{position:absolute;left:50%;bottom:-60px;width:1600px;height:3200px;margin-left:-837px;transform-origin:50% 100%;transform:rotateX(66deg)}
.tiles{position:absolute;left:0;bottom:0;animation:roll 7s linear infinite}
@keyframes roll{from{transform:translateY(0)}to{transform:translateY(800px)}}
.navfog{position:absolute;left:0;right:0;top:400px;height:260px;background:linear-gradient(180deg,#0f1445 0%,#0f1445 26%,rgba(15,20,69,.6) 50%,rgba(15,20,69,0) 100%)}
.me{position:absolute;left:360px;top:668px;filter:drop-shadow(0 6px 10px rgba(0,0,0,.4))}
.pulse{animation:pulse 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes pulse{0%,100%{opacity:.7;transform:scale(.9)}50%{opacity:1;transform:scale(1.1)}}
.eta{position:absolute;left:64px;bottom:40px;display:flex;align-items:center;gap:12px;padding:10px 16px 10px 12px;border-radius:12px;background:rgba(10,13,51,.82);box-shadow:inset 0 0 0 1px rgba(255,255,255,.08);font-size:14px;color:rgba(255,255,255,.8)}
.eta b{color:#fff;font-weight:700}.eta i{width:10px;height:10px;border-radius:50%;background:#e8b800;box-shadow:0 0 0 4px rgba(232,184,0,.2)}
'''
if want('R45SignNav'):
    sign('R45SignNav.dc.html', 'Sign in, dark split, navigation view: the map rolls under the van', NAV_CSS,
         f'<div class="navw"><div class="navp">{nav_plane()}</div></div><div class="navfog"></div>{NAV_TRUCK}'
         '<div class="eta"><i></i><span><b>Pulilan to Port Area</b> · NLEX southbound · 41 km</span></div>')


# ================================================================ S21: the wing van at the dock, its wing lifts
def wing_keys(name):
    """Keyframes for the wing: scaleY = cos(angle), angle 0 to 125 degrees; the outer face shows while cos > 0."""
    def ang(u):
        return 125 * (0.5 - 0.5 * math.cos(math.pi * u))
    sc, out, inn, glow = [], [], [], []
    for a, b, st in ((0, 20, 0), (20, 38, 'up'), (38, 72, 1), (72, 90, 'down'), (90, 100, 0)):
        for pct in range(a, b + 1):
            th = {0: 0, 1: 125}.get(st) if st in (0, 1) else ang((pct - a) / (b - a)) if st == 'up' else ang(1 - (pct - a) / (b - a))
            c = math.cos(math.radians(th))
            sc.append(f'{pct}%{{transform:scaleY({c:.3f})}}')
            out.append(f'{pct}%{{opacity:{1 if c >= 0 else 0}}}')
            inn.append(f'{pct}%{{opacity:{0 if c >= 0 else 1}}}')
            glow.append(f'{pct}%{{opacity:{min(1, th / 90):.2f}}}')
    return (f'@keyframes {name}{{{"".join(sc)}}}@keyframes {name}o{{{"".join(out)}}}'
            f'@keyframes {name}i{{{"".join(inn)}}}@keyframes {name}g{{{"".join(glow)}}}')


def pallets():
    o, r = [], random.Random(4)
    x = 132
    while x < 560:
        w = r.choice([62, 70, 76])
        rows = r.choice([2, 3, 3, 4])
        o.append(f'<rect x="{x}" y="344" width="{w}" height="8" fill="#6b5130"/>')
        for i in range(rows):
            for j in range(2):
                bw = w / 2 - 2
                o.append(f'<rect x="{x + j * (bw + 2) + 1:.0f}" y="{344 - (i + 1) * 26 + 2}" width="{bw:.0f}" height="24" rx="1.5" fill="{r.choice(["#c99556", "#b98447", "#d4a468"])}"/>')
        o.append(f'<rect x="{x}" y="{344 - rows * 26}" width="{w}" height="{rows * 26}" fill="#fff" opacity=".07"/>')
        x += w + r.randint(6, 14)
    return ''.join(o)


def lamp_cone(x):
    return (f'<g><path d="M{x} 48v14" stroke="#2c3590" stroke-width="3"/><rect x="{x - 22}" y="60" width="44" height="7" rx="3" fill="#2c3590"/>'
            f'<rect x="{x - 18}" y="66" width="36" height="4" rx="2" fill="#fff6d6"/><path class="lampb" d="M{x - 18} 70 L{x - 120} 430 H{x + 120} L{x + 18} 70Z" fill="url(#lampc)"/></g>')


def wheel(x, y=398):
    return f'<circle cx="{x}" cy="{y}" r="30" fill="#11131f"/><circle cx="{x}" cy="{y}" r="13" fill="#aab2c5"/><circle cx="{x}" cy="{y}" r="4" fill="#5a6278"/>'


WALL = ''.join(f'<path d="M{x} 40V430"/>' for x in range(0, 841, 14))
RIBS = ''.join(f'<path d="M{x} 168V352"/>' for x in range(160, 600, 40))
WRIBS = ''.join(f'<path d="M{x} 168V306"/>' for x in range(150, 600, 46))
WING = f'''<svg class="dock" viewBox="0 0 840 520" aria-hidden="true">
<defs>
<linearGradient id="lampc" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe9a6" stop-opacity=".26"/><stop offset="1" stop-color="#ffe9a6" stop-opacity="0"/></linearGradient>
<linearGradient id="cargo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd27a" stop-opacity=".55"/><stop offset="1" stop-color="#ff9e3d" stop-opacity=".25"/></linearGradient>
<linearGradient id="wingout" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eef1f7"/><stop offset="1" stop-color="#cfd5e2"/></linearGradient>
<linearGradient id="wingin" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8e97ad"/><stop offset="1" stop-color="#b9c0d0"/></linearGradient>
<radialGradient id="spill"><stop offset="0" stop-color="#ffcf70" stop-opacity=".32"/><stop offset="1" stop-color="#ffcf70" stop-opacity="0"/></radialGradient>
</defs>
<rect x="0" y="40" width="840" height="390" fill="#121852"/>
<g stroke="#fff" stroke-opacity=".03" stroke-width="2">{WALL}</g>
<rect x="0" y="40" width="840" height="8" fill="#1d2570"/>
<text x="40" y="118" font-size="44" font-weight="800" fill="#e8b800" fill-opacity=".22" font-family="IBM Plex Mono,monospace">BAY 2</text>
{lamp_cone(200)}{lamp_cone(470)}{lamp_cone(740)}
<rect x="0" y="430" width="840" height="90" fill="#0a0d33"/><path d="M0 430H840" stroke="#2c3590" stroke-width="2"/>
<path d="M40 500H800" stroke="#e8b800" stroke-opacity=".35" stroke-width="4" stroke-dasharray="30 22"/>
<ellipse cx="430" cy="432" rx="360" ry="10" fill="#000" opacity=".5"/>
<ellipse class="wg" cx="360" cy="440" rx="320" ry="40" fill="url(#spill)"/>
<rect x="112" y="352" width="620" height="18" rx="3" fill="#2a2f45"/>
<rect x="380" y="368" width="90" height="26" rx="4" fill="#3a4058"/><path d="M386 376h78M386 384h78" stroke="#4b526d" stroke-width="2"/>
{wheel(196)}{wheel(268)}{wheel(664)}
<rect x="120" y="164" width="484" height="190" fill="#1b1830"/>
<rect class="wg" x="120" y="164" width="484" height="190" fill="url(#cargo)"/>
<g class="wg">{pallets()}</g>
<g stroke="#000" stroke-opacity=".25" stroke-width="3">{RIBS}</g>
<rect x="114" y="160" width="496" height="8" rx="2" fill="#aeb6ca"/>
<rect x="120" y="306" width="484" height="48" fill="#dfe3ec"/>
<path d="M120 318 C240 310 420 330 604 312 V326 C420 342 240 322 120 330Z" fill="#f29a1f"/>
<path d="M120 330 C240 322 420 342 604 326 V354 H120Z" fill="#1f5cc4"/>
<g class="wing"><g class="wout"><rect x="120" y="168" width="484" height="138" fill="url(#wingout)"/>
<path d="M120 172h484" stroke="#b8c0d0" stroke-width="2"/>
<g transform="translate(160 206) scale(.2)" fill="#e8b800">{LOGO_POLY}</g>
<text x="238" y="242" font-size="40" font-weight="800" font-style="italic" fill="#0f1445" font-family="Inter,sans-serif">WeLinc</text>
<text x="240" y="270" font-size="15" font-weight="600" fill="#0f1445" fill-opacity=".7" font-family="IBM Plex Mono,monospace" letter-spacing=".12em">LOGISTICS</text>
<path d="M120 300h484" stroke="#b8c0d0" stroke-width="1.5"/></g>
<g class="win"><rect x="120" y="168" width="484" height="138" fill="url(#wingin)"/><g stroke="#6f7894" stroke-width="3">{WRIBS}</g></g></g>
<path d="M612 222 H690 Q712 222 722 246 L742 300 Q746 310 746 322 V368 H612Z" fill="#eef1f6"/>
<path d="M624 236 H684 Q698 236 706 252 L722 292 H624Z" fill="#14205a"/>
<path d="M690 250 L700 250 L712 288 H702Z" fill="#fff" opacity=".1"/>
<path d="M612 316 H746" stroke="#c3cad8" stroke-width="2"/>
<rect x="612" y="328" width="134" height="10" fill="#f29a1f"/><rect x="612" y="338" width="134" height="14" fill="#1f5cc4"/>
<rect x="738" y="306" width="10" height="16" rx="2" fill="#fff6d6"/>
<rect x="640" y="296" width="20" height="4" rx="2" fill="#9aa3ba"/>
<path d="M612 222 V368" stroke="#c3cad8" stroke-width="2"/>
<g transform="translate(36 380)"><rect x="0" y="34" width="70" height="8" fill="#6b5130"/><rect x="4" y="2" width="30" height="30" rx="2" fill="#c99556"/><rect x="36" y="8" width="30" height="24" rx="2" fill="#b98447"/>
<path d="M72 40 L96 40 L104 0" stroke="#e8b800" stroke-width="4" fill="none" stroke-linecap="round"/><circle cx="96" cy="44" r="5" fill="#11131f"/><circle cx="12" cy="45" r="4" fill="#11131f"/></g>
</svg>'''

WING_CSS = '''
.dock{position:absolute;left:0;top:380px;width:840px;height:520px}
.dfade{position:absolute;left:0;right:0;top:380px;height:60px;background:linear-gradient(180deg,#0f1445,rgba(15,20,69,0))}
.wing{transform-box:view-box;transform-origin:0 164px;animation:wing 14s linear infinite}
.wout{animation:wingo 14s linear infinite}.win{animation:wingi 14s linear infinite}
.wg{animation:wingg 14s linear infinite}
.lampb{animation:lampb 5s ease-in-out infinite}
@keyframes lampb{0%,100%{opacity:1}50%{opacity:.8}}
''' + wing_keys('wing')
if want('R45SignWing'):
    sign('R45SignWing.dc.html', 'Sign in, dark split, the wing van at the dock, its wing lifting', WING_CSS, WING + '<div class="dfade"></div>')


# ================================================================ S22: the toll gate, the arm lifts and the truck rolls through
_cab = gen45.FRONT.split('<g class="cab">')[1].split('</g>\n<ellipse cx="420" cy="796"')[0] + '</g>'
_defs = gen45.FRONT.split('<defs>')[1].split('</defs>')[0]
VP = (420, 160)


def lane(x_near, col, extra=''):
    return f'<path d="M{VP[0] + (x_near - VP[0]) * .02:.0f} {VP[1]}L{x_near} 520" stroke="{col}" stroke-width="3" {extra}/>'


STRIPES = ''.join(f'<rect x="{x}" y="330" width="22" height="12" fill="#d8333a"/>' for x in range(260, 540, 48))
CANLIGHTS = ''.join(f'<rect x="{x}" y="94" width="40" height="5" rx="2" fill="#fff6d6"/>' for x in (120, 280, 400, 520, 680))
TOLL = f'''<svg class="toll" viewBox="0 0 840 520" aria-hidden="true">
<defs>{_defs}<linearGradient id="road" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d1240"/><stop offset="1" stop-color="#151b5c"/></linearGradient>
<linearGradient id="canl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff6d6" stop-opacity=".22"/><stop offset="1" stop-color="#fff6d6" stop-opacity="0"/></linearGradient></defs>
<rect width="840" height="{VP[1]}" fill="#0f1445"/>
<polygon points="{VP[0] - 6},{VP[1]} {VP[0] + 6},{VP[1]} 900,520 -60,520" fill="url(#road)"/>
<rect x="0" y="{VP[1] - 2}" width="840" height="4" fill="#25307f"/>
{lane(120, '#fff', 'stroke-opacity=".35"')}{lane(720, '#fff', 'stroke-opacity=".35"')}
{lane(-200, '#fff', 'stroke-opacity=".2" stroke-dasharray="20 26"')}{lane(1040, '#fff', 'stroke-opacity=".2" stroke-dasharray="20 26"')}
<polygon points="176,300 236,300 196,520 40,520" fill="#1d2570"/><polygon points="604,300 664,300 800,520 644,520" fill="#1d2570"/>
<polygon points="176,300 236,300 236,292 176,292" fill="#2c3590"/><polygon points="604,300 664,300 664,292 604,292" fill="#2c3590"/>
<g><rect x="150" y="200" width="70" height="104" rx="3" fill="#232b7c"/><rect x="158" y="214" width="54" height="40" rx="2" fill="#ffe9a6" opacity=".7"/><rect x="150" y="196" width="70" height="8" fill="#2c3590"/></g>
<g><rect x="620" y="200" width="70" height="104" rx="3" fill="#232b7c"/><rect x="628" y="214" width="54" height="40" rx="2" fill="#ffe9a6" opacity=".55"/><rect x="620" y="196" width="70" height="8" fill="#2c3590"/></g>
<polygon points="0,40 840,40 840,92 0,92" fill="#1a2263"/><rect x="0" y="88" width="840" height="6" fill="#2c3590"/>
<path d="M0 40H840" stroke="#2c3590" stroke-width="2"/>
<rect x="196" y="94" width="14" height="110" fill="#1a2263"/><rect x="630" y="94" width="14" height="110" fill="#1a2263"/>
<polygon points="250,94 590,94 760,400 80,400" fill="url(#canl)"/>
{CANLIGHTS}
<g transform="translate(372 52)"><rect width="96" height="30" rx="5" fill="#0a0d33" stroke="#2c3590"/><text x="34" y="20" font-size="13" font-weight="700" fill="#c8ccf0" text-anchor="middle" font-family="Inter,sans-serif">RFID</text>
<circle class="sig" cx="74" cy="15" r="7"/></g>
<g class="tk"><g class="tkin">
<g transform="translate(-420 -794)">{_cab}</g>
<path d="M-104 -97 L-330 30 H-30 L-70 -97Z" fill="url(#bm)" opacity=".8"/><path d="M104 -97 L330 30 H30 L70 -97Z" fill="url(#bm)" opacity=".8"/>
<ellipse cx="0" cy="2" rx="170" ry="10" fill="#000" opacity=".45"/></g></g>
<g class="arm"><rect x="228" y="330" width="320" height="12" rx="6" fill="#f4f5fa"/>{STRIPES}<circle cx="540" cy="336" r="4" fill="#d8333a"/></g>
<rect x="206" y="314" width="34" height="56" rx="4" fill="#d8dce8"/><rect x="206" y="314" width="34" height="10" rx="3" fill="#e8b800"/><circle cx="232" cy="336" r="8" fill="#2a2f45"/>
<g transform="translate(244 286)"><rect width="26" height="38" rx="4" fill="#0a0d33"/><circle class="sig" cx="13" cy="12" r="6"/><circle cx="13" cy="27" r="6" fill="#1a2263"/></g>
</svg>'''

TOLL_CSS = '''
.toll{position:absolute;left:0;top:400px;width:840px;height:520px}
.tk{animation:tk 12s linear infinite}
@keyframes tk{0%{transform:translate(420px,172px) scale(.06);opacity:0}6%{opacity:1;animation-timing-function:ease-out}
 34%{transform:translate(420px,316px) scale(.5)}48%{transform:translate(420px,316px) scale(.5);animation-timing-function:ease-in}
 66%{transform:translate(420px,800px) scale(1.7);opacity:1}67%,100%{opacity:0;transform:translate(420px,800px) scale(1.7)}}
.tkin{animation:idle 1.4s ease-in-out infinite}
@keyframes idle{0%,100%{transform:translateY(0)}50%{transform:translateY(.8px)}}
.arm{transform-box:view-box;transform-origin:232px 336px;animation:arm 12s ease-in-out infinite}
@keyframes arm{0%,40%{transform:rotate(0)}48%,68%{transform:rotate(-80deg)}78%,100%{transform:rotate(0)}}
.sig{animation:sig 12s steps(1) infinite}
@keyframes sig{0%{fill:#e8a400}39%{fill:#36d17a}74%{fill:#e8a400}}
'''
if want('R45SignToll'):
    sign('R45SignToll.dc.html', 'Sign in, dark split, the toll gate: the arm lifts, the truck rolls through', TOLL_CSS, TOLL)


# ================================================================ S23: the yard from above at night
def topdown_truck(logo=True):
    lg = f'<g transform="translate(-30 -9) scale(.075)" fill="#e8b800">{LOGO_POLY}</g>' if logo else ''
    return ('<g><rect x="-50" y="-13" width="104" height="30" rx="4" fill="#000" opacity=".4" transform="translate(5 6)"/>'
            '<rect x="-50" y="-13" width="78" height="26" rx="2" fill="#eef1f7"/>'
            f'<path d="M-46 -13v26M-34 -13v26M-22 -13v26M-10 -13v26M2 -13v26M14 -13v26" stroke="#d3d8e3" stroke-width="1"/>{lg}'
            '<rect x="30" y="-11" width="22" height="22" rx="5" fill="#e3e7f0"/><rect x="42" y="-9" width="8" height="18" rx="2" fill="#14205a"/>'
            '<rect x="26" y="-2" width="4" height="4" fill="#9aa3ba"/></g>')


def yard():
    r = random.Random(8)
    o = ['<svg class="yard" viewBox="0 20 840 480" aria-hidden="true"><defs>'
         '<radialGradient id="pool2"><stop offset="0" stop-color="#ffe9a6" stop-opacity=".22"/><stop offset="1" stop-color="#ffe9a6" stop-opacity="0"/></radialGradient>'
         '<linearGradient id="spill2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffcf70" stop-opacity=".38"/><stop offset="1" stop-color="#ffcf70" stop-opacity="0"/></linearGradient></defs>'
         '<rect width="840" height="520" fill="#111750"/>']
    for _ in range(260):
        o.append(f'<circle cx="{r.uniform(0, 840):.0f}" cy="{r.uniform(0, 520):.0f}" r="{r.uniform(.6, 1.6):.1f}" fill="#fff" opacity=".03"/>')
    o.append('<path d="M14 14H826V430H700M600 430H14Z" fill="none" stroke="#2c3590" stroke-width="6"/>')
    o.append('<rect x="0" y="440" width="840" height="80" fill="#0a0d33"/><path d="M0 480H840" stroke="#e8b800" stroke-opacity=".45" stroke-width="3" stroke-dasharray="26 22"/>')
    o.append('<path d="M600 430H612M688 430H700" stroke="#e8b800" stroke-width="8"/><circle class="bcn" cx="606" cy="422" r="5" fill="#ff9e3d"/>')
    o.append('<rect x="40" y="36" width="430" height="190" fill="#1f2878"/><rect x="40" y="36" width="430" height="190" fill="none" stroke="#2c3590" stroke-width="3"/>')
    o.append('<g stroke="#fff" stroke-opacity=".05" stroke-width="2">' + ''.join(f'<path d="M{x} 36V226"/>' for x in range(50, 470, 10)) + '</g>')
    for x in (80, 190, 300, 410):
        o.append(f'<rect class="sky" x="{x - 20}" y="62" width="40" height="140" rx="3" fill="#ffe9a6" opacity=".14"/>')
    o.append('<rect x="40" y="128" width="430" height="6" fill="#141a5a"/>')
    for i, x in enumerate((60, 200, 340)):
        o.append(f'<polygon points="{x},226 {x + 110},226 {x + 140},330 {x - 30},330" fill="url(#spill2)"/>'
                 f'<rect x="{x}" y="222" width="110" height="6" fill="#e8b800" opacity=".7"/>'
                 f'<text x="{x + 55}" y="262" font-size="18" font-weight="700" fill="#e8b800" fill-opacity=".45" text-anchor="middle" font-family="IBM Plex Mono,monospace">{i + 1}</text>')
    for k in range(6):
        y = 70 + k * 64
        o.append(f'<path d="M560 {y}L800 {y - 20}" stroke="#fff" stroke-opacity=".38" stroke-width="2.5"/>')
    for k, park in enumerate((True, True, False, True, True)):
        if park:
            o.append(f'<g transform="translate(690 {92 + k * 64}) rotate(-5) scale(1.05)">{topdown_truck(logo=k != 1)}</g>')
    o.append(f'<g transform="translate(115 290) rotate(-90) scale(1.05)">{topdown_truck()}</g>')
    for x, y in ((520, 60), (520, 380), (250, 400), (800, 220)):
        o.append(f'<circle class="pool" cx="{x}" cy="{y}" r="110" fill="url(#pool2)"/><circle cx="{x}" cy="{y}" r="5" fill="#ffe9a6"/>')
    path = 'M255 210 C255 300 260 360 330 380 S560 380 640 420 S690 470 760 480 L1000 480'
    o.append(f'<g>{topdown_truck()}<animateMotion dur="16s" repeatCount="indefinite" rotate="auto" path="{path}" keyPoints="0;0;1;1" keyTimes="0;.12;.82;1" calcMode="spline" keySplines="0 0 1 1;.45 0 .55 1;0 0 1 1"/></g>')
    o.append(f'<g>{topdown_truck(logo=False)}<animateMotion dur="11s" begin="-4s" repeatCount="indefinite" rotate="auto" path="M960 462 L-120 462"/></g>')
    o.append('</svg>')
    return ''.join(o)


YARD_CSS = '''
.yard{position:absolute;left:0;top:420px;width:840px;height:480px}
.sky{animation:skyl 6s ease-in-out infinite}
@keyframes skyl{0%,100%{opacity:.14}50%{opacity:.2}}
.bcn{animation:bcn 1.2s steps(1) infinite}
@keyframes bcn{50%{opacity:.15}}
.pool{animation:poolb 5s ease-in-out infinite}
@keyframes poolb{0%,100%{opacity:1}50%{opacity:.85}}
.yfade{position:absolute;left:0;right:0;top:416px;height:70px;background:linear-gradient(180deg,#0f1445,rgba(15,20,69,0))}
'''
if want('R45SignYard'):
    sign('R45SignYard.dc.html', 'Sign in, dark split, the yard from above at night', YARD_CSS, yard() + '<div class="yfade"></div>')


# ================================================================ S24: light trails on the interchange
def trails():
    o = ['<svg class="ix" viewBox="-420 -420 840 840" width="840" height="840" overflow="visible" aria-hidden="true">',
         '<defs><filter id="bl" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="4"/></filter></defs>',
         '<rect x="-900" y="-900" width="1800" height="1800" fill="#111750"/>']
    r = random.Random(3)
    g = ''.join(f'M{k + r.uniform(-4, 4):.0f} -900V900M-900 {k + r.uniform(-4, 4):.0f}H900' for k in range(-900, 901, 34))
    o.append(f'<path d="{g}" stroke="#8d96d8" stroke-opacity=".07" stroke-width="2"/>')
    decks, paths = [], []
    decks.append('<rect x="-900" y="-46" width="1800" height="92" fill="#090c30"/>')
    for v, d in ((-34, 1), (-18, 1), (18, -1), (34, -1)):
        paths.append((f'M{-900 * d} {v}H{900 * d}', 'w' if d == 1 else 'r', 0))
        paths.append((f'M{v} {900 * d}V{-900 * d}', 'w' if d == 1 else 'r', 1))
    R0 = 70
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        cx, cy = sx * (34 + R0), sy * (34 + R0)
        top = (cx, cy - sy * R0)
        side = (cx - sx * R0, cy)
        sweep = 1 if sx * sy > 0 else 0
        d = f'M{top[0]} {top[1]}A{R0} {R0} 0 1 {sweep} {side[0]} {side[1]}'
        decks.append(f'<path d="{d}" fill="none" stroke="#0b0f3a" stroke-width="22"/>')
        paths.append((d, 'w' if sx > 0 else 'r', 0))
        od = f'M{sx * 320} {sy * 46}C{sx * 220} {sy * 60} {sx * 250} {sy * 250} {sx * 46} {sy * 320}'
        decks.append(f'<path d="{od}" fill="none" stroke="#0b0f3a" stroke-width="20"/>')
        paths.append((od, 'g' if sx * sy > 0 else 'w', 0))
    o += decks
    col = {'w': '#fff6e0', 'r': '#ff4a3d', 'g': '#ffb020'}

    def trail(d, c):
        dur = r.uniform(2.2, 3.6)
        dash = f'{r.randint(40, 90)} {r.randint(60, 160)}'
        st = f'style="animation-duration:{dur:.1f}s;animation-delay:{-r.uniform(0, 3):.1f}s"'
        return (f'<path class="tr" d="{d}" fill="none" stroke="{col[c]}" stroke-width="9" stroke-opacity=".35" stroke-dasharray="{dash}" filter="url(#bl)" {st}/>'
                f'<path class="tr" d="{d}" fill="none" stroke="{col[c]}" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="{dash}" {st}/>')
    o += [trail(d, c) for d, c, top in paths if not top]
    # the flyover deck on top, with its own trails
    o.append('<rect x="-60" y="-900" width="120" height="1800" fill="#000" opacity=".25"/>')
    o.append('<rect x="-46" y="-900" width="92" height="1800" fill="#0b0f3a"/><path d="M-46 -900V900M46 -900V900" stroke="#2c3590" stroke-width="2"/>')
    o += [trail(d, c) for d, c, top in paths if top]
    o.append('</svg>')
    return ''.join(o)


IX_CSS = '''
.ixw{position:absolute;left:0;top:330px;width:840px;height:840px;transform:perspective(1200px) rotateX(52deg) rotateZ(28deg) scale(1.05);transform-origin:50% 50%}
.tr{animation:tr 3s linear infinite}
@keyframes tr{to{stroke-dashoffset:-400}}
.ixfade{position:absolute;inset:0;background:linear-gradient(180deg,#0f1445 0%,#0f1445 44%,rgba(15,20,69,0) 58%);pointer-events:none}
'''
if want('R45SignTrails'):
    sign('R45SignTrails.dc.html', 'Sign in, dark split, light trails on the interchange', IX_CSS, f'<div class="ixw">{trails()}</div><div class="ixfade"></div>')


# ================================================================ S25: from the driver's seat
CAB_CSS = gen45.ROAD_CSS + '''
.wind{position:absolute;left:0;top:410px;width:840px;height:520px;overflow:hidden}
.dash2{position:absolute;left:0;top:0;width:840px;height:520px}
.ros{transform-box:view-box;transform-origin:420px 52px;animation:ros 4.5s ease-in-out infinite}
@keyframes ros{0%,100%{transform:rotate(5deg)}50%{transform:rotate(-5deg)}}
.ndl{transform-box:view-box;animation:ndl 6s ease-in-out infinite}
@keyframes ndl{0%,100%{opacity:1}50%{opacity:.85}}
.dot{animation:dotm 6s linear infinite}
@keyframes dotm{from{offset-distance:0%}to{offset-distance:100%}}
'''


def gauge_ticks(cx, colour, op):
    return ''.join(f'<path d="M{cx + 24 * math.cos(math.radians(a)):.1f} {24 * math.sin(math.radians(a)):.1f}L{cx + 28 * math.cos(math.radians(a)):.1f} {28 * math.sin(math.radians(a)):.1f}" stroke="{colour}" stroke-opacity="{op}" stroke-width="1.6"/>'
                   for a in range(150, 391, 24))


def rosary():
    beads = []
    n = 18
    for t in range(n + 1):   # a loop of beads hanging from the mirror stem
        a = math.pi * t / n
        beads.append(f'<circle cx="{420 - 15 * math.cos(a):.1f}" cy="{56 + 62 * math.sin(a) ** .9:.1f}" r="2.3" fill="#c9a86a"/>')
    return (f'<g class="ros">{"".join(beads)}<path d="M420 118 V146 M411 128 H429" stroke="#c9a86a" stroke-width="3" stroke-linecap="round"/></g>')


def cab_view():
    road = gen45.night_road(840, 520, 180, 384, 190, 72, lamps=True)
    route = 'M-40 72 C-30 40 -4 44 6 22 S30 2 44 -2'
    return f'''<div class="wind">{road}
<svg class="dash2" viewBox="0 0 840 520" aria-hidden="true">
<defs><linearGradient id="dsh" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2266"/><stop offset=".14" stop-color="#11175a"/><stop offset="1" stop-color="#0a0d33"/></linearGradient>
<radialGradient id="gauge"><stop offset="0" stop-color="#e8b800" stop-opacity=".25"/><stop offset="1" stop-color="#e8b800" stop-opacity="0"/></radialGradient></defs>
<path fill-rule="evenodd" fill="#0f1445" d="M0 0H840V520H0Z M70 34 Q420 14 770 34 L814 340 H26Z"/>
<path d="M70 34 L26 340" stroke="#1a2263" stroke-width="24"/><path d="M770 34 L814 340" stroke="#1a2263" stroke-width="24"/>
<path d="M70 34 Q420 14 770 34" stroke="#1a2263" stroke-width="10" fill="none"/>
<rect x="378" y="30" width="84" height="22" rx="8" fill="#141a4a"/><rect x="384" y="34" width="72" height="14" rx="5" fill="#2c3590" opacity=".6"/>
{rosary()}
<path d="M0 330 Q420 300 840 330 V520 H0Z" fill="url(#dsh)"/>
<path d="M0 330 Q420 300 840 330" stroke="#2c3590" stroke-width="2" fill="none" opacity=".7"/>
<g transform="translate(230 420)"><circle r="78" fill="url(#gauge)"/>
<circle cx="-36" r="30" fill="#0a0d2a" stroke="#2c3590" stroke-width="2"/><circle cx="36" r="30" fill="#0a0d2a" stroke="#2c3590" stroke-width="2"/>
{gauge_ticks(-36, '#e8b800', 1)}{gauge_ticks(36, '#fff', .6)}
<rect class="ndl" x="-36" y="-1.2" width="22" height="2.4" fill="#ff7a3d" transform="rotate(-150 -36 0)"/>
<rect class="ndl" x="36" y="-1.2" width="22" height="2.4" fill="#ff7a3d" transform="rotate(-40 36 0)"/></g>
<path d="M60 520 A200 140 0 0 1 400 520" fill="none" stroke="#0e1236" stroke-width="30"/>
<path d="M75 506 A185 126 0 0 1 385 506" fill="none" stroke="#1c2252" stroke-width="2"/>
<g transform="translate(600 262)"><rect x="-6" y="80" width="12" height="40" fill="#141a4a"/>
<rect x="-64" y="-10" width="128" height="96" rx="12" fill="#05071c" stroke="#2c3590" stroke-width="2"/>
<rect x="-58" y="-4" width="116" height="84" rx="7" fill="#121958"/>
<path d="M-58 20H58M-58 54H58M-30 -4V80M24 -4V80" stroke="#2a3388" stroke-width="3"/>
<path d="{route}" fill="none" stroke="#e8b800" stroke-width="4" stroke-linecap="round"/>
<circle cx="44" cy="-2" r="4" fill="#0b0f3a" stroke="#e8b800" stroke-width="2"/>
<circle class="dot" r="4" fill="#fff" style="offset-path:path('{route}')"/>
<text x="-50" y="12" font-size="9" font-weight="700" fill="#fff" font-family="Inter,sans-serif">Sta. Rosa · 18 km</text></g>
</svg></div>'''


if want('R45SignCab'):
    sign('R45SignCab.dc.html', "Sign in, dark split, from the driver's seat", CAB_CSS, cab_view())

print('gen46 ok')

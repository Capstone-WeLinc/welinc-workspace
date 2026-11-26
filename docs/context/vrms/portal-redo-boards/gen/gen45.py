"""Round 45 (Nov 25, late): dark split sign in, launchers with their own layouts. python3 -I gen45.py <project dir>"""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parts import LOGO, LOGO_POLY, CHEV, V_VAN, V_L300, page  # noqa

OUT = Path(sys.argv[1])
RM = '@media (prefers-reduced-motion:reduce){*{animation:none!important}}'


def write(name, html):
    (OUT / name).write_text(html)


NAVY, DEEP, GOLD = '#0f1445', '#0a0d33', '#e8b800'
ARROW = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>')
EYE = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
       'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>')

BASE = '''*{box-sizing:border-box}
.pg{width:1440px;height:900px;font-family:Inter,system-ui,sans-serif;position:relative;overflow:hidden;color:#fff;background:#0a0d33}
a{color:inherit;text-decoration:none}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace}
.lk{display:flex;align-items:center;gap:10px;color:#fff}.lk svg{height:20px;fill:#e8b800}.lk span{font-weight:800;font-style:italic;font-size:16px}
'''

# ================================================================ dark sign in parts
SIGN_CSS = BASE + '''
.lf{position:absolute;left:0;top:0;width:840px;height:900px;overflow:hidden;background:#0f1445}
.rt{position:absolute;right:0;top:0;width:600px;height:900px;background:#0a0d33;box-shadow:inset 1px 0 0 rgba(255,255,255,.07);display:flex;align-items:center;justify-content:center}
.lf .lk{position:absolute;left:64px;top:44px;z-index:3}
.cp{position:absolute;left:64px;top:124px;z-index:3}
.eb{margin:0;font:600 13px "IBM Plex Mono",monospace;letter-spacing:.12em;color:#e8b800}
h1{margin:16px 0 0;font-size:58px;line-height:1.02;font-weight:800;letter-spacing:-.035em}
h1 em{font-style:normal;color:#e8b800}
.ln{margin:18px 0 0;font-size:17px;line-height:1.55;color:rgba(255,255,255,.66);max-width:420px}
.fm{width:384px;display:flex;flex-direction:column;gap:28px;margin:0}
.fm h2{margin:0;font-size:30px;font-weight:800;letter-spacing:-.02em}
.sub{margin:8px 0 0;font-size:15px;color:rgba(255,255,255,.62)}
.fs{display:flex;flex-direction:column;gap:18px}
.fm label{display:block;font-size:14px;font-weight:600;margin-bottom:8px;color:rgba(255,255,255,.88)}
.row{display:flex;justify-content:space-between;align-items:flex-start}
.row a{font-size:14px;font-weight:600;color:#fff;text-decoration:underline;text-underline-offset:3px;text-decoration-color:rgba(255,255,255,.35)}
.fld{position:relative}
.in{width:100%;height:48px;border:1px solid rgba(255,255,255,.14);border-radius:12px;padding:0 14px;font:15px Inter,sans-serif;color:#fff;background:rgba(255,255,255,.06)}
.in::placeholder{color:rgba(255,255,255,.42)}
.eye{position:absolute;right:6px;top:6px;width:36px;height:36px;border:0;background:none;color:rgba(255,255,255,.6);display:grid;place-items:center;border-radius:8px}
.btn{height:50px;border:0;border-radius:12px;background:#e8b800;color:#0f1445;font:800 16px Inter,sans-serif;display:flex;align-items:center;justify-content:center;gap:10px;cursor:pointer;box-shadow:0 10px 24px rgba(232,184,0,.18)}
.hint{margin:0;font-size:14px;line-height:1.55;color:rgba(255,255,255,.55)}
'''

FORM = f'''<form class="fm"><div><h2>Sign in</h2><p class="sub">Use your WeLinc work email.</p></div>
<div class="fs"><div><label for="e">Work email</label><input id="e" class="in" placeholder="you@welinc.com"></div>
<div><div class="row"><label for="p">Password</label><a href="#">Forgot password?</a></div><div class="fld"><input id="p" type="password" class="in" placeholder="Enter password"><button type="button" class="eye" aria-label="Show password">{EYE}</button></div></div>
<button type="button" class="btn">Sign in {ARROW}</button></div>
<p class="hint">No account yet? Ask your admin to add you. You'll get an email to set your password.</p></form>'''

LK = f'<div class="lk">{LOGO}<span>WeLinc Logistics</span></div>'
COPY = ('<div class="cp"><p class="eb">#HASSLEFREE TRANSPORT SOLUTION</p>'
        '<h1>WeLinc Logistics<br><em>Operations</em><br>Workspace</h1>'
        '<p class="ln">Bookings, maintenance and repairs for the whole fleet, in one place.</p></div>')


def sign(name, title, css, art, copy=COPY, rt_extra=''):
    body = f'<div class="pg"><div class="lf">{art}{LK}{copy}</div><div class="rt"{rt_extra}>{FORM}</div></div>'
    write(name, page(title, SIGN_CSS + css + RM, body))


# ================================================================ 1. the night road (perspective)
def truck_rear(w=170):
    # Rear of a WeLinc 10 ft closed van at night, 170 x 160 design units.
    return f'''<svg class="rear" viewBox="0 0 170 160" width="{w}" aria-hidden="true">
<rect x="9" y="0" width="152" height="118" rx="4" fill="#c4cadb"/>
<rect x="9" y="0" width="152" height="118" rx="4" fill="url(#rearShade)"/>
<rect x="15" y="8" width="140" height="102" rx="2" fill="none" stroke="#9aa3ba" stroke-width="1.5"/>
<path d="M85 8v102" stroke="#9aa3ba" stroke-width="1.5"/>
<path d="M78 50v20M92 50v20" stroke="#6f7894" stroke-width="3" stroke-linecap="round"/>
<g transform="translate(26 20) scale(.13)" fill="#e8b800">{LOGO_POLY}</g>
<text x="72" y="40" font-size="13" font-weight="800" font-style="italic" fill="#0f1445" font-family="Inter,sans-serif" text-anchor="end">WeLinc</text>
<rect x="0" y="118" width="170" height="14" rx="2" fill="#2a2f45"/>
<rect x="64" y="121" width="42" height="11" rx="1.5" fill="#e9ecf4"/><text x="85" y="130" font-size="7.5" font-weight="700" fill="#0f1445" text-anchor="middle" font-family="IBM Plex Mono,monospace">CAK 9043</text>
<g class="tail"><rect x="8" y="98" width="12" height="18" rx="2" fill="#ff4a3d"/><rect x="150" y="98" width="12" height="18" rx="2" fill="#ff4a3d"/>
<circle cx="14" cy="107" r="22" fill="#ff4a3d" opacity=".22"/><circle cx="156" cy="107" r="22" fill="#ff4a3d" opacity=".22"/></g>
<rect x="18" y="132" width="26" height="22" rx="4" fill="#05071f"/><rect x="126" y="132" width="26" height="22" rx="4" fill="#05071f"/>
<defs><linearGradient id="rearShade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f1445" stop-opacity=".35"/><stop offset=".55" stop-color="#0f1445" stop-opacity="0"/><stop offset="1" stop-color="#0f1445" stop-opacity=".25"/></linearGradient></defs>
</svg>'''


def stars(n, w, h, seed=3):
    import random
    r = random.Random(seed)
    return ''.join(f'<circle cx="{r.uniform(0, w):.0f}" cy="{r.uniform(0, h):.0f}" r="{r.choice([.8, 1, 1.2, 1.6])}" fill="#fff" opacity="{r.uniform(.15, .6):.2f}"/>' for _ in range(n))


def skyline(w, seed=7):
    import random
    r = random.Random(seed)
    out, x = [], 0
    while x < w:
        bw, bh = r.randint(18, 46), r.randint(10, 58)
        out.append(f'<rect x="{x}" y="{80 - bh}" width="{bw}" height="{bh}" fill="#0b0f3a"/>')
        for _ in range(r.randint(0, 3)):
            out.append(f'<rect x="{x + r.randint(3, bw - 6)}" y="{80 - bh + r.randint(4, max(5, bh - 6))}" width="3" height="3" fill="#e8b800" opacity="{r.uniform(.3, .8):.2f}"/>')
        x += bw + r.randint(0, 6)
    return ''.join(out)


ROAD_CSS = '''
.night{position:absolute;inset:0;background:linear-gradient(180deg,#090c33 0%,#111865 55%,#25307f 62%,#0a0d33 62%)}
.night .st{position:absolute;left:0;top:0}
.night .sky{position:absolute;left:0;width:100%;height:80px}
.rd{position:absolute;left:0;right:0;bottom:0;perspective:260px;perspective-origin:50% 0;overflow:hidden}
.plane{position:absolute;left:50%;bottom:0;width:900px;height:4000px;margin-left:-450px;transform-origin:50% 100%;transform:rotateX(88deg);
background:linear-gradient(90deg,transparent 0 31%,rgba(255,255,255,.6) 31% 31.6%,transparent 31.6% 68.4%,rgba(255,255,255,.6) 68.4% 69%,transparent 69%),linear-gradient(90deg,#0b0f3a 0 30%,#151b5c 30% 70%,#0b0f3a 70%)}
.dash{position:absolute;left:50%;top:0;width:10px;margin-left:-5px;height:100%;background:repeating-linear-gradient(180deg,#e8b800 0 90px,transparent 90px 220px);animation:dash .9s linear infinite}
@keyframes dash{from{background-position:0 0}to{background-position:0 220px}}
.shoulder{position:absolute;top:0;width:8px;height:100%;background:repeating-linear-gradient(180deg,rgba(255,255,255,.8) 0 18px,transparent 18px 260px);animation:dash2 .9s linear infinite}
@keyframes dash2{from{background-position:0 0}to{background-position:0 260px}}
.pool{position:absolute;left:50%;bottom:-140px;width:760px;height:340px;margin-left:-380px;background:radial-gradient(closest-side,rgba(255,236,170,.20),rgba(255,236,170,0))}
.rear{position:absolute;filter:drop-shadow(0 10px 14px rgba(0,0,0,.5));animation:bob 3.2s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(1.5px)}}
.tail{animation:brake 9s ease-in-out infinite}
.lampg{animation:lampg 4s ease-in-out infinite}
@keyframes lampg{0%,100%{opacity:.16}50%{opacity:.09}}
@keyframes brake{0%,70%,100%{opacity:.75}76%,88%{opacity:1}}
'''


def road_lamps(w, h, horizon):
    vx, out = w / 2, []
    for t in (0.06, 0.11, 0.19, 0.32, 0.55, 0.95):
        y = horizon + (h - horizon) * t
        hh = 260 * t
        for side in (-1, 1):
            x = vx + side * (70 + 780 * t)
            out.append(f'<path d="M{x:.0f} {y:.0f}V{y - hh:.0f}h{-side * hh * .18:.0f}" stroke="#2c3590" stroke-width="{max(1, 5 * t):.1f}" fill="none"/>'
                       f'<circle cx="{x - side * hh * .18:.0f}" cy="{y - hh:.0f}" r="{max(1.2, 7 * t):.1f}" fill="#ffe9a6"/>'
                       f'<circle class="lampg" cx="{x - side * hh * .18:.0f}" cy="{y - hh:.0f}" r="{max(4, 34 * t):.0f}" fill="#ffe9a6" opacity=".16"/>')
    return f'<svg class="lamps" style="position:absolute;left:0;top:0" width="{w}" height="{h}" aria-hidden="true">{"".join(out)}</svg>'


def night_road(w, h, horizon, truck_x, truck_y, truck_w, road_w=560, lamps=False):
    return f'''<div class="night" style="background:linear-gradient(180deg,#090c33 0%,#111865 {horizon / h * 100 - 6:.1f}%,#25307f {horizon / h * 100:.2f}%,#0a0d33 {horizon / h * 100:.2f}%)">
<svg class="st" width="{w}" height="{horizon}" aria-hidden="true">{stars(70, w, horizon - 60)}</svg>
<svg class="sky" style="top:{horizon - 80}px" viewBox="0 0 {w} 80" preserveAspectRatio="none" aria-hidden="true">{skyline(w)}</svg>
<div class="rd" style="top:{horizon}px"><div class="plane"><div class="shoulder" style="left:23%"></div><div class="shoulder" style="right:23%"></div><div class="dash"></div></div><div class="pool"></div></div>
{road_lamps(w, h, horizon) if lamps else ''}<div style="position:absolute;left:{truck_x}px;top:{truck_y}px">{truck_rear(truck_w).replace('class="rear"', 'class="rear" style="position:relative"')}</div>
</div>'''


sign('R45SignRoad.dc.html', 'Sign in, dark split, the night road', ROAD_CSS,
     night_road(840, 900, 560, 372, 572, 96, lamps=True))

# ================================================================ 2. isometric depot at night
C30, S30 = math.cos(math.radians(30)), 0.5


class Iso:
    def __init__(self, ox, oy, s):
        self.ox, self.oy, self.s = ox, oy, s

    def p(self, x, y, z=0):
        return (self.ox + (x - y) * C30 * self.s, self.oy + (x + y) * S30 * self.s - z * self.s)

    def poly(self, pts, fill, extra=''):
        return '<polygon points="' + ' '.join(f'{a:.1f},{b:.1f}' for a, b in (self.p(*q) for q in pts)) + f'" fill="{fill}"{extra}/>'

    def box(self, x, y, z, w, d, h, top, fx, fy, extra=''):
        return ''.join([
            self.poly([(x + w, y, z), (x + w, y + d, z), (x + w, y + d, z + h), (x + w, y, z + h)], fx, extra),
            self.poly([(x, y + d, z), (x + w, y + d, z), (x + w, y + d, z + h), (x, y + d, z + h)], fy, extra),
            self.poly([(x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h), (x, y + d, z + h)], top, extra),
        ])

    def truck_x(self, x, y, livery=True):
        """A box truck facing +x (cargo then cab), 64 long, 16 wide."""
        o = []
        o.append(self.poly([(x - 4, y - 2, 0), (x + 66, y - 2, 0), (x + 66, y + 18, 0), (x - 4, y + 18, 0)], '#000', ' opacity=".35"'))
        o.append(self.box(x, y, 3, 48, 16, 24, '#eef1f7', '#aeb6ca', '#c9d0de'))
        if livery:
            o.append(self.poly([(x, y + 16, 7), (x + 48, y + 16, 12), (x + 48, y + 16, 16), (x, y + 16, 11)], '#f29a1f'))
            o.append(self.poly([(x, y + 16, 3), (x + 48, y + 16, 3), (x + 48, y + 16, 12), (x, y + 16, 7)], '#1f5cc4'))
            # logo on the side
            gx, gy = self.p(x + 6, y + 16, 22)
            o.append(f'<g transform="translate({gx:.1f} {gy:.1f}) skewY(30) scale({.03 * self.s:.3f})" fill="#e8b800">{LOGO_POLY}</g>')
        o.append(self.box(x + 49, y + 1, 3, 13, 14, 17, '#e3e7f0', '#9aa3ba', '#bfc6d6'))
        o.append(self.poly([(x + 62, y + 2, 10), (x + 62, y + 14, 10), (x + 62, y + 14, 18), (x + 62, y + 2, 18)], '#0a0d33'))
        for wx in (x + 8, x + 22, x + 54):
            cx, cy = self.p(wx, y + 16, 3)
            o.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{3.6 * self.s:.1f}" ry="{4.2 * self.s:.1f}" fill="#05071f"/>')
        return ''.join(o)

    def beam_x(self, x, y):
        return self.poly([(x + 62, y + 2, 0), (x + 120, y - 14, 0), (x + 120, y + 30, 0), (x + 62, y + 14, 0)], 'url(#beam)', ' class="beam"')

    def lamp(self, x, y):
        cx, cy = self.p(x, y, 0)
        o = [f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{34 * self.s:.0f}" ry="{18 * self.s:.0f}" fill="url(#pool)"/>']
        o.append(self.box(x, y, 0, 2, 2, 46, '#3b43a3', '#1a2263', '#232a78'))
        hx, hy = self.p(x + 1, y + 1, 47)
        o.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{3 * self.s:.1f}" fill="#ffe9a6"/><circle class="lampg" cx="{hx:.1f}" cy="{hy:.1f}" r="{12 * self.s:.1f}" fill="#ffe9a6" opacity=".18"/>')
        return ''.join(o)


ISO_DEFS = '''<defs><radialGradient id="pool"><stop offset="0" stop-color="#ffe9a6" stop-opacity=".22"/><stop offset="1" stop-color="#ffe9a6" stop-opacity="0"/></radialGradient>
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff3c4" stop-opacity=".34"/><stop offset="1" stop-color="#fff3c4" stop-opacity="0"/></linearGradient>
<linearGradient id="bay" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8b800" stop-opacity=".12"/><stop offset="1" stop-color="#e8b800" stop-opacity=".42"/></linearGradient></defs>'''

ISO_CSS = '''
.iso{position:absolute}
.mv{animation:drive 14s linear infinite}
@keyframes drive{0%{transform:translate(0,0);opacity:0}5%{opacity:1}90%{opacity:1}100%{transform:translate(var(--dx),var(--dy));opacity:0}}
.lampg{animation:lampg 4s ease-in-out infinite}
@keyframes lampg{0%,100%{opacity:.18}50%{opacity:.1}}
.bayl{animation:bayl 5s ease-in-out infinite}
@keyframes bayl{0%,100%{opacity:1}50%{opacity:.8}}
.area{transition:opacity .2s}
'''


def depot_iso(iso, hot=None, wide=False):
    """One depot: building with three bays (dock, service lane, repair bay), a yard, a road along +x."""
    o = [ISO_DEFS]
    W = 300 if wide else 240
    # ground slab and yard grid
    o.append(iso.poly([(-60, -40, 0), (W + 120, -40, 0), (W + 120, 260, 0), (-60, 260, 0)], '#0c1040'))
    grid = []
    for gx in range(-60, W + 121, 20):
        a, b = iso.p(gx, -40), iso.p(gx, 170)
        grid.append(f'M{a[0]:.0f} {a[1]:.0f}L{b[0]:.0f} {b[1]:.0f}')
    for gy in range(-40, 171, 20):
        a, b = iso.p(-60, gy), iso.p(W + 120, gy)
        grid.append(f'M{a[0]:.0f} {a[1]:.0f}L{b[0]:.0f} {b[1]:.0f}')
    o.append(f'<path d="{"".join(grid)}" stroke="#fff" stroke-opacity=".035" fill="none"/>')
    # road along +x at y 190..226, with dashes
    o.append(iso.poly([(-60, 186, 0), (W + 120, 186, 0), (W + 120, 230, 0), (-60, 230, 0)], '#070a2a'))
    for dx in range(-50, W + 120, 30):
        o.append(iso.poly([(dx, 207, 0), (dx + 14, 207, 0), (dx + 14, 209, 0), (dx, 209, 0)], '#e8b800', ' opacity=".5"'))
    # building, three bays on its front (+y) face
    bw = W
    o.append(iso.box(0, 0, 0, bw, 80, 64, '#232b7c', '#141a5a', '#10164d'))
    o.append(iso.box(-2, -2, 64, bw + 4, 84, 4, '#2c3590', '#1a2263', '#1a2263'))
    bays = 3
    seg = bw / bays
    for i in range(bays):
        x0 = i * seg + seg * .14
        x1 = (i + 1) * seg - seg * .14
        lit = '#e8b800' if hot == i else 'url(#bay)'
        op = '.55' if hot == i else '1'
        o.append(iso.poly([(x0, 80, 0), (x1, 80, 0), (x1, 80, 44), (x0, 80, 44)], '#060828'))
        o.append(iso.poly([(x0, 80, 0), (x1, 80, 0), (x1, 80, 44), (x0, 80, 44)], lit, f' class="bayl" opacity="{op}"'))
        o.append(iso.poly([(x0, 80, 36), (x1, 80, 36), (x1, 80, 44), (x0, 80, 44)], '#2c3590'))
    # each bay's own thing in front
    s0, s1, s2 = 0, seg, 2 * seg
    # dock: a raised platform, pallets, a van backed in (facing +y is hard: park it along x in front)
    o.append(iso.box(s0 + 8, 80, 0, seg - 16, 14, 8, '#2c3590', '#1a2263', '#151b5c'))
    o.append(iso.box(s0 + 14, 82, 8, 10, 8, 8, '#8a6a3a', '#5e4826', '#71562e'))
    o.append(iso.box(s0 + 26, 82, 8, 10, 8, 12, '#8a6a3a', '#5e4826', '#71562e'))
    # service lane: canopy posts and a lift-free lane with a checklist board
    o.append(iso.box(s1 + 6, 96, 0, 3, 3, 40, '#3b43a3', '#1a2263', '#232a78'))
    o.append(iso.box(s1 + seg - 9, 96, 0, 3, 3, 40, '#3b43a3', '#1a2263', '#232a78'))
    o.append(iso.box(s1 + 4, 80, 40, seg - 8, 20, 3, '#2c3590', '#1a2263', '#1a2263'))
    # repair bay: tool chest and a car lift
    o.append(iso.box(s2 + seg - 22, 84, 0, 12, 8, 16, '#3b43a3', '#1a2263', '#232a78'))
    o.append(iso.box(s2 + 10, 96, 0, 4, 4, 30, '#3b43a3', '#1a2263', '#232a78'))
    o.append(iso.box(s2 + seg - 30, 96, 0, 4, 4, 30, '#3b43a3', '#1a2263', '#232a78'))
    # parked trucks: one at the dock, one under the canopy, one on the lift (raised a little)
    o.append(iso.truck_x(s0 + 6, 104))
    o.append(iso.truck_x(s1 + 4, 112))
    lift = iso.truck_x(s2 + 4, 118).replace('<polygon', '<polygon', 1)
    o.append(f'<g transform="translate(0 {-6 * iso.s:.1f})">{lift}</g>')
    # office annex with lit windows
    o.append(iso.box(bw + 10, 20, 0, 50, 46, 34, '#232b7c', '#141a5a', '#10164d'))
    for wx in (bw + 16, bw + 30, bw + 44):
        o.append(iso.poly([(wx, 66, 14), (wx + 8, 66, 14), (wx + 8, 66, 24), (wx, 66, 24)], '#ffe9a6', ' opacity=".75"'))
    # lamps
    for lx in (-30, bw / 2, bw + 90):
        o.append(iso.lamp(lx, 176))
    # moving truck along the road, one way
    L = bw + 220
    dx, dy = L * C30 * iso.s, L * S30 * iso.s
    o.append(f'<g class="mv" style="--dx:{dx:.0f}px;--dy:{dy:.0f}px">{iso.beam_x(-150, 194)}{iso.truck_x(-150, 194)}</g>')
    return ''.join(o)


iso_in = Iso(450, 520, 1.3)
sign('R45SignIso.dc.html', 'Sign in, dark split, the depot as a model at night', ISO_CSS + '.lf .iso{left:0;top:0;width:840px;height:900px}',
     f'<svg class="iso" viewBox="0 0 840 900" aria-hidden="true">{depot_iso(iso_in)}</svg>')

# ================================================================ 3. the tilted route map
LAND = [
    '-77.1,288.1 36.0,283.3 77.1,254.0 87.4,224.7 72.0,190.5 56.6,166.0 51.4,136.7 61.7,112.3 102.9,107.4 144.0,117.2 190.3,112.3 221.1,131.9 241.7,151.4 254.6,175.8 262.3,195.3 270.0,212.4 275.1,234.4 277.7,258.8 270.0,268.6 252.0,275.9 231.4,280.8 216.0,288.1 205.7,297.9 180.0,307.7 159.4,341.9 138.9,356.5 87.4,366.3 -77.1,351.6',
    '313.7,239.3 349.7,236.9 365.1,244.2 380.6,268.6 406.3,258.8 432.0,254.0 447.4,278.4 452.6,322.3 478.3,302.8 504.0,293.0 534.9,312.6 504.0,361.4 468.0,390.7 426.9,410.2 401.1,415.1 370.3,390.7 349.7,361.4 344.6,346.7 329.1,332.1 316.3,317.4 308.6,293.0 313.7,263.7',
]
ROADS = [
    ('M324.0 156.3 L324.0 185.6 L318.9 214.9 L308.6 239.3 L303.4 254.0', .1, 2),
    ('M329.1 190.5 L365.1 195.3 L396.0 205.1', .1, 2),
    ('M257.1 273.5 L252.0 337.0 L262.3 385.8 L267.4 424.9', .1, 2),
    ('M108.0 -29.3 L174.9 29.3 L200.6 58.6 L226.3 87.9 L246.9 107.4 L264.9 136.7 L275.1 156.3 L282.9 177.3', .25, 4),
    ('M282.9 177.3 L293.1 205.1 L293.1 234.4', .18, 3),
    ('M293.1 234.4 L303.4 258.8 L306.0 293.0 L311.1 322.3 L329.1 351.6 L349.7 376.0 L365.1 410.2 L385.7 449.3', .25, 4),
]
TRIPS = [
    ('M205 58 Q199 74 186 86', 9, -1.4), ('M205 58 Q243 92 262 139', 12, -4.2), ('M205 58 Q261 67 306 101', 10, -6.9),
    ('M336 186 Q318 181 305 168', 10, -4.7), ('M336 186 Q314 201 288 205', 13, -7.4), ('M336 186 Q328 211 309 230', 11, -10.1),
    ('M336 186 Q340 162 355 142', 9, -12.8), ('M332 357 Q289 357 250 337', 11, -8.9), ('M332 357 Q351 375 360 400', 9, -11.6),
    ('M332 357 Q304 379 270 386', 12, -14.3), ('M332 357 Q310 328 303 293', 10, -17.0),
]
BRANCHES = [(205, 58, 'Pulilan'), (336, 186, 'Marikina'), (332, 357, 'Sta. Rosa')]


def route_map(hot_labels=True):
    o = ['<svg viewBox="-40 -40 620 500" width="620" height="500" aria-hidden="true" overflow="visible">',
         '<defs><radialGradient id="bg"><stop offset="0" stop-color="#e8b800" stop-opacity=".35"/><stop offset="1" stop-color="#e8b800" stop-opacity="0"/></radialGradient></defs>']
    grid = ''.join(f'M{x} -40V460' for x in range(-40, 581, 30)) + ''.join(f'M-40 {y}H580' for y in range(-40, 461, 30))
    o.append(f'<path d="{grid}" stroke="#fff" stroke-opacity=".05" fill="none"/>')
    for pts in LAND:
        o.append(f'<polygon points="{pts}" fill="#1c2675" stroke="#3b43a3" stroke-width="1.4"/>')
    for d, op, w in ROADS:
        o.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-opacity="{op}" stroke-width="{w}" stroke-linecap="round"/>')
    for d, dur, begin in TRIPS:
        o.append(f'<path d="{d}" fill="none" stroke="#e8b800" stroke-opacity=".55" stroke-width="2.2" stroke-dasharray="3 5" stroke-linecap="round"/>')
        o.append(f'<g><rect x="-5" y="-3.5" width="10" height="7" rx="2" fill="#fff"/><rect x="2.5" y="-3.5" width="3.5" height="7" rx="1" fill="#e8b800"/>'
                 f'<animateMotion dur="{dur}s" begin="{begin}s" repeatCount="indefinite" path="{d}" rotate="auto" keyPoints="0;1;1;0;0" keyTimes="0;.42;.5;.92;1" calcMode="linear"/></g>')
    for x, y, nm in BRANCHES:
        o.append(f'<circle cx="{x}" cy="{y}" r="46" fill="url(#bg)"/><circle cx="{x}" cy="{y}" r="11" fill="#0f1445" stroke="#e8b800" stroke-width="2.5"/>'
                 f'<path d="M{x - 5} {y + 4}V{y - 1}L{x} {y - 5}L{x + 5} {y - 1}V{y + 4}Z" fill="#e8b800"/>')
        if hot_labels:
            o.append(f'<text x="{x + 18}" y="{y + 5}" font-size="15" font-weight="700" fill="#fff" font-family="Inter,sans-serif">{nm}</text>')
    o.append('</svg>')
    return ''.join(o)


MAP_CSS = '''
.tilt{position:absolute;transform-style:preserve-3d}
.tilt .pl{transform:perspective(1300px) rotateX(46deg) rotateZ(-16deg);transform-origin:50% 50%}
.vign{position:absolute;inset:0;background:radial-gradient(ellipse 75% 62% at 50% 72%,transparent 50%,#0f1445 92%);pointer-events:none}
'''
sign('R45SignMap.dc.html', 'Sign in, dark split, the route map tilted into the distance', MAP_CSS,
     f'<div class="tilt" style="left:-10px;top:300px;transform:scale(1.5);transform-origin:0 0"><div class="pl">{route_map()}</div></div><div class="vign"></div>')

# ================================================================ 4. headlights at the garage door
FRONT = f'''<svg class="fr" viewBox="0 0 840 900" aria-hidden="true">
<defs>
<linearGradient id="bm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff6d6" stop-opacity=".42"/><stop offset="1" stop-color="#fff6d6" stop-opacity="0"/></linearGradient>
<radialGradient id="gl"><stop offset="0" stop-color="#fffbe8"/><stop offset=".35" stop-color="#fff2b8" stop-opacity=".7"/><stop offset="1" stop-color="#fff2b8" stop-opacity="0"/></radialGradient>
<linearGradient id="door" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8b800" stop-opacity=".05"/><stop offset="1" stop-color="#e8b800" stop-opacity=".22"/></linearGradient>
<linearGradient id="ws" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2c3590"/><stop offset=".5" stop-color="#0a0d33"/><stop offset="1" stop-color="#141a55"/></linearGradient>
</defs>
<rect x="0" y="380" width="840" height="350" fill="#121852"/>
<rect x="150" y="400" width="540" height="330" fill="#070a2e"/>
<rect x="150" y="400" width="540" height="330" fill="url(#door)"/>
<g stroke="#1a2263" stroke-width="3"><path d="M150 412h540M150 424h540M150 436h540"/></g>
<rect x="136" y="388" width="568" height="14" fill="#1a2263"/>
<rect x="0" y="730" width="840" height="170" fill="#0a0d33"/>
<g class="beams"><path d="M318 690 L40 900 H330 L366 690Z" fill="url(#bm)"/><path d="M522 690 L800 900 H510 L474 690Z" fill="url(#bm)"/></g>
<ellipse cx="420" cy="830" rx="330" ry="54" fill="#fff6d6" opacity=".06"/>
<g class="cab">
<rect x="282" y="420" width="276" height="210" rx="6" fill="#c9d0de"/>
<rect x="282" y="420" width="276" height="210" rx="6" fill="#0f1445" opacity=".25"/>
<g transform="translate(330 452) scale(.17)" fill="#e8b800">{LOGO_POLY}</g>
<text x="400" y="482" font-size="28" font-weight="800" font-style="italic" fill="#0f1445" font-family="Inter,sans-serif">WeLinc</text>
<path d="M296 560 C360 548 470 572 544 548 V588 C470 610 360 584 296 598 Z" fill="#f29a1f" opacity=".85"/>
<path d="M296 590 C360 576 470 602 544 580 V624 H296 Z" fill="#1f5cc4" opacity=".85"/>
<path d="M306 598 Q306 560 340 556 H500 Q534 560 534 598 V760 H306 Z" fill="#e9ecf4"/>
<path d="M306 598 Q306 560 340 556 H500 Q534 560 534 598 V760 H306 Z" fill="#0f1445" opacity=".18"/>
<path d="M326 604 Q328 580 350 578 H490 Q512 580 514 604 L506 660 H334 Z" fill="url(#ws)"/>
<path d="M360 590 L392 590 L360 650 Z" fill="#fff" opacity=".08"/>
<rect x="276" y="612" width="18" height="40" rx="4" fill="#2a2f45"/><rect x="546" y="612" width="18" height="40" rx="4" fill="#2a2f45"/>
<path d="M294 626h12M534 626h12" stroke="#2a2f45" stroke-width="4"/>
<rect x="370" y="684" width="100" height="44" rx="5" fill="#1b1f33"/>
<g stroke="#2e3450" stroke-width="3"><path d="M376 696h88M376 706h88M376 716h88"/></g>
<g transform="translate(404 670) scale(.1)" fill="#e8b800">{LOGO_POLY}</g>
<rect x="318" y="684" width="44" height="26" rx="6" fill="#fffbe8"/><rect x="478" y="684" width="44" height="26" rx="6" fill="#fffbe8"/>
<circle class="hl" cx="340" cy="697" r="70" fill="url(#gl)"/><circle class="hl" cx="500" cy="697" r="70" fill="url(#gl)"/>
<rect x="300" y="738" width="240" height="26" rx="5" fill="#2a2f45"/>
<rect x="396" y="742" width="48" height="16" rx="2" fill="#e9ecf4"/><text x="420" y="754" font-size="9.5" font-weight="700" fill="#0f1445" text-anchor="middle" font-family="IBM Plex Mono,monospace">DAK 2917</text>
<rect x="312" y="764" width="36" height="30" rx="5" fill="#05071f"/><rect x="492" y="764" width="36" height="30" rx="5" fill="#05071f"/>
</g>
<ellipse cx="420" cy="796" rx="170" ry="10" fill="#000" opacity=".45"/>
</svg>'''
FRONT_CSS = '''
.fr{position:absolute;left:0;top:70px;width:840px;height:900px}
.beams{animation:beams 6s ease-in-out infinite}
@keyframes beams{0%,100%{opacity:1}48%{opacity:1}50%{opacity:.25}52%{opacity:1}}
.hl{animation:hl 6s ease-in-out infinite}
@keyframes hl{0%,100%{opacity:1}48%{opacity:1}50%{opacity:.2}52%{opacity:1}}
.cab{animation:idle 1.4s ease-in-out infinite}
@keyframes idle{0%,100%{transform:translateY(0)}50%{transform:translateY(.8px)}}
'''
sign('R45SignFront.dc.html', 'Sign in, dark split, headlights at the garage door', FRONT_CSS, FRONT)

# ================================================================ 5. the logo's slashes, a van driving through
SLASH = f'''<svg class="sl" viewBox="0 0 1100 900" aria-hidden="true">
<defs>{V_VAN}<linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1d2570"/><stop offset="1" stop-color="#121852"/></linearGradient></defs>
<g transform="translate(40 330) scale(3.2)">
<polygon points="82,0 144,0 66,183 4,183" fill="url(#sg)"/>
<polygon points="177,0 240,0 162,183 100,183" fill="url(#sg)"/>
<polygon points="265,0 328,0 268,140 328,140 328,183 187,183" fill="url(#sg)"/>
<path d="M144 0 L66 183" stroke="#e8b800" stroke-width="1"/><path d="M240 0 L162 183" stroke="#e8b800" stroke-opacity=".35" stroke-width=".8"/>
</g>
<rect x="0" y="742" width="1100" height="158" fill="#0a0d33"/>
<path d="M0 742H1100" stroke="#2c3590" stroke-width="2"/>
<path class="ln2" d="M0 812H1100" stroke="#e8b800" stroke-opacity=".5" stroke-width="4" stroke-dasharray="40 34"/>
<g class="drive"><ellipse cx="160" cy="744" rx="150" ry="7" fill="#000" opacity=".45"/><use href="#van" x="0" y="620" width="320" height="130"/></g>
</svg>'''
SLASH_CSS = '''
.lf{width:1100px}
.sl{position:absolute;left:0;top:0;width:1100px;height:900px}
.rt{width:760px;clip-path:polygon(384px 0,100% 0,100% 100%,0 100%);padding-left:200px;background:#0a0d33}
.drive{animation:vdrive 11s linear infinite}
@keyframes vdrive{0%{transform:translateX(-360px)}100%{transform:translateX(1160px)}}
.ln2{animation:ln2 1.2s linear infinite}
@keyframes ln2{to{stroke-dashoffset:-74}}
'''
# S20 (the logo's slashes) was dropped after its screenshot: the stripes read as generic.

print('sign in ok')

# ================================================================ LAUNCHER parts
SYS = [
    dict(code='BMS', name='Booking Management System', word='Bookings', role='Operations', desc='Bookings, trips and job orders',
         does=['Take bookings and plan trips', 'Assign trucks, drivers and helpers', 'Close job orders']),
    dict(code='VMMS', name='Vehicle Maintenance Management System', word='Maintenance', role='Operations', desc='Planned and preventive maintenance',
         does=['Keep each truck on its service schedule', 'Log fuel and odometer readings', 'See what is due this week']),
    dict(code='VRMS', name='Vehicle Repair Management System', word='Repairs', role='Chief Mechanic', desc='Repair tickets, mechanics and parts',
         does=['Open and track repair tickets', 'Assign mechanics to the work', 'Record the parts used']),
]

LBASE = BASE + '''
.pg{background:#f3f5f9;color:#0f172a}
.wrap{width:1200px;margin:0 auto;position:relative}
.top{height:64px;display:flex;align-items:center}
.me{margin-left:auto;display:flex;align-items:center;gap:10px;height:44px;padding:0 8px;border-radius:12px;border:0;background:none;color:#fff;font:500 14px Inter,sans-serif}
.av{width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.12);box-shadow:inset 0 0 0 1px rgba(255,255,255,.22);display:grid;place-items:center;font-size:12px;font-weight:600}
.dt{margin:0;font-size:13px;font-weight:600;color:#e8b800}
.hi{margin:8px 0 0;font-size:44px;line-height:1.05;font-weight:800;letter-spacing:-.03em;color:#fff}
.l{margin:10px 0 0;font-size:16px;color:rgba(255,255,255,.7)}
.acct{display:flex;align-items:center;gap:28px;font-size:13px;color:#5b6779;border-top:1px solid #e2e8f0;padding-top:16px}
.acct b{font-weight:600;color:#0f172a}
.acct a{margin-left:auto;font-weight:600;color:#1a1f6e;text-decoration:underline;text-underline-offset:3px;text-decoration-color:#c7cde0}
.acct .sep{width:1px;height:14px;background:#d5dbe6}
''' + '''
/* app previews: each system's real first screen, drawn small */
.pv{display:grid;grid-template-columns:40px 1fr;width:100%;height:100%;background:#f6f7fb;border-radius:12px;overflow:hidden;box-shadow:inset 0 0 0 1px #e2e8f0;font-size:9px;color:#0f172a;text-align:left}
.pv .sb{background:#0f1445;padding:10px 8px;display:flex;flex-direction:column;gap:7px}
.pv .sb i{display:block;height:6px;border-radius:3px;background:rgba(255,255,255,.18)}
.pv .sb i.on{background:rgba(255,255,255,.55)}
.pv .sb b{display:block;width:16px;height:9px;margin-bottom:6px;background:#e8b800;clip-path:polygon(25% 0,45% 0,20% 100%,0 100%)}
.pv .ct{padding:10px 12px;min-width:0}
.pv .t{font-size:11px;font-weight:700;display:flex;justify-content:space-between;align-items:baseline}
.pv .t span{font-weight:500;color:#5b6779;font-size:9px}
.pv .r{display:grid;align-items:center;gap:8px;padding:6px 0;border-top:1px solid #e6e9f1;white-space:nowrap}
.pv .kp{display:flex;gap:10px;margin:7px 0 4px;color:#5b6779;white-space:nowrap}.pv .kp b{font-family:'IBM Plex Mono',monospace;color:#0f172a}.pv .kp .od b{color:#8a5a00}
.pv .r{row-gap:4px}
.pv .m{font-family:"IBM Plex Mono",monospace;font-weight:600;color:#1a1f6e}
.pv .g{color:#5b6779;overflow:hidden;text-overflow:ellipsis}
.pv .s{justify-self:end;font-weight:600;color:#334155}
.pv .pb{height:5px;border-radius:3px;background:#e6e9f1;overflow:hidden}.pv .pb i{display:block;height:100%;background:#1a1f6e}
.pv .od{color:#8a5a00}
.pv .kb{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;margin-top:6px}
.pv .kc{background:#eceff6;border-radius:7px;padding:6px}
.pv .kc>span{display:block;font-weight:600;color:#5b6779;margin-bottom:5px}
.pv .tk{background:#fff;border-radius:5px;padding:5px 6px;margin-top:4px;box-shadow:0 1px 1px rgba(15,23,42,.06);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pv .tk em{display:block;font-style:normal;font-family:"IBM Plex Mono",monospace;color:#5b6779;font-size:8px;margin-top:2px}
'''


def pv_side(active):
    return '<span class="sb"><b></b>' + ''.join(f'<i class="{"on" if k == active else ""}"></i>' for k in range(5)) + '</span>'


def preview(code, big=False):
    if code == 'BMS':
        rows = [('08:00', 'Lipat bahay, Marikina to Antipolo', 'On the road'), ('09:30', 'Office pull out, Pasig to Makati', 'Loading'),
                ('11:00', 'Condo move, Mandaluyong to BGC', 'On the road'), ('13:00', 'Corporate delivery, Taguig to Sta. Rosa', 'Booked'),
                ('14:00', 'Furniture drop, Cainta to San Juan', 'Booked'), ('15:30', 'Lipat bahay, Cainta to Quezon City', 'Booked'),
                ('17:00', 'Office pull out, Ortigas to Pasay', 'Booked'), ('18:30', 'Warehouse run, Pulilan to Malolos', 'Booked')]
        body = ('<span class="t">Today\'s trips<span>Wed, Nov 25</span></span><span class="kp"><span><b>8</b> trips</span><span><b>2</b> on the road</span><span><b>1</b> loading</span></span>' + ''.join(
            f'<span class="r" style="grid-template-columns:34px 1fr auto"><span class="m">{a}</span><span class="g">{b}</span><span class="s">{c}</span></span>' for a, b, c in rows))
        return f'<span class="pv">{pv_side(0)}<span class="ct">{body}</span></span>'
    if code == 'VMMS':
        rows = [('CAK 9043', '10,000 km service', 'Nov 27', 82), ('DAK 2917', 'Oil and filter', '2 days late', 100), ('DCR 5096', 'Tire rotation', 'Dec 3', 46),
                ('NBK 4410', 'Brake check', 'Dec 9', 20), ('NAB 7782', 'Aircon cleaning', 'Dec 11', 15), ('CBE 3315', '20,000 km service', 'Dec 14', 10),
                ('DAG 6021', 'Battery check', 'Dec 18', 6), ('NCF 1189', 'Wheel alignment', 'Dec 20', 4)]
        body = ('<span class="t">Due this week<span>14 trucks</span></span><span class="kp"><span><b>4</b> due</span><span class="od"><b>1</b> late</span><span><b>9</b> on schedule</span></span>' + ''.join(
            f'<span class="r" style="grid-template-columns:50px 1fr auto"><span class="m">{a}</span><span class="g">{b}</span><span class="s{" od" if "late" in c else ""}">{c}</span><span class="pb" style="grid-column:1/-1"><i style="width:{p}%"></i></span></span>' for a, b, c, p in rows))
        return f'<span class="pv">{pv_side(1)}<span class="ct">{body}</span></span>'
    cols = [('Open 3', [('Brake hose cracked', 'DAK 2917'), ('Aircon not cooling', 'CAK 9043'), ('Tail light out', 'NAB 7782'), ('Door seal torn', 'CBE 3315')]),
            ('In progress 2', [('Brake pads worn', 'DCR 5096'), ('Tail lift slow', 'NBK 4410'), ('Wiper motor', 'DAG 6021')]),
            ('Ready 1', [('Clutch slipping', 'NBK 4410'), ('Fan belt squeal', 'NCF 1189')])]
    body = ('<span class="t">Repair tickets<span>Marikina</span></span><span class="kp"><span><b>6</b> open</span><span><b>3</b> mechanics in</span><span><b>1</b> waiting on parts</span></span><span class="kb">' + ''.join(
        f'<span class="kc"><span>{h}</span>' + ''.join(f'<span class="tk">{t}<em>{p}</em></span>' for t, p in ts) + '</span>' for h, ts in cols) + '</span>')
    return f'<span class="pv">{pv_side(2)}<span class="ct">{body}</span></span>'


def topbar():
    return (f'<div class="top">{LK}<button class="me" type="button" aria-label="Account menu for Corazon Villareal">'
            f'<span class="av">CV</span>Corazon Villareal{CHEV}</button></div>')


ACCT = ('<div class="acct"><span>Last sign in <b>yesterday, 5:42 PM</b> on Chrome, Windows</span><span class="sep"></span>'
        '<span><b>2</b> devices signed in</span><span class="sep"></span><span>corazon.villareal@welinc.com</span>'
        '<a href="#">Your profile and sign ins</a></div>')

# ---------- L15: the night road in the band, cards that show the real screen ----------
la_css = LBASE + ROAD_CSS + '''
.band{position:relative;height:420px;background:#0f1445;overflow:hidden}
.band .scn{position:absolute;right:0;top:0;width:820px;height:420px;overflow:hidden}
.band .scn::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,#0f1445 0,rgba(15,20,69,0) 30%)}
.band .gr{padding-top:40px;position:relative;z-index:2}
.cards{display:grid;grid-template-columns:repeat(3,384px);gap:24px;margin:24px 0 0;padding:0;list-style:none}
.cards li{display:flex}
.cd{flex:1;display:block;background:#fff;border-radius:20px;padding:12px 12px 18px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 24px rgba(15,23,42,.07)}
.cd.on{box-shadow:0 0 0 2px #0f1445,0 16px 32px rgba(15,23,42,.14);transform:translateY(-3px)}
.cd .sh{display:block;height:196px}
.cd .nm{display:block;margin:16px 10px 0;font-size:17px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cd .ds{display:flex;justify-content:space-between;margin:6px 10px 0;font-size:13px;color:#5b6779}
.cd .ds b{color:#0f172a;font-weight:600}
.foot{position:absolute;left:0;right:0;bottom:30px}
'''
la_cards = ''.join(f'<li><a class="cd{" on" if i == 2 else ""}" href="#"><span class="sh">{preview(s["code"])}</span><span class="nm">{s["name"]}</span>'
                   f'<span class="ds"><span>{s["desc"]}</span><b>{s["role"]}</b></span></a></li>' for i, s in enumerate(SYS))
la_body = f'''<div class="pg"><div class="band"><div class="scn">{night_road(820, 420, 250, 340, 226, 140)}</div>
<div class="wrap">{topbar()}<div class="gr"><p class="dt">Wednesday, November 25</p><h1 class="hi">Good morning,<br>Corazon</h1><p class="l">Pick where you want to work today.</p></div></div></div>
<div class="wrap"><ul class="cards">{la_cards}</ul></div><div class="wrap foot">{ACCT}</div></div>'''
write('R45LaunchRoad.dc.html', page('Launcher, the night road in the band, cards show the real screen', la_css + RM, la_body))

# ---------- L16: the depot model fills the band, one bar of three underneath ----------
iso_l = Iso(640, 250, 1.25)
lb_css = LBASE + ISO_CSS + '''
.band{position:relative;height:560px;background:#0f1445;overflow:hidden}
.band .iso{position:absolute;left:0;top:0;width:1440px;height:560px}
.band .gr{padding-top:32px;position:relative;z-index:2}
.bar3{display:grid;grid-template-columns:repeat(3,1fr);margin-top:24px;background:#fff;border-radius:20px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 10px 28px rgba(15,23,42,.08);overflow:hidden}
.seg{display:block;padding:22px 26px 24px;position:relative}
.seg+.seg{box-shadow:inset 1px 0 0 #e8ebf2}
.seg.on{background:#0f1445;color:#fff}
.seg .k{display:block;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.08em;color:#5b6779}
.seg.on .k{color:#e8b800}
.seg .nm{display:block;margin-top:8px;font-size:17px;font-weight:700}
.seg .ds{display:block;margin-top:6px;font-size:13px;color:#5b6779}
.seg.on .ds{color:rgba(255,255,255,.7)}
.seg .rl{display:block;margin-top:14px;font-size:13px;color:#5b6779}.seg .rl b{color:#0f172a;font-weight:600}
.seg.on .rl{color:rgba(255,255,255,.7)}.seg.on .rl b{color:#fff}
.foot{position:absolute;left:0;right:0;bottom:30px}
'''
lb_seg = ''.join(f'<a class="seg{" on" if i == 1 else ""}" href="#"><span class="k">{["THE DOCK", "THE SERVICE LANE", "THE REPAIR BAY"][i]}</span><span class="nm">{s["name"]}</span>'
                 f'<span class="ds">{s["desc"]}</span><span class="rl">Your role <b>{s["role"]}</b></span></a>' for i, s in enumerate(SYS))
lb_body = f'''<div class="pg"><div class="band"><svg class="iso" viewBox="0 0 1440 560" aria-hidden="true">{depot_iso(iso_l, hot=1, wide=True)}</svg>
<div class="wrap">{topbar()}<div class="gr"><p class="dt">Wednesday, November 25</p><h1 class="hi">Good morning,<br>Corazon</h1><p class="l">Pick where you want to work today.</p></div></div></div>
<div class="wrap"><nav class="bar3" aria-label="Your systems">{lb_seg}</nav></div><div class="wrap foot">{ACCT}</div></div>'''
write('R45LaunchModel.dc.html', page('Launcher, the depot model fills the band, one bar of three under it', lb_css + RM, lb_body))

# ---------- L17: split, like the sign in; last opened leads ----------
lc_css = LBASE + MAP_CSS + '''
.lp{position:absolute;left:0;top:0;width:520px;height:900px;background:#0f1445;color:#fff;overflow:hidden}
.lp .lk{position:absolute;left:48px;top:22px;z-index:2}
.lp .gr{position:absolute;left:48px;top:104px;z-index:2}
.lp .hi{font-size:40px}
.lp .meta{position:absolute;left:48px;right:48px;bottom:40px;z-index:2;font-size:13px;color:rgba(255,255,255,.66);display:grid;gap:10px}
.lp .meta div{display:flex;justify-content:space-between;border-top:1px solid rgba(255,255,255,.1);padding-top:10px}
.lp .meta b{color:#fff;font-weight:600}
.lp .meta a{color:#fff;font-weight:600;text-decoration:underline;text-underline-offset:3px;text-decoration-color:rgba(255,255,255,.35)}
.rp{position:absolute;left:520px;right:0;top:0;bottom:0;padding:22px 56px}
.rp .bar{display:flex;align-items:center;height:44px}
.rp .bar h2{margin:0;font-size:15px;font-weight:600;color:#5b6779}
.rp .me{color:#0f172a}.rp .av{background:#eef0f8;box-shadow:inset 0 0 0 1px #dfe3ee;color:#1a1f6e}
.lead{display:grid;grid-template-columns:1fr 300px;gap:28px;margin-top:22px;background:#fff;border-radius:22px;padding:16px;box-shadow:0 0 0 2px #0f1445,0 16px 36px rgba(15,23,42,.12)}
.lead .sh{height:400px}
.lead .pv{zoom:1.3;height:308px}
.lead .tx{padding:14px 8px 8px 0;display:flex;flex-direction:column}
.lead .k{font:600 12px "IBM Plex Mono",monospace;letter-spacing:.08em;color:#8a5a00}
.lead .nm{margin-top:10px;font-size:24px;font-weight:800;letter-spacing:-.02em;line-height:1.15}
.lead ul{margin:16px 0 0;padding:0;list-style:none}
.lead li{padding:9px 0;border-top:1px solid #eef1f6;font-size:14px;color:#334155}
.lead .rl{margin-top:auto;font-size:13px;color:#5b6779}.lead .rl b{color:#0f172a}
.two{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:24px}
.sm{display:flex;flex-direction:column;gap:4px;background:#fff;border-radius:20px;padding:12px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 24px rgba(15,23,42,.07)}
.sm .sh{height:216px}
.sm .tx{padding:12px 8px 6px;display:flex;flex-direction:column;flex:1}
.sm .rl{margin-top:10px!important}
.sm .nm{font-size:16px;font-weight:700;line-height:1.25}
.sm .ds{margin-top:6px;font-size:13px;color:#5b6779}
.sm .rl{margin-top:auto;font-size:13px;color:#5b6779}.sm .rl b{color:#0f172a}
'''
v = SYS[2]
lc_body = f'''<div class="pg">
<div class="lp"><div class="tilt" style="left:-60px;top:330px;transform:scale(1.1);transform-origin:0 0"><div class="pl">{route_map(hot_labels=False)}</div></div><div class="vign"></div>
{LK}<div class="gr"><p class="dt">Wednesday, November 25</p><h1 class="hi">Good morning,<br>Corazon</h1><p class="l">Three systems, one sign in.</p></div>
<div class="meta"><div><span>Last sign in</span><b>Yesterday, 5:42 PM, Chrome on Windows</b></div><div><span>Devices signed in</span><b>2</b></div><div><span>corazon.villareal@welinc.com</span><a href="#">Your profile</a></div></div></div>
<div class="rp"><div class="bar"><h2>Your systems</h2><button class="me" type="button" aria-label="Account menu for Corazon Villareal"><span class="av">CV</span>Corazon Villareal{CHEV}</button></div>
<a class="lead" href="#"><span class="sh">{preview("VRMS", big=True)}</span><span class="tx"><span class="k">LAST OPENED YESTERDAY</span><span class="nm">{v["name"]}</span>
<ul>{"".join(f"<li>{d}</li>" for d in v["does"])}</ul><span class="rl">Your role <b>{v["role"]}</b></span></span></a>
<div class="two">{"".join(f'<a class="sm" href="#"><span class="sh">{preview(s["code"])}</span><span class="tx"><span class="nm">{s["name"]}</span><span class="ds">{s["desc"]}</span><span class="rl">Your role <b>{s["role"]}</b></span></span></a>' for s in SYS[:2])}</div>
</div></div>'''
write('R45LaunchSplit.dc.html', page('Launcher, split like the sign in, last opened leads', lc_css + RM, lc_body))

# ---------- L18: bento, the page filled with real things ----------
FRONT_SMALL = FRONT.replace('class="fr" viewBox="0 0 840 900"', 'class="frs" viewBox="120 360 600 470"')
ld_css = LBASE + FRONT_CSS + '''
.hdr{background:#0f1445}
.bento{display:grid;grid-template-columns:repeat(4,1fr);grid-template-rows:210px 270px 270px;gap:16px;margin-top:20px}
.t{border-radius:22px;background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 24px rgba(15,23,42,.06);overflow:hidden;position:relative}
.hello{grid-column:span 2;background:#0f1445;color:#fff;padding:28px 30px}
.hello .frs{position:absolute;right:-30px;bottom:-40px;width:300px;height:235px}
.hello .hi{font-size:38px}
.clock{padding:24px 26px;display:flex;flex-direction:column}
.clock .k,.me3 .k{font:600 12px "IBM Plex Mono",monospace;letter-spacing:.08em;color:#5b6779}
.clock b{margin-top:auto;font:600 52px "IBM Plex Mono",monospace;letter-spacing:-.03em;color:#0f1445}
.clock span{margin-top:6px;font-size:13px;color:#5b6779}
.me3{padding:24px 26px;display:flex;flex-direction:column;font-size:13px;color:#5b6779}
.me3 dl{margin:14px 0 0;display:grid;grid-template-columns:auto 1fr;gap:8px 12px}.me3 dd{margin:0;text-align:right;color:#0f172a;font-weight:500}
.me3 a{margin-top:auto;font-weight:600;color:#1a1f6e;text-decoration:underline;text-underline-offset:3px;text-decoration-color:#c7cde0}
.big{grid-column:span 2;grid-row:span 2;display:flex;flex-direction:column;padding:14px}
.big .sh{height:452px}
.big .pv{zoom:1.45;height:312px}
.big .tx{padding:16px 10px 6px;display:flex;justify-content:space-between;align-items:flex-end;flex:1}
.big .k{font:600 12px "IBM Plex Mono",monospace;letter-spacing:.08em;color:#8a5a00}
.big .nm{display:block;margin-top:6px;font-size:22px;font-weight:800;letter-spacing:-.02em}
.big .rl{font-size:13px;color:#5b6779;text-align:right}.big .rl b{display:block;color:#0f172a;font-size:14px}
.wd{grid-column:span 2;display:grid;grid-template-columns:1fr 250px;gap:16px;padding:14px}
.wd .tx{padding:8px 4px 4px 8px;display:flex;flex-direction:column}
.wd .nm{font-size:17px;font-weight:700;line-height:1.25}
.wd .ds{margin-top:6px;font-size:13px;color:#5b6779}
.wd .rl{margin-top:auto;font-size:13px;color:#5b6779}.wd .rl b{color:#0f172a}
'''
ld_body = f'''<div class="pg"><div class="hdr"><div class="wrap">{topbar()}</div></div><div class="wrap"><div class="bento">
<div class="t hello">{FRONT_SMALL}<p class="dt">Wednesday, November 25</p><h1 class="hi">Good morning,<br>Corazon</h1><p class="l">Pick where you want to work today.</p></div>
<div class="t clock"><span class="k">MANILA</span><b>9:41</b><span>AM, Wednesday</span></div>
<div class="t me3"><span class="k">YOUR ACCOUNT</span><dl><dt>Last sign in</dt><dd>Yesterday, 5:42 PM</dd><dt>Devices</dt><dd>2 signed in</dd><dt>Systems</dt><dd>3</dd></dl><a href="#">Your profile and sign ins</a></div>
<a class="t big" href="#"><span class="sh">{preview("VRMS", big=True)}</span><span class="tx"><span><span class="k">PICK UP WHERE YOU LEFT OFF</span><span class="nm">{v["name"]}</span></span><span class="rl">Your role<b>{v["role"]}</b></span></span></a>
{"".join(f'<a class="t wd" href="#"><span class="tx"><span class="nm">{s["name"]}</span><span class="ds">{s["desc"]}</span><span class="rl">Your role <b>{s["role"]}</b></span></span><span class="sh">{preview(s["code"])}</span></a>' for s in SYS[:2])}
</div></div></div>'''
write('R45LaunchBento.dc.html', page('Launcher, bento, the page filled with real things', ld_css + RM, ld_body))

# ---------- L19: three panels, the one you point at opens up ----------
le_css = LBASE + '''
.hdr{background:#0f1445}
.head{display:flex;align-items:flex-end;justify-content:space-between;padding:30px 0 22px}
.head .dt{color:#1a1f6e}
.head .hi{color:#0f1445;font-size:40px}
.head p.r{margin:0;font-size:14px;color:#5b6779;text-align:right;line-height:1.6}.head p.r b{color:#0f172a}
.pans{display:flex;gap:16px;height:628px}
.pan{flex:1;display:flex;flex-direction:column;border-radius:24px;background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 24px rgba(15,23,42,.06);overflow:hidden;transition:flex .4s cubic-bezier(.2,.8,.2,1);position:relative}
.pan.open{flex:2.5;background:#0f1445;color:#fff}
.pan .sh{display:block;margin:14px 14px 0;height:330px}
.pan.open .sh{height:380px}
.pan.open .pv{zoom:1.5;height:253px}
.pan .tx{padding:22px 26px;display:flex;flex-direction:column;flex:1}
.pan .k{font:600 12px "IBM Plex Mono",monospace;letter-spacing:.08em;color:#5b6779}
.pan.open .k{color:#e8b800}
.pan .nm{margin-top:8px;font-size:20px;font-weight:800;letter-spacing:-.02em;line-height:1.2}
.pan.open .nm{font-size:28px}
.pan .ds{margin-top:8px;font-size:14px;color:#5b6779}
.pan.open .ds{color:rgba(255,255,255,.7)}
.pan .rl{margin-top:auto;font-size:13px;color:#5b6779}.pan .rl b{color:#0f172a}
.pan.open .rl{color:rgba(255,255,255,.7)}.pan.open .rl b{color:#fff}
.pan.open .row{display:flex;gap:28px;margin-top:16px}
.pan.open .row span{font-size:14px;color:rgba(255,255,255,.82);border-top:1px solid rgba(255,255,255,.16);padding-top:10px;flex:1}
'''


def panel(i, s, open_):
    row = ('<span class="row">' + ''.join(f'<span>{d}</span>' for d in s['does']) + '</span>') if open_ else ''
    return (f'<a class="pan{" open" if open_ else ""}" href="#"><span class="sh">{preview(s["code"], big=open_)}</span><span class="tx">'
            f'<span class="k">{s["word"].upper()}</span><span class="nm">{s["name"]}</span><span class="ds">{s["desc"]}</span>{row}'
            f'<span class="rl">Your role <b>{s["role"]}</b></span></span></a>')


le_body = f'''<div class="pg"><div class="hdr"><div class="wrap">{topbar()}</div></div><div class="wrap">
<div class="head"><div><p class="dt">Wednesday, November 25</p><h1 class="hi">Good morning, Corazon</h1></div><p class="r">Last sign in <b>yesterday, 5:42 PM</b><br><b>2</b> devices signed in</p></div>
<div class="pans">{panel(0, SYS[0], False)}{panel(1, SYS[1], False)}{panel(2, SYS[2], True)}</div></div></div>'''
write('R45LaunchPanels.dc.html', page('Launcher, three panels, the one you point at opens up', le_css + RM, le_body))
print('launcher ok')

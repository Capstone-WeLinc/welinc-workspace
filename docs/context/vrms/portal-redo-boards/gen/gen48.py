"""Round 47 (Nov 25): S27 picked plain (no garage turn-taking, no traffic dots); eight looks for its style.
python3 -I gen48.py <project dir> [Board,Board]   (imports gen47, which imports gen45; both rewrite their boards unchanged when no list is given)
Map data (c) OpenStreetMap contributors, ODbL."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen47  # noqa: E402,F401  (sets up gen45 and the shared pieces)
from gen47 import M, D, Tilt, labels, board, LK, COPY, FOOT, BLEED_CSS, T27  # noqa: E402
from gen45 import FORM  # noqa: E402

LAND, SEA, GOLD = M.LAND, M.SEA, '#e8b800'


def mix(a, b, t):
    a, b = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(x + (y - x) * t):02x}' for x, y in zip(a, b))


def mapsvg(base=None, trips=None, labels_on=False):
    base = base if base is not None else M.base(towns=False, water_labels=False, shields=False, traffic=False)
    trips = trips if trips is not None else M.trip_lines()
    return M.svg(base + trips + M.drops(labels=False) + M.trucks() + M.garages(labels=False))


# S27's own fades: the copy side and the top go to navy, the map shows on the right and under the form
FADE27 = ('<div style="position:absolute;inset:0;background:linear-gradient(90deg,#0f1445 0%,rgba(15,20,69,.8) 22%,rgba(15,20,69,0) 42%),'
          'linear-gradient(180deg,#0f1445 0%,#0f1445 34%,rgba(15,20,69,0) 50%)"></div>')


def bleed(name, css, svg, t=T27, fade=FADE27, rt=None, lab=None):
    lab = lab if lab is not None else labels(t, top=420, right=1430)
    rt = rt if rt is not None else f'{FORM}{FOOT}'
    board(name, BLEED_CSS + css,
          f'<div class="pg"><div class="under"><div style="{t.style()}">{svg}</div>{fade}{lab}</div>'
          f'<div class="lf">{LK}{COPY}</div><div class="rt">{rt}</div></div>')


# ---------------------------------------------------------------- 0. S27 as picked: the reference
bleed('R47Plain.dc.html', '', mapsvg())

# ---------------------------------------------------------------- 1. Frosted: a heavier panel, a gold hairline edge
bleed('R47Frost.dc.html', '''
.rt{background:rgba(10,13,51,.76);backdrop-filter:blur(20px) saturate(1.2);-webkit-backdrop-filter:blur(20px) saturate(1.2);box-shadow:inset 1px 0 0 rgba(232,184,0,.5)}
''', mapsvg())

# ---------------------------------------------------------------- 2. Floating card: no panel, the form in a glass card, the map on every side
T_CARD = Tilt(left=0, top=0, A=48, B=-12, S=.9).fit(*D['garages']['Marikina'], 740, 560)
bleed('R47Card.dc.html', '''
.rt{background:transparent;backdrop-filter:none;-webkit-backdrop-filter:none;box-shadow:none;width:640px}
.card{padding:44px 48px 40px;border-radius:24px;background:rgba(10,13,51,.66);backdrop-filter:blur(14px) saturate(1.15);-webkit-backdrop-filter:blur(14px) saturate(1.15);
box-shadow:inset 0 0 0 1px rgba(255,255,255,.13),0 30px 80px rgba(5,7,31,.55)}
.foot{bottom:24px}
''', mapsvg(), t=T_CARD, rt=f'<div class="card">{FORM}</div>{FOOT}', lab=labels(T_CARD, top=420, right=1430, bottom=840))

# ---------------------------------------------------------------- 3. Open: no panel and no card, a navy pool of light behind the form
bleed('R47Open.dc.html', '''
.rt{background:radial-gradient(ellipse 74% 64% at 50% 48%,rgba(10,13,51,.96) 0%,rgba(10,13,51,.9) 55%,rgba(10,13,51,0) 100%);backdrop-filter:none;-webkit-backdrop-filter:none;box-shadow:none}
.in{background:rgba(10,13,51,.72)}
''', mapsvg())

# ---------------------------------------------------------------- 4. Quiet map: the roads dim back, only the runs and garages lit
quiet_base = '<g opacity=".42">' + M.base(towns=False, water_labels=False, shields=False, traffic=False) + '</g>'
bleed('R47Quiet.dc.html', '', mapsvg(quiet_base, M.trip_lines(op=.9, width=3.8)), lab=labels(T27, top=420, right=1430, towns=False, shields=False))


# ---------------------------------------------------------------- 5. Gold etching: fine gold lines on navy, like an engraved chart; the runs in white
def etched():
    keep = dict(M.STYLE), M.DOTS
    M.STYLE.update({'sec': ('#0b0f3a', 0, mix(LAND, GOLD, .3), 1.2), 'pri': ('#0b0f3a', 0, mix(LAND, GOLD, .55), 1.8), 'exp': ('#0b0f3a', 5, mix(LAND, GOLD, .9), 2.6)})
    M.DOTS = {k: (GOLD, op * .55, r * .8) for k, (_, op, r) in M.DOTS.items()}
    try:
        b = M.base(towns=False, water_labels=False, shields=False, traffic=False)
    finally:
        M.STYLE.clear()
        M.STYLE.update(keep[0])
        M.DOTS = keep[1]
    return (b.replace('#3a44a6', mix(LAND, GOLD, .62)).replace(M.SEA_EDGE, mix(SEA, GOLD, .3)))


etch_trips = M.trip_lines(op=.72, width=2.6).replace(f'stroke="{GOLD}"', 'stroke="#ffffff"')
bleed('R47Etch.dc.html', '''
.t-s{color:#e8d9a0;background:#0b0f3a;border-color:rgba(232,184,0,.55)}
.t-t{color:#b9a76a}
''', mapsvg(etched(), etch_trips))

# ---------------------------------------------------------------- 6. City lights: the dense streets glow warm, like the metro from a plane
GLOW = ('<defs><filter id="lights" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="5"/></filter></defs>')


def lights_base():
    keep = M.DOTS
    M.DOTS = {'1': ('#f2cf62', .3, 2.4), '2': ('#f2cf62', .48, 2.8), '3': ('#ffe39a', .7, 3.4)}
    try:
        b = M.base(towns=False, water_labels=False, shields=False, traffic=False)
    finally:
        M.DOTS = keep
    halo = ''.join(f'M{x} {y}h0' for x, y in D['dots']['3'] + D['dots']['2'])
    return b + GLOW + f'<path d="{halo}" stroke="#e8b800" stroke-opacity=".32" stroke-width="14" stroke-linecap="round" filter="url(#lights)"/>'   # over the land and roads, under the runs


lights_trips = M.trip_lines(op=.55, width=2.8).replace(f'stroke="{GOLD}"', 'stroke="#ffffff"')
bleed('R47Lights.dc.html', '', mapsvg(lights_base(), lights_trips))

# ---------------------------------------------------------------- 7. Flat: no tilt, the map seen straight down, true to scale
T_FLAT = Tilt(left=0, top=0, A=0, B=0, S=.56).fit(*D['garages']['Marikina'], 640, 610)
FADE_FLAT = ('<div style="position:absolute;inset:0;background:radial-gradient(ellipse 52% 50% at 18% 26%,#0f1445 0%,rgba(15,20,69,.92) 55%,rgba(15,20,69,0) 100%)"></div>')
bleed('R47Flat.dc.html', '', mapsvg(), t=T_FLAT, fade=FADE_FLAT, lab=labels(T_FLAT, top=380, right=1430, bottom=880))

# ---------------------------------------------------------------- notes
NOTES_CSS = '''
.pg{background:#0a0d33}
.nt{position:absolute;inset:56px 64px;display:grid;grid-template-columns:1.1fr 1fr;gap:56px}
.nt h2{margin:0 0 10px;font-size:28px;font-weight:800;letter-spacing:-.02em}
.nt h3{margin:28px 0 10px;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.14em;color:#e8b800}
.nt p,.nt li{font-size:15px;line-height:1.55;color:rgba(255,255,255,.78)}
.nt ul{margin:0;padding-left:20px}.nt li{margin:0 0 8px}
.nt b{color:#fff}
'''
board('R47Notes.dc.html', NOTES_CSS, '''<div class="pg"><div class="nt"><div>
<h2>Round 47: S27, plain</h2>
<p><b>Picked:</b> S27 as it stood, the map under the whole page and the form on navy glass. No garage turn-taking (that was S28), and <b>no traffic dots</b> on the expressways. The twelve trucks still drive their runs out and back.</p>
<h3>WHAT CHANGES FROM BOARD TO BOARD</h3>
<ul>
<li><b>The form's surface:</b> S27's glass (as picked), heavier frost, a floating card, or no surface at all.</li>
<li><b>The map's look:</b> as picked, dimmed back, gold etching, or the city lit up.</li>
<li><b>The angle:</b> tilted (every board but one) or flat.</li>
</ul>
<p>One surface and one map look can go together, for example the floating card on the etched map.</p>
</div><div>
<h3 style="margin-top:0">FOR THE BUILD</h3>
<ul>
<li><b>Blur over moving trucks costs a little.</b> The glass re-blurs whatever moves under it. The panel and the card blur only a few trucks; no surface (Open) blurs nothing.</li>
<li><b>Reduced motion</b> parks the trucks; the glass then never re-blurs.</li>
<li><b>The map credit</b> stays in the footer under the form, as on Round 46.</li>
</ul>
</div></div></div>''')

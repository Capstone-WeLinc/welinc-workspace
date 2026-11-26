"""Round 63 (Nov 26): K3 picked (moving boxes) and E1g picked (the line, the company name left, "EST. 2018" right).
K3 made to fit the page better: smaller, lined up with the grid, in the tiles' own style. Q1 band, P5 number keys.
python3 -I gen63.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen60 as g60  # noqa: E402
import gen53 as g53  # noqa: E402
import gen56 as g56  # noqa: E402
import gen59 as g59  # noqa: E402
from data49 import CORAZON  # noqa: E402
from data49 import board  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
NAVY = '15,20,69'
FOOT_CSS = '''.ft{height:440px}
.ft .hl{position:absolute;left:0;right:0;bottom:56px;height:1px;background:#e1e5ee;z-index:2}
.ft .est{position:absolute;right:calc(50% - 600px);bottom:22px;font:600 11px "IBM Plex Mono",monospace;letter-spacing:.1em;color:#7a8597}
.ft .bx{position:absolute;bottom:57px;z-index:1}'''


def box(x, y, w, h, detail=True):
    """A closed carton from the front: tape down the middle from the top, the flap seam; a label and arrow if detail."""
    tw = w * .2
    s = (f'<rect class="b" x="{x}" y="{y}" width="{w}" height="{h}" rx="3"/>'
         f'<rect class="tp" x="{x + w / 2 - tw / 2:.1f}" y="{y}" width="{tw:.1f}" height="{h * .38:.1f}"/>'
         f'<path d="M{x} {y + 8}H{x + w}"/>')
    if detail:
        s += (f'<rect x="{x + w * .62:.1f}" y="{y + h * .58:.1f}" width="{w * .26:.1f}" height="{h * .2:.1f}" rx="1.5"/>'
              f'<path d="M{x + w * .12:.1f} {y + h * .7:.1f}l7 -7 7 7M{x + w * .12 + 7:.1f} {y + h * .7 - 7:.1f}v14"/>')
    return s


def page(title, css, svg):
    title, c, body = g60.page(title, FOOT_CSS + css, f'{svg}<div class="hl"></div><span class="est">EST. 2018</span>')
    return title, c, body.replace(' · Since 2018</span>', '</span>')


def ink(stroke, tape_fill, tape_stroke, fill='none'):
    return (f'.ft .bx *{{stroke:{stroke}}}.ft .bx .b{{fill:{fill}}}'
            f'.ft .bx .tp{{fill:{tape_fill};stroke:{tape_stroke}}}')


PYRAMID = [(0, 250, 170, 128), (176, 250, 170, 128), (352, 274, 130, 104), (70, 136, 150, 112), (226, 150, 136, 98), (140, 50, 120, 84)]


def svg(boxes, vb, detail=True, sw=1.6):
    inner = ''.join(box(*b, detail=detail) for b in boxes)
    return f'<svg class="bx" viewBox="{vb}" fill="none" stroke-width="{sw}" stroke-linejoin="round" aria-hidden="true">{inner}</svg>'


# K3 as it was (reference)
def K3():
    css = '.ft .bx{right:calc(50% - 640px);height:300px}' + ink(f'rgba({NAVY},.16)', 'rgba(232,184,0,.22)', 'rgba(232,184,0,.4)')
    return css, svg(PYRAMID, '-2 48 488 332')


# K3a quieter: smaller, no labels or arrows, lighter ink, the right edge on the content edge
def K3a():
    css = '.ft .bx{right:calc(50% - 600px);height:200px}' + ink(f'rgba({NAVY},.12)', 'rgba(232,184,0,.16)', 'rgba(232,184,0,.3)')
    return css, svg(PYRAMID, '-2 48 488 332', detail=False, sw=2)


# K3b in the empty slot: a stack exactly as wide as the fourth tile column, under it
def K3b():
    boxes = [(0, 170, 138, 108), (144, 170, 138, 108), (30, 76, 120, 92), (156, 92, 104, 76), (70, 4, 100, 70)]
    css = '.ft .bx{left:calc(50% - 600px + 918px);width:282px;height:280px}' + ink(f'rgba({NAVY},.15)', 'rgba(232,184,0,.2)', 'rgba(232,184,0,.38)')
    return css, svg(boxes, '-1 3 284 277', sw=1.4)


# K3c white cartons in the tiles' own style: white fill, the tile hairline, gold tape
def K3c():
    css = ('.ft .bx{right:calc(50% - 600px);height:230px;filter:drop-shadow(0 6px 14px rgba(15,23,42,.05))}'
           + ink('#dfe3ec', 'rgba(232,184,0,.32)', 'rgba(232,184,0,.5)', fill='#fff'))
    return css, svg(PYRAMID, '-2 48 488 332', sw=1.6)


# K3d a low row: cartons just unloaded along the floor, never taller than a tile's top half
def K3d():
    boxes = [(0, 46, 150, 104), (156, 74, 110, 76), (272, 30, 160, 120), (438, 82, 92, 68), (536, 58, 128, 92)]
    css = '.ft .bx{right:calc(50% - 600px);height:150px}' + ink(f'rgba({NAVY},.14)', 'rgba(232,184,0,.2)', 'rgba(232,184,0,.36)')
    return css, svg(boxes, '-1 28 666 122', sw=1.5)


for key, t, fn in [
    ('R63K3', 'K3 · As picked, with E1g under it (reference)', K3),
    ('R63K3a', 'K3a · Quieter: smaller, no labels, lighter ink, on the content edge', K3a),
    ('R63K3b', 'K3b · In the empty slot: a stack as wide as the fourth tile column', K3b),
    ('R63K3c', 'K3c · White cartons in the tiles\' own style: white, the tile hairline, gold tape', K3c),
    ('R63K3d', 'K3d · A low row: cartons just unloaded along the floor', K3d),
]:
    BOARDS[key] = (lambda t=t, fn=fn: page(t, *fn()))

# ---------------------------------------------------------------- the system icons (on the page as picked: Q1, P5, K3, E1g)
import gen51 as g51  # noqa: E402
import gen52icons as gi  # noqa: E402

N, GOLD, W = '#0f1445', '#e8b800', '#fff'


def _svg(inner, size):
    return f'<svg class="ai" width="{size}" height="{size}" viewBox="0 0 64 64" aria-hidden="true">{inner}</svg>'


def outline(code):
    """I1's drawings as outlines: the same subjects, a 2.8 line, gold kept for the accent."""
    s = f'fill="none" stroke="{N}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"'
    if code == 'BMS':
        return (f'<path d="M12 19h40a3 3 0 0 1 3 3v6a4 4 0 0 0 0 8v6a3 3 0 0 1-3 3H12a3 3 0 0 1-3-3v-6a4 4 0 0 0 0-8v-6a3 3 0 0 1 3-3z" {s}/>'
                f'<path d="M21 37c7 0 8-10 21-10" fill="none" stroke="{GOLD}" stroke-width="3" stroke-linecap="round" stroke-dasharray="1 5"/>'
                f'<circle cx="20" cy="37" r="3.5" {s}/><circle cx="44" cy="27" r="4.5" fill="{GOLD}"/>')
    if code == 'VMMS':
        return (f'<path d="M13 43a19 19 0 0 1 38 0" {s}/>'
                f'<path d="M44.4 29.6A19 19 0 0 1 51 43" fill="none" stroke="{GOLD}" stroke-width="3.2" stroke-linecap="round"/>'
                f'<path d="M32 43 41 30" stroke="{GOLD}" stroke-width="3" stroke-linecap="round"/><circle cx="32" cy="43" r="3.5" {s}/>'
                f'<path d="M24 52h16" {s} opacity=".45"/>')
    return (g51.WRENCH.format(fg=N).replace('stroke-width="2"', 'stroke-width="1.5"')
            + f'<path d="M46 39.5l6 3.5v7l-6 3.5-6-3.5v-7z" fill="{GOLD}"/><circle cx="46" cy="46.5" r="2.4" fill="{W}"/>')


def objects(code, filled):
    """New subjects from the work itself: the booking clipboard, the service calendar, the repair toolbox."""
    body = f'fill="{N}"' if filled else f'fill="none" stroke="{N}" stroke-width="2.8"'
    s = 'stroke-linecap="round" stroke-linejoin="round"'
    det = W if filled else N
    if code == 'BMS':
        return (f'<rect x="13" y="12" width="38" height="45" rx="5" {body} {s}/><rect x="23" y="7" width="18" height="10" rx="3" fill="{GOLD}"/>'
                f'<path d="M21 29h22M21 37h14" stroke="{det}" stroke-width="2.8" {s} opacity="{1 if filled else .55}"/>'
                f'<path d="m21 47 4 4 9-10" fill="none" stroke="{GOLD}" stroke-width="3.4" {s}/>')
    if code == 'VMMS':
        cells = ''.join(f'<rect x="{x}" y="{y}" width="5" height="5" rx="1.2" fill="{det}" opacity="{1 if filled else .5}"/>'
                        for y in (31, 41) for x in (16, 26, 36) )
        return (f'<rect x="9" y="14" width="46" height="41" rx="6" {body} {s}/>'
                + (f'<path d="M9 24h46" stroke="{N}" stroke-width="2.8"/>' if not filled else f'<rect x="9" y="14" width="46" height="10" rx="5" fill="{N}"/>')
                + f'<path d="M21 9v9M43 9v9" stroke="{N}" stroke-width="3.2" {s}/>{cells}'
                + f'<circle cx="45" cy="44" r="6.5" fill="{GOLD}"/><path d="m42 44 2.2 2.2 4-4.4" fill="none" stroke="{N}" stroke-width="2.2" {s}/>')
    lid = 'M7 31l6-8h38l6 8'
    return (f'<path d="M24 23v-5a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v5" fill="none" stroke="{N}" stroke-width="3" {s}/>'
            f'<path d="{lid}z" {body} {s}/>'
            f'<rect x="7" y="31" width="50" height="25" rx="4" {body} {s}/>'
            f'<path d="M7 31h50" stroke="{det}" stroke-width="2.4" opacity="{1 if filled else .55}"/>'
            f'<rect x="27" y="35" width="10" height="9" rx="2" fill="{GOLD}"/>')


def even(code):
    """I1 with each mark brought to the same visual size: the ticket and the gauge grow, the wrench stays."""
    k = {'BMS': (1.12, 0, 0), 'VMMS': (1.22, 0, -4), 'VRMS': (1, 0, 0)}[code]
    o = 32 * (1 - k[0])
    return f'<g transform="translate({o + k[1]:.2f} {o + k[2]:.2f}) scale({k[0]})">{g51.glyph(code, N, GOLD, W)}</g>'


NEW = {
    'outline': lambda c, z: _svg(outline(c), z),
    'navy': lambda c, z: _svg(g51.glyph(c, N, N, W), z),
    'objline': lambda c, z: _svg(objects(c, False), z),
    'objfill': lambda c, z: _svg(objects(c, True), z),
    'even': lambda c, z: _svg(even(c), z),
}
_orig = gi.icon


def _icon(kind, code, size, dark):
    return NEW[kind](code, size) if kind in NEW else _orig(kind, code, size, dark)


gi.icon = _icon


def icon_page(title, kind):
    css, art = K3()
    lcss, lhtml = g53.L1(g53.items(CORAZON, False), kind)
    lhtml = g59.numbered(lhtml.replace(g53.HINT, ''))
    foot = f'<div class="ft" aria-hidden="true">{art}<div class="hl"></div><span class="est">EST. 2018</span></div>'
    body = (f'<div class="pg">{g59.TOP_HTML}<div class="w below">{lhtml}</div>{foot}'
            f'<span class="co"><b>WeLinc Logistics</b></span></div>')
    return title, (g51.CSS + g53.COMMON + g56.TOP + g59.Q1 + lcss + g59.P5 + g60.BASE + FOOT_CSS + css
                   + '.li{width:52px;height:52px;display:flex;align-items:center;color:#0f1445}'), body


for key, t, kind in [
    ('R63J1', 'J1 · I1 as it is: the drawn marks, filled navy with gold', 'plain'),
    ('R63J2', 'J2 · I2 as it is: the drawn marks in a thin frame', 'frame'),
    ('R63J3', 'J3 · I1 as outlines: the same subjects in a 2.8 line, closer to the boxes', 'outline'),
    ('R63J4', 'J4 · I1 in navy only: gold left for the keys, the boxes and the band', 'navy'),
    ('R63J5', 'J5 · New subjects, line: the booking clipboard, the service calendar, the repair toolbox', 'objline'),
    ('R63J6', 'J6 · New subjects, filled: the same three, solid navy with gold like I1', 'objfill'),
    ('R63J7', 'J7 · I1 evened out: the ticket and the gauge brought up to the wrench\'s visual size', 'even'),
]:
    BOARDS[key] = (lambda t=t, kind=kind: icon_page(t, kind))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in BOARDS.items():
        if ONLY and name not in ONLY:
            continue
        title, css, body = fn()
        (OUT / f'{name}.dc.html').write_text(board(title, css, body, h=900))
        print(name, title)


if __name__ == '__main__':
    main()

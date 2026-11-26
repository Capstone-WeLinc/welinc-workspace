"""Round 62 (Nov 26): a real design for the empty lower part of the page, above E1's still line (the line and the
company line stay). Q1 band, P5 number keys. Static. python3 -I gen62.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen60 as g60  # noqa: E402
from data49 import board  # noqa: E402
from parts import LOGO_POLY  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
NAVY = '15,20,69'
HL = '.ft .hl{position:absolute;left:0;right:0;bottom:56px;height:1px;background:#e1e5ee;z-index:2}'
ART = '''.ft{height:440px}
.ft .art{position:absolute;left:0;right:0;bottom:57px;height:380px;z-index:1}'''
LINE = '<div class="hl"></div>'


def compose(title, css, art):
    return g60.page(title, HL + ART + css, f'<div class="art">{art}</div>{LINE}')


# ---------------------------------------------------------------- K1 halftone rising from the floor
def K1():
    css = f'''.ft .art{{background:radial-gradient(circle,rgba({NAVY},.16) 1.7px,transparent 2px) 0 0/14px 14px;
-webkit-mask:radial-gradient(120% 100% at 80% 100%,#000 0%,rgba(0,0,0,.5) 35%,transparent 70%);
mask:radial-gradient(120% 100% at 80% 100%,#000 0%,rgba(0,0,0,.5) 35%,transparent 70%)}}'''
    return css, ''


# ---------------------------------------------------------------- K2 the depot floor in perspective
def K2():
    vx, vy = 720, -520
    rays = ''.join(f'<path d="M{vx} {vy}L{x} 380"/>' for x in range(-2400, 3900, 150))
    ys, y, step = [], 380.0, 70.0
    while y > 40 and step > 3:
        ys.append(y)
        step *= 0.72
        y -= step
    rows = ''.join(f'<path d="M0 {y:.1f}H1440"/>' for y in ys)
    css = '''.ft .art svg{width:100%;height:100%}
.ft .art{-webkit-mask:linear-gradient(to top,#000 10%,transparent 85%);mask:linear-gradient(to top,#000 10%,transparent 85%)}'''
    svg = (f'<svg viewBox="0 0 1440 380" preserveAspectRatio="none" fill="none" stroke="rgba({NAVY},.10)" stroke-width="1">'
           f'{rays}{rows}</svg>')
    return css, svg


# ---------------------------------------------------------------- K3 moving boxes stacked (lipat bahay)
def box(x, y, w, h):
    """A closed carton seen from the front: tape down the middle from the top, a label, the flap seam."""
    tw = w * .2
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3"/>'
            f'<rect class="tp" x="{x + w / 2 - tw / 2:.1f}" y="{y}" width="{tw:.1f}" height="{h * .38:.1f}"/>'
            f'<path d="M{x} {y + 8}H{x + w}"/>'
            f'<rect x="{x + w * .62:.1f}" y="{y + h * .58:.1f}" width="{w * .26:.1f}" height="{h * .2:.1f}" rx="1.5"/>'
            f'<path d="M{x + w * .12:.1f} {y + h * .7:.1f}l7 -7 7 7M{x + w * .12 + 7:.1f} {y + h * .7 - 7:.1f}v14"/>')


def K3():
    g = 0
    stack = (box(0, 250, 170, 128) + box(176, 250, 170, 128) + box(352, 274, 130, 104)
             + box(70, 136, 150, 112) + box(226, 150, 136, 98)
             + box(140, 50, 120, 84))
    css = f'''.ft .art svg{{position:absolute;right:calc(50% - 640px);bottom:0;height:300px}}
.ft .art svg *{{stroke:rgba({NAVY},.16)}}.ft .art .tp{{fill:rgba(232,184,0,.22);stroke:rgba(232,184,0,.4)}}'''
    return css, f'<svg viewBox="-2 48 488 332" fill="none" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true">{stack}</svg>'


# ---------------------------------------------------------------- K4 a blueprint of the 14 ft closed van
def K4():
    van = ('<rect x="40" y="70" width="340" height="150" rx="4"/>'
           '<path d="M388 112h58l40 46v62h-98z"/><path d="M398 122h40l30 34h-70z"/>'
           '<path d="M30 258h470"/>'
           + ''.join(f'<circle cx="{c}" cy="236" r="22"/><circle cx="{c}" cy="236" r="9"/>' for c in (100, 152, 440))
           + '<path d="M40 70v-34M380 70v-34" stroke-dasharray="3 4"/>'
           '<path d="M46 44h328" /><path d="M46 44l9-5v10zM374 44l-9-5v10z" class="ar"/>')
    css = f'''.ft .art .bp{{position:absolute;right:calc(50% - 640px);bottom:0;width:640px;height:330px;
background:linear-gradient(rgba({NAVY},.08) 1px,transparent 1px) 0 0/20px 20px,linear-gradient(90deg,rgba({NAVY},.08) 1px,transparent 1px) 0 0/20px 20px;
-webkit-mask:radial-gradient(75% 85% at 60% 100%,#000 40%,transparent 100%);mask:radial-gradient(75% 85% at 60% 100%,#000 40%,transparent 100%)}}
.ft .art .bp svg{{position:absolute;left:70px;bottom:0;height:262px}}
.ft .art .bp svg *{{stroke:rgba({NAVY},.28)}}.ft .art .bp .ar{{fill:rgba({NAVY},.28)}}
.ft .art .bp text{{font:600 13px "IBM Plex Mono",monospace;letter-spacing:.1em;fill:rgba({NAVY},.55);stroke:none}}'''
    return css, (f'<div class="bp"><svg viewBox="20 20 500 242" fill="none" stroke-width="1.4" aria-hidden="true">{van}'
                 f'<text x="210" y="34" text-anchor="middle">14 FT</text></svg></div>')


# ---------------------------------------------------------------- K5 branded packing tape across the floor
def K5():
    marks = ''.join(f'<g transform="translate({x} 13) scale(.1)">{LOGO_POLY}</g>'
                    f'<path d="M{x + 70} 31l8-8 8 8M{x + 78} 23v14" fill="none" stroke-width="2.2"/>' for x in range(0, 1800, 140))
    css = f'''.ft .art .tape{{position:absolute;left:-80px;right:-80px;bottom:70px;height:46px;transform:rotate(-4deg);
background:rgba(232,184,0,.28);box-shadow:0 1px 0 rgba(232,184,0,.35),0 -1px 0 rgba(232,184,0,.35)}}
.ft .art .tape svg{{width:100%;height:100%;fill:rgba({NAVY},.22);stroke:rgba({NAVY},.22)}}'''
    return css, f'<div class="tape"><svg viewBox="0 0 1600 46" preserveAspectRatio="xMinYMid slice" aria-hidden="true">{marks}</svg></div>'


# ---------------------------------------------------------------- K6 tyre tracks sweeping across the floor
def K6():
    a = 'M-60 380C300 330 620 300 880 220S1300 60 1520 30'
    b = 'M-60 440C320 392 650 360 910 282S1330 122 1540 92'
    css = f'''.ft .art svg{{width:100%;height:100%}}
.ft .art{{-webkit-mask:linear-gradient(90deg,#000 0%,#000 55%,transparent 95%);mask:linear-gradient(90deg,#000 0%,#000 55%,transparent 95%)}}'''
    tr = f'fill="none" stroke="rgba({NAVY},.07)" stroke-width="20" stroke-dasharray="5 7"'
    return css, f'<svg viewBox="0 0 1440 380" preserveAspectRatio="none" aria-hidden="true"><path d="{a}" {tr}/><path d="{b}" {tr}/></svg>'


for key, t, fn in [
    ('R62K1', 'K1 · Halftone: a navy dot screen rising from the floor, strongest at the bottom right', K1),
    ('R62K2', 'K2 · The depot floor in perspective: a faint grid running back from the line', K2),
    ('R62K3', 'K3 · Moving boxes stacked at the bottom right, taped and labelled (lipat bahay)', K3),
    ('R62K4', 'K4 · A blueprint of the 14 ft closed van on grid paper, bottom right', K4),
    ('R62K5', 'K5 · WeLinc packing tape laid across the floor: the mark and "this side up"', K5),
    ('R62K6', 'K6 · Tyre tracks: two faint tread trails sweeping across the floor', K6),
]:
    BOARDS[key] = (lambda t=t, fn=fn: compose(t, *fn()))


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

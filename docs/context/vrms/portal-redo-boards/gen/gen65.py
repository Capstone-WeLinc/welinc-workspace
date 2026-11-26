"""Round 65 (Nov 26): the arrival A3 with A4 (deal, keys, then the cartons drop), and the launch screens: what
plays after you click a system and before it opens. Launches 1, 2 and 4 are redrawn from their Round 31 notes
(the originals open only on the codesamtm canvas), Launch 3 as built, plus L5 with no vehicle. Each sits over the
launcher as picked (Q1, J1, P5, K3a, E1g), with Replay and Slow. python3 -I gen65.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g51  # noqa: E402
import gen63 as g63  # noqa: E402
import gen64 as g64  # noqa: E402
from gen64 import T  # noqa: E402
from data49 import board  # noqa: E402
from parts import V_VAN, V_WING  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
NAVY, GOLD = '#0f1445', '#e8b800'
CODE, NAME = 'VRMS', 'Vehicle Repair Management System'

# ---------------------------------------------------------------- the arrival: A3 with A4
A3A4 = (f'''.sin{{animation:fadeOut {T(.25)} ease {T(.3)} both}}
.lau .hd{{animation:fadeIn {T(.3)} ease {T(.5)} both}}.lau .ft .hl,.lau .ft .est,.lau .co{{animation:fadeIn {T(.4)} ease {T(.9)} both}}
@keyframes deal{{from{{opacity:0;transform:translateX(-40px)}}to{{opacity:1;transform:none}}}}
@keyframes pop{{from{{opacity:0;transform:scale(.6)}}to{{opacity:1;transform:none}}}}''' + g64.tiles('deal', .55, .09)
        + ''.join(f'.lau .t1:nth-of-type({n + 1}) kbd{{animation:pop {T(.25)} cubic-bezier(.3,1.4,.5,1) {T(round(1.05 + n * .09, 3))} both}}' for n in range(3))
        + g64.boxes(1.3))
BOARDS['R65A34'] = lambda: g64.make('A3 + A4 · The tiles deal in, their keys show, then the cartons drop into their stack', A3A4, '')

# ---------------------------------------------------------------- the launch screens
COVER = f'''.cv{{position:absolute;inset:0;z-index:5;background:{NAVY};color:#fff;font-family:Inter,system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px;
animation:fadeIn {T(.2)} ease {T(.15)} both}}
.cv .eb{{margin:0;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.14em;text-transform:uppercase;color:{GOLD}}}
.cv .cd{{font-size:52px;font-weight:800;letter-spacing:-.03em;text-align:center;line-height:1}}
.cv .nm{{margin-top:10px;font-size:15px;color:rgba(255,255,255,.7);text-align:center}}
.cv .st{{margin:0;font-size:15px;color:rgba(255,255,255,.85)}}
.cv .sc{{width:720px;height:200px;overflow:visible}}
.cv .sc *{{transform-box:fill-box}}
.lau .t1:nth-of-type(3){{box-shadow:0 0 0 2px {GOLD},0 14px 30px rgba(15,23,42,.10)}}'''


def cover(eyebrow, scene, css):
    body = (f'<div class="cv" role="status"><p class="eb">{eyebrow}</p><div><div class="cd">{CODE}</div><div class="nm">{NAME}</div></div>'
            f'<svg class="sc" viewBox="0 -40 720 200" aria-hidden="true"><defs>{V_VAN}{V_WING}'
            f'<pattern id="hz" width="20" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(0)"><rect width="10" height="10" fill="{GOLD}"/><rect x="10" width="10" height="10" fill="#fff"/></pattern>'
            f'<pattern id="sl" width="10" height="9" patternUnits="userSpaceOnUse"><rect width="10" height="7" fill="#3a43a6"/><rect y="7" width="10" height="2" fill="#2c348f"/></pattern>'
            f'</defs><path d="M0 134H720" stroke="rgba(255,255,255,.14)" stroke-width="2"/>{scene}</svg>'
            f'<p class="st">Signed in. Opening {CODE}…</p></div>')
    return COVER + css, body


def L1():
    """Boom gate: the striped boom lifts at the depot gate, the van rolls through."""
    scene = ('<rect x="300" y="64" width="54" height="70" rx="4" fill="#2a3290"/><rect x="310" y="76" width="34" height="22" rx="2" fill="#060828"/>'
             '<rect x="356" y="78" width="14" height="56" rx="2" fill="#3b43a3"/>'
             f'<rect class="boom" x="364" y="80" width="150" height="10" rx="5" fill="url(#hz)"/>'
             '<g class="mv"><use href="#van" x="40" y="80" width="138" height="56"/></g>')
    css = (f'.boom{{transform-origin:0% 50%;animation:lift {T(.45)} cubic-bezier(.4,0,.2,1) {T(.45)} both}}'
           '@keyframes lift{from{transform:none}to{transform:rotate(-78deg)}}'
           f'.mv{{animation:roll {T(1.1)} cubic-bezier(.45,0,.3,1) {T(.6)} both}}@keyframes roll{{from{{transform:none}}to{{transform:translateX(620px)}}}}')
    return cover('Gate open', scene, css)


def L2():
    """Dock door: the shutter rolls up on the system's mark, then the wing van pulls away from the bay."""
    mark = f'<g transform="translate(272 74) scale(.82)">{g51.glyph(CODE, "#fff", GOLD, NAVY)}</g>'
    scene = ('<rect x="200" y="20" width="200" height="114" rx="4" fill="#2a3290"/><rect x="236" y="54" width="128" height="80" fill="#060828"/>'
             f'{mark}<rect class="sh" x="236" y="54" width="128" height="80" fill="url(#sl)"/>'
             f'<rect x="236" y="128" width="128" height="6" fill="url(#hz)"/>'
             '<g class="mv"><use href="#wing" x="410" y="70" width="172" height="64"/></g>')
    css = (f'.sh{{transform-origin:50% 0%;animation:up {T(.5)} cubic-bezier(.4,0,.2,1) {T(.4)} both}}@keyframes up{{to{{transform:scaleY(.04)}}}}'
           f'.mv{{animation:away {T(.9)} cubic-bezier(.5,0,.4,1) {T(.95)} both}}@keyframes away{{to{{transform:translateX(420px)}}}}')
    return cover('At the dock', scene, css)


def L3():
    """Launch 3 as built: the garage on the left, the route draws in gold, the van runs it to the pin."""
    scene = ('<g transform="translate(18 92)"><rect x="0" y="12" width="44" height="30" rx="3" fill="#2a3290"/><path d="M-4 14 22 0l26 14z" fill="#3b43a3"/>'
             '<rect x="8" y="24" width="12" height="18" fill="#060828"/><rect x="24" y="24" width="12" height="18" fill="#060828"/></g>'
             f'<path class="rl" d="M70 134H660" stroke="{GOLD}" stroke-width="4" stroke-linecap="round"/>'
             '<g class="mv"><use href="#van" x="64" y="96" width="69" height="28"/></g>'
             f'<g transform="translate(674 86)"><path d="M12 0C5.4 0 0 5.2 0 11.6 0 20.3 12 34 12 34s12-13.7 12-22.4C24 5.2 18.6 0 12 0z" fill="{GOLD}"/><circle cx="12" cy="11.5" r="4.5" fill="{NAVY}"/></g>')
    css = (f'.rl{{stroke-dasharray:590;stroke-dashoffset:590;animation:draw {T(1.2)} cubic-bezier(.45,0,.2,1) {T(.35)} forwards}}@keyframes draw{{to{{stroke-dashoffset:0}}}}'
           f'.mv{{animation:run {T(1.2)} cubic-bezier(.45,0,.2,1) {T(.35)} both}}@keyframes run{{to{{transform:translateX(560px)}}}}')
    return cover('En route', scene, css)


def L4():
    """Loading: three cartons slide up the ramp into the van's open back, then the doors close."""
    cartons = ''.join(f'<g class="ct ct{n}"><rect x="150" y="104" width="34" height="30" rx="2" fill="#f4f6fb"/>'
                      f'<rect x="163" y="104" width="8" height="12" fill="{GOLD}"/></g>' for n in range(3))
    scene = (f'<path d="M120 134h160" stroke="rgba(255,255,255,.3)" stroke-width="3"/>{cartons}'
             '<use href="#van" x="300" y="78" width="138" height="56"/>'
             f'<rect class="dr" x="298" y="78" width="6" height="40" rx="1" fill="#cbd2ea"/>')
    css = (''.join(f'.ct{n}{{animation:load {T(.45)} cubic-bezier(.4,0,.2,1) {T(round(.4 + n * .3, 2))} both}}' for n in range(3))
           + '@keyframes load{from{opacity:0;transform:translateX(-60px)}25%{opacity:1}80%{opacity:1;transform:translateX(150px)}to{opacity:0;transform:translateX(170px)}}'
           f'.dr{{transform-origin:100% 50%;animation:shut {T(.25)} ease {T(1.45)} both}}@keyframes shut{{from{{transform:scaleX(1)}}to{{transform:scaleX(4)}}}}')
    return cover('Loading', scene, css)


def L5():
    """No vehicle: the cartons stack up like a progress meter; the last one lands and the system opens."""
    stack = [(0, 96, 60, 38), (64, 96, 60, 38), (128, 96, 60, 38), (32, 56, 60, 38), (96, 56, 60, 38), (64, 16, 60, 38)]
    boxes = ''.join(f'<g class="c c{n}" transform="translate(266 0)"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="#f4f6fb"/>'
                    f'<rect x="{x + w / 2 - 6}" y="{y}" width="12" height="{h * .42:.0f}" fill="{GOLD}"/></g>' for n, (x, y, w, h) in enumerate(stack))
    css = (''.join(f'.c{n}{{animation:drop {T(.35)} cubic-bezier(.3,1.35,.5,1) {T(round(.35 + n * .2, 2))} both}}' for n in range(6))
           + '@keyframes drop{from{opacity:0;transform:translate(266px,-90px)}to{opacity:1;transform:translate(266px,0)}}')
    return cover('Packing up', boxes, css)


for key, t, fn in [
    ('R65L1', 'Launch 1 · Boom gate: the boom lifts at the depot gate and the van rolls through (redrawn)', L1),
    ('R65L2', 'Launch 2 · Dock door: the shutter rolls up on the system\'s mark, the wing van pulls away (redrawn)', L2),
    ('R65L3', 'Launch 3 · As built: the route draws from the garage and the van runs it to the pin', L3),
    ('R65L4', 'Launch 4 · Loading: cartons slide into the van, the doors close (redrawn)', L4),
    ('R65L5', 'Launch 5 · New, no vehicle: the cartons stack up like a progress meter', L5),
]:
    BOARDS[key] = (lambda t=t, fn=fn: g64.make(t, *fn()))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in BOARDS.items():
        if ONLY and name not in ONLY:
            continue
        title, css, body = fn()
        if name.startswith('R65L'):  # a launch: no sign in frame, the cover sits over the launcher
            body = body.replace(f'<div class="sin"><img src="{g64.SIGNIN_BLOB}" alt=""></div>', '')
        (OUT / f'{name}.dc.html').write_text(board(title, css, body, logic=g64.LOGIC, h=900))
        print(name, title)


if __name__ == '__main__':
    main()

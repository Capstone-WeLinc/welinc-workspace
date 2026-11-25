"""Round 64 (Nov 26): K3a and J1 picked. Arrival options: from the picked sign in (S27d Quiet, a still frame
uploaded to the canvas) to the launcher as picked (Q1, J1, P5, K3a, E1g). No vehicles, no road. Each board has
Replay and Slow (3x). python3 -I gen64.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g51  # noqa: E402
import gen53 as g53  # noqa: E402
import gen56 as g56  # noqa: E402
import gen59 as g59  # noqa: E402
import gen60 as g60  # noqa: E402
import gen63 as g63  # noqa: E402
from data49 import board, CORAZON  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
SIGNIN_BLOB = '/_blob/1bca22d4638da4a2ac825bd2d844cba6'  # R47Quiet at 1440x900, uploaded to the launcher canvas
NAVY = '15,20,69'


def launcher():
    lcss, lhtml = g53.L1(g53.items(CORAZON, False), 'plain')
    lhtml = g59.numbered(lhtml.replace(g53.HINT, ''))
    boxes = ''.join(f'<g class="c">{g63.box(*b, detail=False)}</g>' for b in g63.PYRAMID)
    art = f'<svg class="bx" viewBox="-2 48 488 332" fill="none" stroke-width="2" stroke-linejoin="round" aria-hidden="true">{boxes}</svg>'
    foot = f'<div class="ft" aria-hidden="true">{art}<div class="hl"></div><span class="est">EST. 2018</span></div>'
    html = f'<div class="pg">{g59.TOP_HTML}<div class="w below">{lhtml}</div>{foot}<span class="co"><b>WeLinc Logistics</b></span></div>'
    k3a = '.ft .bx{right:calc(50% - 600px);height:200px}' + g63.ink(f'rgba({NAVY},.12)', 'rgba(232,184,0,.16)', 'rgba(232,184,0,.3)')
    css = (g51.CSS + g53.COMMON + g56.TOP + g59.Q1 + lcss + g59.P5 + g60.BASE + g63.FOOT_CSS + k3a
           + '.li{width:52px;height:52px;display:flex;align-items:center;color:#0f1445}')
    return css, html


STAGE = '''.arr{position:absolute;inset:0;width:1440px;height:900px;overflow:hidden;--k:1}.arr.k3{--k:3}
.stage,.lau,.sin{position:absolute;inset:0}.sin{z-index:5}.sin img{display:block;width:1440px;height:900px}
.ft .bx .c{transform-box:fill-box;transform-origin:50% 100%}
.ctl{position:absolute;z-index:50;right:24px;bottom:24px;display:flex;gap:6px;padding:6px;border-radius:16px;background:rgba(255,255,255,.94);box-shadow:0 1px 2px rgba(15,23,42,.08),0 8px 24px rgba(15,23,42,.14)}
.ctl button{display:inline-flex;align-items:center;gap:8px;height:44px;padding:0 16px;border:0;border-radius:12px;background:none;color:#1a1f6e;font:600 14px Inter,sans-serif;cursor:pointer}
.ctl button:hover{background:#eef0f8}.ctl .tg.on{background:#0f1445;color:#fff}
@keyframes fadeOut{from{opacity:1}to{opacity:0}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes quiet{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.stage *,.stage{animation-duration:1ms!important;animation-delay:0s!important}}'''

I_REPLAY = '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>'
I_SLOW = '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M10 2h4"/>'


def _i(p):
    return f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg>'


CTL = ('<div class="ctl"><button type="button" onClick="{{replay}}">' + _i(I_REPLAY) + 'Replay</button>'
       '<button type="button" class="{{slowCls}}" aria-pressed="{{slowPressed}}" onClick="{{toggleSlow}}">' + _i(I_SLOW) + 'Slow</button></div>')

LOGIC = '''constructor(props) {
super(props);
this.state = { on: true, slow: false };
}
componentWillUnmount() { clearTimeout(this.t); }
restart() {
clearTimeout(this.t);
this.setState({ on: false });
this.t = setTimeout(() => this.setState({ on: true }), 60);
}
renderVals() {
const slow = this.state.slow;
return {
on: this.state.on,
speed: slow ? 'arr k3' : 'arr',
slowCls: slow ? 'tg on' : 'tg',
slowPressed: slow ? 'true' : 'false',
replay: () => this.restart(),
toggleSlow: () => { this.setState({ slow: !slow }); this.restart(); },
};
}'''


def T(s):
    return f'calc({s}s*var(--k))'


def tiles(anim, start, step, dur=.45, ease='cubic-bezier(.2,.8,.2,1)'):
    return ''.join(f'.lau .t1:nth-of-type({n + 1}){{animation:{anim} {T(dur)} {ease} {T(round(start + n * step, 3))} both}}' for n in range(3))


def boxes(start, step=.12):
    return ''.join(f'.lau .bx .c:nth-of-type({n + 1}){{animation:drop {T(.5)} cubic-bezier(.3,1.35,.5,1) {T(round(start + n * step, 3))} both}}'
                   for n in range(6)) + '@keyframes drop{from{opacity:0;transform:translateY(-120px)}to{opacity:1;transform:none}}'


OPTS = [
    ('R64A1', 'A1 · Quiet: the sign in fades, the launcher rises 12px into place (about 0.9 s)',
     f'.sin{{animation:fadeOut {T(.25)} ease {T(.3)} both}}.lau{{animation:quiet {T(.4)} cubic-bezier(.2,.8,.2,1) {T(.5)} both}}', ''),
    ('R64A2', 'A2 · Roller door: the sign in rolls up like a depot shutter and stops as the band; the tiles rise under it',
     f'''.sin{{animation:roll {T(.8)} cubic-bezier(.6,0,.3,1) {T(.35)} both,fadeOut {T(.18)} ease {T(1.15)} both}}
@keyframes roll{{from{{clip-path:inset(0 0 0 0)}}to{{clip-path:inset(0 0 812px 0)}}}}
.edge{{position:absolute;left:0;right:0;top:892px;height:8px;z-index:6;background:linear-gradient(#0a0d33 0 5px,#e8b800 5px 7px,transparent 7px);
animation:edge {T(.8)} cubic-bezier(.6,0,.3,1) {T(.35)} both,fadeOut {T(.18)} ease {T(1.15)} both}}
@keyframes edge{{from{{transform:none}}to{{transform:translateY(-812px)}}}}
.lau .hd{{animation:fadeIn {T(.3)} ease {T(.8)} both}}.lau .ft{{animation:fadeIn {T(.4)} ease {T(.6)} both}}''' + tiles('quiet', .85, .07),
     '<div class="edge"></div>'),
    ('R64A3', 'A3 · Deal: the sign in fades, the tiles slide in from the left one by one, then their keys show',
     f'''.sin{{animation:fadeOut {T(.25)} ease {T(.3)} both}}
.lau .hd{{animation:fadeIn {T(.3)} ease {T(.5)} both}}.lau .ft{{animation:fadeIn {T(.4)} ease {T(.9)} both}}
@keyframes deal{{from{{opacity:0;transform:translateX(-40px)}}to{{opacity:1;transform:none}}}}
@keyframes pop{{from{{opacity:0;transform:scale(.6)}}to{{opacity:1;transform:none}}}}''' + tiles('deal', .55, .09)
     + ''.join(f'.lau .t1:nth-of-type({n + 1}) kbd{{animation:pop {T(.25)} cubic-bezier(.3,1.4,.5,1) {T(round(1.05 + n * .09, 3))} both}}' for n in range(3)), ''),
    ('R64A4', 'A4 · Boxes last: a quiet arrival, then the cartons drop into their stack one by one and settle',
     f'.sin{{animation:fadeOut {T(.25)} ease {T(.3)} both}}.lau{{animation:quiet {T(.4)} cubic-bezier(.2,.8,.2,1) {T(.5)} both}}' + boxes(1.0), ''),
    ('R64A5', 'A5 · Focus: the sign in steps back and blurs, the launcher comes forward',
     f'''.sin{{transform-origin:50% 50%;animation:back {T(.55)} cubic-bezier(.4,0,.2,1) {T(.3)} both}}
@keyframes back{{to{{opacity:0;transform:scale(.94);filter:blur(8px)}}}}
.lau{{animation:front {T(.6)} cubic-bezier(.2,.8,.2,1) {T(.4)} both}}
@keyframes front{{from{{opacity:0;transform:scale(1.035)}}to{{opacity:1;transform:none}}}}''', ''),
    ('R64A6', 'A6 · No arrival: a plain cut to the launcher (what reduced motion gets anyway)',
     f'.sin{{animation:fadeOut 1ms linear {T(.6)} both}}', ''),
]


def make(title, anim, extra):
    lcss, lhtml = launcher()
    body = ('<div class="{{speed}}"><sc-if value="{{on}}" hint-placeholder-val="{{ true }}"><div class="stage">'
            f'<div class="lau">{lhtml}</div><div class="sin"><img src="{SIGNIN_BLOB}" alt=""></div>{extra}'
            '</div></sc-if>' + CTL + '</div>')
    return title, lcss + STAGE + anim, body


for key, t, anim, extra in OPTS:
    BOARDS[key] = (lambda t=t, anim=anim, extra=extra: make(t, anim, extra))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in BOARDS.items():
        if ONLY and name not in ONLY:
            continue
        title, css, body = fn()
        (OUT / f'{name}.dc.html').write_text(board(title, css, body, logic=LOGIC, h=900))
        print(name, title)


if __name__ == '__main__':
    main()

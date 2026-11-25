"""Arrival boards A1 to A6: Sign in to the launcher, each with Replay and Slow.

Restart works by remounting the stage through <sc-if>; Slow swaps the wrapper's class to k3,
which sets --k:3 and stretches every duration and delay.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parts import *  # noqa

OUT = Path(sys.argv[1])


def T(s):
    return f'calc({s}s*var(--k))'


SIGNIN_CSS = '''.sin{position:absolute;inset:0;display:grid;grid-template-columns:840px 600px}
.sin .lf{position:relative;overflow:hidden;background:#0f1445;color:#fff}
.sin .lk{position:absolute;left:64px;top:40px;display:flex;align-items:center;gap:10px}.sin .lk svg{height:20px;fill:#e8b800}.sin .lk span{font-weight:800;font-style:italic;font-size:16px}
.sin .cp{position:absolute;left:64px;top:172px}
.eb{margin:0;font-size:14px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#e8b800}
.hh{margin:14px 0 0;font-size:72px;line-height:1;font-weight:800;letter-spacing:-.035em}
.hh em{font-style:normal;color:#e8b800}
.ln{margin:22px 0 0;font-size:18px;line-height:1.55;color:rgba(255,255,255,.72);max-width:420px}
.wm{position:absolute;right:-60px;bottom:-40px;height:360px;fill:rgba(255,255,255,.04)}
.sin .rt{background:#fff;display:flex;align-items:center;justify-content:center}
.fm{width:384px;display:flex;flex-direction:column;gap:26px;margin:0}
.fm h2{margin:0;font-size:28px;font-weight:800;letter-spacing:-.02em;color:#0f172a}
.sub{margin:8px 0 0;font-size:15px;color:#475569}
.fs{display:flex;flex-direction:column;gap:18px}
.fm label{display:block;font-size:14px;font-weight:600;margin-bottom:6px;color:#0f172a}
.row{display:flex;justify-content:space-between;align-items:flex-start}
.row a{font-size:14px;font-weight:600;color:#1a1f6e}
.in{box-sizing:border-box;width:100%;height:46px;border:1px solid #64748b;border-radius:12px;padding:0 14px;font:15px Inter,sans-serif;color:#0f172a;background:#fff}
.in::placeholder{color:#5b6779}
.btn{height:48px;border:0;border-radius:12px;background:#0f1445;color:#fff;font:700 16px Inter,sans-serif;display:flex;align-items:center;justify-content:center;gap:10px;cursor:pointer}
.hint{margin:0;font-size:14px;line-height:1.5;color:#5b6779}'''

LEFT_COPY = (f'<div class="lk">{LOGO}<span>WeLinc Logistics</span></div>'
             '<div class="cp"><p class="eb">WeLinc Logistics</p><h2 class="hh"><em>Operations</em><br>Workspace</h2>'
             '<p class="ln">Book trips, plan upkeep and run repairs from one account.</p></div>'
             f'<svg class="wm" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>')

FORM = ('<div class="rt"><form class="fm"><div><h2>Sign in</h2><p class="sub">Use your WeLinc work email.</p></div>'
        '<div class="fs"><div><label for="e">Work email</label><input id="e" class="in" placeholder="you@welinc.com"></div>'
        '<div><div class="row"><label for="p">Password</label><a href="#">Forgot password?</a></div>'
        '<input id="p" type="password" class="in" placeholder="Enter password"></div>'
        f'<button type="button" class="btn">Sign in {ARROW}</button></div>'
        '<p class="hint">No account yet? Ask your admin to add you. You\'ll get an email to set your password.</p></form></div>')

SIGNIN = f'<div class="sin"><div class="lf">{LEFT_COPY}</div>{FORM}</div>'

STAGE_CSS = BASE + '\n' + SCENE_CSS + '\n' + SIGNIN_CSS + '''
.pg{--k:1}
.pg.k3{--k:3}
.stage{position:absolute;inset:0}
.lau{position:absolute;inset:0}
.band{height:400px}
.gr{padding-top:56px}
.ctl{position:absolute;z-index:50;right:24px;bottom:24px;display:flex;gap:6px;padding:6px;border-radius:16px;background:rgba(255,255,255,.94);box-shadow:0 1px 2px rgba(15,23,42,.08),0 8px 24px rgba(15,23,42,.14)}
.ctl button{display:inline-flex;align-items:center;gap:8px;height:44px;padding:0 16px;border:0;border-radius:12px;background:none;color:#1a1f6e;font:600 14px Inter,sans-serif;cursor:pointer}
.ctl button:hover{background:#eef0f8}
.ctl .tg.on{background:#0f1445;color:#fff}
@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes fadeOut{from{opacity:1}to{opacity:0}}
@media (prefers-reduced-motion:reduce){.stage *,.stage{animation-duration:1ms!important;animation-delay:0s!important}}
'''

I_REPLAY = '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>'
I_SLOW = '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M10 2h4"/>'
CTL = (f'<div class="ctl"><button type="button" onClick="{{{{replay}}}}">{icon(I_REPLAY, 18)}Replay</button>'
       f'<button type="button" class="{{{{slowCls}}}}" aria-pressed="{{{{slowPressed}}}}" onClick="{{{{toggleSlow}}}}">{icon(I_SLOW, 18)}Slow</button></div>')

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
speed: slow ? 'k3' : 'k1',
slowCls: slow ? 'tg on' : 'tg',
slowPressed: slow ? 'true' : 'false',
replay: () => this.restart(),
toggleSlow: () => { this.setState({ slow: !slow }); this.restart(); },
};
}'''


def cards_rise(start, step=.08):
    return '\n'.join(
        f'.lau .cards li:nth-child({i + 1}){{animation:rise {T(.45)} cubic-bezier(.2,.8,.2,1) {T(round(start + i * step, 3))} both}}'
        for i in range(3))


def launcher(drive=False, band_extra=''):
    return (f'<div class="lau"><div class="band">{band_extra}{garage_scene(drive)}{topbar()}{greeting()}</div>'
            f'<main class="main">{cards()}</main></div>')


def board(name, title, css, stage):
    body = (f'<div class="pg {{{{speed}}}}"><sc-if value="{{{{on}}}}" hint-placeholder-val="{{{{ true }}}}">'
            f'<div class="stage">{stage}</div></sc-if>{CTL}</div>')
    (OUT / name).write_text(page(title, STAGE_CSS + css, body, logic=LOGIC))


# ---------- A1: the navy side sweeps into the band ----------
a1 = f'''
.lau .band{{background:none}}
.sweep{{position:absolute;left:0;top:0;width:1440px;height:400px;background:#0f1445;overflow:hidden;color:#fff;animation:sweep {T(1)} cubic-bezier(.65,0,.35,1) {T(.35)} both}}
@keyframes sweep{{0%{{width:840px;height:900px}}45%{{width:1440px;height:900px}}100%{{width:1440px;height:400px}}}}
.sweep .lk,.sweep .cp,.sweep .wm{{animation:fadeOut {T(.22)} ease {T(.3)} both}}
.sweep .lk{{position:absolute;left:64px;top:40px;display:flex;align-items:center;gap:10px}}.sweep .lk svg{{height:20px;fill:#e8b800}}.sweep .lk span{{font-weight:800;font-style:italic;font-size:16px}}
.sweep .cp{{position:absolute;left:64px;top:172px;width:700px}}
.form{{position:absolute;right:0;top:0;width:600px;height:900px;display:flex;animation:fadeOut {T(.25)} ease {T(.3)} both}}
.form .rt{{flex:1}}
.lau .sc,.lau .top,.lau .gr{{animation:fadeIn {T(.4)} ease {T(1.25)} both}}
{cards_rise(1.35)}
'''
board('ArrSweep.dc.html', 'Arrival, the navy side sweeps into the band', a1,
      f'<div class="form">{FORM}</div><div class="sweep">{LEFT_COPY}</div>{launcher()}')

# ---------- A2: the sign in page rolls up like a shutter ----------
a2 = f'''
.sin{{z-index:5;animation:roll {T(.8)} cubic-bezier(.6,0,.3,1) {T(.6)} both}}
@keyframes roll{{from{{transform:translateY(0)}}to{{transform:translateY(-100%)}}}}
.slats{{position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(to bottom,transparent 0 26px,rgba(15,20,69,.16) 26px 28px);animation:fadeIn {T(.3)} ease {T(.3)} both}}
.rail{{position:absolute;left:0;right:0;bottom:0;height:18px;background:#1a2263;box-shadow:0 -1px 0 rgba(255,255,255,.12);animation:fadeIn {T(.3)} ease {T(.3)} both}}
.rail::after{{content:"";position:absolute;left:50%;top:5px;width:96px;height:8px;margin-left:-48px;border-radius:4px;background:#e8b800}}
{cards_rise(1.2)}
'''
board('ArrHandoff.dc.html', 'Arrival, the sign in page rolls up like a shutter', a2,
      f'{launcher()}<div class="sin"><div class="lf">{LEFT_COPY}</div>{FORM}<div class="slats"></div><div class="rail"></div></div>')

# ---------- A3: the van pulls out of the garage once ----------
a3 = f'''
.sin{{z-index:5;animation:fadeOut {T(.3)} ease {T(.3)} both}}
.drive,.shadow{{animation:drive {T(1.4)} cubic-bezier(.35,0,.2,1) {T(.55)} both}}
@keyframes drive{{from{{transform:translateX(-300px)}}to{{transform:none}}}}
{cards_rise(1.75)}
'''
board('ArrPark.dc.html', 'Arrival, the van pulls out of the garage', a3, f'{launcher(drive=True)}{SIGNIN}')

# ---------- A4: quiet fade and rise ----------
a4 = f'''
.sin{{z-index:5;animation:fadeOut {T(.25)} ease {T(.3)} both}}
.lau{{animation:quiet {T(.4)} cubic-bezier(.2,.8,.2,1) {T(.5)} both}}
@keyframes quiet{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}
'''
board('ArrQuiet.dc.html', 'Arrival, quiet rise', a4, f'{launcher()}{SIGNIN}')

# ---------- A5: cards dispatched down from the band ----------
cards5 = '\n'.join(
    f'.lau .cards li:nth-child({i + 1}){{animation:deal {T(.6)} cubic-bezier(.3,.7,.3,1) {T(round(.85 + i * .14, 2))} both}}'
    for i in range(3))
a5 = f'''
.sin{{z-index:5;animation:fadeOut {T(.25)} ease {T(.3)} both}}
.lau .band{{position:relative;z-index:2;animation:drop {T(.45)} cubic-bezier(.2,.8,.2,1) {T(.45)} both}}
@keyframes drop{{from{{transform:translateY(-100%)}}to{{transform:none}}}}
.lau .main{{position:relative;z-index:1}}
@keyframes deal{{0%{{opacity:0;transform:translateY(-200px) scale(.9)}}25%{{opacity:1}}75%{{transform:translateY(8px) scale(1)}}100%{{opacity:1;transform:none}}}}
{cards5}
'''
board('ArrDeal.dc.html', 'Arrival, cards dispatched down from the band', a5, f'{launcher()}{SIGNIN}')

# ---------- A6: sign in steps back, launcher comes forward ----------
a6 = f'''
.sin{{z-index:5;transform-origin:50% 45%;animation:back {T(.6)} cubic-bezier(.4,0,.2,1) {T(.3)} both}}
@keyframes back{{from{{opacity:1;transform:none;filter:none}}to{{opacity:0;transform:scale(.94);filter:blur(8px)}}}}
.lau{{transform-origin:50% 40%;animation:fwd {T(.6)} cubic-bezier(.2,.8,.2,1) {T(.45)} both}}
@keyframes fwd{{from{{opacity:0;transform:scale(1.04)}}to{{opacity:1;transform:none}}}}
'''
board('ArrFocus.dc.html', 'Arrival, sign in steps back and the launcher comes forward', a6, f'{launcher()}{SIGNIN}')
print('ok')

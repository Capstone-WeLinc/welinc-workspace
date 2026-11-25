"""Round 49, the rest: launchers E to J, Suite management placements (M1 to M5), suite admin only (S1 to S3)."""
from data49 import I, ic, top, CORAZON, FELICIDAD, SUITE_SYS, SUITE_ALL, DATE, LOGO, LOGO_POLY, V_VAN, V_L300, VAN_TOP, CHEV  # noqa
import gen49 as g

BOARDS = {}
mic, CHR = g.mic, g.CHR


def reg(fn):
    BOARDS[fn.__name__] = fn
    return fn


FR = dict(name='Felicidad Roxas', ini='FR')
LC = dict(name='Leonora Castillo', ini='LC')
CARD = 'background:#fff;border-radius:20px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 24px rgba(15,23,42,.06)'


# ======================================================================== E. Search first, "Where to?"
def perspective_road():
    vx, vy = 1130, 118
    lines = []
    for bx in (420, 1440 + 380):
        lines.append(f'<path d="M{bx} 420 L{vx} {vy}" stroke="rgba(203,210,234,.34)" stroke-width="2.5"/>')
    # dashed centre line converging
    mx = (420 + 1820) / 2
    segs = []
    t = 0.0
    k = 0
    while t < .96:
        L = .09 * (1 - t) ** 1.4 + .006
        if k % 2 == 0:
            x1, y1 = mx + (vx - mx) * t, 420 + (vy - 420) * t
            x2, y2 = mx + (vx - mx) * (t + L), 420 + (vy - 420) * (t + L)
            w = 6 * (1 - t) + .6
            segs.append(f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="#e8b800" stroke-opacity="{.55*(1-t)+.12:.2f}" stroke-width="{w:.2f}"/>')
        t += L
        k += 1
    glow = f'<ellipse cx="{vx}" cy="{vy}" rx="160" ry="34" fill="url(#hz)"/>'
    return (f'<svg class="pr" viewBox="0 0 1440 420" preserveAspectRatio="none" aria-hidden="true"><defs><radialGradient id="hz">'
            f'<stop offset="0" stop-color="#e8b800" stop-opacity=".22"/><stop offset="1" stop-color="#e8b800" stop-opacity="0"/></radialGradient></defs>'
            f'{glow}{"".join(lines)}<g class="dash">{"".join(segs)}</g></svg>')


@reg
def R49Search():
    css = '''.band{height:400px;overflow:visible;z-index:5}
.pr{position:absolute;inset:0;width:100%;height:100%}
.gr{padding-top:40px}
h1{margin:10px 0 0;font-size:56px;line-height:1;font-weight:800;letter-spacing:-.035em}
.sb{position:relative;z-index:4;margin-top:34px;width:760px}
.fld{height:66px;border-radius:16px;background:#fff;color:#0f172a;display:flex;align-items:center;gap:14px;padding:0 18px 0 22px;box-shadow:0 0 0 4px rgba(232,184,0,.35),0 18px 40px rgba(0,0,0,.25)}
.fld svg{color:#3a4486}
.fld .tx{font-size:19px;font-weight:500}
.fld .cr{width:2px;height:26px;background:#0f1445;margin-left:-12px;animation:bl 1s steps(1) infinite}
@keyframes bl{50%{opacity:0}}
.fld kbd{margin-left:auto;font:600 12px "IBM Plex Mono",monospace;color:#5b6779;border:1px solid #dfe4ee;border-bottom-width:2px;border-radius:7px;padding:4px 8px}
.dd{position:absolute;left:0;right:0;top:76px;border-radius:16px;background:#fff;color:#0f172a;padding:8px;box-shadow:0 24px 50px rgba(15,23,42,.22),0 0 0 1px rgba(15,23,42,.05)}
.dd p{margin:6px 12px 6px;font:600 11px "IBM Plex Mono",monospace;letter-spacing:.08em;color:#8a94a8}
.dd a{display:flex;align-items:center;gap:12px;height:52px;padding:0 14px;border-radius:12px;font-size:16px;font-weight:500}
.dd a svg{color:#3a4486}.dd a mark{background:none;color:#0f172a;font-weight:800;text-decoration:underline;text-decoration-color:#e8b800;text-decoration-thickness:3px;text-underline-offset:4px}
.dd a .sy{margin-left:auto;font-size:13px;color:#5b6779}
.dd a.on{background:#f3f5f9}.dd a.on .en{font:600 12px "IBM Plex Mono",monospace;color:#5b6779;margin-left:14px}
.main{margin-top:150px}
.dir{display:grid;grid-template-columns:repeat(3,1fr);gap:40px}
.dir h2{margin:0 0 6px;display:flex;align-items:baseline;gap:10px;font-size:13px;font-weight:600;color:#5b6779}
.dir h2 b{font-size:17px;font-weight:800;color:#0f1445}
.dir a{display:flex;align-items:center;gap:10px;height:36px;border-bottom:1px solid #e6eaf1;font-size:14px;font-weight:500}
.dir a svg{color:#7a85a6}.dir a:hover{color:#1a1f6e}'''
    res = (f'<p>2 MODULES</p><a class="on" href="#">{mic("cal")}<span><mark>Sch</mark>eduling</span><span class="sy">BMS · Operations</span><span class="en">Enter</span></a>'
           f'<a href="#">{mic("cal")}<span><mark>Sch</mark>eduling</span><span class="sy">VMMS · Operations</span></a>')
    sb = (f'<div class="sb"><div class="fld">{ic(I["search"], 22)}<span class="tx">sch</span><span class="cr"></span><kbd>Ctrl K</kbd></div>'
          f'<div class="dd">{res}</div></div>')
    dirs = ''.join(f'<section><h2><b>{s["code"]}</b>{s["role"]}</h2>' + ''.join(f'<a href="#">{mic(k, 16)}{n}</a>' for n, k in s['mods']) + '</section>'
                   for s in CORAZON)
    body = (f'<div class="pg"><div class="band">{perspective_road()}<div class="w">{top()}<div class="gr"><p class="dt">{DATE}</p>'
            f'<h1>Where to, Corazon?</h1>{sb}</div></div></div><main class="w main"><div class="dir">{dirs}</div></main></div>')
    return 'E · Search first: "Where to?" finds any module in any system (shown typing "sch")', css, body, 900


# ======================================================================== F. Menu bar with drop down modules, a moving day hero
def house_scene():
    van = '<use href="#van" x="0" y="0" width="460" height="187"/>'
    return f'''<svg class="hs" viewBox="0 0 1440 470" preserveAspectRatio="xMidYMax slice" aria-hidden="true"><defs>{V_VAN}
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f1445"/><stop offset="1" stop-color="#2a2f7a"/></linearGradient></defs>
<rect width="1440" height="470" fill="url(#sky)"/>
<circle cx="1260" cy="92" r="26" fill="#f6e7a8" opacity=".9"/>
<g fill="#151b5c"><rect x="0" y="300" width="220" height="110"/><rect x="40" y="250" width="90" height="60"/><rect x="250" y="320" width="120" height="90"/></g>
<g fill="#1c2470">
<rect x="560" y="210" width="300" height="200"/><path d="M540 214 L710 130 L880 214 Z"/>
</g>
<path d="M540 214 L710 130 L880 214" fill="none" stroke="#283084" stroke-width="8"/>
<g fill="#f6d25e"><rect x="600" y="246" width="56" height="44" rx="2"/><rect x="764" y="246" width="56" height="44" rx="2" opacity=".55"/><rect x="690" y="320" width="48" height="90"/></g>
<g stroke="#1c2470" stroke-width="3"><path d="M628 246v44M600 268h56"/></g>
<g stroke="#3a4396" stroke-width="3"><path d="M880 340h40M880 352h40"/>{''.join(f'<path d="M{x} 330v80"/>' for x in range(884, 924, 14))}</g>
<rect x="0" y="410" width="1440" height="60" fill="#0a0d33"/>
<g fill="#cbd2ea" opacity=".22">{''.join(f'<rect x="{x}" y="440" width="60" height="4" rx="2"/>' for x in range(20, 1440, 130))}</g>
<g transform="translate(930 226)">{van}
<g class="lift"><rect x="-44" y="104" width="50" height="6" fill="#8d96ab"/>
<g transform="translate(-36 74)"><rect width="34" height="30" fill="#c89b5e"/><rect y="12" width="34" height="5" fill="#a77c45"/><path d="M17 0v12" stroke="#a77c45" stroke-width="3"/></g></g>
<path d="M-2 106 V184" stroke="#5a6278" stroke-width="3"/></g>
<g transform="translate(878 380)"><rect width="30" height="28" fill="#c89b5e"/><rect y="11" width="30" height="5" fill="#a77c45"/></g>
<g transform="translate(842 386)"><rect width="34" height="22" fill="#b98a50"/><rect y="9" width="34" height="4" fill="#97703f"/></g>
</svg>'''


@reg
def R49Menu():
    css = '''.bar{position:relative;z-index:6;height:72px;background:#0a0d33;color:#fff;box-shadow:inset 0 -1px 0 rgba(255,255,255,.08)}
.bar .top{height:72px}
.nav{display:flex;gap:6px;margin-left:44px;height:72px;align-items:center}
.nav button{height:44px;padding:0 14px;border:0;border-radius:12px;background:none;color:rgba(255,255,255,.78);font:600 15px Inter,sans-serif;display:flex;align-items:center;gap:8px;cursor:pointer}
.nav button small{font-weight:500;font-size:12px;color:rgba(255,255,255,.5)}
.nav button.on{background:rgba(255,255,255,.1);color:#fff}
.nav button:hover{background:rgba(255,255,255,.08)}
.mm{position:absolute;left:276px;top:66px;width:620px;border-radius:18px;background:#fff;color:#0f172a;padding:20px 20px 14px;box-shadow:0 28px 60px rgba(5,8,40,.45),0 0 0 1px rgba(15,23,42,.06)}
.mm:before{content:"";position:absolute;left:58px;top:-6px;width:12px;height:12px;background:#fff;transform:rotate(45deg)}
.mm .h{display:flex;align-items:baseline;gap:10px;padding:0 10px 12px;border-bottom:1px solid #eef1f6}
.mm .h b{font-size:16px}.mm .h span{font-size:13px;color:#5b6779}.mm .h em{margin-left:auto;font-style:normal;font-size:13px;color:#5b6779}
.mm .gd{display:grid;grid-template-columns:1fr 1fr;gap:2px 10px;margin-top:10px}
.mm a{display:flex;align-items:center;gap:12px;height:48px;padding:0 10px;border-radius:12px;font-size:15px;font-weight:500}
.mm a svg{color:#3a4486}.mm a:hover,.mm a.on{background:#f3f5f9}
.hero{position:relative;height:500px;overflow:hidden;color:#fff}
.hs{position:absolute;inset:0;width:100%;height:100%}
.lift{animation:lift 6s ease-in-out infinite}
@keyframes lift{0%,15%{transform:translateY(0)}45%,65%{transform:translateY(74px)}95%,100%{transform:translateY(0)}}
.hg{position:absolute;left:120px;bottom:84px;z-index:2;width:420px}
h1{margin:10px 0 0;font-size:54px;line-height:1.02;font-weight:800;letter-spacing:-.035em}
.l{margin:14px 0 0;font-size:16px;line-height:1.5;color:rgba(255,255,255,.7)}
.sys{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:-52px;position:relative;z-index:3}
.sys a{''' + CARD + ''';padding:22px 24px;display:block}
.sys b{font-size:22px;font-weight:800;color:#0f1445}
.sys .r{float:right;font-size:13px;color:#5b6779;margin-top:6px}
.sys p{margin:6px 0 0;font-size:13px;color:#5b6779}'''
    nav = ''.join(f'<button type="button" class="{"on" if s["code"] == "VMMS" else ""}" aria-expanded="{"true" if s["code"] == "VMMS" else "false"}">{s["code"]}{ic(I["down"], 14, 2.4)}</button>'
                  for s in CORAZON)
    v = CORAZON[1]
    mm = (f'<div class="mm"><div class="h"><b>VMMS</b><span>{v["name"]}</span><em>{v["role"]}</em></div><div class="gd">'
          + ''.join(f'<a href="#" class="{"on" if i == 3 else ""}">{mic(k)}{n}</a>' for i, (n, k) in enumerate(v['mods'])) + '</div></div>')
    sys_ = ''.join(f'<a href="#"><span class="r">{s["role"]}</span><b>{s["code"]}</b><p>{s["name"]}</p></a>' for s in CORAZON)
    body = (f'<div class="pg"><div class="bar"><div class="w">{top(extra=f"<nav class=nav>{nav}</nav>")}{mm}</div></div>'
            f'<div class="hero">{house_scene()}<div class="hg"><p class="dt">{DATE}</p><h1>Good morning, Corazon</h1>'
            f'<p class="l">Every system\'s modules sit in the bar above. Point at one to open its menu.</p></div></div>'
            f'<main class="w"><div class="sys">{sys_}</div></main></div>')
    return 'F · Menu bar: each system drops its modules down (VMMS open); a moving day hero, the tail lift working', css, body, 900


# ======================================================================== G. Light ledger, big type
@reg
def R49Ledger():
    css = '''.pg{background:#f7f7f4}
.bar{height:64px;background:#0f1445;color:#fff;position:relative}
.bar:after{content:"";position:absolute;left:0;right:0;bottom:-3px;height:3px;background:#e8b800}
.mini{position:absolute;bottom:-4px;width:58px;animation:mv 40s linear infinite;animation-delay:-12s;z-index:2}
@keyframes mv{from{transform:translateX(-80px)}to{transform:translateX(1520px)}}
.gr{padding:46px 0 34px}
.gr .dt{color:#8a6d00}
h1{margin:12px 0 0;font-size:76px;line-height:.95;font-weight:800;letter-spacing:-.045em;color:#0f1445}
.sec{border-top:2px solid #0f1445;padding:12px 0 20px}
.sh{display:flex;align-items:baseline;gap:14px;font-size:13px;color:#5b6779}
.sh b{font:600 13px "IBM Plex Mono",monospace;color:#0f1445;letter-spacing:.06em}
.sh span:last-child{margin-left:auto}
.gl{display:grid;grid-template-columns:repeat(3,1fr);column-gap:24px;margin-top:6px}
.gl a{display:flex;align-items:center;gap:10px;height:50px;font-size:24px;font-weight:700;letter-spacing:-.02em;color:#0f172a}
.gl a svg{opacity:0;transform:translateX(-6px);transition:.2s;color:#0f1445}
.gl a:hover{color:#1a1f6e}.gl a:hover svg{opacity:1;transform:none}'''
    secs = ''.join(f'<section class="sec"><div class="sh"><b>{s["code"]}</b><span>{s["name"]}</span><span>{s["role"]}</span></div><div class="gl">'
                   + ''.join(f'<a href="#">{n}{ic(I["arrow"], 20, 2.4)}</a>' for n, _ in s['mods']) + '</div></section>' for s in CORAZON)
    body = (f'<div class="pg"><div class="bar"><div class="w">{top()}</div>'
            f'<svg class="mini" viewBox="-6 -2 96 50"><defs>{V_L300}</defs><use href="#l300"/></svg></div>'
            f'<main class="w lt"><div class="gr"><p class="dt">{DATE}</p><h1>Good morning, Corazon.</h1></div>{secs}</main></div>')
    return 'G · Ledger: a light page, big type links, the L300 runs along the gold line', css, body, 900


# ======================================================================== H. The fleet head on, a wide row per system
def front(x, w, h, kind):
    # A truck seen head on, headlights on. w/h in px; drawn in a 100 x 100 box then scaled.
    cab = {'l300': (16, 30, 68, 52), 'van': (14, 30, 72, 54), 'big': (10, 26, 80, 60)}[kind]
    cx, cy, cw, ch = cab
    box_ = '' if kind == 'l300' else f'<rect x="4" y="2" width="92" height="{cy - 2}" rx="2" fill="#e9ecf3"/><rect x="4" y="{cy - 6}" width="92" height="4" fill="#c9d0de"/>'
    return f'''<g transform="translate({x} {130 - h}) scale({w / 100} {h / 100})">
<ellipse cx="50" cy="104" rx="70" ry="9" fill="url(#beam)"/>
{box_}
<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="6" fill="#f7f8fb"/>
<rect x="{cx + 5}" y="{cy + 5}" width="{cw - 10}" height="{ch * .38:.1f}" rx="3" fill="#14205a"/>
<rect x="{cx + 8}" y="{cy + ch * .56:.1f}" width="{cw - 16}" height="{ch * .18:.1f}" rx="2" fill="#2a2f45"/>
<g transform="translate({50 - 6} {cy + ch * .585:.1f}) scale(.036)" fill="#e8b800">{LOGO_POLY}</g>
<circle class="hl" cx="{cx + 7}" cy="{cy + ch * .66:.1f}" r="4.2" fill="#fff8d6"/><circle class="hl" cx="{cx + cw - 7}" cy="{cy + ch * .66:.1f}" r="4.2" fill="#fff8d6"/>
<rect x="{cx - 2}" y="{cy + ch - 6}" width="{cw + 4}" height="7" rx="2" fill="#2a2f45"/>
<rect x="{cx + 2}" y="{cy + ch}" width="10" height="{100 - cy - ch}" rx="2" fill="#11131f"/><rect x="{cx + cw - 12}" y="{cy + ch}" width="10" height="{100 - cy - ch}" rx="2" fill="#11131f"/>
</g>'''


@reg
def R49Fleet():
    css = '''.band{height:300px}
.fl{position:absolute;right:60px;bottom:0;width:640px;height:270px}
.hl{animation:hl 5s ease-in-out infinite}
@keyframes hl{0%,100%{opacity:1}50%{opacity:.82}}
.gr{padding-top:34px}
h1{margin:10px 0 0;font-size:52px;line-height:1;font-weight:800;letter-spacing:-.035em}
.l{margin:12px 0 0;font-size:16px;color:rgba(255,255,255,.68)}
.main{margin-top:26px;display:flex;flex-direction:column;gap:14px}
.row{''' + CARD + ''';display:flex;align-items:center;min-height:132px;padding:0 18px 0 30px}
.id{flex:none;width:230px}
.id b{display:block;font-size:44px;line-height:1;font-weight:800;letter-spacing:-.035em;color:#0f1445}
.id span{display:block;margin-top:8px;font-size:13px;color:#5b6779}
.ms{flex:1;display:flex;flex-wrap:wrap;gap:6px;border-left:1px solid #eef1f6;padding-left:22px}
.ms a{display:flex;flex-direction:column;justify-content:center;gap:8px;width:139px;height:92px;padding:0 14px;border-radius:14px;font-size:14px;font-weight:600;line-height:1.2}
.ms a svg{color:#3a4486}.ms a:hover{background:#f3f5f9}'''
    fleet = (f'<svg class="fl" viewBox="0 0 640 270" aria-hidden="true"><defs><radialGradient id="beam">'
             f'<stop offset="0" stop-color="#fff3b0" stop-opacity=".35"/><stop offset="1" stop-color="#fff3b0" stop-opacity="0"/></radialGradient></defs>'
             f'<rect x="0" y="232" width="640" height="38" fill="#0a0d33"/>'
             f'<g transform="translate(0 102)">{front(40, 130, 130, "l300")}{front(230, 160, 170, "van")}{front(440, 190, 210, "big")}</g></svg>')
    rows = ''.join(f'<section class="row"><div class="id"><b>{s["code"]}</b><span>{s["role"]}<br>{s["name"]}</span></div><div class="ms">'
                   + ''.join(f'<a href="#">{mic(k, 20)}{n}</a>' for n, k in s['mods']) + '</div></section>' for s in CORAZON)
    body = (f'<div class="pg"><div class="band">{fleet}<div class="w">{top()}<div class="gr"><p class="dt">{DATE}</p>'
            f'<h1>Good morning, Corazon</h1><p class="l">Pick a module to start.</p></div></div></div><main class="w main">{rows}</main></div>')
    return 'H · The fleet head on, headlights on; a wide row per system', css, body, 900


# ======================================================================== I. Pinned shortcuts first
@reg
def R49Pins():
    css = '''.band{height:420px}
.wm{position:absolute;right:-120px;top:-40px;height:520px;fill:#e8b800;opacity:.07}
.gr{padding-top:30px}
h1{margin:10px 0 0;font-size:48px;line-height:1;font-weight:800;letter-spacing:-.03em}
.ph{margin:36px 0 12px;display:flex;align-items:baseline;gap:12px;font-size:15px;font-weight:700}
.ph span{font-size:13px;font-weight:500;color:rgba(255,255,255,.6)}
.pins{display:grid;grid-template-columns:repeat(5,1fr);gap:16px}
.pins a{position:relative;height:124px;border-radius:18px;background:#fff;color:#0f172a;padding:18px 18px;display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 12px 28px rgba(0,0,0,.25)}
.pins a .sy{font:600 11px "IBM Plex Mono",monospace;letter-spacing:.06em;color:#5b6779}
.pins a b{font-size:18px;font-weight:700;letter-spacing:-.01em}
.pins a .pn{position:absolute;right:16px;top:16px;color:#c99f00}
.pins a.add{background:none;color:rgba(255,255,255,.75);box-shadow:none;border:1.5px dashed rgba(255,255,255,.3);justify-content:center;align-items:center;gap:8px;flex-direction:row;font-size:14px;font-weight:600}
.main{margin-top:36px}
.ah{margin:0 0 12px;font-size:15px;font-weight:700}
.cols{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.col{''' + CARD + ''';padding:16px 10px 8px}
.col h2{margin:0 12px 6px;display:flex;align-items:baseline;gap:8px;font-size:18px;font-weight:800;color:#0f1445}
.col h2 span{margin-left:auto;font-size:13px;font-weight:500;color:#5b6779}
.col a{display:flex;align-items:center;gap:10px;height:40px;padding:0 12px;border-radius:10px;font-size:14px;font-weight:500}
.col a svg{color:#3a4486}.col a .tg{margin-left:auto;color:#c3cad8;opacity:0}
.col a:hover{background:#f3f5f9}.col a:hover .tg{opacity:1}.col a .tg.on{opacity:1;color:#c99f00}'''
    pinned = [('VRMS', 'Repair tickets'), ('VMMS', 'Work orders'), ('BMS', 'Scheduling'), ('VRMS', 'New repair')]
    pins = ''.join(f'<a href="#"><span class="sy">{c}</span><b>{n}</b>{ic(I["pin"], 18, 2, "pn")}</a>' for c, n in pinned)
    pins += f'<a href="#" class="add">{ic(I["plus"], 18)}Pin a module</a>'
    ps = set(pinned)
    cols = ''.join(f'<section class="col"><h2>{s["code"]}<span>{s["role"]}</span></h2>'
                   + ''.join(f'<a href="#">{mic(k, 16)}{n}{ic(I["pin"], 16, 2, "tg on" if (s["code"], n) in ps else "tg")}</a>' for n, k in s['mods'])
                   + '</section>' for s in CORAZON)
    body = (f'<div class="pg"><div class="band"><svg class="wm" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg><div class="w">{top()}'
            f'<div class="gr"><p class="dt">{DATE}</p><h1>Good morning, Corazon</h1></div>'
            f'<div class="ph">Pinned<span>Your shortcuts across every system</span></div><div class="pins">{pins}</div></div></div>'
            f'<main class="w main"><h2 class="ah">All modules</h2><div class="cols">{cols}</div></main></div>')
    return 'I · Pinned first: your own shortcuts across systems, then every module (pin from any row)', css, body, 900


# ======================================================================== J. Stacked drawers, one open at a time
def aerial_road():
    tv = VAN_TOP.replace('class="van"', 'class="tv"')
    vans = ''.join(f'<div class="aerv a{i}">{tv}</div>' for i in range(2))
    return (f'<div class="air"><svg viewBox="0 0 1440 104" preserveAspectRatio="none" class="as"><rect width="1440" height="104" fill="#0a0d33"/>'
            f'<rect y="0" width="1440" height="3" fill="#232a78"/><rect y="101" width="1440" height="3" fill="#232a78"/>'
            f'<path d="M0 52H1440" stroke="#e8b800" stroke-opacity=".5" stroke-width="2" stroke-dasharray="40 30"/></svg>{vans}</div>')


@reg
def R49Drawers():
    css = '''.rd{position:absolute;opacity:0;pointer-events:none}
.band{height:300px}
.gr{padding-top:28px}
h1{margin:10px 0 0;font-size:48px;line-height:1;font-weight:800;letter-spacing:-.03em}
.air{position:absolute;left:0;right:0;bottom:0;height:104px}
.as{position:absolute;inset:0;width:100%;height:100%}
.aerv{position:absolute;left:0;top:0;animation:air 24s linear infinite}
.aerv svg{position:absolute;left:0;width:84px;height:40px}
.a0 svg{top:6px}.a1 svg{top:58px}
.a0{animation-delay:-6s}.a1{animation-delay:-17s;animation-duration:30s}
@keyframes air{from{transform:translateX(-80px)}to{transform:translateX(1520px)}}
.main{margin-top:24px;display:flex;flex-direction:column;gap:12px}
.dr{''' + CARD + ''';overflow:hidden}
.dh{display:flex;align-items:center;gap:16px;height:78px;padding:0 26px;cursor:pointer}
.dh b{font-size:24px;font-weight:800;color:#0f1445;width:90px}
.dh .nm{font-size:14px;color:#5b6779}
.dh .rl{margin-left:auto;font-size:14px;font-weight:600}
.dh .ct{font:500 12px "IBM Plex Mono",monospace;color:#8a94a8;width:84px;text-align:right}
.dh svg{transition:transform .3s;color:#5b6779}
.bd{display:none;grid-template-columns:repeat(3,1fr);gap:10px;padding:2px 22px 22px}
.bd a{display:flex;align-items:center;gap:14px;height:64px;padding:0 18px;border-radius:14px;background:#f5f7fb;font-size:16px;font-weight:600}
.bd a svg{color:#3a4486}.bd a:hover{background:#eceff6}
#d1:checked~.main .x1 .bd,#d2:checked~.main .x2 .bd,#d3:checked~.main .x3 .bd{display:grid}
#d1:checked~.main .x1 .dh svg,#d2:checked~.main .x2 .dh svg,#d3:checked~.main .x3 .dh svg{transform:rotate(180deg)}
#d1:checked~.main .x1,#d2:checked~.main .x2,#d3:checked~.main .x3{box-shadow:0 0 0 2px #0f1445,0 12px 28px rgba(15,23,42,.10)}'''
    radios = ''.join(f'<input class="rd" type="radio" name="d" id="d{i+1}"{" checked" if i == 2 else ""} aria-label="{s["code"]}">' for i, s in enumerate(CORAZON))
    drs = ''.join(f'<section class="dr x{i+1}"><label class="dh" for="d{i+1}"><b>{s["code"]}</b><span class="nm">{s["name"]}</span>'
                  f'<span class="rl">{s["role"]}</span><span class="ct">{len(s["mods"])} modules</span>{ic(I["down"], 20)}</label><div class="bd">'
                  + ''.join(f'<a href="#">{mic(k, 20)}{n}</a>' for n, k in s['mods']) + '</div></section>' for i, s in enumerate(CORAZON))
    body = (f'<div class="pg">{radios}<div class="band"><div class="w">{top()}<div class="gr"><p class="dt">{DATE}</p><h1>Good morning, Corazon</h1></div></div>'
            f'{aerial_road()}</div><main class="w main">{drs}</main></div>')
    return 'J · Drawers: one system open at a time (click a row); the road from above', css, body, 900


# ======================================================================== Suite management placements (Felicidad Roxas, VMMS Admin and VRMS Admin)
ADM_BAND = '''.band{height:236px}
.gr{padding-top:26px}
h1{margin:10px 0 0;font-size:44px;line-height:1;font-weight:800;letter-spacing:-.03em}
.l{margin:10px 0 0;font-size:15px;color:rgba(255,255,255,.66)}
.rl{position:absolute;left:0;right:0;bottom:0;height:46px;background:#0a0d33}
.rl i{position:absolute;left:0;right:0;top:22px;height:2px;background:repeating-linear-gradient(90deg,rgba(203,210,234,.3) 0 30px,transparent 30px 74px)}
.rl svg{position:absolute;bottom:6px;width:96px;animation:rv 34s linear infinite;animation-delay:-9s}
@keyframes rv{from{transform:translateX(-120px)}to{transform:translateX(1560px)}}
.grp{margin-top:12px}
.grp p{margin:0 0 2px;font:600 11px "IBM Plex Mono",monospace;letter-spacing:.08em;color:#8a94a8;text-transform:uppercase}
.gg{display:grid;grid-template-columns:1fr 1fr;column-gap:8px}
.gg a{display:flex;align-items:center;gap:9px;height:36px;padding:0 8px;margin:0 -8px;border-radius:9px;font-size:14px;font-weight:500}
.gg a svg{color:#3a4486;flex:none}.gg a:hover{background:#f3f5f9}
.sc{''' + CARD + ''';padding:20px 24px 18px}
.sc .hd{display:flex;align-items:baseline;gap:10px;padding-bottom:10px;border-bottom:1px solid #eef1f6}
.sc .hd b{font-size:22px;font-weight:800;color:#0f1445}.sc .hd span{margin-left:auto;font-size:13px;color:#5b6779}'''


def adm_band(line='Two systems and Suite management.', extra='', name=FR):
    return (f'<div class="band"><div class="w">{top(name["name"], name["ini"])}<div class="gr"><p class="dt">{DATE}</p>'
            f'<h1>Good morning, {name["name"].split()[0]}</h1><p class="l">{line}</p></div>{extra}</div>'
            f'<div class="rl"><i></i><svg viewBox="-8 -2 138 56"><defs>{V_VAN}</defs><use href="#van"/></svg></div></div>')


def sys_card(s, cols=2):
    gg = ''.join(f'<div class="grp"><p>{gn}</p><div class="gg" style="grid-template-columns:repeat({cols},1fr)">'
                 + ''.join(f'<a href="#">{mic(k, 16)}{n}</a>' for n, k in mods) + '</div></div>' for gn, mods in s['groups'])
    return f'<section class="sc"><div class="hd"><b>{s["code"]}</b><span>{s["role"]}</span></div>{gg}</section>'


@reg
def R49AdmColumn():
    css = ADM_BAND + '''.main{margin-top:26px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:24px;align-items:start}
.su{background:#0f1445;color:#fff;border-radius:20px;padding:20px 14px 12px;box-shadow:0 14px 34px rgba(15,20,69,.25)}
.su .hd{display:flex;align-items:baseline;padding:0 10px 10px;border-bottom:1px solid rgba(255,255,255,.12)}
.su .hd b{font-size:20px;font-weight:800}.su .hd span{margin-left:auto;font-size:13px;color:rgba(255,255,255,.6)}
.su a{display:flex;align-items:center;gap:12px;height:50px;padding:0 10px;border-radius:12px;font-size:15px;font-weight:500}
.su a svg{color:#e8b800;flex:none}.su a em{margin-left:auto;font-style:normal;font-size:13px;color:#e8b800;font-weight:600}
.su a:hover{background:rgba(255,255,255,.08)}'''
    su = ('<aside class="su"><div class="hd"><b>Suite management</b><span>VMMS, VRMS</span></div>'
          + ''.join(f'<a href="#">{mic(k)}{n}{f"<em>{c}</em>" if c else ""}</a>' for n, k, c in SUITE_SYS) + '</aside>')
    body = f'<div class="pg">{adm_band()}<main class="w main">{sys_card(FELICIDAD[0])}{sys_card(FELICIDAD[1])}{su}</main></div>'
    return 'M1 · Suite management as a navy third column beside the systems', css, body, 900


@reg
def R49AdmStrip():
    css = ADM_BAND + '''.st{margin-top:-0px;position:relative;z-index:2;background:#fff;border-radius:18px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 24px rgba(15,23,42,.06);display:flex;align-items:stretch;overflow:hidden;margin-top:24px}
.st .tl{flex:none;width:210px;background:#0f1445;color:#fff;padding:18px 22px;display:flex;flex-direction:column;justify-content:center}
.st .tl b{font-size:16px;font-weight:800}.st .tl span{margin-top:4px;font-size:12px;color:rgba(255,255,255,.6)}
.st a{flex:1;display:flex;flex-direction:column;justify-content:center;gap:4px;padding:14px 20px;border-left:1px solid #eef1f6;font-size:15px;font-weight:600}
.st a span{display:flex;align-items:center;gap:8px}.st a svg{color:#3a4486}
.st a em{font-style:normal;font-size:13px;font-weight:500;color:#5b6779;padding-left:26px}
.st a em.n{color:#8a6d00;font-weight:600}
.st a:hover{background:#f7f8fb}
.main{margin-top:20px;display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start}'''
    st = ('<div class="st"><div class="tl"><b>Suite management</b><span>For VMMS and VRMS</span></div>'
          + ''.join(f'<a href="#"><span>{mic(k)}{n}</span><em class="{"n" if c else ""}">{c or "&nbsp;"}</em></a>' for n, k, c in SUITE_SYS) + '</div>')
    body = (f'<div class="pg">{adm_band()}<div class="w">{st}</div>'
            f'<main class="w main">{sys_card(FELICIDAD[0], 3)}{sys_card(FELICIDAD[1], 3)}</main></div>')
    return 'M2 · Suite management as one strip across the top, the systems below', css, body, 900


@reg
def R49AdmMenu():
    css = ADM_BAND + '''.sm{position:relative;margin-left:auto;margin-right:10px;height:44px;padding:0 14px;border-radius:12px;border:0;background:rgba(255,255,255,.1);color:#fff;font:600 14px Inter,sans-serif;display:flex;align-items:center;gap:10px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.18)}
.sm svg{color:#e8b800}.sm em{font-style:normal;font-size:12px;font-weight:600;color:#0f1445;background:#e8b800;border-radius:6px;padding:2px 7px}
.top .me{margin-left:0}
.dd{position:absolute;right:190px;top:64px;z-index:8;width:340px;border-radius:16px;background:#fff;color:#0f172a;padding:10px;box-shadow:0 24px 50px rgba(5,8,40,.35)}
.dd p{margin:6px 12px 8px;font-size:12px;color:#5b6779}
.dd a{display:flex;align-items:center;gap:12px;height:46px;padding:0 12px;border-radius:12px;font-size:15px;font-weight:500}
.dd a svg{color:#3a4486}.dd a em{margin-left:auto;font-style:normal;font-size:13px;color:#8a6d00;font-weight:600}
.dd a:hover,.dd a.on{background:#f3f5f9}
.band{overflow:visible;z-index:5}
.main{margin-top:26px;display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start}'''
    btn = f'<button class="sm" type="button" aria-expanded="true">{ic(I["shield"], 18)}Suite management<em>4 to review</em>{ic(I["down"], 14, 2.4)}</button>'
    dd = ('<div class="dd"><p>For VMMS and VRMS</p>' + ''.join(f'<a href="#" class="{"on" if i == 0 else ""}">{mic(k)}{n}{f"<em>{c}</em>" if c else ""}</a>'
                                                             for i, (n, k, c) in enumerate(SUITE_SYS)) + '</div>')
    band = adm_band(line='Suite management sits in the bar, beside your account.').replace(
        '<button class="me"', btn + '<button class="me"', 1).replace('<div class="gr">', dd + '<div class="gr">', 1)
    body = f'<div class="pg">{band}<main class="w main">{sys_card(FELICIDAD[0], 3)}{sys_card(FELICIDAD[1], 3)}</main></div>'
    return 'M3 · Suite management in the top bar, a menu with the count on the button (shown open)', css, body, 900


@reg
def R49AdmTabs():
    css = '''.rd{position:absolute;opacity:0;pointer-events:none}
.band{height:360px}
.gr{padding-top:22px;display:flex;align-items:baseline}
h1{margin:0;font-size:32px;font-weight:800;letter-spacing:-.02em}.gr .dt{margin-left:auto}
.tabs{position:absolute;left:0;right:0;top:146px;display:grid;grid-template-columns:1fr 1fr 1.25fr}
.tab{display:block;cursor:pointer;opacity:.42;transition:opacity .3s}
.tab:hover{opacity:.7}
.tab .c{display:block;font-size:58px;line-height:1;font-weight:800;letter-spacing:-.035em}
.tab .r{display:block;margin-top:12px;font-size:14px;color:rgba(255,255,255,.75)}
.tab.su .c{font-size:40px;padding-top:14px;letter-spacing:-.025em}
.tab.su .c em{font-style:normal;color:#e8b800}
#a1:checked~.band .t1,#a2:checked~.band .t2,#a3:checked~.band .t3{opacity:1}
.track{position:absolute;left:0;right:0;bottom:40px;height:2px;background:rgba(255,255,255,.14)}
.van{position:absolute;bottom:42px;width:120px}
#a1:checked~.band .van{left:0;animation:i1 1s cubic-bezier(.3,.7,.3,1) both}
#a2:checked~.band .van{left:369px;animation:i2 1.1s cubic-bezier(.3,.7,.3,1) both}
#a3:checked~.band .van{left:738px;animation:i3 1.2s cubic-bezier(.3,.7,.3,1) both}
@keyframes i1{from{left:-160px}}@keyframes i2{from{left:-160px}}@keyframes i3{from{left:-160px}}
.main{margin-top:30px}
.pn{display:none;grid-template-columns:repeat(4,1fr);gap:14px}
#a1:checked~.main .p1,#a2:checked~.main .p2,#a3:checked~.main .p3{display:grid}
.pn a{height:96px;border-radius:16px;background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 22px rgba(15,23,42,.05);padding:16px 18px;display:flex;flex-direction:column;justify-content:space-between}
.pn a svg{color:#3a4486}.pn a span{font-size:16px;font-weight:700}
.pn.p3{grid-template-columns:repeat(3,1fr)}
.pn.p3 a{height:150px;padding:22px 24px}.pn.p3 a span{font-size:20px}
.pn a em{font-style:normal;font-size:14px;font-weight:600;color:#8a6d00;margin-top:-8px}'''
    radios = ''.join(f'<input class="rd" type="radio" name="a" id="a{i}"{" checked" if i == 3 else ""} aria-label="{t}">' for i, t in ((1, 'VMMS'), (2, 'VRMS'), (3, 'Suite management')))
    tabs = ''.join(f'<label class="tab t{i+1}" for="a{i+1}"><span class="c">{s["code"]}</span><span class="r">{s["role"]} · {len(s["mods"])} modules</span></label>'
                   for i, s in enumerate(FELICIDAD))
    tabs += '<label class="tab t3 su" for="a3"><span class="c">Suite <em>management</em></span><span class="r">For VMMS and VRMS · 4 to review</span></label>'
    pns = ''.join(f'<div class="pn p{i+1}">' + ''.join(f'<a href="#">{mic(k, 20)}<span>{n}</span></a>' for n, k in s['mods']) + '</div>' for i, s in enumerate(FELICIDAD))
    pns += '<div class="pn p3">' + ''.join(f'<a href="#">{mic(k, 22)}<span>{n}</span>{f"<em>{c}</em>" if c else ""}</a>' for n, k, c in SUITE_SYS) + '</div>'
    body = (f'<div class="pg">{radios}<div class="band"><div class="w" style="height:100%">{top(FR["name"], FR["ini"])}<div class="gr"><h1>Good morning, Felicidad</h1><p class="dt">{DATE}</p></div>'
            f'<div class="tabs">{tabs}</div><div class="track"></div><div class="van"><svg viewBox="-6 -2 96 50"><defs>{V_L300}</defs><use href="#l300"/></svg></div></div></div>'
            f'<main class="w main">{pns}</main></div>')
    return 'M4 · Suite management as a third tab (pairs with B; shown on Suite management)', css, body, 900


@reg
def R49AdmFirst():
    css = ADM_BAND + '''.band{height:380px}
.nd{position:absolute;left:0;right:0;top:206px;display:grid;grid-template-columns:1fr 1fr 1.1fr;gap:16px}
.nd a{border-radius:16px;padding:18px 20px;background:rgba(255,255,255,.07);box-shadow:inset 0 0 0 1px rgba(255,255,255,.12);display:flex;align-items:center;gap:16px}
.nd a .n{font-size:40px;font-weight:800;color:#e8b800;line-height:1;font-variant-numeric:tabular-nums}
.nd a b{display:block;font-size:16px}.nd a span{display:block;font-size:13px;color:rgba(255,255,255,.62);margin-top:2px}
.nd a:hover{background:rgba(255,255,255,.12)}
.nd .ot{background:none;box-shadow:none;flex-direction:column;align-items:flex-start;justify-content:center;gap:6px;padding:10px 4px}
.nd .ot p{margin:0;font:600 11px "IBM Plex Mono",monospace;letter-spacing:.08em;color:rgba(255,255,255,.5)}
.nd .ot nav{display:flex;gap:18px}.nd .ot nav a{padding:0;background:none;box-shadow:none;font-size:15px;font-weight:600;gap:8px}
.nd .ot nav a svg{color:#e8b800}
.main{margin-top:26px;display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start}'''
    nd = ('<div class="nd"><a href="#"><span class="n">3</span><span><b>People need a look</b><span>Locked, not set up or waiting for a role</span></span></a>'
          '<a href="#"><span class="n">1</span><span><b>Deletion request</b><span>Waiting for your approval</span></span></a>'
          '<div class="ot"><p>SUITE MANAGEMENT</p><nav>' + ''.join(f'<a href="#">{mic(k, 16)}{n}</a>' for n, k, _ in SUITE_SYS[2:]) + '</nav></div></div>')
    body = (f'<div class="pg">{adm_band(line="Two things in Suite management need you today.", extra=nd)}'
            f'<main class="w main">{sys_card(FELICIDAD[0], 3)}{sys_card(FELICIDAD[1], 3)}</main></div>')
    return 'M5 · What needs you first: the two counts lead in the band, the rest of Suite management as links', css, body, 900


# ======================================================================== suite admin only (Leonora Castillo)
@reg
def R49SuiteHome():
    css = ADM_BAND + '''.band{height:300px}
.ov{position:absolute;right:0;top:120px;width:380px;border-radius:18px;padding:20px 22px;background:#e8b800;color:#0f1445;display:flex;flex-direction:column;gap:6px}
.ov b{font-size:22px;font-weight:800;display:flex;align-items:center;gap:10px}.ov span{font-size:14px;font-weight:500}
.main{margin-top:26px;display:grid;grid-template-columns:repeat(3,1fr);gap:24px;align-items:start}
.gp h2{margin:0 0 10px;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.1em;color:#5b6779}
.gp a{''' + CARD + ''';display:flex;flex-direction:column;justify-content:space-between;height:120px;padding:18px 20px;margin-bottom:14px}
.gp a .t{display:flex;align-items:center;gap:10px;font-size:18px;font-weight:700}.gp a svg{color:#3a4486}
.gp a em{font-style:normal;font-size:14px;font-weight:600;color:#8a6d00}.gp a em.q{color:#8a94a8;font-weight:500}'''
    ov = f'<a class="ov" href="#"><b>{mic("dash", 22)}Overview</b><span>The whole suite: people, roles and sign ins across BMS, VMMS and VRMS</span></a>'
    hints = {'Roles': 'Every system\'s roles', 'Activity': 'Sign ins and changes'}
    gps = ''.join(f'<section class="gp"><h2>{gn.upper()}</h2>' + ''.join(
        f'<a href="#"><span class="t">{mic(k, 20)}{n}</span><em class="{"" if c else "q"}">{c or hints.get(n, "&nbsp;")}</em></a>' for n, k, c in mods) + '</section>'
        for gn, mods in SUITE_ALL[1:])
    body = (f'<div class="pg">{adm_band(line="Suite admin. You manage people and access for every system.", extra=ov, name=LC)}'
            f'<main class="w main">{gps}</main></div>')
    return 'S1 · Suite admin, no systems: Overview leads, then Accounts, Access and Audit', css, body, 900


@reg
def R49SuiteLedger():
    css = '''.pg{background:#f7f7f4}
.bar{height:64px;background:#0f1445;color:#fff;position:relative}
.bar:after{content:"";position:absolute;left:0;right:0;bottom:-3px;height:3px;background:#e8b800}
.gr{padding:46px 0 30px}.gr .dt{color:#8a6d00}
h1{margin:12px 0 0;font-size:72px;line-height:.95;font-weight:800;letter-spacing:-.045em;color:#0f1445}
.gr p.s{margin:16px 0 0;font-size:16px;color:#5b6779}
.sec{border-top:2px solid #0f1445;padding:12px 0 18px;display:grid;grid-template-columns:200px 1fr}
.sec h2{margin:12px 0 0;font:600 13px "IBM Plex Mono",monospace;letter-spacing:.08em;color:#0f1445}
.gl{display:grid;grid-template-columns:repeat(3,1fr);column-gap:24px}
.gl a{display:flex;flex-direction:column;justify-content:center;height:70px}
.gl a b{font-size:26px;font-weight:700;letter-spacing:-.02em;color:#0f172a}
.gl a em{font-style:normal;font-size:13px;font-weight:600;color:#8a6d00;margin-top:2px}
.gl a:hover b{color:#1a1f6e;text-decoration:underline;text-decoration-color:#e8b800;text-decoration-thickness:3px;text-underline-offset:6px}'''
    secs = ''.join(f'<section class="sec"><h2>{gn.upper()}</h2><div class="gl">' + ''.join(
        f'<a href="#"><b>{n}</b>{f"<em>{c}</em>" if c else ""}</a>' for n, _, c in mods) + '</div></section>' for gn, mods in SUITE_ALL)
    body = (f'<div class="pg"><div class="bar"><div class="w">{top(LC["name"], LC["ini"])}</div></div>'
            f'<main class="w lt"><div class="gr"><p class="dt">{DATE}</p><h1>Suite management.</h1><p class="s">Good morning, Leonora. You run people and access for BMS, VMMS and VRMS.</p></div>{secs}</main></div>')
    return 'S2 · Suite admin as a ledger (pairs with G)', css, body, 900


@reg
def R49SuiteKeys():
    css = g.R49Keys()[1]
    rows = ''
    tagcls = {'Overview': 's0', 'Accounts': 's1', 'Access': 's2', 'Audit': 's1'}
    allg = [('Overview', SUITE_ALL[0][1] + SUITE_ALL[3][1]), SUITE_ALL[1], SUITE_ALL[2]]
    names = {0: ('Overview', 'and Activity'), 1: ('Accounts', 'People and admins'), 2: ('Access', 'Roles and passes')}
    for i, (gn, mods) in enumerate(allg):
        t, sub = names[i]
        cls = ['s0', 's1', 's2'][i]
        keys = ''.join(f'<a class="key {cls}" href="#"><span class="hook"></span><span class="ring"></span><span class="tag"><span>{n}</span>'
                       f'<em>{mic(k, 13)}{c or "SUITE-%02d" % (j + 1)}</em></span></a>' for j, (n, k, c) in enumerate(mods))
        rows += f'<div class="row"><div class="plate"><b>{t}</b><span>{sub}</span><i>{len(mods)} modules</i></div><div class="rail">{keys}</div></div>'
    body = (f'<div class="pg"><div class="band"><div class="w">{top(LC["name"], LC["ini"])}<div class="gr"><p class="dt">{DATE}</p>'
            f'<h1>Good morning, Leonora</h1></div></div></div><main class="w"><div class="cab">{rows}</div></main></div>')
    return 'S3 · Suite admin on the key cabinet (pairs with C)', css, body, 900

"""Round 51 (Nov 25, late night): the launcher as an app grid from the top left, under a navy navbar.

Two choices to mix: the grid (G1 to G5, all under navbar N2) and the navbar (N1 to N4, all over grid G1).
Only BMS, VMMS and VRMS are clickable (plus Suite management for an admin); no system content on the tiles.
python3 -I gen51.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from data49 import board, CORAZON, FELICIDAD, DATE, ic, I  # noqa: E402
from parts import LOGO, CHEV, V_VAN, V_L300, V_WING  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}


def reg(fn):
    BOARDS[fn.__name__] = fn
    return fn


NAVY, DEEP, GOLD = '#0f1445', '#0a0d33', '#e8b800'

# ---------------------------------------------------------------- app icons (64 box), one drawn glyph per system
WRENCH = ('<path transform="translate(9.5 9.5) scale(1.9)" d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77'
          'a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" '
          'fill="none" stroke="{fg}" stroke-width="2" stroke-linejoin="round"/>')


def glyph(code, fg, ac, hole):
    if code == 'BMS':  # a booking ticket with a trip drawn on it
        return (f'<path d="M12 19h40a3 3 0 0 1 3 3v6a4 4 0 0 0 0 8v6a3 3 0 0 1-3 3H12a3 3 0 0 1-3-3v-6a4 4 0 0 0 0-8v-6a3 3 0 0 1 3-3z" fill="{fg}"/>'
                f'<path d="M21 37c7 0 8-10 21-10" fill="none" stroke="{ac}" stroke-width="3" stroke-linecap="round" stroke-dasharray="1 5"/>'
                f'<circle cx="20" cy="37" r="4" fill="{hole}"/><circle cx="44" cy="27" r="4.5" fill="{ac}"/>')
    if code == 'VMMS':  # an upkeep gauge
        return (f'<path d="M13 43a19 19 0 0 1 38 0" fill="none" stroke="{fg}" stroke-width="5.5" stroke-linecap="round"/>'
                f'<path d="M44.4 29.6A19 19 0 0 1 51 43" fill="none" stroke="{ac}" stroke-width="5.5" stroke-linecap="round"/>'
                f'<path d="M32 43 41 30" stroke="{ac}" stroke-width="3.5" stroke-linecap="round"/>'
                f'<circle cx="32" cy="43" r="5" fill="{fg}"/><circle cx="32" cy="43" r="2" fill="{hole}"/>'
                f'<path d="M24 52h16" stroke="{fg}" stroke-width="3.5" stroke-linecap="round" opacity=".45"/>')
    if code == 'VRMS':  # a wrench and a nut
        return (WRENCH.format(fg=fg) +
                f'<path d="M46 39.5l6 3.5v7l-6 3.5-6-3.5v-7z" fill="{ac}"/><circle cx="46" cy="46.5" r="2.4" fill="{hole}"/>')
    # Suite management: a shield with people access check
    return (f'<path d="M32 11c5 4 11 6 17 6v13c0 11-7 18-17 22-10-4-17-11-17-22V17c6 0 12-2 17-6z" fill="{fg}"/>'
            f'<path d="m24 32 6 6 11-12" fill="none" stroke="{ac}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')


def app_icon(code, size=56, scheme='navy', cls='ai'):
    if scheme == 'own':  # each system its own colour way, like real app icons
        scheme = {'BMS': 'gold', 'VMMS': 'white', 'VRMS': 'navy', 'Suite': 'deep'}[code]
    bg, fg, ac, hole, ring = {
        'navy': (f'url(#ai-n)', '#fff', GOLD, NAVY, 'none'),
        'gold': (GOLD, NAVY, '#fff', GOLD, 'none'),
        'white': ('#fff', NAVY, GOLD, '#fff', '#d9deea'),
        'deep': (DEEP, '#fff', GOLD, DEEP, GOLD),
        'grey': ('#e7eaf1', '#aeb6c6', '#c7cdd9', '#e7eaf1', 'none'),
        'bare': (None, NAVY, GOLD, '#fff', 'none'),
        'bareDark': (None, '#fff', GOLD, NAVY, 'none'),
    }[scheme]
    stroke = f' stroke="{ring}" stroke-width="1.5"' if ring != 'none' else ''
    return (f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 64 64" aria-hidden="true">'
            f'<defs><linearGradient id="ai-n" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1d2775"/><stop offset="1" stop-color="{NAVY}"/></linearGradient></defs>'
            + (f'<rect x=".75" y=".75" width="62.5" height="62.5" rx="17"{stroke} fill="{bg}"/>' if bg else '') + f'{glyph(code, fg, ac, hole)}</svg>')


# ---------------------------------------------------------------- shared css: tiles grid under every navbar
CSS = '''.pg{background:#f3f5f9;height:900px}
.w{width:1200px;margin:0 auto;position:relative}
.row{height:64px;display:flex;align-items:center;gap:16px}
.lk{display:flex;align-items:center;gap:10px;white-space:nowrap}.lk svg{height:20px;fill:#e8b800}.lk b{font-weight:800;font-style:italic;font-size:16px}
.lk em{font-style:normal;font-size:14px;font-weight:500;color:rgba(255,255,255,.62);padding-left:12px;margin-left:2px;border-left:1px solid rgba(255,255,255,.18)}
.sp{flex:1}
.hb{width:40px;height:40px;border-radius:12px;border:0;background:none;color:rgba(255,255,255,.7);display:grid;place-items:center;cursor:pointer}
.hb:hover{background:rgba(255,255,255,.08);color:#fff}
.me{display:flex;align-items:center;gap:10px;height:44px;padding:0 10px 0 6px;border-radius:12px;border:0;background:none;color:#fff;font:500 14px Inter,sans-serif;cursor:pointer}
.me:hover{background:rgba(255,255,255,.08)}
.av{width:32px;height:32px;border-radius:50%;background:#e8b800;color:#0f1445;display:grid;place-items:center;font-size:12px;font-weight:700}
.nd{font:600 12px "IBM Plex Mono",monospace;letter-spacing:.05em;color:rgba(255,255,255,.55);white-space:nowrap}
.hd{display:flex;align-items:baseline;gap:12px;margin:0 0 16px}
.hd h2{margin:0;font-size:15px;font-weight:700;letter-spacing:-.005em;color:#0f172a}
.hd span{font:600 12px "IBM Plex Mono",monospace;color:#7a8597}
.hd p{margin:0 0 0 auto;font-size:13px;color:#7a8597}
.foot{position:absolute;left:0;right:0;bottom:22px;font-size:13px;color:#7a8597}
.foot .w{display:flex;gap:24px}.foot .w span:first-child{margin-right:auto}
/* G1 tiles */
.tiles{display:grid;grid-template-columns:repeat(4,282px);gap:24px}
.tl{position:relative;height:272px;padding:22px 22px 20px;border-radius:20px;background:#fff;display:flex;flex-direction:column;
box-shadow:0 0 0 1px #e3e7ef,0 1px 2px rgba(15,23,42,.04);transition:transform .2s cubic-bezier(.2,.8,.2,1),box-shadow .2s}
.tl:hover{transform:translateY(-3px);box-shadow:0 0 0 1px #d5dbe7,0 14px 30px rgba(15,23,42,.10)}
.tl:focus-visible{outline:3px solid #e8b800;outline-offset:3px}
.tl .ai{flex:none}
.tl b{margin-top:18px;font-size:26px;line-height:1;font-weight:800;letter-spacing:-.03em;color:#0f1445}
.tl .nm{margin-top:8px;font-size:14px;font-weight:600;line-height:1.35;color:#0f172a}
.tl .ln{margin-top:4px;font-size:13px;line-height:1.45;color:#5b6779}
.tl .rl{margin-top:auto;padding-top:12px;font-size:13px;color:#5b6779}.tl .rl strong{color:#0f172a;font-weight:600}
.ghost{height:272px;border-radius:20px;border:1.5px dashed #cfd5e1;padding:22px;display:flex;flex-direction:column;justify-content:flex-end;color:#7a8597;font-size:13px;line-height:1.5}
.ghost strong{color:#3c4759;font-weight:600;font-size:14px}
'''

SUN = ic('<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01"/>', 20, 2)


def nav_row(name='Corazon Villareal', ini='CV', date=False, extra=''):
    d = f'<span class="nd">{DATE.upper()}</span>' if date else ''
    return (f'<div class="row"><div class="lk">{LOGO}<b>WeLinc Logistics</b><em>Operations Workspace</em></div>{extra}<span class="sp"></span>{d}'
            f'<button class="hb" type="button" aria-label="Help">{SUN}</button>'
            f'<button class="me" type="button"><span class="av" aria-hidden="true">{ini}</span>{name}{CHEV}</button></div>')


def tile(s, scheme='navy', cls='tl'):
    return (f'<a class="{cls}" href="#">{app_icon(s["code"], 52, scheme)}<b>{s["code"]}</b><span class="nm">{s["name"]}</span>'
            f'<span class="ln">{s["line"]}</span><span class="rl">Your role: <strong>{s["role"]}</strong></span></a>')


def foot(left='WeLinc Logistics · Since 2018'):
    return (f'<div class="foot"><div class="w"><span>{left}</span><span>Last sign in: Tuesday, Nov 24, 6:12 PM · Chrome on Windows</span>'
            f'<span>Help: IT desk, local 214</span></div></div>')


def van(cls, kind='van'):
    vb = {'van': '-8 -2 138 56', 'l300': '-6 -2 96 50', 'wing': '-8 -2 172 64'}[kind]
    return f'<svg class="{cls}" viewBox="{vb}" aria-hidden="true"><use href="#{kind}"/></svg>'


SYMS = f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{V_VAN}{V_L300}{V_WING}</defs></svg>'


# ================================================================ navbars
def N1(greet_in_page=True):
    """Road rail: a 64px bar, then a 30px road where the van and the L300 drive."""
    css = '''.n1{background:#0f1445;color:#fff;position:relative}
.n1 .rail{position:relative;height:30px;background:#0a0d33;overflow:hidden;box-shadow:inset 0 1px 0 rgba(255,255,255,.06)}
.n1 .rail i{position:absolute;left:0;right:0;top:27px;height:2px;background:repeating-linear-gradient(90deg,rgba(232,184,0,.55) 0 18px,transparent 18px 40px)}
.n1 .v{position:absolute;bottom:4px;left:0;animation:n1 34s linear infinite}
.n1 .va{height:24px;animation-delay:-4s}.n1 .vb{height:21px;animation-delay:-19s}
@keyframes n1{from{transform:translateX(-90px)}to{transform:translateX(1530px)}}
.pt{padding-top:34px}
.pt h1{margin:0;font-size:34px;line-height:1.1;font-weight:800;letter-spacing:-.03em;color:#0f1445}
.pt>p{margin:6px 0 0;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.05em;color:#7a8597}
.pt .hd{margin-top:30px}'''
    html = (f'<header class="n1"><div class="w">{nav_row()}</div><div class="rail"><i></i>{van("v va")}{van("v vb", "l300")}</div></header>'
            f'<div class="w pt"><p>{DATE.upper()}</p><h1>Good morning, Corazon</h1>')
    return css, html, '</div>'


def N2():
    """Compact hero: today's navy band cut to 216px, the greeting beside the road with the van and the L300."""
    css = '''.n2{position:relative;height:216px;background:#0f1445;color:#fff;overflow:hidden}
.n2 .gr{padding-top:22px}
.n2 .dt{margin:0;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.06em;color:#e8b800}
.n2 h1{margin:8px 0 0;font-size:36px;line-height:1.05;font-weight:800;letter-spacing:-.03em}
.n2 .l{margin:8px 0 0;font-size:15px;color:rgba(255,255,255,.66)}
.n2 .road{position:absolute;right:0;bottom:0;width:760px;height:86px;-webkit-mask-image:linear-gradient(90deg,transparent,#000 22%);mask-image:linear-gradient(90deg,transparent,#000 22%)}
.n2 .road b{position:absolute;left:0;right:0;bottom:0;height:22px;background:#0a0d33;box-shadow:inset 0 1px 0 rgba(255,255,255,.08)}
.n2 .road i{position:absolute;left:0;right:0;bottom:10px;height:2px;background:repeating-linear-gradient(90deg,rgba(203,210,234,.35) 0 26px,transparent 26px 60px)}
.n2 .road u{position:absolute;bottom:22px;height:1px;left:0;right:0;background:rgba(255,255,255,.12)}
.n2 .lamp{position:absolute;bottom:22px;width:2px;height:58px;background:rgba(255,255,255,.16)}
.n2 .lamp:after{content:"";position:absolute;top:0;left:0;width:14px;height:2px;background:rgba(255,255,255,.16)}
.n2 .lamp:before{content:"";position:absolute;top:2px;left:10px;width:5px;height:3px;border-radius:0 0 3px 3px;background:#e8b800;box-shadow:0 0 14px 4px rgba(232,184,0,.25)}
.n2 .v{position:absolute;left:0;animation:n2 22s linear infinite}
.n2 .va{bottom:6px;height:54px;animation-delay:-3s}.n2 .vb{bottom:6px;height:42px;animation-delay:-14s}
@keyframes n2{from{transform:translateX(-150px)}to{transform:translateX(800px)}}
.below{padding-top:30px}'''
    lamps = ''.join(f'<span class="lamp" style="left:{x}px"></span>' for x in (250, 470, 690))
    html = (f'<header class="n2"><div class="w">{nav_row()}<div class="gr"><p class="dt">{DATE.upper()}</p><h1>Good morning, Corazon</h1>'
            f'<p class="l">Three systems, one sign in. Pick one to start.</p></div></div>'
            f'<div class="road">{lamps}<u></u><b></b><i></i>{van("v va")}{van("v vb", "l300")}</div></header>'
            f'<div class="w below">')
    return css, html, '</div>'


def depot_svg():
    """Three garages in outline (Marikina, Sta. Rosa, Pulilan); a van leaves each in turn, always outbound."""
    g = ''
    for i, (x, name) in enumerate([(30, 'MARIKINA'), (210, 'STA. ROSA'), (390, 'PULILAN')]):
        g += (f'<g transform="translate({x} 0)"><path d="M0 108V58l60-22 60 22v50" fill="#141a55" stroke="rgba(255,255,255,.22)"/>'
              f'<rect x="26" y="66" width="68" height="42" fill="#080b2e"/>'
              f'<g stroke="#1d2470" stroke-width="2"><path d="M26 70h68M26 76h68M26 82h68"/></g>'
              f'<rect class="door d{i}" x="26" y="84" width="68" height="24" fill="#e8b800" opacity=".12"/>'
              f'<text x="60" y="54" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="9.5" font-weight="600" letter-spacing=".08em" fill="rgba(255,255,255,.55)">{name}</text></g>')
    vans = ''.join(f'<use class="dv dv{i}" href="#van" x="{x}" y="86" width="58" height="24"/>' for i, x in enumerate((60, 240, 420)))
    return (f'<svg class="dep" viewBox="0 0 680 136" aria-hidden="true">{g}'
            f'<rect x="0" y="108" width="680" height="28" fill="#0a0d33"/>'
            f'<path d="M0 123H680" stroke="rgba(232,184,0,.45)" stroke-width="2" stroke-dasharray="14 18"/>{vans}</svg>')


def N3():
    """Depot skyline: a 136px band, the greeting on the left, the three garages drawn on the right."""
    css = '''.n3{position:relative;height:172px;background:#0f1445;color:#fff;overflow:hidden}
.n3 .dep{position:absolute;right:calc(50% - 600px);bottom:0;width:680px;height:136px}
.n3 .row{position:relative;z-index:2}
.n3 .gr{position:relative;z-index:2;display:flex;flex-direction:column;gap:6px;padding-top:22px}
.n3 h1{margin:0;font-size:30px;font-weight:800;letter-spacing:-.025em}
.n3 .dt{font:600 12px "IBM Plex Mono",monospace;letter-spacing:.06em;color:#e8b800}
.n3 .row .me,.n3 .row .hb{position:relative;z-index:3}
.n3 .row{width:auto}
.n3 .dep{z-index:1}
.n3 .rd{position:absolute;left:0;right:0;bottom:0;height:28px;background:#0a0d33}.n3 .rd:after{content:"";position:absolute;left:0;right:0;top:14px;height:2px;background:repeating-linear-gradient(90deg,rgba(232,184,0,.45) 0 14px,transparent 14px 32px)}
.dv{opacity:0;animation:out 15s linear infinite}
.dv1{animation-delay:5s}.dv2{animation-delay:10s}
@keyframes out{0%{opacity:0;transform:translateX(0)}4%{opacity:1}30%{opacity:1}36%{opacity:0;transform:translateX(300px)}100%{opacity:0;transform:translateX(300px)}}
.door{animation:door 15s linear infinite}.d1{animation-delay:5s}.d2{animation-delay:10s}
@keyframes door{0%,30%{opacity:.34}40%,100%{opacity:.12}}
.below{padding-top:34px}'''
    html = (f'<header class="n3"><span class="rd"></span>{depot_svg()}<div class="w">{nav_row()}<div class="gr"><h1>Good morning, Corazon</h1>'
            f'<span class="dt">{DATE.upper()}</span></div></div></header><div class="w below">')
    return css, html, '</div>'


def N4():
    """Floating bar: a navy bar that sits inside the light page, a gold route along its foot with a top down van."""
    css = '''.n4{position:relative;margin:20px auto 0;width:1200px;height:92px;border-radius:22px;background:#0f1445;color:#fff;
box-shadow:0 18px 40px -18px rgba(15,20,69,.55);overflow:hidden}
.n4 .row{height:72px;padding:0 14px 0 22px}
.n4 .rt{position:absolute;left:0;right:0;bottom:0;height:20px;background:#0a0d33}.n4 .rt:after{content:"";position:absolute;left:0;right:0;top:12px;height:2px;background:repeating-linear-gradient(90deg,rgba(232,184,0,.5) 0 10px,transparent 10px 20px)}
.n4 .tv{position:absolute;bottom:5px;left:0;height:17px;animation:n4 24s linear infinite}
@keyframes n4{from{transform:translateX(-50px)}to{transform:translateX(1210px)}}
.n4 .tv rect{shape-rendering:geometricPrecision}
.pt{padding-top:40px}
.pt h1{margin:0;font-size:40px;line-height:1.05;font-weight:800;letter-spacing:-.035em;color:#0f1445}
.pt>p{margin:8px 0 0;font-size:15px;color:#5b6779}.pt>p span{font:600 12px "IBM Plex Mono",monospace;letter-spacing:.05em;color:#7a8597;margin-right:10px}
.pt .hd{margin-top:30px}'''
    tv = van('tv', 'l300')
    html = (f'<header class="n4">{nav_row()}<span class="rt"></span>{tv}</header>'
            f'<div class="w pt"><h1>Good morning, Corazon</h1><p><span>{DATE.upper()}</span>Three systems, one sign in.</p>')
    return css, html, '</div>'


# ================================================================ grids
def G1(people=CORAZON):
    hd = '<div class="hd"><h2>Your systems</h2><span>3</span><p>Open one to start. You stay signed in to all three.</p></div>'
    return '', hd + '<div class="tiles">' + ''.join(tile(s) for s in people) + '</div>'


def G2():
    css = '''.cards{display:grid;grid-template-columns:repeat(3,384px);gap:24px}
.ac{display:grid;grid-template-columns:64px 1fr;column-gap:18px;align-items:start;padding:22px 24px;border-radius:18px;background:#fff;
box-shadow:0 0 0 1px #e3e7ef;transition:box-shadow .2s,transform .2s}
.ac:hover{box-shadow:0 0 0 1.5px #0f1445,0 12px 26px rgba(15,23,42,.08)}
.ac .ai{grid-row:span 3}
.ac .t{display:flex;align-items:baseline;gap:10px}.ac b{font-size:20px;font-weight:800;letter-spacing:-.02em;color:#0f1445}
.ac .t span{font-size:13px;color:#5b6779}
.ac .nm{margin-top:4px;font-size:14px;font-weight:600;color:#0f172a}
.ac .ln{margin-top:2px;font-size:13px;color:#5b6779;line-height:1.45}
.acc{margin-top:36px;display:flex;align-items:center;gap:14px;padding:16px 20px;border-radius:16px;background:#e9ecf3;font-size:13.5px;color:#3c4759}
.acc strong{color:#0f172a}'''
    cards = ''.join(f'<a class="ac" href="#">{app_icon(s["code"], 64)}<span class="t"><b>{s["code"]}</b><span>{s["role"]}</span></span>'
                    f'<span class="nm">{s["name"]}</span><span class="ln">{s["line"]}</span></a>' for s in CORAZON)
    html = ('<div class="hd"><h2>App launcher</h2><span>3 systems</span></div>'
            f'<div class="cards">{cards}</div>'
            f'<div class="acc">{ic(I["key"], 18, 2)}<span>Need a system that is not here? <strong>Ask its admin</strong> to give you a role, then sign in again.</span></div>')
    return css, html


def G3():
    css = '''.panel{border-radius:24px;background:#fff;box-shadow:0 0 0 1px #e3e7ef;padding:30px 34px 34px}
.panel .hd{margin-bottom:26px}
.icons{display:grid;grid-template-columns:repeat(5,200px);gap:8px}
.ic{display:flex;flex-direction:column;align-items:flex-start;padding:16px;border-radius:18px;transition:background .2s}
.ic:hover{background:#f3f5f9}.ic:hover .ai{transform:translateY(-3px)}
.ic .ai{transition:transform .25s cubic-bezier(.2,.8,.2,1);filter:drop-shadow(0 8px 14px rgba(15,20,69,.16))}
.ic b{margin-top:16px;font-size:18px;font-weight:800;letter-spacing:-.02em;color:#0f1445}
.ic .nm{margin-top:4px;font-size:13px;line-height:1.4;color:#5b6779}
.ic .rl{margin-top:10px;font:600 11px "IBM Plex Mono",monospace;letter-spacing:.06em;color:#7a8597;text-transform:uppercase}'''
    icons = ''.join(f'<a class="ic" href="#">{app_icon(s["code"], 96, "own")}<b>{s["code"]}</b><span class="nm">{s["name"]}</span>'
                    f'<span class="rl">{s["role"]}</span></a>' for s in CORAZON)
    html = (f'<div class="panel"><div class="hd"><h2>Apps</h2><span>3</span><p>Point at one for its name, click to open.</p></div>'
            f'<div class="icons">{icons}</div></div>')
    return css, html


def scene(code):
    """Line drawn scene for an illustrated module card (380 x 168)."""
    ground = '<rect x="0" y="140" width="380" height="28" fill="#e4e8f1"/><path d="M0 154H380" stroke="#fff" stroke-width="2" stroke-dasharray="16 14"/>'
    if code == 'BMS':  # a wing van at the dock, its trip dotted behind it
        return (f'<path d="M20 70c50-36 120 10 170-14s110-26 170 0" fill="none" stroke="#c3cad8" stroke-width="2" stroke-dasharray="2 6" stroke-linecap="round"/>'
                f'<circle cx="20" cy="70" r="6" fill="#0f1445"/><path d="M360 44a10 10 0 0 0-10 10c0 8 10 16 10 16s10-8 10-16a10 10 0 0 0-10-10z" fill="#e8b800"/>'
                f'<rect x="232" y="88" width="120" height="52" fill="#fff" stroke="#c9d0de"/><path d="M232 100h120M232 112h120M232 124h120" stroke="#e4e8f1"/>'
                f'{ground}<use href="#wing" x="40" y="88" width="180" height="67"/>')
    if code == 'VMMS':  # the L300 at its service check, a due list on a board
        return (f'<rect x="248" y="34" width="92" height="106" rx="6" fill="#fff" stroke="#c9d0de"/>'
                f'<g stroke="#c3cad8" stroke-width="3" stroke-linecap="round"><path d="M278 62h46M278 84h46M278 106h34"/></g>'
                f'<g fill="none" stroke="#0f1445" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="m260 62 4 4 7-8M260 84l4 4 7-8"/></g>'
                f'<rect x="258" y="100" width="12" height="12" rx="3" fill="none" stroke="#e8b800" stroke-width="2.4"/>'
                f'{ground}<use href="#l300" x="48" y="82" width="160" height="83"/>')
    return (f'<rect x="60" y="64" width="12" height="76" fill="#c3cad8"/><rect x="300" y="64" width="12" height="76" fill="#c3cad8"/>'
            f'<rect x="54" y="112" width="264" height="8" rx="2" fill="#0f1445"/>'
            f'{ground}<use href="#van" x="88" y="54" width="196" height="80"/>'
            f'<g transform="translate(320 18) scale(1.6)">{WRENCH.format(fg="#0f1445").replace("translate(9.5 9.5) scale(1.9)", "")}</g>')


def G4():
    css = '''.mods{display:grid;grid-template-columns:repeat(3,384px);gap:24px}
.md{display:flex;flex-direction:column;border-radius:20px;background:#fff;overflow:hidden;box-shadow:0 0 0 1px #e3e7ef;transition:transform .2s,box-shadow .2s}
.md:hover{transform:translateY(-3px);box-shadow:0 0 0 1px #d5dbe7,0 16px 34px rgba(15,23,42,.1)}
.md .art{height:168px;background:#f3f5f9;position:relative}
.md .art svg{position:absolute;inset:0;width:100%;height:100%}
.md .tx{padding:18px 22px 20px;display:grid;grid-template-columns:1fr auto;column-gap:12px}
.md b{font-size:22px;font-weight:800;letter-spacing:-.025em;color:#0f1445}
.md .rl{align-self:center;font-size:13px;color:#5b6779}
.md .nm{grid-column:1/-1;margin-top:6px;font-size:14px;font-weight:600;color:#0f172a}
.md .ln{grid-column:1/-1;margin-top:3px;font-size:13px;color:#5b6779}'''
    mods = ''.join(f'<a class="md" href="#"><span class="art"><svg viewBox="0 0 380 168" preserveAspectRatio="xMidYMax meet" aria-hidden="true">{scene(s["code"])}</svg></span>'
                   f'<span class="tx"><b>{s["code"]}</b><span class="rl">{s["role"]}</span><span class="nm">{s["name"]}</span>'
                   f'<span class="ln">{s["line"]}</span></span></a>' for s in CORAZON)
    return css, '<div class="hd"><h2>Your systems</h2><span>3</span></div>' + f'<div class="mods">{mods}</div>'


def G5():
    """Felicidad Roxas, VMMS and VRMS Admin: her two systems, BMS greyed (no role), Suite management in its own group."""
    css = '''.grp{display:grid;grid-template-columns:repeat(4,282px);gap:24px}
.gl{font:600 11px "IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase;color:#7a8597;margin:0 0 -10px}
.gl.su{grid-column:4}
.tl.off{background:#eef1f6;box-shadow:none;cursor:default}.tl.off:hover{transform:none;box-shadow:none}
.tl.off b,.tl.off .nm{color:#8b94a6}.tl.off .ln{color:#99a2b3}
.tl.su{background:#0f1445;box-shadow:0 14px 30px -12px rgba(15,20,69,.5)}
.tl.su b,.tl.su .nm{color:#fff}.tl.su .ln{color:rgba(255,255,255,.66)}.tl.su .rl{color:rgba(255,255,255,.66)}.tl.su .rl strong{color:#e8b800}'''
    bms = CORAZON[0]
    off = (f'<div class="tl off">{app_icon("BMS", 52, "grey")}<b>BMS</b><span class="nm">{bms["name"]}</span>'
           f'<span class="ln">{bms["line"]}</span><span class="rl">No role yet. Ask a BMS admin.</span></div>')
    su = (f'<a class="tl su" href="#">{app_icon("Suite", 52, "deep")}<b>Suite</b><span class="nm">Suite management</span>'
          f'<span class="ln">People, roles and access for VMMS and VRMS</span><span class="rl"><strong>4 to review</strong></span></a>')
    html = ('<div class="hd"><h2>Your systems</h2><span>2 of 3</span><p>Systems are always in the same order: BMS, VMMS, VRMS.</p></div>'
            '<div class="grp"><p class="gl" style="grid-column:1/4">Systems</p><p class="gl su">Admin</p>'
            f'{off}{"".join(tile(s) for s in FELICIDAD)}{su}</div>')
    return css, html


def compose(nav, grid, title, name='Corazon Villareal', ini='CV'):
    ncss, nopen, nclose = nav()
    gcss, ghtml = grid
    nopen = nopen.replace('Corazon Villareal', name).replace('>CV<', f'>{ini}<')
    if name != 'Corazon Villareal':
        nopen = nopen.replace('Good morning, Corazon', 'Good morning, Felicidad').replace('Three systems, one sign in. Pick one to start.', 'Your systems and Suite management, one sign in.')
    body = f'<div class="pg">{SYMS}{nopen}{ghtml}{nclose}{foot()}</div>'
    return title, CSS + ncss + gcss, body


@reg
def R51G1Tiles():
    return compose(N2, G1(), 'G1 · Tiles from the top left (four to a row, like a launchpad); navbar N2')


@reg
def R51G2Cards():
    return compose(N2, G2(), 'G2 · App launcher cards: icon on the left, name and role beside it; navbar N2')


@reg
def R51G3Icons():
    return compose(N2, G3(), 'G3 · Big app icons in one panel, each system its own colour way; navbar N2')


@reg
def R51G4Scenes():
    return compose(N2, G4(), 'G4 · Module cards with a drawn scene (wing van, L300, van on the lift); navbar N2')


@reg
def R51G5Admin():
    return compose(N2, G5(), 'G5 · Admin (Felicidad Roxas): BMS greyed, Suite management as its own tile in the fourth slot; navbar N2',
                   name='Felicidad Roxas', ini='FR')


@reg
def R51N1Rail():
    return compose(N1, G1(), 'N1 · Navbar: a 64px bar over a 30px road rail with the van and L300; the greeting moves onto the page')


@reg
def R51N3Depot():
    return compose(N3, G1(), 'N3 · Navbar: 136px, the three garages drawn on the right, a van leaves each in turn')


@reg
def R51N4Float():
    return compose(N4, G1(), 'N4 · Navbar: a floating navy bar inside the page, a gold route with a top down van along its foot')


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

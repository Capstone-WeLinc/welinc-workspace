"""Round 49 (Nov 25, night): launchers as module pickers, Suite management placements.
python3 -I gen49.py <project dir> [Board,Board]"""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from data49 import *  # noqa: F401,F403
from data49 import I, ic, top, board, CORAZON, FELICIDAD, SUITE_SYS, SUITE_ALL, DATE, LOGO, LOGO_POLY, V_VAN, V_L300, V_WING, VAN_TOP  # noqa

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}


def reg(fn):
    BOARDS[fn.__name__] = fn
    return fn


def mic(key, s=18, cls=''):
    return ic(I[key], s, cls=cls)


CHR = ic(I['right'], 16, 2.2, 'chr')


# ======================================================================== A. Road band, module columns
@reg
def R49Road():
    css = '''.band{height:356px}
.gr{padding-top:30px}
h1{margin:10px 0 0;font-size:52px;line-height:1;font-weight:800;letter-spacing:-.03em}
.l{margin:12px 0 0;font-size:16px;color:rgba(255,255,255,.68)}
.road{position:absolute;left:0;right:0;bottom:0;height:84px;background:#0a0d33;box-shadow:inset 0 1px 0 rgba(255,255,255,.08)}
.road i{position:absolute;left:0;right:0;top:44px;height:3px;background:repeating-linear-gradient(90deg,rgba(203,210,234,.32) 0 44px,transparent 44px 104px)}
.road b{position:absolute;left:0;right:0;top:0;height:6px;background:#141a55}
.veh{position:absolute;bottom:14px;left:0;animation:drive 30s linear infinite}
.veh.v1{width:190px;animation-delay:-5s}.veh.v2{width:128px;bottom:13px;animation-delay:-19s}
@keyframes drive{from{transform:translateX(-240px)}to{transform:translateX(1700px)}}
.main{margin-top:28px}
.cols{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}
.card{background:#fff;border-radius:20px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 24px rgba(15,23,42,.06);padding:22px 12px 12px}
.hd{padding:0 12px;display:flex;align-items:baseline;gap:10px}
.code{font-size:24px;font-weight:800;letter-spacing:-.01em;color:#0f1445}
.role{margin-left:auto;font-size:13px;font-weight:500;color:#5b6779}
.nm{padding:0 12px;margin-top:4px;font-size:13px;color:#5b6779}
.ls{list-style:none;margin:16px 0 0;padding:8px 0 0;border-top:1px solid #eef1f6}
.m{display:flex;align-items:center;gap:12px;height:46px;padding:0 12px;border-radius:12px;font-size:15px;font-weight:500}
.m svg{color:#3a4486;flex:none}.m .chr{margin-left:auto;opacity:0;transition:opacity .15s,transform .15s;color:#0f1445}
.m:hover{background:#f3f5f9}.m:hover .chr{opacity:1;transform:translateX(2px)}'''
    cols = ''.join(
        f'<section class="card"><div class="hd"><span class="code">{s["code"]}</span><span class="role">{s["role"]}</span></div>'
        f'<div class="nm">{s["name"]}</div><ul class="ls">'
        + ''.join(f'<li><a class="m" href="#">{mic(k)}{n}{CHR}</a></li>' for n, k in s['mods']) + '</ul></section>'
        for s in CORAZON)
    body = (f'<div class="pg"><div class="band"><div class="w">{top()}<div class="gr"><p class="dt">{DATE}</p>'
            f'<h1>Good morning, Corazon</h1><p class="l">Pick a module to start. Each system opens where you choose.</p></div></div>'
            f'<div class="road"><b></b><i></i>'
            f'<svg class="veh v1" viewBox="-8 -2 138 56"><defs>{V_VAN}</defs><use href="#van"/></svg>'
            f'<svg class="veh v2" viewBox="-6 -2 96 50"><defs>{V_L300}</defs><use href="#l300"/></svg></div></div>'
            f'<main class="w main"><div class="cols">{cols}</div></main></div>')
    return 'A · Road band, a module column per system', css, body, 900


# ======================================================================== B. Tabs, the van drives to the system
@reg
def R49Tabs():
    css = '''.rd{position:absolute;opacity:0;pointer-events:none}
.band{height:388px}
.gr{padding-top:22px;display:flex;align-items:baseline;gap:18px}
h1{margin:0;font-size:34px;font-weight:800;letter-spacing:-.02em}
.gr .dt{order:2;margin-left:auto}
.tabs{position:absolute;left:0;right:0;top:150px;display:grid;grid-template-columns:repeat(3,1fr)}
.tab{display:block;padding:18px 0 0;cursor:pointer;opacity:.42;transition:opacity .3s}
.tab:hover{opacity:.7}
.tab .c{display:block;font-size:64px;line-height:1;font-weight:800;letter-spacing:-.035em}
.tab .r{display:block;margin-top:12px;font-size:14px;color:rgba(255,255,255,.75)}
.tab .r b{color:#fff;font-weight:600}
.track{position:absolute;left:0;right:0;bottom:44px;height:2px;background:rgba(255,255,255,.14)}
.track:before{content:"";position:absolute;left:0;top:-5px;width:100%;height:12px;background:repeating-linear-gradient(90deg,rgba(255,255,255,.18) 0 2px,transparent 2px 100px)}
.van{position:absolute;bottom:46px;width:120px;left:0}
.van svg{display:block;width:120px}
#b1:checked~.band .t1,#b2:checked~.band .t2,#b3:checked~.band .t3{opacity:1}
#b1:checked~.band .van{left:0;animation:in1 1s cubic-bezier(.3,.7,.3,1) both}
#b2:checked~.band .van{left:400px;animation:in2 1.1s cubic-bezier(.3,.7,.3,1) both}
#b3:checked~.band .van{left:800px;animation:in3 1.2s cubic-bezier(.3,.7,.3,1) both}
@keyframes in1{from{left:-160px}}@keyframes in2{from{left:-160px}}@keyframes in3{from{left:-160px}}
.main{margin-top:32px}
.pn{display:none;grid-template-columns:repeat(3,1fr);gap:18px}
#b1:checked~.main .p1,#b2:checked~.main .p2,#b3:checked~.main .p3{display:grid}
.pn a{position:relative;height:150px;border-radius:18px;background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 22px rgba(15,23,42,.05);padding:20px 22px;display:flex;flex-direction:column;justify-content:space-between;transition:transform .2s,box-shadow .2s}
.pn a svg{color:#3a4486}
.pn a span{font-size:19px;font-weight:700;letter-spacing:-.01em}
.pn a .chr{position:absolute;right:20px;top:22px;color:#94a0b4}
.pn a:hover{transform:translateY(-2px);box-shadow:0 2px 4px rgba(15,23,42,.06),0 14px 30px rgba(15,23,42,.09)}
.pn a:hover .chr{color:#0f1445}'''
    radios = ''.join(f'<input class="rd" type="radio" name="t" id="b{i+1}"{" checked" if i == 1 else ""} aria-label="{s["code"]}">' for i, s in enumerate(CORAZON))
    tabs = ''.join(f'<label class="tab t{i+1}" for="b{i+1}"><span class="c">{s["code"]}</span><span class="r"><b>{s["role"]}</b> · {s["name"]}</span></label>'
                   for i, s in enumerate(CORAZON))
    pns = ''.join(f'<div class="pn p{i+1}">' + ''.join(f'<a href="#">{mic(k, 22)}<span>{n}</span>{CHR}</a>' for n, k in s['mods']) + '</div>'
                  for i, s in enumerate(CORAZON))
    body = (f'<div class="pg">{radios}<div class="band"><div class="w" style="height:100%">{top()}<div class="gr"><h1>Good morning, Corazon</h1><p class="dt">{DATE}</p></div>'
            f'<div class="tabs">{tabs}</div><div class="track"></div>'
            f'<div class="van"><svg viewBox="-6 -2 96 50"><defs>{V_L300}</defs><use href="#l300"/></svg></div></div></div>'
            f'<main class="w main">{pns}</main></div>')
    return 'B · Tabs: the van drives to the system you pick (click BMS, VMMS, VRMS)', css, body, 900


# ======================================================================== C. Key cabinet
@reg
def R49Keys():
    css = '''.band{height:214px}
.gr{padding-top:26px}
h1{margin:10px 0 0;font-size:44px;line-height:1;font-weight:800;letter-spacing:-.03em}
.cab{margin-top:-34px;position:relative;z-index:2;border-radius:22px;padding:26px 28px 10px;
background:radial-gradient(circle at 11px 11px,rgba(15,20,69,.13) 2.2px,transparent 2.6px) 0 0/22px 22px,linear-gradient(#e7ebf2,#dde2eb);
box-shadow:0 1px 0 rgba(255,255,255,.8) inset,0 0 0 1px #cfd5e1,0 18px 40px rgba(15,23,42,.12)}
.row{display:flex;align-items:flex-start;gap:24px;padding-bottom:22px}
.plate{flex:none;width:196px;margin-top:22px;border-radius:12px;padding:14px 16px;background:linear-gradient(#141a55,#0f1445);color:#fff;box-shadow:0 2px 0 #070a2e,0 6px 14px rgba(15,20,69,.25)}
.plate b{display:block;font-size:26px;font-weight:800;letter-spacing:-.02em}
.plate span{display:block;margin-top:2px;font-size:13px;color:rgba(255,255,255,.7)}
.plate i{display:block;margin-top:8px;font:500 11px "IBM Plex Mono",monospace;color:#e8b800;font-style:normal}
.rail{position:relative;flex:1;display:flex;gap:12px;padding-top:6px}
.rail:before{content:"";position:absolute;left:-6px;right:-6px;top:0;height:8px;border-radius:4px;background:linear-gradient(#b8c0cf,#98a1b3);box-shadow:0 2px 3px rgba(15,23,42,.18)}
.key{position:relative;width:140px;display:flex;flex-direction:column;align-items:center;transform-origin:50% 0;transition:transform .45s cubic-bezier(.3,1.6,.5,1)}
.key:hover{transform:rotate(-7deg)}
.key .hook{width:4px;height:12px;background:#8a93a6;border-radius:2px}
.key .ring{width:22px;height:22px;margin-top:-4px;border-radius:50%;border:3px solid #9aa3b5}
.key .tag{margin-top:-6px;width:140px;height:96px;border-radius:14px 14px 18px 18px;padding:18px 14px 10px;display:flex;flex-direction:column;position:relative;box-shadow:0 1px 0 rgba(255,255,255,.4) inset,0 6px 12px rgba(15,23,42,.16)}
.key .tag:before{content:"";position:absolute;left:62px;top:6px;width:16px;height:6px;border-radius:3px;background:rgba(0,0,0,.22)}
.key .tag span{font-size:14px;font-weight:700;line-height:1.2}
.key .tag em{margin-top:auto;font:500 11px "IBM Plex Mono",monospace;font-style:normal;opacity:.65;display:flex;align-items:center;gap:6px}
.s0 .tag{background:#e8b800;color:#0f1445}
.s1 .tag{background:#fff;color:#0f1445}
.s2 .tag{background:#1a2263;color:#fff}'''
    rows = ''
    for si, s in enumerate(CORAZON):
        keys = ''.join(f'<a class="key s{si}" href="#"><span class="hook"></span><span class="ring"></span>'
                       f'<span class="tag"><span>{n}</span><em>{mic(k, 13)}{s["code"]}-{j+1:02d}</em></span></a>'
                       for j, (n, k) in enumerate(s['mods']))
        rows += (f'<div class="row"><div class="plate"><b>{s["code"]}</b><span>{s["role"]}</span><i>{len(s["mods"])} modules</i></div>'
                 f'<div class="rail">{keys}</div></div>')
    body = (f'<div class="pg"><div class="band"><div class="w">{top()}<div class="gr"><p class="dt">{DATE}</p>'
            f'<h1>Good morning, Corazon</h1></div></div></div><main class="w"><div class="cab">{rows}</div></main></div>')
    return 'C · Key cabinet: every module is a key tag on its system\'s rail', css, body, 900


# ======================================================================== D. Isometric depot, the part you point at lights up
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))


def P(x, y, z, s=14, ox=300, oy=132):
    return (ox + (x - y) * C30 * s, oy + (x + y) * S30 * s - z * s)


def poly(pts, fill, cls='', extra=''):
    c = f' class="{cls}"' if cls else ''
    return f'<polygon{c} points="' + ' '.join(f'{a:.1f},{b:.1f}' for a, b in (P(*p) for p in pts)) + f'" fill="{fill}"{extra}/>'


def box(x, y, z, dx, dy, dz, top, yf, xf, cls=''):
    x1, y1, z1 = x + dx, y + dy, z + dz
    return (poly([(x, y, z1), (x1, y, z1), (x1, y1, z1), (x, y1, z1)], top, cls)
            + poly([(x, y1, z), (x1, y1, z), (x1, y1, z1), (x, y1, z1)], yf, cls)
            + poly([(x1, y, z), (x1, y1, z), (x1, y1, z1), (x1, y, z1)], xf, cls))


def yrect(x0, x1, y, z0, z1, fill, cls=''):
    return poly([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], fill, cls)


def iso_van(x, y, along_y=True):
    # A van as boxes. along_y: long axis along y (nose toward +y).
    if along_y:
        return (box(x, y, .3, 2.2, 4.4, 2.3, '#f7f8fb', '#dfe3ec', '#eef1f6')
                + poly([(x + 2.2, y, .9), (x + 2.2, y + 4.4, .9), (x + 2.2, y + 4.4, 1.5), (x + 2.2, y, 1.5)], '#1f5cc4')
                + poly([(x + 2.2, y, 1.5), (x + 2.2, y + 4.4, 1.5), (x + 2.2, y + 4.4, 1.8), (x + 2.2, y, 1.8)], '#f29a1f')
                + box(x + .1, y + 4.4, .3, 2.0, 1.4, 1.7, '#eef1f6', '#cfd5e1', '#e6e9f0')
                + poly([(x + .3, y + 5.8, 1.1), (x + 1.9, y + 5.8, 1.1), (x + 1.9, y + 5.8, 1.85), (x + .3, y + 5.8, 1.85)], '#14205a'))
    return ''


def depot_svg():
    g = []
    g.append(poly([(-3, -2, 0), (34, -2, 0), (34, 23, 0), (-3, 23, 0)], '#0b0f3c'))
    # apron markings
    for x0 in (11.5, 21.5):
        g.append(poly([(x0, 10.4, 0), (x0 + .25, 10.4, 0), (x0 + .25, 22, 0), (x0, 22, 0)], 'rgba(232,184,0,.35)'))
        g.append(poly([(x0 + 6.75, 10.4, 0), (x0 + 7, 10.4, 0), (x0 + 7, 22, 0), (x0 + 6.75, 22, 0)], 'rgba(232,184,0,.35)'))
    for yy in (13, 16.5, 20):
        g.append(poly([(14.6, yy, 0), (15.4, yy, 0), (15.4, yy + 1.4, 0), (14.6, yy + 1.4, 0)], 'rgba(203,210,234,.28)'))
    # building
    g.append(box(0, 0, 0, 30, 10, 7, '#2a3290', '#1c2470', '#151b5c'))
    g.append(box(-.3, -.3, 7, 30.6, 10.6, .5, '#333c9c', '#232b7d', '#1a2066'))
    for xp in (10, 20):
        g.append(yrect(xp - .15, xp + .15, 10, 0, 7, '#283084'))
    zones = {
        'z1': [(1.4, 4.4, 1.3, 5.2), (5.6, 8.6, 1.3, 5.2)],
        'z2': [(11.5, 18.5, 0, 5.4)],
        'z3': [(21.5, 28.5, 0, 5.4)],
    }
    for z, doors in zones.items():
        parts = []
        for x0, x1, z0, z1 in doors:
            parts.append(yrect(x0, x1, 10, z0, z1, '#0a0e3a'))
            parts.append(yrect(x0, x1, 10, z0, z1, 'url(#lit)', 'glow'))
            parts.append(yrect(x0, x1, 10, z1 - .35, z1, '#3b43a3'))
        if z == 'z3':
            for xp in (23.2, 26.8):
                parts.append(yrect(xp, xp + .35, 10, 0, 4.6, '#e8b800', 'post'))
            parts.append(yrect(23.2, 27.15, 10, 2.4, 2.75, '#c99f00', 'post'))
        if z == 'z2':
            parts.append(yrect(11.5, 18.5, 10, 0, .06, '#e8b800'))
        g.append(f'<g class="zn {z}">' + ''.join(parts) + '</g>')
    # dock platform and bumpers
    g.append(box(0, 10, 0, 10, 1.8, 1.3, '#2a3290', '#1a2165', '#141a55'))
    for x0 in (2.2, 3.4, 6.4, 7.6):
        g.append(yrect(x0, x0 + .4, 11.8, .5, 1.1, '#e8b800'))
    # vans: one backed onto the dock, one heading into the service lane
    g.append(iso_van(1.8, 12.0))
    g.append(iso_van(14, 15.2))
    # sign on the face: the mark and the name, drawn on the y=10 plane
    a, b = C30, S30
    sx, sy = P(11.3, 10, 6.6)
    g.append(f'<g transform="matrix({a*14:.3f},{b*14:.3f},0,14,{sx:.1f},{sy:.1f})">'
             f'<g transform="scale(.0042)" fill="#e8b800">{LOGO_POLY}</g>'
             f'<text x="1.65" y=".66" font-size=".72" font-weight="800" font-style="italic" fill="#fff" font-family="Inter,sans-serif">WeLinc Logistics</text></g>')
    for code, xc in (('BMS', 4.2), ('VMMS', 14.1), ('VRMS', 24.1)):
        tx, ty = P(xc, 10, 6.05)
        g.append(f'<g transform="matrix({a*14:.3f},{b*14:.3f},0,14,{tx:.1f},{ty:.1f})"><text x="0" y="0" font-size=".5" font-weight="600" '
                 f'fill="rgba(255,255,255,.55)" font-family="IBM Plex Mono,monospace" letter-spacing=".05">{code}</text></g>')
    return ('<svg class="dep" viewBox="0 0 800 440" aria-hidden="true"><defs><linearGradient id="lit" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#fff1b8" stop-opacity=".25"/><stop offset="1" stop-color="#ffd84d"/></linearGradient></defs>' + ''.join(g) + '</svg>')


@reg
def R49Depot():
    css = '''.band{height:470px}
.gr{padding-top:56px;width:440px}
h1{margin:12px 0 0;font-size:52px;line-height:1.02;font-weight:800;letter-spacing:-.03em}
.l{margin:14px 0 0;font-size:16px;line-height:1.5;color:rgba(255,255,255,.68)}
.dep{position:absolute;right:30px;top:14px;width:800px;height:440px}
.dep .glow{opacity:.7;transition:opacity .35s}
.dep .zn{transition:opacity .35s}
.pg:has(.c0:hover) .z1 .glow,.pg:has(.c1:hover) .z2 .glow,.pg:has(.c2:hover) .z3 .glow{opacity:1}
.pg:has(.card:hover) .glow{opacity:.08}
.main{margin-top:-46px;position:relative;z-index:3}
.cols{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.card{background:#fff;border-radius:20px;box-shadow:0 1px 2px rgba(15,23,42,.06),0 14px 34px rgba(15,23,42,.10);padding:20px 22px 14px;transition:box-shadow .25s}
.card:hover{box-shadow:0 0 0 2px #e8b800,0 14px 34px rgba(15,23,42,.12)}
.hd{display:flex;align-items:baseline;gap:10px;padding-bottom:12px;border-bottom:1px solid #eef1f6}
.code{font-size:22px;font-weight:800;color:#0f1445}
.role{font-size:13px;color:#5b6779;margin-left:auto}
.gl{display:grid;grid-template-columns:1fr 1fr;gap:2px 12px;margin-top:10px}
.gl a{display:flex;align-items:center;gap:9px;height:38px;font-size:14px;font-weight:500;border-radius:10px;padding:0 8px;margin:0 -8px}
.gl a svg{color:#3a4486;flex:none}.gl a:hover{background:#f3f5f9}'''
    cols = ''.join(f'<section class="card c{i}"><div class="hd"><span class="code">{s["code"]}</span><span class="role">{s["role"]}</span></div>'
                   f'<div class="gl">' + ''.join(f'<a href="#">{mic(k, 16)}{n}</a>' for n, k in s['mods']) + '</div></section>'
                   for i, s in enumerate(CORAZON))
    body = (f'<div class="pg"><div class="band">{depot_svg()}<div class="w">{top()}<div class="gr"><p class="dt">{DATE}</p>'
            f'<h1>Good morning,<br>Corazon</h1><p class="l">The dock, the service lane and the repair shop. Point at a system to see its part of the depot.</p></div></div></div>'
            f'<main class="w main"><div class="cols">{cols}</div></main></div>')
    return 'D · Isometric depot: point at a system, its part of the depot lights up', css, body, 900


# ======================================================================== write
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'support.js').touch()
    for name, fn in BOARDS.items():
        if ONLY and name not in ONLY:
            continue
        title, css, body, h = fn()
        (OUT / f'{name}.dc.html').write_text(board(title, css, body, h=h))
        print(name, title)


if __name__ == '__main__':
    import gen49b
    BOARDS.update(gen49b.BOARDS)
    main()

"""Round 50 (Nov 25, night): the launcher's only choices are the systems (BMS, VMMS, VRMS); Suite management sits elsewhere.
python3 -I gen50.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from data49 import I, ic, top, board, CORAZON, FELICIDAD, DATE, LOGO_POLY, V_VAN, V_L300, CHEV  # noqa
import gen49 as g49
import gen49b as g49b

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
ARW = ic(I['arrow'], 22, 2.2, 'arw')


def reg(fn):
    BOARDS[fn.__name__] = fn
    return fn


SHADOW = '0 1px 2px rgba(15,23,42,.05),0 10px 28px rgba(15,23,42,.07)'


# ======================================================================== 1. Road band, three system cards
@reg
def R50Road():
    css = '''.band{height:400px}
.gr{padding-top:40px}
h1{margin:12px 0 0;font-size:60px;line-height:1;font-weight:800;letter-spacing:-.035em}
.l{margin:14px 0 0;font-size:17px;color:rgba(255,255,255,.68)}
.road{position:absolute;left:0;right:0;bottom:0;height:96px;background:#0a0d33;box-shadow:inset 0 1px 0 rgba(255,255,255,.08)}
.road b{position:absolute;left:0;right:0;top:0;height:6px;background:#141a55}
.road i{position:absolute;left:0;right:0;top:52px;height:3px;background:repeating-linear-gradient(90deg,rgba(203,210,234,.32) 0 44px,transparent 44px 104px)}
.veh{position:absolute;left:0;animation:drive 30s linear infinite}
.v1{width:210px;bottom:16px;animation-delay:-6s}.v2{width:140px;bottom:15px;animation-delay:-20s}
@keyframes drive{from{transform:translateX(-260px)}to{transform:translateX(1700px)}}
.cards{margin-top:36px;display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.cards a{position:relative;display:flex;flex-direction:column;min-height:250px;padding:30px 30px 28px;border-radius:24px;background:#fff;box-shadow:''' + SHADOW + ''';transition:transform .25s,box-shadow .25s}
.cards a:hover{transform:translateY(-4px);box-shadow:0 2px 4px rgba(15,23,42,.06),0 22px 44px rgba(15,23,42,.12)}
.cards b{font-size:44px;line-height:1;font-weight:800;letter-spacing:-.035em;color:#0f1445}
.cards .nm{margin-top:12px;font-size:15px;font-weight:600}
.cards .ln{margin-top:6px;font-size:14px;color:#5b6779;line-height:1.5}
.cards .rl{margin-top:auto;padding-top:20px;font-size:14px;color:#5b6779}
.cards .rl strong{color:#0f172a;font-weight:600}
.cards .arw{position:absolute;right:28px;top:34px;color:#c3cad8;transition:transform .25s,color .25s}
.cards a:hover .arw{color:#0f1445;transform:translateX(4px)}'''
    cards = ''.join(f'<a href="#"><b>{s["code"]}</b>{ARW}<span class="nm">{s["name"]}</span><span class="ln">{s["line"]}</span>'
                    f'<span class="rl">Your role: <strong>{s["role"]}</strong></span></a>' for s in CORAZON)
    body = (f'<div class="pg"><div class="band"><div class="w">{top()}<div class="gr"><p class="dt">{DATE}</p>'
            f'<h1>Good morning, Corazon</h1><p class="l">Pick a system to start.</p></div></div>'
            f'<div class="road"><b></b><i></i><svg class="veh v1" viewBox="-8 -2 138 56"><defs>{V_VAN}</defs><use href="#van"/></svg>'
            f'<svg class="veh v2" viewBox="-6 -2 96 50"><defs>{V_L300}</defs><use href="#l300"/></svg></div></div>'
            f'<main class="w"><div class="cards">{cards}</div></main></div>')
    return 'R50-1 · Road band, three system cards', css, body


# ======================================================================== 2. Stage: the three names are the choices, the van drives to the one you point at
@reg
def R50Stage():
    css = '''.bg{position:absolute;left:0;right:0;top:0;height:470px;background:#0f1445}
.top{color:#fff}
.gr{position:relative;z-index:2;padding-top:28px;color:#fff;display:flex;align-items:baseline;gap:20px}
h1{margin:0;font-size:34px;font-weight:800;letter-spacing:-.02em}.gr .dt{margin-left:auto}
.sys{position:relative;z-index:2;margin-top:60px;display:grid;grid-template-columns:repeat(3,1fr)}
.sys a{display:flex;flex-direction:column}
.sys .c{height:236px;color:#fff;font-size:100px;line-height:1;font-weight:800;letter-spacing:-.05em;opacity:.38;transition:opacity .3s}
.sys a:hover .c{opacity:1}
.sys .nm{margin-top:42px;font-size:17px;font-weight:700;color:#0f172a}
.sys .ln{margin-top:6px;font-size:14px;color:#5b6779}
.sys .rl{margin-top:14px;font-size:14px;color:#5b6779}.sys .rl strong{color:#0f172a;font-weight:600}
.trk{position:absolute;z-index:1;left:0;right:0;top:426px;height:2px;background:rgba(255,255,255,.16)}
.trk:before{content:"";position:absolute;left:0;right:0;top:-5px;height:12px;background:repeating-linear-gradient(90deg,rgba(255,255,255,.2) 0 2px,transparent 2px 100px)}
.van{position:absolute;z-index:2;top:362px;left:0;width:124px;transition:left 1.1s cubic-bezier(.4,0,.2,1)}
.pg:has(.s0:hover) .van{left:0}.pg:has(.s1:hover) .van{left:400px}.pg:has(.s2:hover) .van{left:800px}
'''
    sys_ = ''.join(f'<a class="s{i}" href="#"><span class="c">{s["code"]}</span><span class="nm">{s["name"]}</span>'
                   f'<span class="ln">{s["line"]}</span><span class="rl">Your role: <strong>{s["role"]}</strong></span></a>'
                   for i, s in enumerate(CORAZON))
    van = f'<svg viewBox="-6 -2 96 50"><defs>{V_L300}</defs><use href="#l300"/></svg>'
    body = (f'<div class="pg"><div class="bg"></div><div class="w">{top()}<div class="gr"><h1>Good morning, Corazon</h1><p class="dt">{DATE}</p></div>'
            f'<div class="trk"></div><div class="van">{van}</div><div class="sys">{sys_}</div></div></div>')
    return 'R50-2 · Stage: the system names are the buttons; point at one and the van drives under it', css, body


# ======================================================================== 3. Three keys on the board
@reg
def R50Keys():
    css = '''.band{height:300px}
.gr{padding-top:34px}
h1{margin:12px 0 0;font-size:52px;line-height:1;font-weight:800;letter-spacing:-.035em}
.l{margin:12px 0 0;font-size:16px;color:rgba(255,255,255,.68)}
.cab{margin-top:-50px;position:relative;z-index:2;border-radius:26px;padding:40px 60px 54px;
background:radial-gradient(circle at 12px 12px,rgba(15,20,69,.12) 2.4px,transparent 2.8px) 0 0/24px 24px,linear-gradient(#e7ebf2,#dde2eb);
box-shadow:0 1px 0 rgba(255,255,255,.8) inset,0 0 0 1px #cfd5e1,0 22px 48px rgba(15,23,42,.14)}
.rail{position:relative;display:flex;justify-content:space-around;padding-top:8px}
.rail:before{content:"";position:absolute;left:-20px;right:-20px;top:0;height:10px;border-radius:5px;background:linear-gradient(#b8c0cf,#98a1b3);box-shadow:0 3px 4px rgba(15,23,42,.18)}
.key{width:300px;display:flex;flex-direction:column;align-items:center;transform-origin:50% 0;transition:transform .6s cubic-bezier(.3,1.7,.5,1)}
.key:hover{transform:rotate(-6deg)}
.hook{width:6px;height:18px;background:#8a93a6;border-radius:3px}
.ring{width:34px;height:34px;margin-top:-6px;border-radius:50%;border:4px solid #9aa3b5}
.tag{margin-top:-8px;width:300px;height:330px;border-radius:22px 22px 30px 30px;padding:46px 30px 26px;display:flex;flex-direction:column;position:relative;box-shadow:0 1px 0 rgba(255,255,255,.4) inset,0 14px 26px rgba(15,23,42,.2)}
.tag:before{content:"";position:absolute;left:126px;top:14px;width:48px;height:12px;border-radius:6px;background:rgba(0,0,0,.24)}
.tag b{font-size:64px;line-height:1;font-weight:800;letter-spacing:-.045em}
.tag .nm{margin-top:16px;font-size:16px;font-weight:700;line-height:1.3}
.tag .ln{margin-top:8px;font-size:14px;line-height:1.45;opacity:.75}
.tag .rl{margin-top:auto;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.06em;opacity:.7}
.k0 .tag{background:#e8b800;color:#0f1445}.k1 .tag{background:#fff;color:#0f1445}.k2 .tag{background:#1a2263;color:#fff}'''
    keys = ''.join(f'<a class="key k{i}" href="#"><span class="hook"></span><span class="ring"></span><span class="tag"><b>{s["code"]}</b>'
                   f'<span class="nm">{s["name"]}</span><span class="ln">{s["line"]}</span><span class="rl">{s["role"].upper()}</span></span></a>'
                   for i, s in enumerate(CORAZON))
    body = (f'<div class="pg"><div class="band"><div class="w">{top()}<div class="gr"><p class="dt">{DATE}</p>'
            f'<h1>Good morning, Corazon</h1><p class="l">Take a key: each one opens a system.</p></div></div></div>'
            f'<main class="w"><div class="cab"><div class="rail">{keys}</div></div></main></div>')
    return 'R50-3 · Key board: one key tag per system, it swings when you point at it', css, body


# ======================================================================== 4. The depot, each part is a system
@reg
def R50Depot():
    css = '''.band{height:520px}
.gr{padding-top:60px;width:440px}
h1{margin:12px 0 0;font-size:56px;line-height:1.02;font-weight:800;letter-spacing:-.035em}
.l{margin:16px 0 0;font-size:16px;line-height:1.5;color:rgba(255,255,255,.68)}
.dep{position:absolute;right:10px;top:40px;width:860px;height:473px}
.dep .glow{opacity:.7;transition:opacity .35s}
.pg:has(.cards a:hover) .glow{opacity:.08}
.pg:has(.c0:hover) .z1 .glow,.pg:has(.c1:hover) .z2 .glow,.pg:has(.c2:hover) .z3 .glow{opacity:1}
.cards{margin-top:-60px;position:relative;z-index:3;display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.cards a{display:block;padding:24px 26px;border-radius:22px;background:#fff;box-shadow:0 1px 2px rgba(15,23,42,.06),0 16px 36px rgba(15,23,42,.12);transition:box-shadow .25s,transform .25s}
.cards a:hover{transform:translateY(-3px);box-shadow:0 0 0 3px #e8b800,0 18px 40px rgba(15,23,42,.14)}
.cards b{font-size:34px;font-weight:800;letter-spacing:-.03em;color:#0f1445}
.cards .rl{float:right;margin-top:12px;font-size:14px;color:#5b6779}
.cards p{margin:8px 0 0;font-size:14px;color:#5b6779;line-height:1.5}.cards p strong{display:block;color:#0f172a;font-weight:600}'''
    parts = ['the dock', 'the service lane', 'the repair shop']
    cards = ''.join(f'<a class="c{i}" href="#"><span class="rl">{s["role"]}</span><b>{s["code"]}</b>'
                    f'<p><strong>{s["name"]}</strong>{s["line"]}</p></a>' for i, s in enumerate(CORAZON))
    body = (f'<div class="pg"><div class="band">{g49.depot_svg()}<div class="w">{top()}<div class="gr"><p class="dt">{DATE}</p>'
            f'<h1>Good morning,<br>Corazon</h1><p class="l">One depot, three systems: the dock, the service lane and the repair shop. Point at a system to light up its part.</p></div></div></div>'
            f'<main class="w"><div class="cards">{cards}</div></main></div>')
    return 'R50-4 · Isometric depot: each system is a part of it; pointing at a card lights its part', css, body


# ======================================================================== 5. Ledger: three huge rows of type
@reg
def R50Ledger():
    css = '''.pg{background:#f7f7f4}
.bar{height:64px;background:#0f1445;color:#fff;position:relative}
.bar:after{content:"";position:absolute;left:0;right:0;bottom:-3px;height:3px;background:#e8b800}
.mini{position:absolute;bottom:-4px;width:58px;animation:mv 40s linear infinite;animation-delay:-12s;z-index:2}
@keyframes mv{from{transform:translateX(-80px)}to{transform:translateX(1520px)}}
.gr{padding:48px 0 30px}.gr .dt{color:#8a6d00}
h1{margin:12px 0 0;font-size:40px;font-weight:800;letter-spacing:-.03em;color:#0f1445}
.rows a{display:grid;grid-template-columns:420px 1fr auto 40px;align-items:center;gap:24px;height:176px;border-top:2px solid #0f1445;transition:background .2s}
.rows a:last-child{border-bottom:2px solid #0f1445}
.rows b{font-size:136px;line-height:1;font-weight:800;letter-spacing:-.06em;color:#0f1445;transition:transform .3s}
.rows .nm{font-size:20px;font-weight:700}.rows .ln{display:block;margin-top:6px;font-size:15px;color:#5b6779}
.rows .rl{font-size:15px;color:#5b6779}
.rows .arw{color:#0f1445;opacity:0;transform:translateX(-8px);transition:.25s}
.rows a:hover b{transform:translateX(10px)}.rows a:hover .arw{opacity:1;transform:none}'''
    rows = ''.join(f'<a href="#"><b>{s["code"]}</b><span><span class="nm">{s["name"]}</span><span class="ln">{s["line"]}</span></span>'
                   f'<span class="rl">{s["role"]}</span>{ARW}</a>' for s in CORAZON)
    body = (f'<div class="pg"><div class="bar"><div class="w">{top()}</div>'
            f'<svg class="mini" viewBox="-6 -2 96 50"><defs>{V_L300}</defs><use href="#l300"/></svg></div>'
            f'<main class="w lt"><div class="gr"><p class="dt">{DATE}</p><h1>Good morning, Corazon. Where are you working today?</h1></div><div class="rows">{rows}</div></main></div>')
    return 'R50-5 · Ledger: a light page, the three systems as huge rows of type', css, body


# ======================================================================== 6. Moving day hero, three cards on it
@reg
def R50Hero():
    css = '''.hero{position:relative;height:470px;overflow:hidden;color:#fff}
.hs{position:absolute;inset:0;width:100%;height:100%}
.lift{animation:lift 6s ease-in-out infinite}
@keyframes lift{0%,15%{transform:translateY(0)}45%,65%{transform:translateY(74px)}95%,100%{transform:translateY(0)}}
.hero .top{color:#fff}
.hg{position:relative;z-index:2;padding-top:50px;width:520px}
h1{margin:12px 0 0;font-size:58px;line-height:1.02;font-weight:800;letter-spacing:-.035em}
.l{margin:14px 0 0;font-size:16px;color:rgba(255,255,255,.7)}
.cards{margin-top:-60px;position:relative;z-index:3;display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.cards a{display:flex;flex-direction:column;gap:12px;padding:26px 28px;border-radius:22px;background:#fff;box-shadow:0 18px 40px rgba(10,13,51,.22);transition:transform .25s}
.cards a:hover{transform:translateY(-4px)}
.cards b{font-size:40px;line-height:1;font-weight:800;letter-spacing:-.035em;color:#0f1445}
.cards span{font-size:14px;color:#5b6779;line-height:1.5}.cards strong{display:block;font-size:15px;color:#0f172a}
.cards em{display:block;margin-top:6px;font-style:normal;font-size:13px}'''
    scene = g49b.house_scene().replace('viewBox="0 0 1440 470"', 'viewBox="0 0 1440 470"')
    cards = ''.join(f'<a href="#"><b>{s["code"]}</b><span><strong>{s["name"]}</strong>{s["line"]}<em>{s["role"]}</em></span></a>' for s in CORAZON)
    body = (f'<div class="pg"><div class="hero">{scene}<div class="w">{top()}<div class="hg"><p class="dt">{DATE}</p>'
            f'<h1>Good morning, Corazon</h1><p class="l">#hasslefree, from the booking to the last repair.</p></div></div></div>'
            f'<main class="w"><div class="cards">{cards}</div></main></div>')
    return 'R50-6 · Moving day hero (the tail lift working), three system cards across it', css, body


# ======================================================================== 7. Fleet head on, three wide bars
@reg
def R50Fleet():
    css = '''.band{height:330px}
.fl{position:absolute;right:60px;bottom:0;width:640px;height:270px}
.hl{animation:hl 5s ease-in-out infinite}@keyframes hl{0%,100%{opacity:1}50%{opacity:.82}}
.gr{padding-top:40px}
h1{margin:12px 0 0;font-size:56px;line-height:1;font-weight:800;letter-spacing:-.035em}
.l{margin:12px 0 0;font-size:16px;color:rgba(255,255,255,.68)}
.bars{margin-top:30px;display:flex;flex-direction:column;gap:14px}
.bars a{display:grid;grid-template-columns:200px 1fr 220px 40px;align-items:center;gap:20px;height:146px;padding:0 34px;border-radius:22px;background:#fff;box-shadow:''' + SHADOW + ''';transition:transform .25s,box-shadow .25s}
.bars a:hover{transform:translateX(6px);box-shadow:inset 6px 0 0 #e8b800,''' + SHADOW + '''}
.bars b{font-size:56px;font-weight:800;letter-spacing:-.045em;color:#0f1445}
.bars .nm{font-size:18px;font-weight:700}.bars .ln{display:block;margin-top:4px;font-size:14px;color:#5b6779}
.bars .rl{font-size:14px;color:#5b6779;text-align:right}
.bars .arw{color:#c3cad8}.bars a:hover .arw{color:#0f1445}'''
    fleet = (f'<svg class="fl" viewBox="0 0 640 270" aria-hidden="true"><defs><radialGradient id="beam">'
             f'<stop offset="0" stop-color="#fff3b0" stop-opacity=".35"/><stop offset="1" stop-color="#fff3b0" stop-opacity="0"/></radialGradient></defs>'
             f'<rect x="0" y="232" width="640" height="38" fill="#0a0d33"/>'
             f'<g transform="translate(0 102)">{g49b.front(40, 130, 130, "l300")}{g49b.front(230, 160, 170, "van")}{g49b.front(440, 190, 210, "big")}</g></svg>')
    bars = ''.join(f'<a href="#"><b>{s["code"]}</b><span><span class="nm">{s["name"]}</span><span class="ln">{s["line"]}</span></span>'
                   f'<span class="rl">{s["role"]}</span>{ARW}</a>' for s in CORAZON)
    body = (f'<div class="pg"><div class="band">{fleet}<div class="w">{top()}<div class="gr"><p class="dt">{DATE}</p>'
            f'<h1>Good morning, Corazon</h1><p class="l">Pick a system to start.</p></div></div></div><main class="w"><div class="bars">{bars}</div></main></div>')
    return 'R50-7 · The fleet head on, headlights on; three wide system bars', css, body


# ======================================================================== 8. Three tall panels, numbered like loading bays
MK = ('<svg class="mk" viewBox="0 0 300 150" preserveAspectRatio="none" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="4">'
      '<path d="M20 0V150M280 0V150" stroke-dasharray="16 10"/><path d="M110 132H190" stroke-width="10" stroke-linecap="round"/>'
      '<path d="M150 20V70M132 52l18 18 18-18" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>')


@reg
def R50Bays():
    css = '''.band{height:230px}
.gr{padding-top:32px;display:flex;align-items:flex-end;gap:24px}
h1{margin:12px 0 0;font-size:52px;line-height:1;font-weight:800;letter-spacing:-.035em}
.gr .l{margin:0 0 6px auto;font-size:15px;color:rgba(255,255,255,.6)}
.bays{margin-top:-40px;position:relative;z-index:2;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;border-radius:24px;overflow:hidden;box-shadow:0 22px 48px rgba(15,23,42,.14)}
.bays a{position:relative;display:flex;flex-direction:column;height:520px;padding:34px 36px;background:#fff;border-left:1px solid #e6eaf1;transition:background .3s}
.bays a:first-child{border-left:0}
.bays a:before{content:"";position:absolute;left:0;right:0;top:0;height:14px;background:repeating-linear-gradient(-45deg,#e8b800 0 14px,#0f1445 14px 28px);transform:scaleY(.3);transform-origin:top;transition:transform .3s}
.bays a:hover:before{transform:scaleY(1)}
.bays a:hover{background:#fbfaf3}
.bays .no{font:600 13px "IBM Plex Mono",monospace;letter-spacing:.1em;color:#8a94a8}
.bays .nm{margin-top:auto;font-size:17px;font-weight:700}
.bays .ln{margin-top:6px;font-size:14px;color:#5b6779;line-height:1.5}
.bays .rl{margin-top:22px;padding-top:16px;border-top:1px solid #eef1f6;font-size:14px;color:#5b6779}
.bays b{display:block;margin-top:14px;font-size:100px;line-height:.9;font-weight:800;letter-spacing:-.06em;color:#0f1445}
.bays .mk{position:absolute;left:36px;right:36px;top:64px;height:150px;color:#dfe4ee;transition:color .3s}
.bays a:hover .mk{color:#e8b800}'''
    bays = ''.join(f'<a href="#"><span class="no">BAY {i+1:02d}</span><span class="nm">{s["name"]}</span><span class="ln">{s["line"]}</span>'
                   f'<b>{s["code"]}</b><span class="rl">{s["role"]}</span>{MK}</a>' for i, s in enumerate(CORAZON))
    body = (f'<div class="pg"><div class="band"><div class="w">{top()}<div class="gr"><div><p class="dt">{DATE}</p><h1>Good morning, Corazon</h1></div>'
            f'<p class="l">Three systems, one sign in.</p></div></div></div><main class="w"><div class="bays">{bays}</div></main></div>')
    return 'R50-8 · Bays: three tall numbered panels; pointing at one drops the hazard stripe', css, body


# ======================================================================== Suite management placements (Felicidad Roxas: VMMS Admin, VRMS Admin)
def two_cards():
    return ''.join(f'<a href="#"><b>{s["code"]}</b>{ARW}<span class="nm">{s["name"]}</span><span class="ln">{s["line"]}</span>'
                   f'<span class="rl">Your role: <strong>{s["role"]}</strong></span></a>' for s in FELICIDAD)


P_CSS = '''.band{height:330px}
.gr{padding-top:40px}
h1{margin:12px 0 0;font-size:56px;line-height:1;font-weight:800;letter-spacing:-.035em}
.l{margin:12px 0 0;font-size:16px;color:rgba(255,255,255,.68)}
.road{position:absolute;left:0;right:0;bottom:0;height:70px;background:#0a0d33}
.road i{position:absolute;left:0;right:0;top:36px;height:3px;background:repeating-linear-gradient(90deg,rgba(203,210,234,.3) 0 44px,transparent 44px 104px)}
.road svg{position:absolute;left:0;bottom:10px;width:160px;animation:drive 30s linear infinite;animation-delay:-8s}
@keyframes drive{from{transform:translateX(-200px)}to{transform:translateX(1660px)}}
.cards{margin-top:32px;display:grid;grid-template-columns:repeat(2,1fr);gap:24px}
.cards a{position:relative;display:flex;flex-direction:column;min-height:230px;padding:30px;border-radius:24px;background:#fff;box-shadow:''' + SHADOW + '''}
.cards b{font-size:44px;line-height:1;font-weight:800;letter-spacing:-.035em;color:#0f1445}
.cards .nm{margin-top:12px;font-size:15px;font-weight:600}.cards .ln{margin-top:6px;font-size:14px;color:#5b6779}
.cards .rl{margin-top:auto;padding-top:20px;font-size:14px;color:#5b6779}.cards .rl strong{color:#0f172a;font-weight:600}
.cards .arw{position:absolute;right:28px;top:34px;color:#c3cad8}
.sm{height:44px;padding:0 16px;margin:0 10px 0 auto;border:0;border-radius:12px;background:rgba(255,255,255,.1);box-shadow:inset 0 0 0 1px rgba(255,255,255,.18);color:#fff;font:600 14px Inter,sans-serif;display:flex;align-items:center;gap:10px}
.sm svg{color:#e8b800}.sm em{font-style:normal;font-size:12px;color:#0f1445;background:#e8b800;border-radius:6px;padding:2px 7px}
.top .sm+.me{margin-left:0}'''


def p_band(extra_top='', after_gr=''):
    t = top('Felicidad Roxas', 'FR')
    if extra_top:
        t = t.replace('<button class="me"', extra_top + '<button class="me"', 1)
    return (f'<div class="band"><div class="w">{t}{after_gr}<div class="gr"><p class="dt">{DATE}</p><h1>Good morning, Felicidad</h1>'
            f'<p class="l">Pick a system to start.</p></div></div><div class="road"><i></i>'
            f'<svg viewBox="-8 -2 138 56"><defs>{V_VAN}</defs><use href="#van"/></svg></div></div>')


@reg
def R50SuiteBar():
    btn = f'<a class="sm" href="#">{ic(I["shield"], 18)}Suite management<em>4 to review</em></a>'
    body = f'<div class="pg">{p_band(btn)}<main class="w"><div class="cards">{two_cards()}</div></main></div>'
    return 'P1 · Suite management as a button in the top bar, beside your account', P_CSS, body


@reg
def R50SuiteAccount():
    css = P_CSS + '''.band{overflow:visible;z-index:5}
.mn{position:absolute;right:0;top:60px;z-index:9;width:300px;border-radius:16px;background:#fff;color:#0f172a;padding:8px;box-shadow:0 24px 50px rgba(5,8,40,.35)}
.mn .who{padding:12px 12px 10px;border-bottom:1px solid #eef1f6;margin-bottom:6px}
.mn .who b{display:block;font-size:15px}.mn .who span{font-size:13px;color:#5b6779}
.mn a{display:flex;align-items:center;gap:12px;height:44px;padding:0 12px;border-radius:10px;font-size:15px;font-weight:500}
.mn a svg{color:#3a4486}.mn a em{margin-left:auto;font-style:normal;font-size:12px;font-weight:600;color:#0f1445;background:#e8b800;border-radius:6px;padding:2px 7px}
.mn a.on{background:#f3f5f9}.mn hr{border:0;border-top:1px solid #eef1f6;margin:6px 0}'''
    mn = (f'<div class="mn"><div class="who"><b>Felicidad Roxas</b><span>VMMS Admin, VRMS Admin</span></div>'
          f'<a href="#">{ic(I["idcard"], 18)}Profile</a><a href="#" class="on">{ic(I["shield"], 18)}Suite management<em>4</em></a><hr>'
          f'<a href="#">{ic(I["arrow"], 18)}Sign out</a></div>')
    body = f'<div class="pg">{p_band(after_gr=mn)}<main class="w"><div class="cards">{two_cards()}</div></main></div>'
    return 'P2 · Suite management inside the account menu (shown open)', css, body


@reg
def R50SuiteLine():
    css = P_CSS + '''.ln2{margin-top:28px;display:flex;align-items:center;gap:16px;padding:18px 0;border-top:1px solid #e1e6ee;font-size:15px;color:#5b6779}
.ln2 svg{color:#0f1445}.ln2 a{font-weight:700;color:#0f1445;display:flex;align-items:center;gap:8px}
.ln2 a:hover{text-decoration:underline;text-decoration-color:#e8b800;text-decoration-thickness:2px;text-underline-offset:4px}'''
    ln = (f'<div class="ln2">{ic(I["shield"], 18)}<span>You also run accounts for VMMS and VRMS.</span>'
          f'<a href="#">Suite management, 4 to review {ic(I["arrow"], 16, 2.4)}</a></div>')
    body = f'<div class="pg">{p_band()}<main class="w"><div class="cards">{two_cards()}</div>{ln}</main></div>'
    return 'P3 · Suite management as one quiet line under the systems', css, body


@reg
def R50SuiteGreeting():
    css = P_CSS + '''.gr .l a{color:#fff;font-weight:600;text-decoration:underline;text-decoration-color:#e8b800;text-decoration-thickness:2px;text-underline-offset:4px}'''
    band = p_band().replace('<p class="l">Pick a system to start.</p>',
                            '<p class="l">Pick a system to start. 4 things wait in <a href="#">Suite management</a>.</p>')
    body = f'<div class="pg">{band}<main class="w"><div class="cards">{two_cards()}</div></main></div>'
    return 'P4 · Suite management as a link in the greeting line', css, body


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in BOARDS.items():
        if ONLY and name not in ONLY:
            continue
        title, css, body = fn()
        (OUT / f'{name}.dc.html').write_text(board(title, css, body, h=900))
        print(name, title)


if __name__ == '__main__':
    import gen50four  # noqa: F401
    import gen50
    BOARDS.update(gen50.BOARDS)
    main()

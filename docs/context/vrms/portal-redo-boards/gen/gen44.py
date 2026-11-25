"""Round 44 (Nov 25): launcher and sign in redo. python3 -I gen44.py <project dir>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parts import FONTS, LOGO, LOGO_POLY, CHEV, V_VAN, V_L300, page  # noqa

OUT = Path(sys.argv[1])
RM = '@media (prefers-reduced-motion:reduce){*{animation:none!important}}'


def write(name, html):
    (OUT / name).write_text(html)


# ---------------------------------------------------------------- systems
SYS = [
    dict(code='BMS', name='Booking Management System', word='Bookings', role='Operations',
         desc='Bookings, trips and job orders',
         does=['Take bookings and plan trips', 'Assign trucks, drivers and helpers', 'Close job orders']),
    dict(code='VMMS', name='Vehicle Maintenance Management System', word='Maintenance', role='Operations',
         desc='Planned and preventive maintenance for the fleet',
         does=['Keep each truck on its service schedule', 'Log fuel and odometer readings', 'See what is due this week']),
    dict(code='VRMS', name='Vehicle Repair Management System', word='Repairs', role='Chief Mechanic',
         desc='Repair tickets, mechanics and parts',
         does=['Open and track repair tickets', 'Assign mechanics to the work', 'Record the parts used']),
]

# ---------------------------------------------------------------- the depot (one connected scene)
# Each zone is 384 wide and 220 tall, ground at y=200, road 200..220. Zones sit 408 apart so they
# line up over three 384px cards with 24px gaps. Two themes through CSS variables: navy and line.
LINE_VAN = '''<symbol id="lvan" viewBox="-8 -2 138 56">
<rect x="0" y="0" width="92" height="38" rx="2.5" fill="#fff" stroke="#0f1445" stroke-width="1.6"/>
<g transform="translate(6 6) scale(0.0541)" fill="#e8b800">''' + LOGO_POLY + '''</g>
<text x="26" y="15" font-size="11" font-weight="800" font-style="italic" fill="#0f1445" font-family="Inter,sans-serif">WeLinc</text>
<path d="M0.5 28H91.5" stroke="#0f1445" stroke-width="1" opacity=".35"/>
<path d="M95 10h16l13 13v15H95z" fill="#fff" stroke="#0f1445" stroke-width="1.6"/>
<path d="M99 14h10l8 8h-18z" fill="#eef0f8" stroke="#0f1445" stroke-width="1.2"/>
<rect x="86" y="36" width="38" height="5" fill="#fff" stroke="#0f1445" stroke-width="1.4"/>
<circle cx="16" cy="44" r="7" fill="#fff" stroke="#0f1445" stroke-width="1.6"/><circle cx="16" cy="44" r="2.5" fill="#0f1445"/>
<circle cx="34" cy="44" r="7" fill="#fff" stroke="#0f1445" stroke-width="1.6"/><circle cx="34" cy="44" r="2.5" fill="#0f1445"/>
<circle cx="110" cy="44" r="7" fill="#fff" stroke="#0f1445" stroke-width="1.6"/><circle cx="110" cy="44" r="2.5" fill="#0f1445"/>
<rect x="124" y="24" width="4" height="6" rx="1" fill="#e8b800"/>
</symbol>'''

THEME_NAVY = ('--w:#121852;--p:#1a2263;--d:#070a2e;--b:#2a3290;--k:#05071f;--e:none;--sw:0;--bd:#1f2670;'
              '--bl:#3b43a3;--rd:#0a0d36;--dash:rgba(203,210,234,.28);--tick:#e8b800')
THEME_LINE = ('--w:#fff;--p:#fff;--d:#eef0f8;--b:#fff;--k:#0f1445;--e:#0f1445;--sw:1.6;--bd:#fff;'
              '--bl:#0f1445;--rd:#fff;--dash:rgba(15,20,69,.22);--tick:#0f1445')

SCENE_CSS = '''.dep .w{fill:var(--w);stroke:var(--e);stroke-width:var(--sw)}
.dep .p{fill:var(--p);stroke:var(--e);stroke-width:var(--sw)}
.dep .d{fill:var(--d);stroke:var(--e);stroke-width:var(--sw)}
.dep .b{fill:var(--b);stroke:var(--e);stroke-width:var(--sw)}
.dep .k{fill:var(--k)}
.dep .bd{fill:var(--bd);stroke:var(--e);stroke-width:var(--sw)}
.dep .bl{stroke:var(--bl);stroke-width:2;fill:none;stroke-linecap:round}
.dep .rd{fill:var(--rd)}
.dep .rdl{stroke:var(--e);stroke-width:var(--sw)}
.dep .dash{stroke:var(--dash);stroke-width:3;stroke-dasharray:28 26}
.dep .tk{stroke:var(--tick);stroke-width:2.4;fill:none;stroke-linecap:round;stroke-linejoin:round}
.dep .glow{fill:#e8b800}
.box{animation:box 7s ease-in-out infinite;transform-box:fill-box}
@keyframes box{0%,12%{transform:translateX(0);opacity:1}46%{transform:translateX(58px);opacity:1}52%,100%{transform:translateX(58px);opacity:0}}
.box.n2{animation-delay:-3.5s}
.t1,.t2,.t3,.t4{opacity:0;animation:tick 8s linear infinite}
.t2{animation-delay:1.2s}.t3{animation-delay:2.4s}.t4{animation-delay:3.6s}
@keyframes tick{0%{opacity:0}4%,70%{opacity:1}76%,100%{opacity:0}}
.lift{animation:lift 9s ease-in-out infinite}
@keyframes lift{0%,14%{transform:translateY(0)}46%,64%{transform:translateY(-26px)}96%,100%{transform:translateY(0)}}
.cone{animation:cone 4.6s ease-in-out infinite}
@keyframes cone{0%,100%{opacity:.18}50%{opacity:.11}}
.pass{animation:pass 16s linear infinite}
@keyframes pass{0%{transform:translateX(-140px)}100%{transform:translateX(1340px)}}
.hot .cone{opacity:.34;animation:none}
'''


def van(x, line, w=160):
    h = w * 56 / 138
    y = 200 - (53 / 56) * h
    sym = '#lvan' if line else '#van'
    return f'<use href="{sym}" x="{x}" y="{y:.1f}" width="{w}" height="{h:.1f}"/>'


def zone_bms(line):
    return f'''<g>
<rect class="p" x="0" y="30" width="226" height="12"/>
<rect class="w" x="8" y="42" width="210" height="158"/>
<rect class="d" x="112" y="78" width="96" height="88"/>
<rect class="p" x="112" y="78" width="96" height="12"/>
<g class="b"><rect x="122" y="140" width="22" height="22"/><rect x="146" y="140" width="22" height="22"/><rect x="134" y="118" width="22" height="22"/><rect x="176" y="146" width="16" height="16"/></g>
<rect class="w" x="24" y="96" width="62" height="40"/>
<path class="bl" d="M32 108h46M32 118h30M32 128h38"/>
<rect class="p" x="104" y="166" width="118" height="34"/>
<rect class="k" x="218" y="170" width="6" height="14" rx="1"/>
<path class="bl" d="M214 70l14-8"/><rect class="p" x="224" y="56" width="14" height="10" rx="2"/>
<path class="glow cone" d="M231 66 L212 160 H300 Z"/>
<rect class="b box" x="176" y="146" width="16" height="16"/>
<rect class="b box n2" x="186" y="150" width="12" height="12"/>
{van(222, line)}
</g>'''


def zone_vmms(line):
    return f'''<g>
<rect class="w" x="24" y="52" width="336" height="148"/>
<rect class="p" x="6" y="36" width="372" height="16"/>
<rect class="p" x="18" y="52" width="10" height="148"/><rect class="p" x="356" y="52" width="10" height="148"/>
<g class="glow"><rect x="120" y="52" width="40" height="4" opacity=".7"/><rect x="232" y="52" width="40" height="4" opacity=".7"/></g>
<path class="glow cone" d="M124 56 L100 200 H180 L156 56Z"/>
<path class="glow cone" d="M236 56 L212 200 H292 L268 56Z" style="animation-delay:-2s"/>
<rect class="bd" x="44" y="72" width="66" height="92" rx="3"/>
<g class="bl" stroke-width="1.6"><rect x="52" y="84" width="10" height="10" rx="2"/><rect x="52" y="102" width="10" height="10" rx="2"/><rect x="52" y="120" width="10" height="10" rx="2"/><rect x="52" y="138" width="10" height="10" rx="2"/>
<path d="M68 89h32M68 107h26M68 125h32M68 143h22"/></g>
<path class="tk t1" d="M53 89l3 3 6-7"/><path class="tk t2" d="M53 107l3 3 6-7"/><path class="tk t3" d="M53 125l3 3 6-7"/><path class="tk t4" d="M53 143l3 3 6-7"/>
<path class="bl" d="M77 164v36"/>
<g class="k"><ellipse cx="338" cy="194" rx="16" ry="6"/><ellipse cx="338" cy="186" rx="16" ry="6"/><ellipse cx="338" cy="178" rx="16" ry="6"/></g>
{van(142, line)}
</g>'''


def zone_vrms(line):
    return f'''<g>
<rect class="w" x="6" y="44" width="372" height="156"/>
<rect class="p" x="0" y="30" width="384" height="14"/>
<path class="bl" d="M196 44v16"/><path class="p" d="M182 60h28l6 10h-40z"/>
<path class="glow cone" d="M184 70 L120 200 H272 L208 70Z"/>
<rect class="p" x="90" y="84" width="12" height="116"/><rect class="p" x="290" y="84" width="12" height="116"/>
<g class="lift">
<rect class="b" x="84" y="190" width="224" height="8"/>
{van(116, line)}
</g>
<rect class="w" x="324" y="132" width="44" height="68" rx="2"/>
<path class="bl" d="M330 148h32M330 164h32M330 180h32"/>
<rect class="w" x="22" y="150" width="46" height="50" rx="2"/>
<path class="bl" d="M30 162h30M30 174h30"/>
</g>'''


def depot(line=False, passing=True, cls='', w=1200, hot=None):
    zones = [zone_bms(line), zone_vmms(line), zone_vrms(line)]
    hc = ' class="hot"'
    gs = ''.join(f'<g transform="translate({408 * i} 0)"{hc if hot == i else ""}>{z}</g>' for i, z in enumerate(zones))
    road = ('<rect class="rd" x="-200" y="200" width="1600" height="20"/>'
            '<path class="rdl" d="M-200 200H1400" fill="none"/>'
            '<path class="dash" d="M-200 211H1400"/>')
    fence = '<g class="bl" opacity=".5"><path d="M384 120h24M384 150h24M792 120h24M792 150h24M396 110v90M804 110v90"/></g>'
    pas = ''
    if passing:
        pas = f'<g class="pass"><use href="{"#lvan" if line else "#l300"}" x="0" y="{200 - 44 if not line else 168}" width="{86 if not line else 80}" height="{45 if not line else 32}"/></g>'
    theme = THEME_LINE if line else THEME_NAVY
    return f'''<svg class="dep {cls}" style="{theme}" viewBox="0 0 {w} 220" aria-hidden="true" overflow="hidden">
<defs>{V_VAN}{V_L300}{LINE_VAN}</defs>
{fence}{gs}{road}{pas}
</svg>'''


def one_zone(i, line=False, hot=False, h=220):
    z = [zone_bms, zone_vmms, zone_vrms][i](line)
    theme = THEME_LINE if line else THEME_NAVY
    return f'''<svg class="dep" style="{theme}" viewBox="0 0 384 {h}" aria-hidden="true">
<defs>{V_VAN}{V_L300}{LINE_VAN}</defs>
<g transform="translate(0 {h - 220})"{' class="hot"' if hot else ''}>{z}
<rect class="rd" x="-10" y="200" width="404" height="20"/><path class="rdl" d="M-10 200H394"/><path class="dash" d="M-10 211H394"/></g>
</svg>'''


# ---------------------------------------------------------------- page bits
BASE = '''*{box-sizing:border-box}
.pg{width:1440px;height:900px;background:#f3f5f9;font-family:Inter,system-ui,sans-serif;position:relative;overflow:hidden;color:#0f172a}
.wrap{width:1200px;margin:0 auto;position:relative}
.top{height:64px;display:flex;align-items:center}
.lk{display:flex;align-items:center;gap:10px;color:#fff}.lk svg{height:20px;fill:#e8b800}.lk span{font-weight:800;font-style:italic;font-size:16px}
.me{margin-left:auto;display:flex;align-items:center;gap:10px;height:44px;padding:0 8px;border-radius:12px;border:0;background:none;color:#fff;font:500 14px Inter,sans-serif}
.av{width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.12);box-shadow:inset 0 0 0 1px rgba(255,255,255,.2);display:grid;place-items:center;font-size:12px;font-weight:600}
.dt{margin:0;font-size:13px;font-weight:600;color:#e8b800}
h1{margin:8px 0 0;font-size:44px;line-height:1.05;font-weight:800;letter-spacing:-.03em}
.l{margin:10px 0 0;font-size:16px;color:rgba(255,255,255,.72)}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace}
a{color:inherit;text-decoration:none}
.acct{display:flex;align-items:center;gap:28px;font-size:13px;color:#5b6779;border-top:1px solid #e2e8f0;padding-top:16px}
.acct b{font-weight:600;color:#0f172a}
.acct a{margin-left:auto;font-weight:600;color:#1a1f6e;text-decoration:underline;text-underline-offset:3px;text-decoration-color:#c7cde0}
.acct .sep{width:1px;height:14px;background:#d5dbe6}
'''


def topbar(light=False):
    return (f'<div class="top"><div class="lk">{LOGO}<span>WeLinc Logistics</span></div>'
            f'<button class="me" type="button" aria-label="Account menu for Corazon Villareal"><span class="av">CV</span>Corazon Villareal{CHEV}</button></div>')


def greet(br=False, line='Pick where you want to work today.'):
    return (f'<p class="dt">Wednesday, November 25</p><h1>Good morning,{"<br>" if br else " "}Corazon</h1>'
            f'<p class="l">{line}</p>')


ROWS_CSS = '.rows{list-style:none;margin:16px 0 0;padding:0}.rows li{padding:9px 0;border-top:1px solid #eef1f6;font-size:14px;color:#334155}'

def rows(s):
    return '<ul class="rows">' + ''.join(f'<li>{d}</li>' for d in s['does']) + '</ul>'


ACCT = ('<div class="acct"><span>Last sign in <b>yesterday, 5:42 PM</b> on Chrome, Windows</span><span class="sep"></span>'
        '<span><b>2</b> devices signed in</span><span class="sep"></span><span>corazon.villareal@welinc.com</span>'
        '<a href="#">Your profile and sign ins</a></div>')

# ================================================================ LAUNCHER
# ---------- A: one depot across the band, a column under each part ----------
a_css = BASE + SCENE_CSS + '''
.band{background:#0f1445;color:#fff;height:424px;position:relative;overflow:hidden}
.gr{padding-top:20px}
.band .dep{position:absolute;left:0;bottom:0;width:1200px;height:220px}
.cols{display:grid;grid-template-columns:repeat(3,384px);gap:24px;margin-top:0;list-style:none;padding:0}
.cols li{display:flex}
.col{flex:1;display:flex;flex-direction:column;background:#fff;border-radius:0 0 20px 20px;padding:20px 24px 22px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 24px rgba(15,23,42,.06);position:relative}
.col::before{content:"";position:absolute;left:0;right:0;top:0;height:3px;background:transparent}
.col.on{box-shadow:0 0 0 2px #0f1445,0 12px 28px rgba(15,23,42,.12)}
.col .wd{font-size:13px;font-weight:600;color:#5b6779}
.col .nm{display:block;margin-top:6px;font-size:19px;font-weight:700;letter-spacing:-.01em;line-height:1.25}
.col .ds{display:block;margin-top:6px;font-size:14px;color:#5b6779}
.col .rl{display:flex;justify-content:space-between;margin-top:auto;padding-top:14px;border-top:1px solid #eef1f6;font-size:13px;color:#5b6779}
.col .rl b{font-weight:600;color:#0f172a}
.col .nm{font-size:18px}
.col .rows{margin-bottom:18px}
''' + ROWS_CSS + '''
.foot{position:absolute;left:0;right:0;bottom:36px}
''' + RM

def col(s, on=False):
    return (f'<li><a class="col{" on" if on else ""}" href="#"><span class="wd">{s["word"]}</span>'
            f'<span class="nm">{s["name"]}</span><span class="ds">{s["desc"]}</span>{rows(s)}'
            f'<span class="rl"><span>Your role</span><b>{s["role"]}</b></span></a></li>')

a_body = f'''<div class="pg">
<div class="band"><div class="wrap" style="height:100%">{topbar()}<div class="gr">{greet()}</div>{depot(hot=2)}</div></div>
<div class="wrap"><ul class="cols">{''.join(col(s, on=(i == 2)) for i, s in enumerate(SYS))}</ul></div>
<div class="wrap foot">{ACCT}</div>
</div>'''
write('R44Depot.dc.html', page('Launcher, one depot, a column under each part', a_css, a_body))

# ---------- B: tall cards, each opens on its part of the depot ----------
b_css = BASE + SCENE_CSS + '''
.band{background:#0f1445;color:#fff;height:236px;position:relative;overflow:hidden}
.band .mk{position:absolute;right:-30px;top:30px;height:220px;fill:rgba(255,255,255,.04)}
.gr{padding-top:24px}
h1{font-size:40px}
.cards{display:grid;grid-template-columns:repeat(3,384px);gap:24px;margin:28px 0 0;padding:0;list-style:none}
.cd{display:flex;flex-direction:column;background:#fff;border-radius:22px;overflow:hidden;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 24px rgba(15,23,42,.06);height:452px}
.sc .wd{position:absolute;left:24px;top:20px;z-index:1;font-size:13px;font-weight:600;color:rgba(255,255,255,.75)}
.cd.on{box-shadow:0 0 0 2px #0f1445,0 14px 30px rgba(15,23,42,.14)}
.sc{background:#0f1445;height:260px;position:relative;overflow:hidden}
.sc .dep{position:absolute;left:0;bottom:0;width:384px;height:240px}
.tx{padding:22px 26px;display:flex;flex-direction:column;flex:1}
.tx .nm{font-size:22px;font-weight:800;letter-spacing:-.02em;line-height:1.2}
.tx .ds{margin-top:8px;font-size:14px;color:#5b6779;line-height:1.45}
.tx .rl{margin-top:auto;font-size:13px;color:#5b6779}
.tx .rl b{color:#0f172a;font-weight:600}
.foot{position:absolute;left:0;right:0;bottom:30px}
''' + RM

def tall(i, s, on=False):
    return (f'<li><a class="cd{" on" if on else ""}" href="#"><span class="sc"><span class="wd">{s["word"]}</span>{one_zone(i, hot=on, h=240)}</span>'
            f'<span class="tx"><span class="nm">{s["name"]}</span><span class="ds">{s["desc"]}</span>'
            f'<span class="rl">You work here as <b>{s["role"]}</b></span></span></a></li>')

b_body = f'''<div class="pg">
<div class="band"><svg class="mk" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg><div class="wrap">{topbar()}<div class="gr">{greet()}</div></div></div>
<div class="wrap"><ul class="cards">{''.join(tall(i, s, on=(i == 1)) for i, s in enumerate(SYS))}</ul></div>
<div class="wrap foot">{ACCT}</div>
</div>'''
write('R44Tall.dc.html', page('Launcher, tall cards, each opens on its part of the depot', b_css, b_body))

# ---------- C: pick on the left, a big look on the right ----------
c_css = BASE + SCENE_CSS + '''
.band{background:#0f1445;color:#fff;height:316px}
.gr{padding-top:20px}
.panel{margin-top:-96px;background:#fff;border-radius:24px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 14px 40px rgba(15,23,42,.10);display:grid;grid-template-columns:372px 1fr;overflow:hidden;height:520px}
.list{padding:18px;display:flex;flex-direction:column;gap:6px;border-right:1px solid #eef1f6;margin:0;list-style:none}
.it{display:block;border-radius:16px;padding:18px 20px;border:0;background:none;text-align:left;width:100%;font:inherit;color:inherit;cursor:pointer}
.it .nm{display:block;font-size:16px;font-weight:700}
.it .rl{display:block;margin-top:4px;font-size:13px;color:#5b6779}
.it.on{background:#0f1445;color:#fff}.it.on .rl{color:rgba(255,255,255,.7)}
.it:not(.on):hover{background:#f3f5f9}
.lh{font-size:12px;font-weight:600;color:#5b6779;padding:6px 20px 4px}
.lnote{margin-top:auto;padding:16px 20px;font-size:13px;line-height:1.5;color:#5b6779;border-top:1px solid #eef1f6}
.view{display:flex;flex-direction:column}
.big{background:#0f1445;height:300px;position:relative;overflow:hidden;margin:14px 14px 0;border-radius:16px}
.big .dep{position:absolute;left:50%;bottom:0;width:640px;height:367px;transform:translateX(-50%)}
.vt{padding:22px 32px 0 32px;display:grid;grid-template-columns:1fr auto;gap:0 32px;align-items:start}
.vt h2{margin:0;font-size:24px;font-weight:800;letter-spacing:-.02em}
.vt .rows{grid-column:1/3;display:grid;grid-template-columns:repeat(3,1fr);gap:0 24px;margin-top:14px}
.vt .rows li{border-top:1px solid #e2e8f0;padding-top:10px}
.go{grid-column:2;grid-row:1;align-self:center;height:48px;padding:0 26px;border-radius:12px;background:#0f1445;color:#fff;font-weight:700;font-size:15px;display:flex;align-items:center}
.foot{margin-top:24px}
''' + ROWS_CSS + RM

CHECK = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5L20 7"/></svg>'
c_list = ''.join(f'<li><button type="button" class="it{" on" if i == 2 else ""}" aria-pressed="{"true" if i == 2 else "false"}"><span class="nm">{s["name"]}</span><span class="rl">{s["role"]}</span></button></li>' for i, s in enumerate(SYS))
v = SYS[2]
c_body = f'''<div class="pg">
<div class="band"><div class="wrap">{topbar()}<div class="gr">{greet(line='Your three systems, one sign in.')}</div></div></div>
<div class="wrap"><div class="panel">
<ul class="list"><li class="lh">Your systems</li>{c_list}<li class="lnote">Need a role in another system? Ask your admin.</li></ul>
<div class="view"><div class="big">{one_zone(2, hot=True)}</div>
<div class="vt"><h2>{v["name"]}</h2><a class="go" href="#">Open Repairs</a>
{rows(v)}</div></div>
</div><div class="foot">{ACCT}</div></div>
</div>'''
write('R44Preview.dc.html', page('Launcher, pick on the left, a big look on the right', c_css, c_body))

# ---------- D: light, line drawn depot (matches sign in S1) ----------
d_css = BASE + SCENE_CSS + '''
.band{background:#fff;color:#0f1445;height:424px;position:relative;overflow:hidden;box-shadow:inset 0 -1px 0 #e2e8f0}
.lk{color:#0f1445}.lk svg{fill:#0f1445}.me{color:#0f1445}.av{background:#eef0f8;box-shadow:inset 0 0 0 1px #dfe3ee}
.dt{color:#1a1f6e}.l{color:#475569}
h1 em{font-style:normal;box-shadow:inset 0 -12px 0 #e8b800}
.gr{padding-top:20px}
.band .dep{position:absolute;left:0;bottom:0;width:1200px;height:220px}
.cols{display:grid;grid-template-columns:repeat(3,384px);gap:24px;margin:24px 0 0;padding:0;list-style:none}
.cd{display:block;background:#fff;border-radius:20px;padding:22px 24px;box-shadow:0 0 0 1px #e2e8f0;height:300px}
.cd.on{box-shadow:0 0 0 2px #0f1445}
.n{font:600 13px "IBM Plex Mono",monospace;color:#1a1f6e;padding-top:3px}
.cd .nm{display:block;font-size:18px;font-weight:700;line-height:1.25}
.cd .ds{display:block;margin-top:6px;font-size:14px;color:#5b6779}
.cd .rl{display:block;margin-top:14px;font-size:13px;color:#5b6779}.cd .rl b{color:#0f172a;font-weight:600}
.foot{position:absolute;left:0;right:0;bottom:36px}
''' + ROWS_CSS + RM

def lcard(i, s, on=False):
    return (f'<li><a class="cd{" on" if on else ""}" href="#"><span><span class="nm">{s["name"]}</span>'
            f'<span class="ds">{s["desc"]}</span>{rows(s)}<span class="rl">Your role <b>{s["role"]}</b></span></span></a></li>')

d_body = f'''<div class="pg">
<div class="band"><div class="wrap" style="height:100%">{topbar()}<div class="gr"><p class="dt">Wednesday, November 25</p><h1>Good morning, <em>Corazon</em></h1><p class="l">Pick where you want to work today.</p></div>{depot(line=True, hot=0)}</div></div>
<div class="wrap"><ul class="cols">{''.join(lcard(i, s, on=(i == 0)) for i, s in enumerate(SYS))}</ul></div>
<div class="wrap foot">{ACCT}</div>
</div>'''
write('R44Light.dc.html', page('Launcher, light band with the line drawn depot', d_css, d_body))

ROAD = f'''<svg class="road" viewBox="0 0 1440 90" aria-hidden="true"><defs>{V_VAN}{V_L300}</defs>
<rect x="0" y="60" width="1440" height="30" fill="#0a0d36"/><path d="M0 75H1440" stroke="rgba(203,210,234,.28)" stroke-width="3" stroke-dasharray="28 26"/>
<g class="pass"><use href="#van" x="0" y="8" width="138" height="56"/></g><g class="pass" style="animation-delay:-8s"><use href="#l300" x="0" y="18" width="88" height="46"/></g></svg>'''

# ---------- E: big words, the work first ----------
e_css = BASE + SCENE_CSS + '''
.band{background:#0f1445;color:#fff;height:300px;position:relative;overflow:hidden}
.road{position:absolute;left:0;bottom:0;width:1440px;height:90px}\n.road .pass{animation:pass2 22s linear infinite}\n@keyframes pass2{0%{transform:translateX(-160px)}100%{transform:translateX(1600px)}}
.gr{padding-top:20px}
h1{font-size:44px}
.cards{display:grid;grid-template-columns:repeat(3,384px);gap:24px;margin:28px 0 0;padding:0;list-style:none}
.cd{display:block;position:relative;overflow:hidden;background:#fff;border-radius:22px;padding:26px 28px;height:420px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 24px rgba(15,23,42,.06)}
.cd.on{box-shadow:0 0 0 2px #0f1445,0 14px 30px rgba(15,23,42,.12)}
.wd{display:block;font-size:44px;font-weight:800;letter-spacing:-.035em;line-height:1;color:#0f1445}
.nm{display:block;margin-top:10px;font-size:14px;font-weight:600;color:#334155}
.rl{display:block;margin-top:4px;font-size:13px;color:#5b6779}
.cd .dep{position:absolute;left:0;bottom:0;width:384px;height:220px}
.foot{position:absolute;left:0;right:0;bottom:36px}
''' + RM

def ecard(i, s, on=False):
    return (f'<li><a class="cd{" on" if on else ""}" href="#"><span class="wd">{s["word"]}</span><span class="nm">{s["name"]}</span>'
            f'<span class="rl">as {s["role"]}</span>{one_zone(i, line=True, hot=on)}</a></li>')

e_body = f'''<div class="pg">
<div class="band"><div class="wrap" style="height:100%">{topbar()}<div class="gr">{greet()}</div></div>{ROAD}</div>
<div class="wrap"><ul class="cards">{''.join(ecard(i, s, on=(i == 1)) for i, s in enumerate(SYS))}</ul></div>
<div class="wrap foot">{ACCT}</div>
</div>'''
write('R44Words.dc.html', page('Launcher, big words, the work first', e_css, e_body))

# ---------- F: cards plus an account column ----------
f_css = BASE + SCENE_CSS + '''
.band{background:#0f1445;color:#fff;height:424px;position:relative;overflow:hidden}
.band .dep{position:absolute;left:0;bottom:0;width:1200px;height:220px}
.gr{padding-top:20px}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr 300px;gap:20px;margin-top:24px}
.cd{display:flex;flex-direction:column;background:#fff;border-radius:20px;padding:20px 22px;height:300px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 24px rgba(15,23,42,.06)}
.cd.on{box-shadow:0 0 0 2px #0f1445,0 12px 28px rgba(15,23,42,.12)}
.cd .wd{font-size:13px;font-weight:600;color:#5b6779}
.cd .nm{margin-top:6px;font-size:18px;font-weight:700;line-height:1.25}
''' + ROWS_CSS + '''
.cd .rows li{font-size:13px}
.note{margin-top:20px;font-size:13px;color:#5b6779}
.cd .rl{margin-top:auto;padding-top:12px;border-top:1px solid #eef1f6;font-size:13px;color:#5b6779;display:flex;justify-content:space-between}.cd .rl b{color:#0f172a;font-weight:600}
.me2{background:#fff;border-radius:20px;padding:20px 22px;box-shadow:0 0 0 1px #e2e8f0;height:300px;display:flex;flex-direction:column;font-size:13px;color:#5b6779}
.me2 .who{display:flex;gap:12px;align-items:center}
.me2 .ini{width:44px;height:44px;border-radius:50%;background:#eef0f8;color:#1a1f6e;display:grid;place-items:center;font-weight:700;font-size:15px}
.me2 .wn{font-size:15px;font-weight:700;color:#0f172a}
.me2 dl{margin:18px 0 0;display:grid;grid-template-columns:auto 1fr;gap:10px 14px}
.me2 dt{color:#5b6779}.me2 dd{margin:0;color:#0f172a;font-weight:500;text-align:right}
.me2 a{margin-top:auto;height:40px;border-radius:10px;box-shadow:inset 0 0 0 1px #c7cde0;display:grid;place-items:center;font-weight:600;color:#1a1f6e}
''' + RM

def fcard(s, on=False):
    return (f'<a class="cd{" on" if on else ""}" href="#"><span class="wd">{s["word"]}</span><span class="nm">{s["name"]}</span>'
            f'{rows(s)}'
            f'<span class="rl"><span>Your role</span><b>{s["role"]}</b></span></a>')

f_body = f'''<div class="pg">
<div class="band"><div class="wrap" style="height:100%">{topbar()}<div class="gr">{greet()}</div>{depot()}</div></div>
<div class="wrap"><div class="grid">{''.join(fcard(s, on=(i == 2)) for i, s in enumerate(SYS))}
<aside class="me2" aria-label="Your account"><div class="who"><span class="ini">CV</span><span><span class="wn">Corazon Villareal</span><br>corazon.villareal@welinc.com</span></div>
<dl><dt>Last sign in</dt><dd>Yesterday, 5:42 PM</dd><dt>On</dt><dd>Chrome, Windows</dd><dt>Devices signed in</dt><dd>2</dd><dt>Systems</dt><dd>3</dd></dl>
<a href="#">Your profile</a></aside></div><p class="note">Need a role in another system? Ask your admin.</p></div>
</div>'''
write('R44Account.dc.html', page('Launcher, cards with what you do there, and your account', f_css, f_body))
print('launcher ok')


# ================================================================ SIGN IN
from parts import V_WING  # noqa: E402

ARROW = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
FORM_CSS = '''.fm{width:384px;display:flex;flex-direction:column;gap:26px;margin:0}
.fm h2{margin:0;font-size:28px;font-weight:800;letter-spacing:-.02em;color:#0f172a}
.sub{margin:8px 0 0;font-size:15px;color:#475569}
.fs{display:flex;flex-direction:column;gap:18px}
.fm label{display:block;font-size:14px;font-weight:600;margin-bottom:6px;color:#0f172a}
.row{display:flex;justify-content:space-between;align-items:flex-start}
.row a{font-size:14px;font-weight:600;color:#1a1f6e;text-decoration:underline;text-underline-offset:3px;text-decoration-color:#c7cde0}
.in{width:100%;height:46px;border:1px solid #64748b;border-radius:12px;padding:0 14px;font:15px Inter,sans-serif;color:#0f172a;background:#fff}
.in::placeholder{color:#5b6779}
.btn{height:48px;border:0;border-radius:12px;background:#0f1445;color:#fff;font:700 16px Inter,sans-serif;display:flex;align-items:center;justify-content:center;gap:10px;cursor:pointer}
.hint{margin:0;font-size:14px;line-height:1.5;color:#5b6779}
.slk{display:flex;align-items:center;gap:10px;color:#0f1445}.slk svg{height:20px;fill:#0f1445}.slk span{font-weight:800;font-style:italic;font-size:16px}
'''


def form(title='Sign in', sub='Use your WeLinc work email.'):
    return f'''<form class="fm"><div><h2>{title}</h2><p class="sub">{sub}</p></div>
<div class="fs"><div><label for="e">Work email</label><input id="e" class="in" placeholder="you@welinc.com"></div>
<div><div class="row"><label for="p">Password</label><a href="#">Forgot password?</a></div><input id="p" type="password" class="in" placeholder="Enter password"></div>
<button type="button" class="btn">Sign in {ARROW}</button></div>
<p class="hint">No account yet? Ask your admin to add you. You'll get an email to set your password.</p></form>'''


SLOGO = f'<div class="slk">{LOGO}<span>WeLinc Logistics</span></div>'
HEAD = 'WeLinc Logistics<br><em>Operations</em><br>Workspace'
LINE = 'Bookings, maintenance and repairs for the whole fleet, in one place.'
SBASE = BASE + SCENE_CSS + FORM_CSS + '''
h1{margin:0;font-size:64px;line-height:1;font-weight:800;letter-spacing:-.035em;color:#0f1445}
h1 em{font-style:normal;box-shadow:inset 0 -14px 0 #e8b800}
.ln{margin:22px 0 0;font-size:18px;line-height:1.55;color:#475569;max-width:440px}
'''

# ---------- SA: S1's light side, the dock drawn big ----------
sa_css = SBASE + '''
.pg{display:grid;grid-template-columns:840px 600px}
.lf{position:relative;overflow:hidden;background:#f3f5f9;border-right:1px solid #e2e8f0}
.lf .slk{position:absolute;left:64px;top:40px}
.cp{position:absolute;left:64px;top:132px}
.lf .dep{position:absolute;left:-64px;bottom:-4px;width:900px;height:515px}
.rt{background:#fff;display:flex;align-items:center;justify-content:center}
''' + RM
sa_body = f'''<div class="pg"><div class="lf">{SLOGO}<div class="cp"><h1>{HEAD}</h1><p class="ln">{LINE}</p></div>{one_zone(0, line=True)}</div>
<div class="rt">{form()}</div></div>'''
write('R44SignDock.dc.html', page('Sign in, light side with the dock drawn big', sa_css, sa_body))

# ---------- SB: type and the mark, facts along the bottom ----------
sb_css = SBASE + '''
.pg{background:#f3f5f9}
.mk{position:absolute;left:470px;top:150px;height:520px;fill:none;stroke:#0f1445;stroke-opacity:.07;stroke-width:2}
.pg>.slk{position:absolute;left:120px;top:40px}
.cp{position:absolute;left:120px;top:150px}
h1{font-size:96px;letter-spacing:-.045em}
.card{position:absolute;right:120px;top:120px;background:#fff;border-radius:24px;padding:44px 48px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 18px 48px rgba(15,23,42,.10)}
.facts{position:absolute;left:120px;right:120px;bottom:48px;display:grid;grid-template-columns:repeat(3,1fr);gap:32px;border-top:1px solid #d5dbe6;padding-top:22px}
.facts b{display:block;font:600 30px "IBM Plex Mono",monospace;color:#0f1445}
.facts span{display:block;margin-top:6px;font-size:14px;line-height:1.5;color:#475569}
'''
sb_body = f'''<div class="pg"><svg class="mk" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>{SLOGO}
<div class="cp"><h1>Operations<br><em>Workspace</em></h1><p class="ln">{LINE}</p></div>
<div class="card">{form()}</div>
<div class="facts"><div><b>2018</b><span>On the road since, moving homes, offices and cargo</span></div><div><b>3 garages</b><span>Marikina, Sta. Rosa and Pulilan</span></div><div><b>1 account</b><span>For bookings, maintenance and repairs</span></div></div></div>'''
write('R44SignType.dc.html', page('Sign in, type and the mark, facts along the bottom', sb_css, sb_body))

# ---------- SC: centred card above the whole depot ----------
sc_css = SBASE + '''
.pg{background:#f3f5f9}
.mid{position:absolute;left:0;right:0;top:44px;display:flex;flex-direction:column;align-items:center}
.ttl{margin:26px 0 0;font-size:15px;color:#475569}
.card{margin-top:22px;background:#fff;border-radius:24px;padding:36px 40px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 18px 48px rgba(15,23,42,.10);position:relative;z-index:2}
.pg>.dep{position:absolute;left:0;bottom:0;width:1440px;height:264px}
'''
sc_body = f'''<div class="pg"><div class="mid">{SLOGO}<p class="ttl">Operations Workspace</p><div class="card">{form()}</div></div>
{depot(line=True)}</div>'''
write('R44SignCentre.dc.html', page('Sign in, centred card above the whole depot', sc_css, sc_body))

# ---------- SD: a look at the workspace ----------
sd_css = SBASE + '''
.pg{display:grid;grid-template-columns:840px 600px}
.lf{position:relative;overflow:hidden;background:#f3f5f9;border-right:1px solid #e2e8f0}
.lf .slk{position:absolute;left:64px;top:40px}
.cp{position:absolute;left:64px;top:120px}
h1{font-size:56px}
.ln{margin-top:18px}
.rt{background:#fff;display:flex;align-items:center;justify-content:center}
.shot{position:absolute;left:64px;top:470px;width:1200px;height:700px;transform:scale(.62);transform-origin:0 0;border-radius:22px;overflow:hidden;background:#f3f5f9;box-shadow:0 0 0 1px #dfe3ee,0 30px 60px rgba(15,20,69,.18)}
.shot .band{height:330px;background:#0f1445;position:relative;padding:28px 48px;color:#fff}
.shot .band .dep{position:absolute;left:0;bottom:0;width:1200px;height:220px}
.shot .h{font-size:34px;font-weight:800;letter-spacing:-.03em}
.shot .d{font-size:13px;font-weight:600;color:#e8b800;margin-bottom:6px}
.shot .cs{display:grid;grid-template-columns:repeat(3,384px);gap:24px;padding:0}
.shot .c{background:#fff;height:200px;border-radius:0 0 18px 18px;padding:20px 24px;box-shadow:0 1px 2px rgba(15,23,42,.06)}
.shot .c b{display:block;font-size:22px;font-weight:800;color:#0f1445;letter-spacing:-.02em}
.shot .c i{display:block;height:10px;border-radius:5px;background:#e6e9f1;margin-top:14px;width:70%}
.shot .c i+i{width:52%}
''' + RM
sd_body = f'''<div class="pg"><div class="lf">{SLOGO}<div class="cp"><h1>{HEAD}</h1><p class="ln">{LINE}</p></div>
<div class="shot" aria-hidden="true"><div class="band"><div class="d">Today</div><div class="h">Good morning</div>{depot(passing=False)}</div>
<div class="cs"><div class="c"><b>Bookings</b><i></i><i></i></div><div class="c"><b>Maintenance</b><i></i><i></i></div><div class="c"><b>Repairs</b><i></i><i></i></div></div></div></div>
<div class="rt">{form()}</div></div>'''
write('R44SignPreview.dc.html', page('Sign in, a look at the workspace', sd_css, sd_body))

# ---------- SE: the band on top, like the launcher ----------
se_css = SBASE + '''
.band{background:#0f1445;color:#fff;height:392px;position:relative;overflow:hidden}
.band .dep{position:absolute;left:0;bottom:0;width:1200px;height:220px}
.band .slk{color:#fff;height:64px}.band .slk svg{fill:#e8b800}
.band h1{color:#fff;font-size:44px;line-height:1.05;margin-top:24px}
.band h1 em{box-shadow:none;color:#e8b800}
.below{display:grid;grid-template-columns:432px 1fr;gap:72px;margin-top:-16px;position:relative;z-index:2}
.card{background:#fff;border-radius:24px;padding:32px 24px 28px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 18px 48px rgba(15,23,42,.12)}
.card .fm{width:384px}
.side{padding-top:56px}
.side p{margin:0;font-size:18px;line-height:1.55;color:#334155;max-width:520px}
.side ul{margin:28px 0 0;padding:0;list-style:none;display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.side li{border-top:1px solid #d5dbe6;padding-top:14px;font-size:14px;color:#475569;line-height:1.5}
.side li b{display:block;font-size:16px;color:#0f172a;margin-bottom:4px}
.top{height:64px;display:flex;align-items:center}
''' + RM
se_body = f'''<div class="pg"><div class="band"><div class="wrap" style="height:100%"><div class="top">{SLOGO}</div>
<h1>WeLinc Logistics <em>Operations</em> Workspace</h1>{depot()}</div></div>
<div class="wrap below"><div class="card">{form()}</div>
<div class="side"><p>{LINE}</p><ul><li><b>Bookings</b>Trips, job orders, drivers and helpers</li><li><b>Maintenance</b>Each truck on its service schedule</li><li><b>Repairs</b>Tickets, mechanics and parts</li></ul></div></div></div>'''
write('R44SignBand.dc.html', page('Sign in, the band on top like the launcher', se_css, se_body))

# ---------- SF: on the road since 2018, the fleet parked ----------
sf_css = SBASE + '''
.pg{display:grid;grid-template-columns:840px 600px}
.lf{position:relative;overflow:hidden;background:#f3f5f9;border-right:1px solid #e2e8f0}
.lf .slk{position:absolute;left:64px;top:40px}
.cp{position:absolute;left:64px;top:132px}
.facts{position:absolute;left:64px;top:420px;display:flex;gap:44px}
.facts b{display:block;font:600 44px "IBM Plex Mono",monospace;color:#0f1445;line-height:1}
.facts span{display:block;margin-top:10px;font-size:14px;line-height:1.45;color:#475569;max-width:170px}
.fleet{position:absolute;left:0;bottom:0;width:840px;height:200px}
.rt{background:#fff;display:flex;align-items:center;justify-content:center}
.puff{animation:puff 2.4s ease-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes puff{0%{opacity:0;transform:translate(0,0) scale(.4)}20%{opacity:.5}100%{opacity:0;transform:translate(-30px,-20px) scale(1.6)}}
''' + RM
sf_body = f'''<div class="pg"><div class="lf">{SLOGO}<div class="cp"><h1>On the road<br><em>since 2018.</em></h1><p class="ln">The WeLinc Logistics operations workspace: bookings, maintenance and repairs.</p></div>
<div class="facts"><div><b>3</b><span>garages: Marikina, Sta. Rosa and Pulilan</span></div><div><b>3</b><span>kinds of truck, from the L300 to the 14 ft six wheeler</span></div><div><b>1</b><span>account for all of your work</span></div></div>
<svg class="fleet" viewBox="0 0 840 200" aria-hidden="true"><defs>{V_L300}{V_VAN}{V_WING}</defs>
<rect x="0" y="168" width="840" height="32" fill="#e6e9f1"/><path d="M0 168H840" stroke="#c7cde0"/>
<g fill="#000" opacity=".12"><ellipse cx="128" cy="170" rx="70" ry="4"/><ellipse cx="370" cy="170" rx="96" ry="5"/><ellipse cx="664" cy="170" rx="122" ry="5"/></g>
<use href="#l300" x="64" y="98" width="134" height="70"/>
<use href="#van" x="268" y="88" width="206" height="84"/>
<use href="#wing" x="540" y="72" width="254" height="96"/>
<circle class="puff" cx="537" cy="148" r="5" fill="#aab2c5"/>
</svg></div>
<div class="rt">{form()}</div></div>'''
write('R44SignFleet.dc.html', page('Sign in, on the road since 2018, the fleet parked', sf_css, sf_body))
print('sign in ok')

"""Launcher boards L1, L2, L6, L7, L8 (Corazon Villareal, three systems)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parts import *  # noqa

OUT = Path(sys.argv[1])
RM = '@media (prefers-reduced-motion:reduce){*{animation:none!important}}'


def write(name, html):
    (OUT / name).write_text(html)


# ---------- L1: slim header, each card shows its work ----------
ART = {
    'BMS': '''<svg class="art-s" viewBox="0 0 384 188" aria-hidden="true" fill="none" stroke="#1a1f6e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<g stroke-opacity=".07" stroke-width="1"><path d="M0 47H384M0 94H384M0 141H384M64 0V188M128 0V188M192 0V188M256 0V188M320 0V188"/></g>
<path d="M44 150V116l26-18 26 18v34z" fill="#fff"/><path d="M60 150v-18h20v18"/>
<path d="M98 136C170 136 180 66 250 66H300" stroke-dasharray="2 8" stroke-opacity=".45"/>
<path d="M300 66C326 66 326 86 300 86H252C186 86 176 146 98 148" stroke-dasharray="2 8" stroke-opacity=".45"/>
<path d="M314 70c-9-10-13-16-13-23a13 13 0 0 1 26 0c0 7-4 13-13 23z" fill="#fff"/><circle cx="314" cy="47" r="4" fill="#e8b800" stroke="none"/>
</svg>
<div class="trip">''' + VAN_TOP + '</div>',
    'VMMS': '''<svg class="art-s" viewBox="0 0 384 188" aria-hidden="true" fill="none" stroke="#1a1f6e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<g><rect x="72" y="22" width="28" height="28" rx="6" fill="#fff"/><rect x="108" y="22" width="28" height="28" rx="6" fill="#fff"/><rect x="144" y="22" width="28" height="28" rx="6" fill="#fff"/><rect x="180" y="22" width="28" height="28" rx="6" fill="#fff"/>
<rect class="today" x="216" y="22" width="28" height="28" rx="6" fill="#fff" stroke="#e8b800" stroke-width="2.5"/>
<rect x="252" y="22" width="28" height="28" rx="6" fill="#fff" stroke-opacity=".3"/><rect x="288" y="22" width="28" height="28" rx="6" fill="#fff" stroke-opacity=".3"/>
<path d="M79 36l5 5 9-9M115 36l5 5 9-9M151 36l5 5 9-9M187 36l5 5 9-9"/></g>
<rect x="78" y="78" width="170" height="66" rx="4" fill="#fff"/>
<path d="M252 98h32l24 24v22h-56z" fill="#fff"/><path d="M260 106h20l16 16h-36z"/>
<circle cx="116" cy="152" r="13" fill="#eef0f8"/><circle cx="116" cy="152" r="4"/>
<circle cx="150" cy="152" r="13" fill="#eef0f8"/><circle cx="150" cy="152" r="4"/>
<circle cx="282" cy="152" r="13" fill="#eef0f8"/><circle cx="282" cy="152" r="4"/>
<path d="M40 166H344" stroke-opacity=".2"/>
</svg>''',
    'VRMS': '''<svg class="art-s" viewBox="0 0 384 188" aria-hidden="true" fill="none" stroke="#1a1f6e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path class="cone" d="M182 58 L118 156 H266 L202 58z" fill="#e8b800" fill-opacity=".16" stroke="none"/>
<path d="M66 172V34M318 172V34M58 34h268"/>
<path d="M192 34v14"/><path d="M178 58h28l-6-10h-16z" fill="#fff"/>
<rect x="100" y="82" width="130" height="50" rx="4" fill="#fff"/>
<path d="M234 98h26l20 20v14h-46z" fill="#fff"/><path d="M240 104h16l14 14h-30z"/>
<circle cx="130" cy="140" r="11" fill="#eef0f8"/><circle cx="158" cy="140" r="11" fill="#eef0f8"/><circle cx="256" cy="140" r="11" fill="#eef0f8"/>
<path d="M88 156h208" stroke="#e8b800" stroke-width="3"/><path d="M118 156v16M266 156v16"/>
<path d="M40 172H344" stroke-opacity=".2"/>
</svg>''',
}

l1_css = BASE + '''
.band{height:200px}
.gr{padding-top:20px}
h1{font-size:40px}
.mk{position:absolute;right:120px;top:52px;height:120px;fill:rgba(255,255,255,.05)}
.main{margin-top:28px}
.card{padding-top:0;min-height:0}
.ds{margin-bottom:18px}
.art{position:relative;display:block;height:188px;margin:0 -24px 20px;border-radius:24px 24px 0 0;background:#eef0f8;overflow:hidden}
.art-s{position:absolute;inset:0;width:384px;height:188px}
.trip{position:absolute;left:0;top:0;width:22px;height:11px;offset-path:path('M98 136C170 136 180 66 250 66H300C326 66 326 86 300 86H252C186 86 176 146 98 148');offset-rotate:auto;animation:trip 9s linear infinite}
.trip .van{display:block;width:22px;height:11px;filter:drop-shadow(0 1px 1px rgba(15,20,69,.4))}
.trip .van rect:first-child{fill:#fff;stroke:#1a1f6e;stroke-width:1}
@keyframes trip{0%{offset-distance:0%;opacity:0}6%{opacity:1}94%{opacity:1}100%{offset-distance:100%;opacity:0}}
.today{animation:today 2.4s ease-in-out infinite}
@keyframes today{0%,100%{stroke-opacity:1}50%{stroke-opacity:.35}}
.cone{animation:cone 4s ease-in-out infinite}
@keyframes cone{0%,100%{opacity:1}50%{opacity:.6}}
''' + RM


def card_art(code, role, name, desc, ic):
    return card(code, role, name, desc, ic, extra=f'<span class="art">{ART[code]}</span>')


l1_body = f'''<div class="pg">
<div class="band">
<svg class="mk" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>
{topbar()}
{greeting(br=False)}
</div>
<main class="main"><ul class="cards">{''.join(card_art(*s) for s in SYSTEMS)}</ul></main>
</div>'''
write('LauScenes.dc.html', page('Launcher, slim header, each card shows its work', l1_css, l1_body))


# ---------- L2: light band, line drawing (no livery colours) ----------
l2_css = BASE + '''
.band{height:400px;background:#fff;color:#0f1445;box-shadow:inset 0 -1px 0 #e2e8f0}
.lk svg{fill:#0f1445}
.av{background:#eef0f8;box-shadow:inset 0 0 0 1px #dfe3ee}
.gr{padding-top:56px}
.dt{color:#1a1f6e}
.l{color:#475569}
.art{position:absolute;right:0;bottom:0;width:760px;height:336px}
''' + RM

LINE_VAN = '''<svg class="art" viewBox="0 0 760 336" aria-hidden="true" fill="none" stroke="#0f1445" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round">
<g opacity=".16"><path d="M0 300H760"/><path d="M40 320h60M150 320h60M260 320h60M370 320h60M480 320h60M590 320h60M700 320h60" stroke-width="3"/></g>
<g transform="translate(196 92) scale(1.02)">
<rect x="0" y="0" width="330" height="150" rx="6"/>
<g transform="translate(22 22) scale(.16)" fill="#e8b800" stroke="none">''' + LOGO_POLY + '''</g>
<path d="M0 118h330" opacity=".35"/>
<path d="M342 40h66l46 48v64H342z"/>
<path d="M356 54h46l30 32h-76z"/>
<path d="M342 118h112" opacity=".35"/>
<rect x="300" y="150" width="160" height="14" rx="3"/>
<path d="M-14 106v46"/>
<circle cx="64" cy="176" r="26" fill="#fff"/><circle cx="64" cy="176" r="10"/>
<circle cx="132" cy="176" r="26" fill="#fff"/><circle cx="132" cy="176" r="10"/>
<circle cx="410" cy="176" r="26" fill="#fff"/><circle cx="410" cy="176" r="10"/>
<path d="M454 96h10v18h-10" stroke="#e8b800"/>
</g>
</svg>'''

l2_body = f'''<div class="pg">
<div class="band">
{LINE_VAN}
{topbar()}
{greeting()}
</div>
<main class="main">{cards()}</main>
</div>'''
write('LauLivery.dc.html', page('Launcher, light band with a line drawing', l2_css, l2_body))


# ---------- L6: the fleet parked in bays ----------
l6_css = BASE + '''
.band{height:400px}
.gr{padding-top:56px}
''' + SCENE_CSS + '''
.lamp{animation:lamp 5s ease-in-out infinite}
.lamp.b{animation-delay:-1.7s}.lamp.c{animation-delay:-3.3s}
@keyframes lamp{0%,100%{opacity:1}50%{opacity:.7}}
''' + RM

LINEUP = f'''<svg class="sc" viewBox="0 0 760 336" aria-hidden="true">
<defs>{V_VAN}{V_L300}{V_WING}<linearGradient id="cone" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8b800" stop-opacity=".16"/><stop offset="1" stop-color="#e8b800" stop-opacity="0"/></linearGradient></defs>
<rect x="8" y="58" width="752" height="236" fill="#10164d"/>
<g class="lamp"><path d="M98 66 L40 294 H192 L134 66z" fill="url(#cone)"/></g>
<g class="lamp b"><path d="M323 66 L250 294 H432 L359 66z" fill="url(#cone)"/></g>
<g class="lamp c"><path d="M590 66 L500 294 H716 L626 66z" fill="url(#cone)"/></g>
<rect x="0" y="40" width="760" height="18" fill="#1a2263"/>
<g fill="#cbd2ea" opacity=".55"><rect x="102" y="58" width="28" height="8" rx="2"/><rect x="327" y="58" width="28" height="8" rx="2"/><rect x="594" y="58" width="28" height="8" rx="2"/></g>
<g fill="#141a55"><rect x="8" y="58" width="12" height="236"/><rect x="212" y="58" width="10" height="236"/><rect x="462" y="58" width="10" height="236"/><rect x="748" y="58" width="12" height="236"/></g>
<rect x="0" y="294" width="760" height="42" fill="#0a0d36"/>
<g fill="#cbd2ea" opacity=".3"><rect x="214" y="294" width="6" height="42"/><rect x="464" y="294" width="6" height="42"/></g>
<g fill="#000" opacity=".35"><ellipse cx="116" cy="296" rx="72" ry="5"/><ellipse cx="341" cy="296" rx="100" ry="6"/><ellipse cx="608" cy="296" rx="124" ry="6"/></g>
<use href="#l300" x="46" y="226" width="139" height="72"/>
<use href="#van" x="241" y="217" width="200" height="81"/>
<use href="#wing" x="484" y="206" width="249" height="93"/>
<g fill="#cbd2ea"><circle class="puff" cx="244" cy="268" r="5"/><circle class="puff b" cx="244" cy="268" r="5"/><circle class="puff c" cx="244" cy="268" r="5"/></g>
</svg>'''

l6_body = f'''<div class="pg">
<div class="band">
{LINEUP}
{topbar()}
{greeting()}
</div>
<main class="main">{cards()}</main>
</div>'''
write('LauLineup.dc.html', page('Launcher, the fleet parked in bays', l6_css, l6_body))


# ---------- L7: one trip, out and back ----------
ROUTE = 'M120 252 C260 252 300 150 420 128 C520 110 590 88 640 100 C680 110 676 146 636 150 C560 158 480 172 410 210 C340 248 250 270 120 266 C100 265 100 252 120 252'
l7_css = BASE + f'''
.band{{height:400px}}
.gr{{padding-top:56px}}
.map{{position:absolute;right:0;bottom:0;width:760px;height:336px}}
.map svg.bg{{position:absolute;inset:0}}
.mv{{position:absolute;left:0;top:0;width:34px;height:16px;offset-path:path('{ROUTE}');offset-rotate:auto;animation:trip 12s linear infinite}}
.mv .van{{display:block;width:34px;height:16px}}
@keyframes trip{{from{{offset-distance:0%}}to{{offset-distance:100%}}}}
.trail{{stroke-dasharray:120 1400;animation:trail 12s linear infinite}}
@keyframes trail{{from{{stroke-dashoffset:120}}to{{stroke-dashoffset:-1280}}}}
.stop{{animation:stop 12s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
@keyframes stop{{0%,36%,56%,100%{{opacity:.55}}44%,48%{{opacity:1}}}}
''' + RM

l7_body = f'''<div class="pg">
<div class="band">
<div class="map">
<svg class="bg" width="760" height="336" viewBox="0 0 760 336" aria-hidden="true" fill="none">
<g stroke="#fff" stroke-opacity=".05"><path d="M0 64H760M0 144H760M0 224H760M0 304H760M100 0V336M260 0V336M420 0V336M580 0V336M740 0V336"/></g>
<path d="{ROUTE}" stroke="#fff" stroke-opacity=".3" stroke-width="3" stroke-dasharray="2 10" stroke-linecap="round"/>
<path class="trail" pathLength="1400" d="{ROUTE}" stroke="#e8b800" stroke-width="4" stroke-linecap="round"/>
<g transform="translate(62 222) scale(1.3)"><path d="M0 18 L22 4 L44 18 V44 H0 Z" fill="#1a2263" stroke="#8ca0f0" stroke-opacity=".5"/><rect x="12" y="26" width="20" height="18" fill="#060828"/><path d="M12 30h20M12 35h20" stroke="#2a3290"/></g>
<g class="stop"><circle cx="660" cy="124" r="8" fill="#0f1445" stroke="#e8b800" stroke-width="2.5"/></g>
</svg>
<div class="mv">{VAN_TOP}</div>
</div>
{topbar()}
{greeting()}
</div>
<main class="main">{cards()}</main>
</div>'''
write('LauRoute.dc.html', page('Launcher, one trip out and back', l7_css, l7_body))


# ---------- L8: no band, gold hairline ----------
l8_css = BASE + '''
.pg{background:#f7f8fb}
.band{background:none;color:#0f1445;overflow:visible}
.lk svg{fill:#0f1445}
.av{background:#eef0f8;box-shadow:inset 0 0 0 1px #dfe3ee}
.gr{padding-top:64px;padding-bottom:40px}
.dt{color:#1a1f6e}
h1{font-size:56px}
.l{color:#475569}
.rule{width:1200px;height:2px;margin:0 auto;background:#e8b800}
.main{margin-top:40px}
.card{box-shadow:0 0 0 1px #e2e8f0}
'''

l8_body = f'''<div class="pg">
<div class="band">
{topbar()}
{greeting(br=False)}
</div>
<div class="rule"></div>
<main class="main">{cards()}</main>
</div>'''
write('LauWhite.dc.html', page('Launcher, no band, a gold hairline', l8_css, l8_body))
print('ok')

"""Round 52 (Nov 25, late night): no road, no vehicles. Navbars in the N1 family (a slim bar, the greeting on the page)
and the N3 family (a taller band at the top holding the greeting); grids G1 and G2 only, for Corazon and for an admin.
No line under the greeting; systems without a role are not shown; nothing is called "apps".
python3 -I gen52.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g  # noqa: E402
from data49 import board, CORAZON, FELICIDAD, DATE  # noqa: E402
from parts import LOGO_POLY  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}


def reg(fn):
    BOARDS[fn.__name__] = fn
    return fn


D = DATE.upper()
HINT = '<p>Open one to start. You stay signed in to all of them.</p>'

# ---------------------------------------------------------------- page greeting (N1 family)
PAGE_GREET = '''.pt{padding-top:36px}
.pt>.dt{margin:0;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.06em;color:#7a8597}
.pt h1{margin:6px 0 0;font-size:36px;line-height:1.1;font-weight:800;letter-spacing:-.03em;color:#0f1445}
.pt .hd{margin-top:30px}'''


def page_greet(first, date=True):
    dt = f'<p class="dt">{D}</p>' if date else ''
    return f'<div class="w pt">{dt}<h1>Good morning, {first}</h1>'


# ---------------------------------------------------------------- navbars
def A_plain(first):
    css = '.na{background:#0f1445;color:#fff}\n' + PAGE_GREET
    return css, f'<header class="na"><div class="w">{{ROW}}</div></header>' + page_greet(first)


def B_edge(first):
    css = '''.nb{background:#0f1445;color:#fff;box-shadow:inset 0 -3px 0 #e8b800}
.nb .row{height:68px}''' + PAGE_GREET
    return css, f'<header class="nb"><div class="w">{{ROW_DATE}}</div></header>' + page_greet(first, date=False)


def C_inbar(first):
    """The greeting sits in the bar itself; the page starts straight with the systems."""
    css = '''.nc{background:#0f1445;color:#fff}
.nc .row{height:84px}
.nc .gx{display:flex;flex-direction:column;gap:3px;padding-left:20px;margin-left:6px;border-left:1px solid rgba(255,255,255,.16)}
.nc .gx span{font:600 11px "IBM Plex Mono",monospace;letter-spacing:.06em;color:#e8b800}
.nc .gx strong{font-size:19px;font-weight:700;letter-spacing:-.015em}
.nc .lk em{display:none}
.below{padding-top:36px}'''
    gx = f'<div class="gx"><span>{D}</span><strong>Good morning, {first}</strong></div>'
    return css, f'<header class="nc"><div class="w">{{ROW_GX:{gx}}}</div></header><div class="w below">'


BAND = '''.nd3{position:relative;height:184px;background:#0f1445;color:#fff;overflow:hidden}
.nd3 .gr{position:relative;z-index:2;padding-top:24px}
.nd3 .gr .dt{margin:0;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.06em;color:#e8b800}
.nd3 h1{margin:8px 0 0;font-size:38px;line-height:1.05;font-weight:800;letter-spacing:-.03em}
.nd3 .row{position:relative;z-index:3}
.below{padding-top:34px}'''


def band(first, art=''):
    return (f'<header class="nd3">{art}<div class="w">{{ROW}}<div class="gr"><p class="dt">{D}</p>'
            f'<h1>Good morning, {first}</h1></div></div></header><div class="w below">')


def D_band(first):
    return BAND, band(first)


def E_mark(first):
    """The WeLinc mark, oversized and faint, cropped by the band's right edge."""
    css = BAND + '''.nd3 .mk{position:absolute;right:calc(50% - 720px);top:-40px;height:300px;fill:rgba(255,255,255,.045)}
.nd3 .mk2{position:absolute;right:calc(50% - 600px);bottom:26px;height:14px;fill:#e8b800;opacity:.9}'''
    art = f'<svg class="mk" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>'
    return css, band(first, art)


def F_garages(first):
    """The three garages as a still outline on the right; nothing moves."""
    css = BAND + '''.nd3 .gs{position:absolute;right:calc(50% - 600px);bottom:0;width:560px;height:120px}'''
    gs = ''
    for i, (x, name) in enumerate([(0, 'MARIKINA'), (200, 'STA. ROSA'), (400, 'PULILAN')]):
        gs += (f'<g transform="translate({x} 0)"><path d="M10 120V62l70-26 70 26v58" fill="none" stroke="rgba(255,255,255,.18)" stroke-width="1.5"/>'
               f'<path d="M42 120V76h76v44" fill="none" stroke="rgba(255,255,255,.14)" stroke-width="1.5"/>'
               f'<path d="M42 84h76M42 92h76M42 100h76" stroke="rgba(255,255,255,.08)"/>'
               f'<text x="80" y="58" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="10" font-weight="600" letter-spacing=".08em" fill="rgba(255,255,255,.42)">{name}</text></g>')
    art = f'<svg class="gs" viewBox="0 0 560 120" aria-hidden="true">{gs}<path d="M0 119.5H560" stroke="rgba(255,255,255,.18)"/></svg>'
    return css, band(first, art)


# ---------------------------------------------------------------- grids
def g1(people, suite=False):
    css = '''.grp{display:grid;grid-template-columns:repeat(4,282px);gap:24px}
.grp>a{grid-row:2}
.gl{grid-row:1;font:600 11px "IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase;color:#7a8597;margin:0 0 -10px}
.tl.su{background:#0f1445;box-shadow:0 14px 30px -12px rgba(15,20,69,.5)}
.tl.su b,.tl.su .nm{color:#fff}.tl.su .ln,.tl.su .rl{color:rgba(255,255,255,.7)}.tl.su .rl strong{color:#e8b800}'''
    n = len(people)
    tiles = ''.join(g.tile(s, 'bare') for s in people)
    if suite:
        su = (f'<a class="tl su" href="#">{g.app_icon("Suite", 52, "bareDark")}<b>Suite</b><span class="nm">Suite management</span>'
              f'<span class="ln">People, roles and access for VMMS and VRMS</span><span class="rl"><strong>4 to review</strong></span></a>')
        body = (f'<div class="hd"><h2>Your systems</h2><span>{n}</span>{HINT}</div>'
                f'<div class="grp"><p class="gl" style="grid-column:1/{n + 1}">Systems</p><p class="gl">Admin</p>{tiles}{su}</div>')
    else:
        body = f'<div class="hd"><h2>Your systems</h2><span>{n}</span>{HINT}</div><div class="tiles">{tiles}</div>'
    return css, body


def g2(people, suite=False):
    css, _ = g.G2()
    css += '''.ac.su{background:#0f1445;box-shadow:0 14px 30px -12px rgba(15,20,69,.5)}
.ac.su b,.ac.su .nm{color:#fff}.ac.su .ln,.ac.su .t span{color:rgba(255,255,255,.7)}.ac.su .t span{color:#e8b800;font-weight:600}'''
    cards = ''.join(f'<a class="ac" href="#">{g.app_icon(s["code"], 64, "bare")}<span class="t"><b>{s["code"]}</b><span>{s["role"]}</span></span>'
                    f'<span class="nm">{s["name"]}</span><span class="ln">{s["line"]}</span></a>' for s in people)
    if suite:
        cards += (f'<a class="ac su" href="#">{g.app_icon("Suite", 64, "bareDark")}<span class="t"><b>Suite</b><span>4 to review</span></span>'
                  f'<span class="nm">Suite management</span><span class="ln">People, roles and access for VMMS and VRMS</span></a>')
    return css, f'<div class="hd"><h2>Your systems</h2><span>{len(people)}</span>{HINT}</div><div class="cards">{cards}</div>'


# ---------------------------------------------------------------- the bottom of the page
BOTTOM_CSS = {
    'panel': '''.bt{position:absolute;left:0;right:0;bottom:0;background:#e9ecf3;border-top:1px solid #dfe3ec}
.bt .cols{display:grid;grid-template-columns:repeat(3,1fr);gap:48px;padding:28px 0 22px}
.bt h3{margin:0;display:flex;align-items:center;gap:8px;font-size:13px;font-weight:700;color:#0f172a}
.bt h3 svg{color:#5b6779}
.bt p{margin:6px 0 0;font-size:13px;line-height:1.55;color:#5b6779}
.bt .ft{display:flex;justify-content:space-between;padding:14px 0 18px;border-top:1px solid #dfe3ec;font-size:12px;color:#7a8597}''',
    'outline': '''.bt{position:absolute;left:0;right:0;bottom:0;height:230px}
.bt svg{position:absolute;left:50%;bottom:0;width:1440px;height:230px;transform:translateX(-50%)}
.bt .w{position:static}
.bt .ft{position:absolute;left:50%;width:1200px;margin-left:-600px;bottom:8px;display:flex;justify-content:space-between;font-size:12px;color:#7a8597}''',
}


def bottom(kind, name):
    ft = '<div class="ft"><span>WeLinc Logistics · Since 2018</span><span>Privacy · Terms</span></div>'
    if kind == 'panel':
        cols = [(g.I['shield'], 'Signed in as ' + name, 'Last sign in: Tuesday, Nov 24, 6:12 PM, Chrome on Windows. Not you? Change your password from the account menu.'),
                (g.I['key'], 'Missing a system?', 'Each system\'s admin gives its roles. Ask them for one, then sign in again to see it here.'),
                (g.I['users'], 'Need help?', 'IT desk, local 214. Monday to Saturday, 7 AM to 7 PM.')]
        c = ''.join(f'<div><h3>{g.ic(i, 16, 2)}{h}</h3><p>{t}</p></div>' for i, h, t in cols)
        return f'<div class="bt"><div class="w"><div class="cols">{c}</div>{ft}</div></div>'
    gs = ''
    for x, w, h in [(110, 260, 104), (590, 260, 116), (1070, 260, 104)]:
        roof = 150 - h
        gs += (f'<path d="M{x} 200V{roof + 40}l{w / 2} -{40}l{w / 2} {40}V200" fill="none" stroke="#dfe3ec" stroke-width="1.5"/>'
               f'<path d="M{x + w * .22} 200V{roof + 80}h{w * .56}V200" fill="none" stroke="#e3e7ef" stroke-width="1.5"/>'
               + ''.join(f'<path d="M{x + w * .22} {roof + 80 + k * 12}h{w * .56}" stroke="#e8ebf2"/>' for k in range(1, 6)))
    art = f'<svg viewBox="0 0 1440 230" aria-hidden="true">{gs}<path d="M0 200.5H1440" stroke="#dfe3ec" stroke-width="1.5"/></svg>'
    return f'<div class="bt">{art}<div class="w">{ft}</div></div>'


# ---------------------------------------------------------------- compose
def compose(nav, grid, title, person='C', bot='panel'):
    first, name, ini = ('Corazon', 'Corazon Villareal', 'CV') if person == 'C' else ('Felicidad', 'Felicidad Roxas', 'FR')
    ncss, nopen = nav(first)
    gcss, ghtml = grid
    if '{ROW_GX:' in nopen:
        pre, rest = nopen.split('{ROW_GX:', 1)
        cut = rest.rindex('}')
        nopen = pre + g.nav_row(name, ini, extra=rest[:cut]) + rest[cut + 1:]
    nopen = nopen.replace('{ROW}', g.nav_row(name, ini)).replace('{ROW_DATE}', g.nav_row(name, ini, date=True))
    body = f'<div class="pg">{nopen}{ghtml}</div>{bottom(bot, name)}</div>'
    return title, g.CSS + ncss + gcss + BOTTOM_CSS[bot], body


C, F = CORAZON, FELICIDAD

# navbar page: each navbar over G1 (Corazon)
NAVS = [('R52NavPlain', A_plain, 'N1a · Slim bar at the top, nothing else in it; the greeting on the page'),
        ('R52NavEdge', B_edge, 'N1b · Slim bar with a gold bottom edge and today\'s date in the bar'),
        ('R52NavInBar', C_inbar, 'N1c · The greeting sits in the bar itself; the page starts with the systems'),
        ('R52NavBand', D_band, 'N3a · Navy band at the top holding the greeting, nothing else'),
        ('R52NavMark', E_mark, 'N3b · Navy band with the WeLinc mark, oversized and faint, on the right'),
        ('R52NavGarages', F_garages, 'N3c · Navy band with the three garages as a still outline (nothing moves)')]
for key, fn, t in NAVS:
    BOARDS[key] = (lambda fn=fn, t=t: compose(fn, g1(C), t + '; G1 + B1'))

BOARDS['R52G1Panel'] = lambda: compose(D_band, g1(C), 'G1 + B1 · Tiles; the bottom is a help and account panel; navbar N3a')
BOARDS['R52G2Panel'] = lambda: compose(D_band, g2(C), 'G2 + B1 · Cards; the bottom is a help and account panel; navbar N3a')
BOARDS['R52G1Outline'] = lambda: compose(D_band, g1(C), 'G1 + B2 · Tiles; the three garages as a faint still outline along the bottom; navbar N3a', bot='outline')
BOARDS['R52G2Outline'] = lambda: compose(D_band, g2(C), 'G2 + B2 · Cards; the three garages as a faint still outline along the bottom; navbar N3a', bot='outline')
BOARDS['R52G1Admin'] = lambda: compose(D_band, g1(F, True), 'G1 admin · Felicidad Roxas: her two systems, then Suite management (no BMS: no role); B1', 'F')
BOARDS['R52G2Admin'] = lambda: compose(D_band, g2(F, True), 'G2 admin · Felicidad Roxas: her two systems, then Suite management (no BMS: no role); B1', 'F')

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

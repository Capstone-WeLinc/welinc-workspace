"""Admin launcher boards M1 to M4: Victor Ramos, VRMS Admin, one system plus Suite management."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parts import *  # noqa

OUT = Path(sys.argv[1])
NAME, INIT, FIRST = 'Victor Ramos', 'VR', 'Victor'
VRMS = ('VRMS', 'Admin', 'Vehicle Repair Management System', 'Repair tickets, mechanics and workshop work', I_VRMS)


def write(name, html):
    (OUT / name).write_text(html)


ADM = BASE + '''
.band{height:300px}
.gr{padding-top:48px}
.mk{position:absolute;right:120px;top:96px;height:150px;fill:rgba(255,255,255,.05)}
.main{margin-top:24px}
.panel{background:#fff;border-radius:24px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 6px 20px rgba(15,23,42,.06);box-sizing:border-box}
.wide{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:20px;padding:24px 28px;text-decoration:none;color:inherit}
.wide .tile{width:56px;height:56px}
.wt{display:flex;flex-direction:column;gap:4px}
.wt .hd{gap:10px}
.wt .nm{margin-top:4px}.wt .ds{margin-top:0}
.go{display:inline-flex;align-items:center;gap:8px;height:44px;padding:0 18px;border-radius:12px;background:#0f1445;color:#fff;font-size:15px;font-weight:700}
.sh{flex:none;width:44px;height:44px;border-radius:14px;background:#e6ecfa;color:#1e3a8a;display:grid;place-items:center}
.st{display:flex;flex-direction:column;gap:2px}
.st b{font-size:16px;font-weight:700}
.st span{font-size:13px;color:#5b6779}
.ol{display:inline-flex;align-items:center;gap:8px;height:44px;padding:0 16px;border-radius:12px;border:1px solid #cbd2e0;background:#fff;color:#1a1f6e;font:600 14px Inter,sans-serif;text-decoration:none}
.n{font-family:"IBM Plex Mono",monospace;font-weight:600}
.cnt{min-width:28px;height:24px;padding:0 8px;border-radius:8px;background:#e6ecfa;color:#1e3a8a;display:inline-grid;place-items:center;font-size:13px;box-sizing:border-box}
'''


def band():
    return (f'<div class="band"><svg class="mk" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>'
            f'{topbar(NAME, INIT)}{greeting(FIRST, br=False)}</div>')


def wide_card():
    code, role, name, desc, ic = VRMS
    return (f'<a class="panel wide" href="#"><span class="tile">{icon(ic, 26)}</span>'
            f'<span class="wt"><span class="hd"><span class="code">{code}</span><span class="chip">{role}</span></span>'
            f'<span class="nm">{name}</span><span class="ds">{desc}</span></span>'
            f'<span class="go">Open {code} {ARROW}</span></a>')


SUITE_HEAD = (f'<span class="sh">{icon(I_SHIELD, 22)}</span><span class="st"><b>Suite management</b>'
              f'<span>Users and permissions</span></span>')

# ---------- M1: a row under the card ----------
m1_css = ADM + '''
.stack{display:flex;flex-direction:column;gap:16px}
.strip{display:grid;grid-template-columns:260px repeat(3,minmax(0,1fr)) auto;align-items:center;gap:12px;padding:14px 16px 14px 24px}
.who{display:flex;align-items:center;gap:14px}
.mt{display:flex;align-items:center;gap:12px;height:64px;padding:0 16px;border-radius:16px;background:#f6f7fb;text-decoration:none;color:inherit;box-shadow:inset 0 0 0 1px #eef1f6}
.mt svg{color:#1a1f6e;flex:none}
.mt .v{display:flex;flex-direction:column;line-height:1.2}
.mt .v b{font-size:20px}
.mt .v span{font-size:13px;color:#5b6779}
.mt .v .tl{font-size:14px;font-weight:600;color:#0f172a}
'''


def strip_tile(label, count, ic, line):
    if count is None:
        v = f'<span class="v"><span class="tl">{label}</span><span>{line}</span></span>'
        return f'<a class="mt" href="#">{icon(ic, 20)}{v}</a>'
    v = f'<span class="v"><b class="n">{count}</b><span>{label}</span></span>'
    return f'<a class="mt" href="#" aria-label="{label}: {count}">{icon(ic, 20)}{v}</a>'


m1_body = f'''<div class="pg">
{band()}
<main class="main"><div class="stack">
{wide_card()}
<div class="panel strip"><span class="who">{SUITE_HEAD}</span>{''.join(strip_tile(*t) for t in TILES)}<a class="ol" href="#">Open {icon(I_RIGHT, 16)}</a></div>
</div></main>
</div>'''
write('AdmStrip.dc.html', page('Admin launcher, Suite management as a row under the card', m1_css, m1_body))

# ---------- M2: beside the system ----------
m2_css = ADM + '''
.two{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}
.sys{display:flex;flex-direction:column;padding:28px;text-decoration:none;color:inherit;min-height:332px}
.sys .tile{width:56px;height:56px}
.sys .nm{margin-top:20px;font-size:16px}
.sys .ds{font-size:14px}
.sys .bt{margin-top:auto;display:flex;justify-content:flex-end}
.su{display:flex;flex-direction:column;padding:28px;min-height:332px}
.su .who{display:flex;align-items:center;gap:14px}
.rows{list-style:none;margin:20px 0 0;padding:0}
.rows li+li{border-top:1px solid #eef1f6}
.rw{display:flex;align-items:center;gap:14px;height:56px;text-decoration:none;color:inherit;font-size:15px;font-weight:500}
.rw svg.i{color:#1a1f6e}
.rw .sp{margin-left:auto;display:flex;align-items:center;gap:10px;color:#5b6779;font-size:13px;font-weight:400}
.su .bt{margin-top:auto;display:flex;justify-content:flex-end}
'''


def row(label, count, ic, line):
    right = f'<span class="cnt n">{count}</span>' if count is not None else f'<span>{line}</span>'
    aria = f' aria-label="{label}: {count}"' if count is not None else ''
    ico = icon(ic, 20).replace('<svg ', '<svg class="i" ', 1)
    return (f'<li><a class="rw" href="#"{aria}>{ico}{label}'
            f'<span class="sp">{right}{icon(I_RIGHT, 16)}</span></a></li>')


code, role, name, desc, ic = VRMS
m2_body = f'''<div class="pg">
{band()}
<main class="main"><div class="two">
<a class="panel sys" href="#"><span class="hd"><span class="tile">{icon(ic, 26)}</span><span class="code">{code}</span><span class="chip">{role}</span></span><span class="nm">{name}</span><span class="ds">{desc}</span><span class="bt"><span class="go">Open {code} {ARROW}</span></span></a>
<section class="panel su" aria-label="Suite management"><div class="who">{SUITE_HEAD}</div><ul class="rows">{''.join(row(*t) for t in TILES)}</ul><div class="bt"><a class="ol" href="#">Open Suite management {icon(I_RIGHT, 16)}</a></div></section>
</div></main>
</div>'''
write('AdmColumn.dc.html', page('Admin launcher, Suite management beside the system', m2_css, m2_body))

# ---------- M3: a right column over the band ----------
m3_css = ADM + '''
.lay{display:grid;grid-template-columns:minmax(0,1fr) 384px;gap:24px;align-items:start}
.side{margin-top:-140px;position:relative;z-index:3;padding:24px;display:flex;flex-direction:column}
.side .who{display:flex;align-items:center;gap:14px}
.rows{list-style:none;margin:16px 0 0;padding:0}
.rows li+li{border-top:1px solid #eef1f6}
.rw{display:flex;align-items:center;gap:14px;height:56px;text-decoration:none;color:inherit;font-size:15px;font-weight:500}
.rw svg.i{color:#1a1f6e}
.rw .sp{margin-left:auto;display:flex;align-items:center;gap:10px;color:#5b6779;font-size:13px;font-weight:400}
.side .ol{margin-top:16px;justify-content:center}
.sys{display:flex;flex-direction:column;padding:28px;text-decoration:none;color:inherit}
.sys .tile{width:56px;height:56px}
.sys .nm{margin-top:20px;font-size:16px}
.sys .ds{font-size:14px}
.sys .ft{margin-top:24px;padding-top:16px;font-size:15px}
.mk{display:none}
'''
m3_body = f'''<div class="pg">
{band()}
<main class="main"><div class="lay">
<a class="panel sys" href="#"><span class="hd"><span class="tile">{icon(ic, 26)}</span><span class="code">{code}</span><span class="chip">{role}</span></span><span class="nm">{name}</span><span class="ds">{desc}</span><span class="ft">Open {code} {ARROW}</span></a>
<aside class="panel side" aria-label="Suite management"><div class="who">{SUITE_HEAD}</div><ul class="rows">{''.join(row(*t) for t in TILES)}</ul><a class="ol" href="#">Open Suite management {icon(I_RIGHT, 16)}</a></aside>
</div></main>
</div>'''
write('AdmSide.dc.html', page('Admin launcher, Suite management in a right column', m3_css, m3_body))

# ---------- M4: counts in the band ----------
m4_css = ADM + '''
.band{height:340px}
.gr{padding-top:56px}
.bx{position:absolute;z-index:2;right:120px;top:120px;width:600px}
.bh{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.bh .lb{display:flex;align-items:center;gap:10px;font-size:14px;font-weight:600;color:rgba(255,255,255,.85)}
.bh .lb svg{color:#aebcf2}
.bh a{display:inline-flex;align-items:center;gap:6px;height:44px;padding:0 6px;color:#fff;font-size:14px;font-weight:600;text-decoration:none}
.bt3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.bt{display:flex;flex-direction:column;justify-content:space-between;height:120px;padding:16px 18px;border-radius:16px;background:rgba(255,255,255,.06);box-shadow:inset 0 0 0 1px rgba(255,255,255,.1);color:#fff;text-decoration:none;box-sizing:border-box}
.bt svg{color:rgba(255,255,255,.7)}
.bt b{font-size:34px;line-height:1}
.bt .lbl{font-size:13px;color:rgba(255,255,255,.75)}
.bt .tl{font-size:16px;font-weight:600}
.mk{display:none}
'''


def band_tile(label, count, ic, line):
    if count is None:
        return f'<a class="bt" href="#">{icon(ic, 20)}<span><span class="tl">{label}</span><br><span class="lbl">{line}</span></span></a>'
    return f'<a class="bt" href="#" aria-label="{label}: {count}">{icon(ic, 20)}<span><b class="n">{count}</b><br><span class="lbl">{label}</span></span></a>'


m4_body = f'''<div class="pg">
<div class="band">
{topbar(NAME, INIT)}
{greeting(FIRST, br=False)}
<section class="bx" aria-label="Suite management"><div class="bh"><span class="lb">{icon(I_SHIELD, 18)}Suite management</span><a href="#">Open {icon(I_RIGHT, 16)}</a></div>
<div class="bt3">{''.join(band_tile(*t) for t in TILES)}</div></section>
</div>
<main class="main">{wide_card()}</main>
</div>'''
write('AdmBand.dc.html', page('Admin launcher, Suite management counts in the band', m4_css, m4_body))
print('ok')

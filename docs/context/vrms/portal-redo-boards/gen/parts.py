"""Shared parts for the portal redo boards (launcher, admin, arrival)."""

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=IBM+Plex+Mono:wght@500;600&amp;display=swap">'

LOGO_POLY = '<polygon points="82,0 144,0 66,183 4,183"/><polygon points="177,0 240,0 162,183 100,183"/><polygon points="265,0 328,0 268,140 328,140 328,183 187,183"/>'
LOGO = f'<svg viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>'
ARROW = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
CHEV = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" opacity=".7" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>'


def icon(paths, size=22, sw=2):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths}</svg>')


I_BMS = '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M9 16l2 2 4-4"/>'
I_VMMS = ('<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/>'
          '<path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/>'
          '<circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/>')
I_VRMS = ('<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91'
          'a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>')
I_USERS = ('<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
           '<path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>')
I_USERX = '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="m17 8 5 5M22 8l-5 5"/>'
I_AUDIT = '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>'
I_SHIELD = ('<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 '
            '6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>')
I_RIGHT = '<path d="m9 18 6-6-6-6"/>'

SYSTEMS = [
    ('BMS', 'Operations', 'Booking Management System', 'Bookings, trips and drivers', I_BMS),
    ('VMMS', 'Operations', 'Vehicle Maintenance Management System', 'Maintenance schedules and fleet upkeep', I_VMMS),
    ('VRMS', 'Chief Mechanic', 'Vehicle Repair Management System', 'Repair tickets, mechanics and workshop work', I_VRMS),
]

# Suite management tiles: labels from welinc-web-portal SuiteEntry.tsx; counts are sample values.
TILES = [
    ('Users need a look', '3', I_USERS, None),
    ('Deletion requests', '1', I_USERX, None),
    ('Audit log', None, I_AUDIT, 'Sign ins and changes'),
]

# ---------- vehicles (side view, facing right). Livery colours only on trucks. ----------

V_VAN = '''<symbol id="van" viewBox="-8 -2 138 56">
<rect x="0" y="0" width="92" height="38" rx="2.5" fill="#f7f8fb" stroke="#c9d0de"/>
<path d="M0.5 25 C28 19 60 31 91.5 15 V22 C60 34 28 24 0.5 30 Z" fill="#f29a1f"/>
<path d="M0.5 30 C28 24 60 34 91.5 22 V36 a2 2 0 0 1 -2 2 H2.5 a2 2 0 0 1 -2 -2 Z" fill="#1f5cc4"/>
<g transform="translate(6 6) scale(0.0541)" fill="#e8b800">''' + LOGO_POLY + '''</g>
<text x="26" y="15" font-size="11" font-weight="800" font-style="italic" fill="#0f1445" font-family="Inter,sans-serif">WeLinc</text>
<path d="M95 10h16l13 13v15H95z" fill="#eef1f6" stroke="#c3cad8"/>
<path d="M99 14h10l8 8h-18z" fill="#14205a"/>
<rect x="95" y="30" width="29" height="3" fill="#c3cad8"/>
<rect x="86" y="36" width="38" height="5" fill="#2a2f45"/>
<rect x="-4" y="27" width="4" height="13" rx="1" fill="#8d96ab"/>
<circle cx="16" cy="44" r="7" fill="#11131f"/><circle cx="16" cy="44" r="3" fill="#aab2c5"/>
<circle cx="34" cy="44" r="7" fill="#11131f"/><circle cx="34" cy="44" r="3" fill="#aab2c5"/>
<circle cx="110" cy="44" r="7" fill="#11131f"/><circle cx="110" cy="44" r="3" fill="#aab2c5"/>
<rect x="124" y="24" width="4" height="6" rx="1" fill="#f29a1f"/>
</symbol>'''

V_L300 = '''<symbol id="l300" viewBox="-6 -2 96 50">
<path d="M0 4a4 4 0 0 1 4-4h52l20 17a4 4 0 0 1 1.5 3V34a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2z" fill="#f7f8fb" stroke="#c9d0de"/>
<path d="M58 4l15 13H58z" fill="#14205a"/>
<rect x="45" y="4" width="11" height="12" rx="1.5" fill="#14205a"/>
<path d="M0.5 21H77v5H0.5z" fill="#f29a1f"/>
<path d="M0.5 26H77v8a2 2 0 0 1-2 2H2a1.5 1.5 0 0 1-1.5-1.5z" fill="#1f5cc4"/>
<g transform="translate(4 7) scale(0.035)" fill="#e8b800">''' + LOGO_POLY + '''</g>
<text x="16.5" y="13.5" font-size="7.5" font-weight="800" font-style="italic" fill="#0f1445" font-family="Inter,sans-serif">WeLinc</text>
<rect x="74" y="29" width="7" height="6" rx="1" fill="#2a2f45"/>
<rect x="75" y="20" width="3" height="5" rx="1" fill="#f29a1f"/>
<circle cx="16" cy="38" r="7" fill="#11131f"/><circle cx="16" cy="38" r="3" fill="#aab2c5"/>
<circle cx="62" cy="38" r="7" fill="#11131f"/><circle cx="62" cy="38" r="3" fill="#aab2c5"/>
</symbol>'''

V_WING = '''<symbol id="wing" viewBox="-8 -2 172 64">
<rect x="0" y="0" width="120" height="44" rx="2.5" fill="#f7f8fb" stroke="#c9d0de"/>
<path d="M1 4H119" stroke="#c9d0de"/>
<path d="M0.5 29 C36 22 80 36 119.5 18 V26 C80 40 36 28 0.5 35 Z" fill="#f29a1f"/>
<path d="M0.5 35 C36 28 80 40 119.5 26 V42 a2 2 0 0 1-2 2 H2.5 a2 2 0 0 1-2-2 Z" fill="#1f5cc4"/>
<g transform="translate(7 9) scale(0.066)" fill="#e8b800">''' + LOGO_POLY + '''</g>
<text x="31" y="20" font-size="13" font-weight="800" font-style="italic" fill="#0f1445" font-family="Inter,sans-serif">WeLinc</text>
<path d="M123 12h18l14 14v18h-32z" fill="#eef1f6" stroke="#c3cad8"/>
<path d="M127 16h12l10 10h-22z" fill="#14205a"/>
<rect x="112" y="42" width="46" height="6" fill="#2a2f45"/>
<rect x="-4" y="32" width="4" height="14" rx="1" fill="#8d96ab"/>
<circle cx="18" cy="51" r="8" fill="#11131f"/><circle cx="18" cy="51" r="3.4" fill="#aab2c5"/>
<circle cx="37" cy="51" r="8" fill="#11131f"/><circle cx="37" cy="51" r="3.4" fill="#aab2c5"/>
<circle cx="140" cy="51" r="8" fill="#11131f"/><circle cx="140" cy="51" r="3.4" fill="#aab2c5"/>
<rect x="154" y="28" width="4" height="7" rx="1" fill="#f29a1f"/>
</symbol>'''

# Top-down van for map views (rotates along a path, so it never shows upside down).
VAN_TOP = ('<svg class="van" viewBox="0 0 30 14" aria-hidden="true"><rect x="0" y="0" width="21" height="14" rx="2" fill="#f7f8fb"/>'
           '<rect x="22" y="1" width="8" height="12" rx="2.5" fill="#eef1f6"/><rect x="25" y="2.5" width="3" height="9" rx="1" fill="#14205a"/>'
           '<rect x="2" y="5" width="17" height="1.6" fill="#e8b800"/></svg>')

# ---------- page shell ----------


def page(title, css, body, logic='renderVals() { return {}; }', w=1440, h=900):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
{FONTS}
<style>
body{{margin:0}}
{css}
</style>
</helmet>
{body}
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{w},"height":{h}}}}}'>
class Component extends DCLogic {{
{logic}
}}
</script>
</body>
</html>
'''


# Launcher base CSS: dark band header, cards. Band height and greeting padding vary per board.
BASE = '''.pg{width:1440px;height:900px;background:#f3f5f9;font-family:Inter,system-ui,sans-serif;position:relative;overflow:hidden;color:#0f172a}
.band{position:relative;background:#0f1445;color:#fff;overflow:hidden}
.top{position:relative;z-index:2;height:64px;width:1200px;margin:0 auto;display:flex;align-items:center}
.lk{display:flex;align-items:center;gap:10px}.lk svg{height:20px;fill:#e8b800}.lk span{font-weight:800;font-style:italic;font-size:16px}
.me{margin-left:auto;display:flex;align-items:center;gap:10px;height:44px;padding:0 8px;border-radius:12px;border:0;background:none;color:inherit;font:500 14px Inter,sans-serif;cursor:pointer}
.av{width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.12);box-shadow:inset 0 0 0 1px rgba(255,255,255,.2);display:grid;place-items:center;font-size:12px;font-weight:600}
.gr{position:relative;z-index:2;width:1200px;margin:0 auto}
.dt{margin:0;font-size:13px;font-weight:600;color:#e8b800}
h1{margin:10px 0 0;font-size:48px;line-height:1;font-weight:800;letter-spacing:-.03em}
.l{margin:12px 0 0;font-size:16px;color:rgba(255,255,255,.7)}
.main{width:1200px;margin:24px auto 0}
.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px;list-style:none;margin:0;padding:0}
.cards li{display:flex}
.card{flex:1;display:flex;flex-direction:column;min-height:196px;background:#fff;border-radius:24px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 6px 20px rgba(15,23,42,.06);padding:22px 24px 18px;text-decoration:none;color:inherit;box-sizing:border-box}
.hd{display:flex;align-items:center;gap:14px}
.tile{flex:none;width:48px;height:48px;border-radius:16px;background:#eef0f8;color:#1a1f6e;display:grid;place-items:center}
.code{font-size:20px;font-weight:700}
.chip{font-size:12px;font-weight:500;padding:3px 10px;border-radius:999px;background:#eef1f6;color:#475569;box-shadow:inset 0 0 0 1px #e2e8f0}
.nm{margin-top:14px;font-size:14px;font-weight:500}
.ds{margin-top:4px;font-size:13px;color:#5b6779}
.ft{margin-top:auto;padding-top:12px;border-top:1px solid #eef1f6;display:flex;justify-content:space-between;align-items:center;font-size:14px;font-weight:600;color:#1a1f6e}'''


def topbar(name='Corazon Villareal', initials='CV'):
    return (f'<div class="top"><div class="lk">{LOGO}<span>WeLinc Logistics</span></div>'
            f'<button class="me" type="button" aria-label="Account menu for {name}"><span class="av">{initials}</span>{name}{CHEV}</button></div>')


def greeting(first='Corazon', br=True, line='Pick where you want to work today.'):
    sep = '<br>' if br else ' '
    return f'<div class="gr"><p class="dt">Wednesday, November 25</p><h1>Good morning,{sep}{first}</h1><p class="l">{line}</p></div>'


def card(code, role, name, desc, ic, extra='', li_cls=''):
    cls = f' class="{li_cls}"' if li_cls else ''
    return (f'<li{cls}><a class="card" href="#">{extra}<span class="hd"><span class="tile">{icon(ic)}</span>'
            f'<span class="code">{code}</span><span class="chip">{role}</span></span>'
            f'<span class="nm">{name}</span><span class="ds">{desc}</span>'
            f'<span class="ft">Open {code} {ARROW}</span></a></li>')


def cards(li_cls=''):
    return '<ul class="cards">' + ''.join(card(*s, li_cls=li_cls) for s in SYSTEMS) + '</ul>'


# The garage-and-van band scene (LauVan), 760x336, right side of a 400px band.
def garage_scene(drive=False):
    van = '<use href="#van" x="290" y="135" width="414" height="168"/>'
    puffs = ('<g fill="#cbd2ea"><circle class="puff" cx="302" cy="262" r="6"/><circle class="puff b" cx="302" cy="262" r="6"/>'
             '<circle class="puff c" cx="302" cy="262" r="6"/></g>')
    if drive:
        # Door fully rolled up so the van clears it; the van is clipped to the doorway's left edge.
        door = ('<rect x="84" y="110" width="202" height="184" fill="#060828"/>'
                '<rect x="84" y="110" width="202" height="16" fill="#232a78"/><rect x="84" y="124" width="202" height="4" fill="#3b43a3"/>'
                '<rect class="glow" x="84" y="128" width="202" height="166" fill="#e8b800" opacity=".14"/>')
        vehicle = f'<g clip-path="url(#door)"><g class="drive">{van}{puffs}</g></g>'
        clip = '<clipPath id="door"><rect x="84" y="0" width="676" height="336"/></clipPath>'
    else:
        door = ('<rect x="84" y="110" width="202" height="184" fill="#060828"/>'
                '<rect x="84" y="110" width="202" height="70" fill="#232a78"/>'
                '<g stroke="#141a55" stroke-width="2"><path d="M84 122h202M84 134h202M84 146h202M84 158h202M84 170h202"/></g>'
                '<rect x="84" y="176" width="202" height="5" fill="#3b43a3"/>'
                '<rect class="glow" x="84" y="181" width="202" height="113" fill="#e8b800" opacity=".14"/>')
        vehicle = van + puffs
        clip = ''
    return f'''<svg class="sc" viewBox="0 0 760 336" aria-hidden="true">
<defs>{V_VAN}<linearGradient id="spill" x1="0" x2="1"><stop offset="0" stop-color="#e8b800" stop-opacity=".12"/><stop offset="1" stop-color="#e8b800" stop-opacity="0"/></linearGradient>{clip}</defs>
<rect x="60" y="58" width="250" height="236" fill="#141a55"/>
<rect x="48" y="46" width="274" height="16" fill="#1a2263"/>
{door}
<path d="M286 294 L620 294 L286 200 Z" fill="url(#spill)"/>
<rect x="0" y="294" width="760" height="42" fill="#0a0d36"/>
<g fill="#cbd2ea" opacity=".3"><rect x="330" y="314" width="56" height="4" rx="2"/><rect x="450" y="314" width="56" height="4" rx="2"/><rect x="570" y="314" width="56" height="4" rx="2"/><rect x="690" y="314" width="56" height="4" rx="2"/></g>
<ellipse class="shadow" cx="510" cy="296" rx="200" ry="6" fill="#000" opacity=".35"/>
{vehicle}
</svg>'''


SCENE_CSS = '''.sc{position:absolute;right:0;bottom:0;width:760px;height:336px}
.puff{animation:puff 2.4s ease-out infinite;transform-box:fill-box;transform-origin:center}
.puff.b{animation-delay:.8s}.puff.c{animation-delay:1.6s}
@keyframes puff{0%{opacity:0;transform:translate(0,0) scale(.4)}20%{opacity:.45}100%{opacity:0;transform:translate(-34px,-24px) scale(1.6)}}
.glow{animation:glow 3.2s ease-in-out infinite}
@keyframes glow{0%,100%{opacity:.14}50%{opacity:.08}}'''

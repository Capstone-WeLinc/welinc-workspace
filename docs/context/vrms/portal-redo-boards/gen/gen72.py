"""Round 72: option A, translucent panels that are not darker (from gen71.py) (the Round 70 options stay for A, the reference). Boards built from a snapshot of the built sign in page
(welinc-web-portal feat/portal-redesign, /login at 1440x900, CSS and markup captured with
Playwright into r70-snap.json), plus one block of CSS per option.

python3 -I gen70.py <snap.json> <outdir>
"""
import json, re, sys, os

snap, out = sys.argv[1], sys.argv[2]
d = json.load(open(snap))
if isinstance(d, str):
    d = json.loads(d)
css, html = d['css'], d['html']

# Fonts come from Google on the canvas, not the app's node_modules
css = re.sub(r'@font-face\s*\{[^}]*\}', '', css)
css += "\n:root{--default-font-family:Inter,system-ui,sans-serif;--default-mono-font-family:'IBM Plex Mono',ui-monospace,monospace}\n"

# Hooks for the option CSS
html = html.replace('<div aria-hidden="true" class="pointer-events-none absolute inset-0 overflow-hidden bg-sidebar">',
                    '<div id="map" aria-hidden="true" class="pointer-events-none absolute inset-0 overflow-hidden bg-sidebar">', 1)
html = html.replace('<span class="flex items-center gap-2.5">', '<span class="lk flex items-center gap-2.5">', 1)
html = html.replace('class="signin-glass ', 'id="glass" class="signin-glass ', 1)
html = html.replace('<main class="signin-dark ', '<main id="form" class="signin-dark ', 1)
html = html.replace('id="login-email" placeholder="you@example.com" required="" autocomplete="username" type="text" value=""',
                    'id="login-email" placeholder="you@example.com" required="" autocomplete="username" type="text" value="mech.juan@welinc.com"', 1)
html = re.sub(r'(id="login-password"[^>]*?)value=""', r'\1value="workshop2026"', html, count=1)
html = html.replace('<section aria-label="Notifications alt+T"', '<section hidden aria-label="Notifications alt+T"', 1)

TRUCK = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
         "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2'/>"
         "<path d='M15 18H9'/><path d='M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14'/>"
         "<circle cx='17' cy='18' r='2'/><circle cx='7' cy='18' r='2'/></svg>")

# Shared pieces of the options
LIT_MAP = """
#map{background:radial-gradient(ellipse 62% 58% at 47% 70%, {c1} 0%, {c2} 38%, #0f1445 78%)}
#map > .signin-stage:first-child svg > g:first-of-type{opacity:{b}}
#map::after{content:"";position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 78% 74% at 44% 62%, transparent 52%, rgba(4,6,26,.6) 100%)}
"""
def lit(c1,c2,b):
    return LIT_MAP.replace("{c1}",c1).replace("{c2}",c2).replace("{b}",b)

GOLD_TILE = """
.lk{gap:14px}
.lk svg{box-sizing:content-box;height:17px;padding:12px 10px;margin-block:-11px;background:#e8b800;color:#0f1445;border-radius:12px;
  box-shadow:0 8px 22px rgba(232,184,0,.22), inset 0 -2px 0 rgba(0,0,0,.12)}
.lk > span{font-style:normal;font-size:19px}
"""
LABEL_LEFT = """
#map span[style*="left: 843px"]{transform:translate(calc(-100% - 36px),-50%)}
"""
INSET_FIELDS = """
#form input{background:rgba(3,5,24,.62);border-color:rgba(255,255,255,.11);box-shadow:inset 0 1px 3px rgba(0,0,0,.45)}
"""

OPTIONS70 = [
    ("R70Built", "As built (reference)", ""),
    ("R70Lit", "A Lit map and real glass (recommended)",
     lit("#26358c","#19236f",".64") + LABEL_LEFT + GOLD_TILE + INSET_FIELDS + """
#glass{background:linear-gradient(180deg, rgba(255,255,255,.075), rgba(255,255,255,.03) 60%), rgba(8,11,42,.40);
  backdrop-filter:blur(16px) saturate(1.35);
  box-shadow:inset 1px 0 0 rgba(255,255,255,.17), inset 0 1px 0 rgba(255,255,255,.10), -24px 0 60px rgba(3,5,22,.35)}
"""),
    ("R70Frost", "B Clear glass, the network runs under the form",
     lit("#2c3d9a","#1b2674",".72") + GOLD_TILE + INSET_FIELDS + """
#map .signin-trucks-clip{width:100% !important}
#glass{background:linear-gradient(180deg, rgba(255,255,255,.10), rgba(255,255,255,.03) 60%), rgba(10,14,52,.12);
  backdrop-filter:blur(2.5px) saturate(1.4);
  box-shadow:inset 1px 0 0 rgba(255,255,255,.26), inset 0 1px 0 rgba(255,255,255,.14), -30px 0 80px rgba(3,5,22,.35)}
#glass::before{content:"";position:absolute;left:0;right:0;top:0;height:3px;
  background:linear-gradient(90deg, rgba(232,184,0,0), rgba(232,184,0,.85) 30%, rgba(232,184,0,.85) 70%, rgba(232,184,0,0))}
"""),
    ("R70Card", "C Floating card on the map",
     lit("#24338a","#18226c",".64") + GOLD_TILE + INSET_FIELDS + """
#map .signin-trucks-clip{width:100% !important}
#glass{background:radial-gradient(ellipse 80% 70% at 55% 50%, rgba(4,6,26,.0), rgba(4,6,26,.35));backdrop-filter:none;box-shadow:none}
#form{max-width:468px;padding:40px 40px 36px;border-radius:24px;
  background:linear-gradient(180deg, rgba(24,31,92,.82), rgba(14,19,66,.86));
  backdrop-filter:blur(14px) saturate(1.2);
  border:1px solid rgba(255,255,255,.12);
  box-shadow:0 34px 90px rgba(2,4,22,.65), 0 2px 0 rgba(255,255,255,.05) inset}
#form::before{content:"";width:52px;height:52px;border-radius:14px;margin-bottom:-8px;
  background:#e8b800 center/26px no-repeat;box-shadow:0 10px 24px rgba(232,184,0,.25);
  -webkit-mask:none}
#form::after{content:"";position:absolute;top:53px;left:53px;width:26px;height:26px;background:#0f1445;
  -webkit-mask:url("TRUCKURL") center/contain no-repeat;mask:url("TRUCKURL") center/contain no-repeat}
#form{position:relative}
""".replace("TRUCKURL", TRUCK)),
    ("R70TwoTone", "D Two tones, no glass",
     lit("#2a3a96","#1a2471",".66") + LABEL_LEFT + GOLD_TILE + """
#map .signin-trucks-clip{width:840px}
#glass{background:linear-gradient(180deg, #0a0e33, #070a27);backdrop-filter:none;
  box-shadow:-1px 0 0 rgba(255,255,255,.06), -40px 0 80px rgba(2,4,20,.55)}
#form input{background:#141a55;border-color:rgba(255,255,255,.09);box-shadow:0 1px 0 rgba(255,255,255,.04) inset}
#form h2::after{content:"";display:block;width:36px;height:3px;border-radius:2px;background:#e8b800;margin-top:14px}
"""),
]

OPTIONS70_A = OPTIONS70[1][2]

A_BASE = lit("#26358c","#19236f",".64") + LABEL_LEFT + GOLD_TILE + INSET_FIELDS

OPTIONS71 = [
    ("R71Glass", "A as published: glass (too glassy)", OPTIONS70_A),
    ("R71Matte", "A1 Matte: the panel solid enough to stop the blur, one faint edge line",
     A_BASE + """
#glass{background:rgba(9,12,46,.86);backdrop-filter:none;box-shadow:inset 1px 0 0 rgba(255,255,255,.08)}
"""),
    ("R71Smoke", "A2 Smoke: a darker tint with a light blur, no shine, no edge lines",
     A_BASE + """
#glass{background:rgba(8,11,42,.70);backdrop-filter:blur(5px);box-shadow:none}
"""),
    ("R71Solid", "A3 Solid: a deep panel with no line, a soft shadow falls onto the map",
     A_BASE + """
#glass{background:#0a0d33;backdrop-filter:none;box-shadow:-36px 0 72px rgba(2,4,20,.5)}
"""),
    ("R71Fade", "A4 Fade: no edge at all, the map dissolves into the deep side over 160px",
     A_BASE + """
#glass{background:linear-gradient(90deg, rgba(10,13,51,0) 0, rgba(10,13,51,.88) 160px, #0a0d33 260px);backdrop-filter:none;box-shadow:none}
#map span[style*="left: 943px"]{transform:translate(-62px, 16px)}
"""),
]

TANAY_UNDER = """
#map span[style*="left: 943px"]{transform:translate(-62px, 16px)}
"""

OPTIONS = [
    ("R72Glass", "A as published: glass (too glassy), for comparison", OPTIONS70_A),
    ("R72Veil", "A5 Veil: the map's own navy at 45%, no blur, no edges",
     A_BASE + TANAY_UNDER + """
#glass{background:rgba(15,20,69,.45);backdrop-filter:none;box-shadow:none}
"""),
    ("R72Haze", "A6 Haze: the map's navy at 35% with a 2px soften, no edges",
     A_BASE + TANAY_UNDER + """
#glass{background:rgba(15,20,69,.35);backdrop-filter:blur(2px);box-shadow:none}
"""),
    ("R72Tint", "A7 Tint: a lighter blue at 30%, a touch lighter than the map, a 3px soften",
     A_BASE + TANAY_UNDER + """
#glass{background:rgba(44,60,150,.30);backdrop-filter:blur(3px);box-shadow:none}
"""),
    ("R72Mist", "A8 Mist: a thin white mist only, no navy added, one very faint edge",
     A_BASE + TANAY_UNDER + """
#glass{background:rgba(255,255,255,.045);backdrop-filter:blur(1.5px);box-shadow:inset 1px 0 0 rgba(255,255,255,.07)}
"""),
]

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Sign in · WeLinc Logistics Operations Workspace</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=IBM+Plex+Mono:wght@500;600&amp;display=swap">
<style>
@@CSS@@
body{margin:0}
#root{width:1440px;height:900px;overflow:hidden}
#root .min-h-dvh{min-height:900px;height:900px}
/* Round 70 option */
@@EXTRA@@
</style>
</helmet>
@@HTML@@
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":1440,"height":900}}'>
class Component extends DCLogic {
renderVals() { return {}; }
}
</script>
</body>
</html>
"""

os.makedirs(out, exist_ok=True)
for name, title, extra in OPTIONS:
    with open(os.path.join(out, name + '.dc.html'), 'w') as f:
        f.write(HEAD.replace('@@CSS@@', css).replace('@@EXTRA@@', extra).replace('@@HTML@@', html))
    print(name, title)

"""Round 50, Suite management as a fourth choice. Registered into gen50.BOARDS."""
from gen50 import reg, P_CSS, ARW, p_band, two_cards, R50Road, R50Keys, CORAZON

SUITE = dict(code='Suite', name='Suite management', line='People, roles and access for your systems', role='4 to review')
FULL = [dict(s, role='Admin') for s in CORAZON]
NAVY_CARD = '''.cards a.su{background:#0f1445;color:#fff;box-shadow:0 14px 34px rgba(15,20,69,.25)}
.cards a.su b{color:#fff}.cards a.su .nm{color:#fff}.cards a.su .ln,.cards a.su .rl{color:rgba(255,255,255,.66)}.cards a.su .rl strong{color:#e8b800}
.cards a.su .arw{color:rgba(255,255,255,.4)}'''


def suite_card(line):
    return (f'<a class="su" href="#"><b>Suite</b>{ARW}<span class="nm">Suite management</span><span class="ln">{line}</span>'
            f'<span class="rl"><strong>4 to review</strong></span></a>')


@reg
def R50SuiteCard():
    css = P_CSS + '.cards{grid-template-columns:repeat(3,1fr)}\n' + NAVY_CARD
    body = f'<div class="pg">{p_band()}<main class="w"><div class="cards">{two_cards()}{suite_card("People, roles and access for VMMS and VRMS")}</div></main></div>'
    return 'P5 · Suite management as a third choice beside her two systems, in navy', css, body


@reg
def R50FourRoad():
    _, css0, body0 = R50Road()
    css = css0 + '''.cards{grid-template-columns:repeat(4,1fr);gap:20px}
.cards a{min-height:270px;padding:28px 26px}.cards b{font-size:40px}.cards .arw{right:24px;top:30px}
''' + NAVY_CARD
    cards = ''.join(f'<a href="#"><b>{s["code"]}</b>{ARW}<span class="nm">{s["name"]}</span><span class="ln">{s["line"]}</span>'
                    f'<span class="rl">Your role: <strong>{s["role"]}</strong></span></a>' for s in FULL)
    cards += suite_card('People, roles and access for your systems')
    body = body0[:body0.index('<main')] + f'<main class="w"><div class="cards">{cards}</div></main></div>'
    return 'P6 · Fullest case (sample: Admin in all three systems): Suite management as the fourth card', css, body


@reg
def R50FourKeys():
    _, css0, body0 = R50Keys()
    css = css0 + '''.key{width:240px}.tag{width:240px;height:320px;padding:44px 24px 24px}.tag:before{left:96px}
.tag b{font-size:54px}
.k3 .tag{background:#0a0d33;color:#fff;box-shadow:inset 0 0 0 2px #e8b800,0 14px 26px rgba(15,23,42,.2)}
.k3 .tag .rl{color:#e8b800;opacity:1}'''
    keys = ''.join(f'<a class="key k{i}" href="#"><span class="hook"></span><span class="ring"></span><span class="tag"><b>{s["code"]}</b>'
                   f'<span class="nm">{s["name"]}</span><span class="ln">{s["line"]}</span><span class="rl">{s["role"].upper()}</span></span></a>'
                   for i, s in enumerate(FULL + [SUITE]))
    body = body0[:body0.index('<main')] + f'<main class="w"><div class="cab"><div class="rail">{keys}</div></div></main></div>'
    return 'P7 · Fullest case on the key board: Suite management is the fourth key', css, body

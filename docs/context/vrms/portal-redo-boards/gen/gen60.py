"""Round 60 (Nov 26): Q1 band as picked, P5 number keys picked. The bottom of the page: low-key motion that
doesn't pull the eye (E1 to E4), or quiet designs that fit in (E5, E6). No vehicles, no road (out on the launcher).
Every animation stops under prefers-reduced-motion. python3 -I gen60.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g  # noqa: E402
import gen53 as g53  # noqa: E402
import gen56 as g56  # noqa: E402
import gen59 as g59  # noqa: E402
from data49 import board, CORAZON  # noqa: E402
from parts import LOGO_POLY  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
NAME = 'WeLinc Logistics'
LINE = f'<span class="co"><b>{NAME}</b> · Since 2018</span>'
BASE = '''.co{position:absolute;left:calc(50% - 600px);bottom:20px;font-size:13px;color:#5b6779;z-index:2}.co b{color:#0f172a;font-weight:700}
.ft{position:absolute;left:0;right:0;bottom:0;height:140px;overflow:hidden;pointer-events:none}
@media (prefers-reduced-motion:reduce){.ft *,.ft *:before,.ft *:after,.ft:before,.ft:after{animation:none!important}}'''


def page(title, css, foot):
    lcss, lhtml = g53.L1(g53.items(CORAZON, False), 'plain')
    lhtml = g59.numbered(lhtml.replace(g53.HINT, ''))
    body = f'<div class="pg">{g59.TOP_HTML}<div class="w below">{lhtml}</div><div class="ft" aria-hidden="true">{foot}</div>{LINE}</div>'
    return title, g.CSS + g53.COMMON + g56.TOP + g59.Q1 + lcss + g59.P5 + BASE + css, body


# ---------------------------------------------------------------- low-key motion
def E1():
    """A glint: a hairline across the bottom; every 9 s a soft gold light runs along it once, then rests."""
    css = '''.ft .hl{position:absolute;left:0;right:0;bottom:56px;height:1px;background:#e1e5ee}
.ft .hl i{position:absolute;top:-1px;left:0;width:220px;height:3px;border-radius:2px;
background:linear-gradient(90deg,rgba(232,184,0,0),rgba(232,184,0,.85),rgba(232,184,0,0));animation:gl 9s cubic-bezier(.45,0,.55,1) infinite}
@keyframes gl{0%{transform:translateX(-240px);opacity:0}4%{opacity:1}34%{transform:translateX(1440px);opacity:1}35%,100%{transform:translateX(1440px);opacity:0}}'''
    return css, '<div class="hl"><i></i></div>'


def E2():
    """Bay lights: a row of small gold lights, like the lamps over the loading bays; a slow wave brightens them in turn."""
    dots = ''.join(f'<i style="left:{120 + n * 40}px;animation-delay:{n * 0.11:.2f}s"></i>' for n in range(31))
    css = '''.ft i{position:absolute;bottom:58px;width:6px;height:6px;margin-left:-3px;border-radius:50%;background:#e8b800;opacity:.2;animation:bl 7s ease-in-out infinite}
@keyframes bl{0%,22%,100%{opacity:.2;transform:scale(1)}9%{opacity:.85;transform:scale(1.35)}}'''
    return css, dots


def E3():
    """The mark's slashes as a slow belt: faint navy slashes drift right at 8 px/s, fading at both ends."""
    polys = ''.join(f'<polygon points="{x},14 {x + 5},0 {x + 11},0 {x + 6},14"/>' for x in range(-24, 1500, 24))
    css = '''.ft .bt{position:absolute;left:0;right:0;bottom:52px;height:14px;
-webkit-mask:linear-gradient(90deg,transparent,#000 18%,#000 82%,transparent);mask:linear-gradient(90deg,transparent,#000 18%,#000 82%,transparent)}
.ft .bt svg{position:absolute;left:0;top:0;width:1524px;height:14px;fill:rgba(15,20,69,.08);animation:belt 3s linear infinite}
@keyframes belt{from{transform:translateX(-24px)}to{transform:translateX(0)}}'''
    return css, f'<div class="bt"><svg viewBox="0 0 1524 14">{polys}</svg></div>'


def E4():
    """Today as a quiet line: the day from midnight to midnight, gold up to now, a soft pulse at the current time."""
    now = (10 + 40 / 60) / 24  # 10:40 AM on the board
    ticks = ''.join(f'<i class="tk" style="left:{h / 24 * 100:.3f}%"></i>' for h in range(25))
    labels = ''.join(f'<em style="left:{h / 24 * 100:.3f}%">{t}</em>' for h, t in [(0, '12 AM'), (6, '6 AM'), (12, '12 PM'), (18, '6 PM'), (24, '12 AM')])
    css = f'''.ft .dl{{position:absolute;left:calc(50% - 600px);width:1200px;bottom:78px;height:1px;background:#dfe3ec}}
.ft .dl .tk{{position:absolute;top:-3px;width:1px;height:7px;background:#d3d8e3}}
.ft .dl .fl{{position:absolute;left:0;top:-1px;height:3px;border-radius:2px;width:{now * 100:.3f}%;background:linear-gradient(90deg,rgba(232,184,0,.25),#e8b800)}}
.ft .dl .nw{{position:absolute;left:{now * 100:.3f}%;top:-4px;width:9px;height:9px;margin-left:-4.5px;border-radius:50%;background:#e8b800}}
.ft .dl .nw:after{{content:"";position:absolute;inset:0;border-radius:50%;border:1.5px solid #e8b800;animation:pu 2.8s ease-out infinite}}
@keyframes pu{{from{{transform:scale(1);opacity:.7}}to{{transform:scale(3.2);opacity:0}}}}
.ft .dl em{{position:absolute;top:10px;transform:translateX(-50%);font:600 10.5px "IBM Plex Mono",monospace;font-style:normal;letter-spacing:.06em;color:#9aa3b3;white-space:nowrap}}
.ft .dl em:first-of-type{{transform:none}}.ft .dl em:last-of-type{{transform:translateX(-100%)}}'''
    return css, f'<div class="dl">{ticks}<div class="fl"></div><span class="nw"></span>{labels}</div>'


# ---------------------------------------------------------------- quiet designs that fit in
def E5():
    """The band's echo: the same thin gold fade that closes the band closes the page; the line centred under it."""
    css = '''.ft:before{content:"";position:absolute;left:0;right:0;bottom:56px;height:2px;
background:linear-gradient(90deg,rgba(232,184,0,0),rgba(232,184,0,.7) 50%,rgba(232,184,0,0))}
.co{left:0;right:0;text-align:center}'''
    return css, ''


def E6():
    """A quiet floor: the last strip of the page a shade deeper, the gold fade on its top edge, a small gold mark by the line."""
    css = '''.ft{height:64px;background:#eaedf3}
.ft:before{content:"";position:absolute;left:0;right:0;top:0;height:1px;background:linear-gradient(90deg,rgba(232,184,0,0),rgba(232,184,0,.45) 50%,rgba(232,184,0,0))}
.co{display:flex;align-items:center;gap:10px;bottom:22px}.co svg{height:12px;fill:#e8b800}'''
    return css, ''


LINE_E6 = f'<span class="co"><svg viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg><span><b>{NAME}</b> · Since 2018</span></span>'

for key, t, fn in [
    ('R60E1', 'E1 · Moves: a gold glint runs along a hairline once every 9 s', E1),
    ('R60E2', 'E2 · Moves: bay lights, a slow wave brightens a row of small gold lamps', E2),
    ('R60E3', 'E3 · Moves: the mark\'s slashes drift right like a slow belt (8 px/s)', E3),
    ('R60E4', 'E4 · Moves: today as a quiet line, gold up to now, a soft pulse at the time', E4),
    ('R60E5', 'E5 · Still: the band\'s gold fade echoed at the bottom, the line centred', E5),
    ('R60E6', 'E6 · Still: a quiet floor a shade deeper, a small gold mark by the line', E6),
]:
    BOARDS[key] = (lambda t=t, fn=fn: page(t, *fn()))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in BOARDS.items():
        if ONLY and name not in ONLY:
            continue
        title, css, body = fn()
        if name == 'R60E6':
            body = body.replace(LINE, LINE_E6)
        (OUT / f'{name}.dc.html').write_text(board(title, css, body, h=900))
        print(name, title)


if __name__ == '__main__':
    main()

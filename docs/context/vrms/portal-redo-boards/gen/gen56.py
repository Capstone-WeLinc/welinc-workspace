"""Round 56 (Nov 25, late night): no greeting, a shorter band, a white profile circle, a nicer top.
All keep M1's faint mark and add a soft light behind it. L1 tiles, I1 icons, the company line as the footer.
python3 -I gen56.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g  # noqa: E402
import gen53 as g53  # noqa: E402
import gen55 as g55  # noqa: E402
from data49 import board, CORAZON, DATE  # noqa: E402
from parts import LOGO, LOGO_POLY, CHEV  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
D = DATE.upper()
MK = f'<svg class="mk" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>'
ME = f'<button class="me" type="button"><span class="av" aria-hidden="true">CV</span>Corazon Villareal{CHEV}</button>'
TOOLS = f'<span class="sp"></span><button class="hb" type="button" aria-label="Help">{g.SUN}</button>{ME}'
LOCK = f'<div class="lk">{LOGO}<b>WeLinc Logistics</b><em>Operations Workspace</em></div>'

TOP = '''.tp{position:relative;background:radial-gradient(720px 260px at 82% 0%,#1d2678 0%,rgba(29,38,120,0) 70%),#0f1445;color:#fff;overflow:hidden}
.tp:after{content:"";position:absolute;left:0;right:0;bottom:0;height:1px;background:linear-gradient(90deg,rgba(232,184,0,0),rgba(232,184,0,.35) 50%,rgba(232,184,0,0))}
.tp .mk{position:absolute;right:calc(50% - 720px);top:-60px;height:280px;fill:rgba(255,255,255,.05);z-index:0}
.tp .row{position:relative;z-index:3}
.tp .av{background:#fff;color:#0f1445;box-shadow:0 0 0 3px rgba(255,255,255,.14)}
.tp .lk em{color:rgba(255,255,255,.6)}'''
TILE_HD_OFF = '.below>.hd{display:none}'


def P1():
    """The section title moves into the band: "Your systems" in white, the count, the hint at the right."""
    css = '''.tp{height:148px}
.tp .tt{position:relative;z-index:2;display:flex;align-items:baseline;gap:12px;padding-top:20px}
.tp h1{margin:0;font-size:30px;font-weight:800;letter-spacing:-.025em}
.tp .n{font:600 13px "IBM Plex Mono",monospace;color:#e8b800}
.tp .h{margin-left:auto;font-size:13px;color:rgba(255,255,255,.6)}
.below{padding-top:32px}''' + TILE_HD_OFF
    html = (f'<header class="tp">{MK}<div class="w"><div class="row">{LOCK}{TOOLS}</div>'
            f'<div class="tt"><h1>Your systems</h1><span class="n">3</span><span class="h">Open one to start. You stay signed in to all of them.</span></div></div></header>')
    return css, html


def P2():
    """One taller row: a larger lockup and the account, nothing else; the date sits quietly in the middle."""
    css = '''.tp{height:104px}
.tp .row{height:104px}
.tp .lk svg{height:26px}.tp .lk b{font-size:20px}.tp .lk em{font-size:15px;padding-left:14px}
.tp .dt{position:absolute;left:50%;transform:translateX(-50%);font:600 12px "IBM Plex Mono",monospace;letter-spacing:.08em;color:rgba(255,255,255,.5)}
.below{padding-top:36px}'''
    html = (f'<header class="tp">{MK}<div class="w"><div class="row">{LOCK}<span class="dt">{D}</span>{TOOLS}</div></div></header>')
    return css, html


def P3():
    """The workspace name as the title: "Operations Workspace" large, the date in gold beside it."""
    css = '''.tp{height:152px}
.tp .lk em{display:none}
.tp .tt{position:relative;z-index:2;display:flex;align-items:baseline;gap:16px;padding-top:18px}
.tp h1{margin:0;font-size:34px;font-weight:800;letter-spacing:-.03em}
.tp .dt{font:600 12px "IBM Plex Mono",monospace;letter-spacing:.06em;color:#e8b800}
.below{padding-top:34px}'''
    html = (f'<header class="tp">{MK}<div class="w"><div class="row">{LOCK}{TOOLS}</div>'
            f'<div class="tt"><h1>Operations Workspace</h1><span class="dt">{D}</span></div></div></header>')
    return css, html


def P4():
    """Just the bar and one quiet line: the date in gold, nothing to read twice."""
    css = '''.tp{height:118px}
.tp .ln{position:relative;z-index:2;display:flex;gap:14px;align-items:center;padding-top:6px;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.07em}
.tp .ln span:first-child{color:#e8b800}.tp .ln i{width:4px;height:4px;border-radius:50%;background:rgba(255,255,255,.3)}
.tp .ln span:last-child{color:rgba(255,255,255,.55)}
.below{padding-top:34px}'''
    html = (f'<header class="tp">{MK}<div class="w"><div class="row">{LOCK}{TOOLS}</div>'
            f'<div class="ln"><span>{D}</span><i></i><span>3 SYSTEMS</span></div></div></header>')
    return css, html


def P5():
    """The title in the band (as P1), set larger, with the mark bigger and warmer behind it."""
    css = '''.tp{height:164px;background:radial-gradient(900px 320px at 88% 10%,#232d86 0%,rgba(35,45,134,0) 68%),#0f1445}
.tp .mk{height:340px;top:-90px;fill:rgba(232,184,0,.07)}
.tp .tt{position:relative;z-index:2;display:flex;align-items:baseline;gap:14px;padding-top:24px}
.tp h1{margin:0;font-size:38px;font-weight:800;letter-spacing:-.03em}
.tp .n{font:600 13px "IBM Plex Mono",monospace;color:#e8b800}
.below{padding-top:32px}''' + TILE_HD_OFF
    html = (f'<header class="tp">{MK}<div class="w"><div class="row">{LOCK}{TOOLS}</div>'
            f'<div class="tt"><h1>Your systems</h1><span class="n">3</span></div></div></header>')
    return css, html


def compose(title, header):
    hcss, hhtml = header()
    lcss, lhtml = g53.L1(g53.items(CORAZON, False), 'plain')
    body = f'<div class="pg">{hhtml}<div class="w below">{lhtml}</div>{g55.FOOT}</div>'
    return title, g.CSS + g53.COMMON + TOP + hcss + lcss + g55.FOOT_CSS, body


for key, fn, t in [
    ('R56P1', P1, 'P1 · "Your systems" moves into the band; 148px'),
    ('R56P2', P2, 'P2 · One taller row: a larger lockup and the account; 104px'),
    ('R56P3', P3, 'P3 · "Operations Workspace" as the title, the date beside it; 152px'),
    ('R56P4', P4, 'P4 · The bar and one quiet line (the date, 3 systems); 118px'),
    ('R56P5', P5, 'P5 · As P1, larger, the mark warmer behind it; 164px'),
]:
    BOARDS[key] = (lambda fn=fn, t=t: compose(t, fn))


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

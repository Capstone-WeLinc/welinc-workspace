"""Round 55 (Nov 25, late night): the whole top area (navbar and band together) reworked. L1 and I1 below,
the footer is the company line only (no Privacy or Terms: no such pages exist).
python3 -I gen55.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g  # noqa: E402
import gen53 as g53  # noqa: E402
from data49 import board, CORAZON, DATE  # noqa: E402
from parts import LOGO, LOGO_POLY, CHEV  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
D = DATE.upper()
MK = f'<svg class="mk" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>'
HELP = g.SUN
ME = f'<button class="me" type="button"><span class="av" aria-hidden="true">CV</span>Corazon Villareal{CHEV}</button>'
TOOLS = f'<span class="sp"></span><button class="hb" type="button" aria-label="Help">{HELP}</button>{ME}'
LOCK = f'<div class="lk">{LOGO}<b>WeLinc Logistics</b><em>Operations Workspace</em></div>'
MARK_CSS = '.mk{position:absolute;right:calc(50% - 720px);top:-40px;height:300px;fill:rgba(255,255,255,.045);z-index:0}'
BELOW = '.below{padding-top:34px}'


def H1():
    """One band: logo, greeting and account share a single 128px row."""
    css = MARK_CSS + '''.h1{position:relative;height:128px;background:#0f1445;color:#fff;overflow:hidden}
.h1 .mk{top:-80px;height:280px}
.h1 .row{position:relative;z-index:2;height:128px;gap:28px}
.h1 .lk em{display:none}
.h1 .gx{padding-left:28px;border-left:1px solid rgba(255,255,255,.16);display:flex;flex-direction:column;gap:6px}
.h1 .gx span{font:600 11.5px "IBM Plex Mono",monospace;letter-spacing:.06em;color:#e8b800}
.h1 .gx strong{font-size:30px;font-weight:800;letter-spacing:-.03em;line-height:1}''' + BELOW
    html = (f'<header class="h1">{MK}<div class="w"><div class="row">{LOCK}<div class="gx"><span>{D}</span><strong>Good morning, Corazon</strong></div>{TOOLS}</div></div></header>')
    return css, html


def H2():
    """A white navbar over the navy band: the bar reads as chrome, the band as the greeting."""
    css = MARK_CSS + '''.h2n{background:#fff;box-shadow:0 1px 0 #e3e7ef;position:relative;z-index:3}
.h2n .lk b{color:#0f1445}.h2n .lk em{color:#5b6779;border-left-color:#dfe3ec}
.h2n .hb{color:#5b6779}.h2n .hb:hover{background:#f3f5f9;color:#0f1445}
.h2n .me{color:#0f172a}.h2n .me:hover{background:#f3f5f9}.h2n .av{background:#0f1445;color:#fff}
.h2b{position:relative;height:150px;background:#0f1445;color:#fff;overflow:hidden}
.h2b .mk{top:-70px}
.h2b .gr{position:relative;z-index:2;padding-top:34px}
.h2b .dt{margin:0;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.06em;color:#e8b800}
.h2b h1{margin:8px 0 0;font-size:38px;line-height:1.05;font-weight:800;letter-spacing:-.03em}''' + BELOW
    html = (f'<header class="h2n"><div class="w"><div class="row">{LOCK}{TOOLS}</div></div></header>'
            f'<section class="h2b">{MK}<div class="w gr"><p class="dt">{D}</p><h1>Good morning, Corazon</h1></div></section>')
    return css, html


def H3():
    """Dispatch clock: the greeting on the left, today's time and date set large on the right."""
    css = MARK_CSS + '''.h3{position:relative;height:200px;background:#0f1445;color:#fff;overflow:hidden}
.h3 .mk{top:-30px;height:260px;right:calc(50% - 760px)}
.h3 .row{position:relative;z-index:3}
.h3 .gr{position:relative;z-index:2;display:flex;align-items:flex-end;padding-top:30px}
.h3 h1{margin:0;font-size:40px;line-height:1.05;font-weight:800;letter-spacing:-.03em}
.h3 .ck{margin-left:auto;text-align:right;font-family:"IBM Plex Mono",monospace}
.h3 .ck b{display:block;font-size:48px;font-weight:600;line-height:1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.h3 .ck span{display:block;margin-top:8px;font-size:12px;font-weight:600;letter-spacing:.08em;color:#e8b800}''' + BELOW
    html = (f'<header class="h3">{MK}<div class="w"><div class="row">{LOCK}{TOOLS}</div><div class="gr"><h1>Good morning, Corazon</h1>'
            f'<div class="ck"><b>8:14 AM</b><span>WED · NOV 25 · MANILA</span></div></div></div></header>')
    return css, html


def H4():
    """Editorial: a taller band, the greeting set very large on the band's bottom edge, the mark bleeding off."""
    css = '''.h4{position:relative;height:250px;background:#0f1445;color:#fff;overflow:hidden}
.h4 .mk{position:absolute;right:calc(50% - 780px);bottom:-90px;height:400px;fill:rgba(255,255,255,.045)}
.h4 .row{position:relative;z-index:3}
.h4 .gr{position:absolute;left:0;right:0;bottom:30px;z-index:2;display:flex;align-items:baseline;gap:22px}
.h4 h1{margin:0;font-size:64px;line-height:.95;font-weight:800;letter-spacing:-.045em}
.h4 .dt{font:600 12px "IBM Plex Mono",monospace;letter-spacing:.06em;color:#e8b800}''' + BELOW
    html = (f'<header class="h4">{MK}<div class="w" style="height:250px"><div class="row">{LOCK}{TOOLS}</div>'
            f'<div class="gr"><h1>Good morning, Corazon</h1><span class="dt">{D}</span></div></div></header>')
    return css, html


def H5():
    """Brand first: the bar keeps only help and the account; the band carries the WeLinc name, the greeting under it."""
    css = MARK_CSS + '''.h5{position:relative;height:210px;background:#0f1445;color:#fff;overflow:hidden}
.h5 .row{position:relative;z-index:3}
.h5 .br{position:relative;z-index:2;display:flex;align-items:center;gap:16px;padding-top:8px}
.h5 .br svg{height:40px;fill:#e8b800}
.h5 .br b{font-size:40px;font-weight:800;font-style:italic;letter-spacing:-.025em;line-height:1}
.h5 .br em{font:600 12px "IBM Plex Mono",monospace;font-style:normal;letter-spacing:.08em;color:rgba(255,255,255,.55);padding-left:16px;border-left:1px solid rgba(255,255,255,.18);align-self:center}
.h5 .gln{position:relative;z-index:2;margin:18px 0 0;font-size:17px;color:rgba(255,255,255,.8)}
.h5 .gln span{color:#e8b800;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.06em;margin-left:10px}''' + BELOW
    html = (f'<header class="h5">{MK}<div class="w"><div class="row">{TOOLS}</div>'
            f'<div class="br">{LOGO}<b>WeLinc Logistics</b><em>OPERATIONS WORKSPACE</em></div>'
            f'<p class="gln">Good morning, Corazon<span>{D}</span></p></div></header>')
    return css, html


def H6():
    """Personal: the person's initials large beside the greeting; the bar keeps the account menu by name."""
    css = MARK_CSS + '''.h6{position:relative;height:196px;background:#0f1445;color:#fff;overflow:hidden}
.h6 .row{position:relative;z-index:3}
.h6 .row .av{display:none}
.h6 .gr{position:relative;z-index:2;display:flex;align-items:center;gap:22px;padding-top:22px}
.h6 .big{width:76px;height:76px;border-radius:50%;background:#e8b800;color:#0f1445;display:grid;place-items:center;font-size:26px;font-weight:800;letter-spacing:-.02em;box-shadow:0 0 0 6px rgba(232,184,0,.14)}
.h6 .dt{margin:0;font:600 12px "IBM Plex Mono",monospace;letter-spacing:.06em;color:#e8b800}
.h6 h1{margin:8px 0 0;font-size:38px;line-height:1.05;font-weight:800;letter-spacing:-.03em}''' + BELOW
    html = (f'<header class="h6">{MK}<div class="w"><div class="row">{LOCK}{TOOLS}</div>'
            f'<div class="gr"><span class="big" aria-hidden="true">CV</span><div><p class="dt">{D}</p><h1>Good morning, Corazon</h1></div></div></div></header>')
    return css, html


FOOT_CSS = '''.fl0{position:absolute;left:0;right:0;bottom:20px;font-size:13px;color:#5b6779}.fl0 b{color:#0f172a}'''
FOOT = '<div class="fl0"><div class="w"><span><b>WeLinc Logistics</b> · Since 2018</span></div></div>'


def compose(title, header):
    hcss, hhtml = header()
    lcss, lhtml = g53.L1(g53.items(CORAZON, False), 'plain')
    body = f'<div class="pg">{hhtml}<div class="w below">{lhtml}</div>{FOOT}</div>'
    css = g.CSS + g53.COMMON + hcss + lcss + FOOT_CSS
    return title, css, body


for key, fn, t in [
    ('R55H1', H1, 'H1 · One band: logo, greeting and account in a single 128px row'),
    ('R55H2', H2, 'H2 · A white navbar over the navy band'),
    ('R55H3', H3, 'H3 · Dispatch clock: the greeting left, the time and date large on the right'),
    ('R55H4', H4, 'H4 · Editorial: a taller band, the greeting very large on its bottom edge'),
    ('R55H5', H5, 'H5 · Brand first: the band carries the WeLinc name, the greeting under it'),
    ('R55H6', H6, 'H6 · Personal: the initials large beside the greeting'),
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

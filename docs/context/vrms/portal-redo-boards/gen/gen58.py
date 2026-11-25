"""Round 58 (Nov 26): Q1 picked (the 88px band, the bar is the whole band). Refinements of Q1, and footers drawn
on the page itself (around D1; no navy bar at the bottom). L1 tiles, I1 icons.
python3 -I gen58.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g  # noqa: E402
import gen53 as g53  # noqa: E402
import gen55 as g55  # noqa: E402
import gen56 as g56  # noqa: E402
from data49 import board, CORAZON  # noqa: E402
from parts import LOGO_POLY  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
NAME = 'WeLinc Logistics'
Q1 = '.tp{height:88px}.tp .row{height:88px}.tp .mk{top:-110px;height:300px}.below{padding-top:36px}'


# ---------------------------------------------------------------- Q1 refinements (all 88px, no text in the band)
TOPS = [
    ('R58Q1', 'Q1 · as picked: 88px, the faint mark on the right', ''),
    ('R58Q1a', 'Q1a · The mark much larger, its slashes sweep across the right half', '''
.tp .mk{right:120px;top:-30px;height:560px;fill:rgba(255,255,255,.055)}'''),
    ('R58Q1b', 'Q1b · The mark bleeds off the window\'s right edge, the light follows it', '''
.tp{background:radial-gradient(520px 200px at 96% 0%,#222c84 0%,rgba(34,44,132,0) 72%),#0f1445}
.tp .mk{right:-150px;top:-150px;height:380px;fill:rgba(255,255,255,.055)}'''),
    ('R58Q1c', 'Q1c · No large mark: its slant as faint stripes fading in from the right', '''
.tp .mk{display:none}
.tp:before{content:"";position:absolute;right:0;top:0;bottom:0;width:58%;z-index:0;
background:repeating-linear-gradient(113deg,rgba(255,255,255,.05) 0 26px,transparent 26px 64px);
-webkit-mask:linear-gradient(90deg,transparent,#000 70%);mask:linear-gradient(90deg,transparent,#000 70%)}'''),
    ('R58Q1d', 'Q1d · A solid gold livery line along the bottom instead of the fade', '''
.tp:after{height:3px;background:#e8b800}'''),
    ('R58Q1e', 'Q1e · Deeper on the left, lighter under the mark; the mark in faint gold', '''
.tp{background:linear-gradient(90deg,#0a0d33 0%,#0f1445 45%,#1b2475 100%)}
.tp .mk{fill:rgba(232,184,0,.13)}'''),
    ('R58Q1f', 'Q1f · Help and profile joined in one soft pill', '''
.tp .hb,.tp .me{background:none}
.tp .row .hb{margin-right:0;border-radius:999px 0 0 999px;background:rgba(255,255,255,.07);height:44px;width:48px;margin-right:-16px}
.tp .row .me{border-radius:0 999px 999px 0;background:rgba(255,255,255,.07);padding:0 14px 0 6px;box-shadow:inset 1px 0 0 rgba(255,255,255,.1)}'''),
]

PLAIN_CSS = g55.FOOT_CSS
PLAIN = g55.FOOT


def page(title, top_css, foot_css, foot_html):
    hhtml = f'<header class="tp">{g56.MK}<div class="w"><div class="row">{g56.LOCK}{g56.TOOLS}</div></div></header>'
    lcss, lhtml = g53.L1(g53.items(CORAZON, False), 'plain')
    body = f'<div class="pg">{hhtml}<div class="w below">{lhtml}</div>{foot_html}</div>'
    return title, g.CSS + g53.COMMON + g56.TOP + Q1 + top_css + lcss + foot_css, body


for key, t, css in TOPS:
    BOARDS[key] = (lambda t=t, css=css: page(t, css, PLAIN_CSS, PLAIN))


# ---------------------------------------------------------------- footers on the page (no navy bar)
BIG = '''.ft{position:absolute;left:0;right:0;bottom:0;height:250px;overflow:hidden}
.ft .ln{position:absolute;left:50%;width:1200px;margin-left:-600px;top:22px;font-size:13px;color:#5b6779;z-index:2}
.ft .ln b{color:#0f172a;font-weight:700}
.ft .big{position:absolute;left:50%;transform:translateX(-50%);bottom:-36px;white-space:nowrap;font-size:150px;line-height:1;
font-weight:800;font-style:italic;letter-spacing:-.045em;color:#e6e9f0}'''
LINE = f'<div class="ln"><b>{NAME}</b> · Since 2018</div>'


def ft(extra_css, inner, line=LINE):
    return BIG + extra_css, f'<div class="ft">{line}{inner}</div>'


def big(text=NAME):
    return f'<div class="big" aria-hidden="true">{text}</div>'


MARK = f'<svg class="bm" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>'

FOOTS = [
    ('R58F1', 'F1 · D1 under Q1: the name huge and faint, cropped, a hairline above',
     lambda: ft('.ft{border-top:1px solid #e3e7ef}', big())),
    ('R58F2', 'F2 · The name as a thin navy outline, cropped by the bottom edge',
     lambda: ft('.ft .big{color:#f3f5f9;text-shadow:1px 0px 0 rgba(15,20,69,.17),-1px 0px 0 rgba(15,20,69,.17),0px 1px 0 rgba(15,20,69,.17),0px -1px 0 rgba(15,20,69,.17),1px 1px 0 rgba(15,20,69,.17),-1px -1px 0 rgba(15,20,69,.17),1px -1px 0 rgba(15,20,69,.17),-1px 1px 0 rgba(15,20,69,.17)}', big())),
    ('R58F3', 'F3 · No rule: the name rises out of the page, fading upward',
     lambda: ft('.ft .big{color:transparent;background:linear-gradient(180deg,rgba(214,220,232,0) 5%,#d6dce8 80%);'
                '-webkit-background-clip:text;background-clip:text;padding-right:20px}', big())),
    ('R58F4', 'F4 · The whole lockup at scale: the mark and "WeLinc", faint, cropped',
     lambda: ft('''.ft .big{display:flex;align-items:flex-end;gap:36px;bottom:-30px;font-size:170px}
.ft .bm{height:128px;fill:#e6e9f0;margin-bottom:34px}''', f'<div class="big" aria-hidden="true">{MARK}WeLinc</div>')),
    ('R58F5', 'F5 · The name parked on a gold lane line, like a bay marking',
     lambda: ft('''.ft .lane{position:absolute;left:0;right:0;bottom:70px;height:3px;z-index:1;
background:repeating-linear-gradient(90deg,rgba(232,184,0,.55) 0 44px,transparent 44px 76px)}
.ft .big{bottom:58px;font-size:120px}.ft .ln{top:auto;bottom:24px}''', '<div class="lane"></div>' + big())),
    ('R58F6', 'F6 · Letterpress: the name pressed into the page, light from above',
     lambda: ft('.ft .big{color:#e7eaf1;text-shadow:0 2px 1px #fff,0 -1px 0 rgba(15,23,42,.16)}', big())),
    ('R58F7', 'F7 · "2018" in huge faint figures on the right, the line on the left',
     lambda: ft('''.ft .big{left:auto;right:calc(50% - 640px);transform:none;font:700 230px/1 "IBM Plex Mono",monospace;
letter-spacing:-.06em;font-style:normal;bottom:-58px;color:#e6e9f0}
.ft .ln{top:auto;bottom:28px}''', big('2018'))),
    ('R58F8', 'F8 · Two tone: "WeLinc" faint navy, "Logistics" faint gold',
     lambda: ft('.ft .big span{color:#f1e7c2}', f'<div class="big" aria-hidden="true">WeLinc <span>Logistics</span></div>')),
]

for key, t, fn in FOOTS:
    BOARDS[key] = (lambda t=t, fn=fn: page(t, '', *fn()))


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

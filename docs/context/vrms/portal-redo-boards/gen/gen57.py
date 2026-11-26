"""Round 57 (Nov 25, late night): no text in place of the greeting. The band holds the navbar and the mark only;
the options differ in height and in how the mark and the light sit. L1 tiles, I1 icons, the company line as the footer.
python3 -I gen57.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g  # noqa: E402
import gen53 as g53  # noqa: E402
import gen55 as g55  # noqa: E402
import gen56 as g56  # noqa: E402
from data49 import board, CORAZON  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}

OPTS = [
    ('R57Q1', 'Q1 · 88px: one row, the bar is the whole band', '''.tp{height:88px}.tp .row{height:88px}
.tp .mk{top:-110px;height:300px}.below{padding-top:36px}'''),
    ('R57Q2', 'Q2 · 112px: one taller row, a larger lockup', '''.tp{height:112px}.tp .row{height:112px}
.tp .lk svg{height:26px}.tp .lk b{font-size:20px}.tp .lk em{font-size:15px;padding-left:14px}
.tp .mk{top:-90px;height:300px}.below{padding-top:36px}'''),
    ('R57Q3', 'Q3 · 128px: the bar at the top, the mark fills the space under it', '''.tp{height:128px}
.tp .mk{top:-60px;height:260px}.below{padding-top:36px}'''),
    ('R57Q4', 'Q4 · 140px: the bar at the top, the mark larger and warmer', '''.tp{height:140px;background:radial-gradient(900px 320px at 88% 10%,#232d86 0%,rgba(35,45,134,0) 68%),#0f1445}
.tp .mk{height:340px;top:-100px;fill:rgba(232,184,0,.07)}.below{padding-top:36px}'''),
    ('R57Q5', 'Q5 · 128px: the mark crisp and small in gold on the right, no large mark', '''.tp{height:128px}
.tp .mk{right:calc(50% - 600px);top:auto;bottom:22px;height:30px;fill:#e8b800;opacity:.9}.below{padding-top:36px}'''),
]


def compose(title, css):
    hhtml = f'<header class="tp">{g56.MK}<div class="w"><div class="row">{g56.LOCK}{g56.TOOLS}</div></div></header>'
    lcss, lhtml = g53.L1(g53.items(CORAZON, False), 'plain')
    body = f'<div class="pg">{hhtml}<div class="w below">{lhtml}</div>{g55.FOOT}</div>'
    return title, g.CSS + g53.COMMON + g56.TOP + css + lcss + g55.FOOT_CSS, body


import gen54 as g54  # noqa: E402

STRIP = ['<span>·</span><span>Privacy · Terms</span>', '<span class="r">Privacy · Terms</span>', '<span>Privacy · Terms</span>', ' · Privacy · Terms']
Q3 = OPTS[2][2]


def compose_foot(title, dfn):
    dcss, dhtml = dfn()
    for x in STRIP:
        dhtml = dhtml.replace(x, '')
    hhtml = f'<header class="tp">{g56.MK}<div class="w"><div class="row">{g56.LOCK}{g56.TOOLS}</div></div></header>'
    lcss, lhtml = g53.L1(g53.items(CORAZON, False), 'plain')
    body = f'<div class="pg">{hhtml}<div class="w below">{lhtml}</div>{dhtml}</div>'
    return title, g.CSS + g53.COMMON + g56.TOP + Q3 + lcss + dcss, body


for key, t, fn in [
    ('R57D1', 'D1 · The name as huge faint type, cropped by the bottom edge', g54.D1),
    ('R57D2', 'D2 · A navy strip with the mark\'s slant repeated across it', g54.D2),
    ('R57D3', 'D3 · A navy band mirroring the top, the faint mark on the left', g54.D3),
    ('R57D4', 'D4 · A company seal like a dispatch stamp, bottom right', g54.D4),
    ('R57D5', 'D5 · The gold mark between two hairlines, the line under it', g54.D5),
    ('R57D6', 'D6 · A navy strip with the three gold slashes at its right end', g54.D6),
]:
    BOARDS[key] = (lambda t=t, fn=fn: compose_foot(t, fn))

for key, t, css in OPTS:
    BOARDS[key] = (lambda t=t, css=css: compose(t, css))


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

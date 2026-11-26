"""Round 67 (Nov 26): fewer rows in a tile, and VMMS's full name on one line. "Vehicle Maintenance Management
System" is 288px at 14px semibold; a four-across tile has 238px. So either the tiles widen (three across) or the
name becomes a small label, and the description goes or shrinks. Launcher as picked (Q1, J1, P5, K3a, E1g).
python3 -I gen67.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen53 as g53  # noqa: E402
import gen64 as g64  # noqa: E402
from data49 import board, CORAZON  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
SHORT = {'BMS': 'Bookings and trips', 'VMMS': 'Planned maintenance', 'VRMS': 'Truck repairs'}
THREE = '.lay{grid-template-columns:repeat(3,384px)}.t1 .nm{white-space:nowrap}'


def build(title, css, short_in_name=False, short_line=False):
    lcss, html = g64.launcher()
    for it in g53.items(CORAZON, False):
        ln = f'<span class="ln">{it["line"]}</span>'
        if short_in_name:  # the code and a short line; the full name goes to the tooltip and the accessible name
            html = html.replace(f'<span class="nm">{it["name"]}</span>{ln}', f'<span class="nm">{SHORT[it["code"]]}</span>')
            html = html.replace(f'<a class="t1" href="#" data-key="', f'<a class="t1" href="#" title="{it["name"]}" data-k="', 1)
        else:
            html = html.replace(ln, f'<span class="ln">{SHORT[it["code"]]}</span>' if short_line else '')
    html = html.replace('data-k="', 'data-key="')
    return title, lcss + css, html


OPTS = [
    ('R67N1', 'N1 · Three across: the full name on one line, no description',
     THREE + '.t1{height:212px}.t1 .nm{font-size:15px}', {}),
    ('R67N2', 'N2 · Three across: the full name on one line, then a short line ("Planned maintenance")',
     THREE + '.t1{height:236px}.t1 .nm{font-size:15px}', {'short_line': True}),
    ('R67N3', 'N3 · Four across kept: the full name as a small one line label, no description',
     '.t1{height:212px}.t1 .nm{margin-top:10px;font:600 10px "IBM Plex Mono",monospace;letter-spacing:.01em;text-transform:uppercase;color:#5b6779;white-space:nowrap}', {}),
    ('R67N4', 'N4 · Four across kept: the code and a short line; the full name in the tooltip',
     '.t1{height:200px}.t1 .nm{font-size:15px;font-weight:600;color:#334155}', {'short_in_name': True}),
]

for key, t, css, kw in OPTS:
    BOARDS[key] = (lambda t=t, css=css, kw=kw: build(t, css, **kw))


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

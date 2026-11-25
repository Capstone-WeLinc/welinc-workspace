"""Round 66 (Nov 26): A3 only, each number key arriving with its own tile. New one line descriptions for the
systems (the current ones name people, like "mechanics"); four wordings on the launcher as picked.
python3 -I gen66.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen53 as g53  # noqa: E402
import gen59 as g59  # noqa: E402
import gen63 as g63  # noqa: E402
import gen64 as g64  # noqa: E402
from gen64 import T  # noqa: E402
from data49 import board, CORAZON  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}

# ---------------------------------------------------------------- A3, keys with their tiles
A3 = (f'''.sin{{animation:fadeOut {T(.25)} ease {T(.3)} both}}
.lau .hd{{animation:fadeIn {T(.3)} ease {T(.5)} both}}.lau .ft{{animation:fadeIn {T(.4)} ease {T(.9)} both}}
@keyframes deal{{from{{opacity:0;transform:translateX(-40px)}}to{{opacity:1;transform:none}}}}''' + g64.tiles('deal', .55, .09))
BOARDS['R66A3'] = lambda: g64.make('A3 · The tiles deal in one by one, each number key arriving with its own tile', A3, '')

# ---------------------------------------------------------------- the descriptions
SETS = [
    ('R66D1', 'D1 · What you do there: a short verb line each',
     {'BMS': 'Take bookings and plan every trip', 'VMMS': 'Schedule services before anything breaks', 'VRMS': 'Log a repair and see it through'}),
    ('R66D2', 'D2 · From start to finish: where the work begins and ends',
     {'BMS': 'From customer booking to finished trip', 'VMMS': 'From service plan to road-ready truck', 'VRMS': 'From breakdown report to verified repair'}),
    ('R66D3', 'D3 · The work as things: what the system keeps',
     {'BMS': 'Bookings, trips and job orders', 'VMMS': 'Service schedules and maintenance records', 'VRMS': 'Repair tickets, parts and repair costs'}),
    ('R66D4', 'D4 · Short: two or three words',
     {'BMS': 'Bookings and trips', 'VMMS': 'Planned maintenance', 'VRMS': 'Truck repairs'}),
]


def lines_board(title, lines):
    css, html = g64.launcher()
    for it in g53.items(CORAZON, False):
        html = html.replace(f'<span class="ln">{it["line"]}</span>', f'<span class="ln">{lines[it["code"]]}</span>')
    return title, css, html


for key, t, lines in SETS:
    BOARDS[key] = (lambda t=t, lines=lines: lines_board(t, lines))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in BOARDS.items():
        if ONLY and name not in ONLY:
            continue
        title, css, body = fn()
        logic = g64.LOGIC if name == 'R66A3' else 'renderVals() { return {}; }'
        (OUT / f'{name}.dc.html').write_text(board(title, css, body, logic=logic, h=900))
        print(name, title)


if __name__ == '__main__':
    main()

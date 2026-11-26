"""Round 69 (Nov 26): three to a row picked. The name label a little bigger (10px to 11.5px). Suite management
reads "Suite management" in full, no "N to review" count (the bottom says which systems it covers), and a new
icon: S1 to S5 on their own board, S1 (people) on the person boards until picked.
python3 -I gen69.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen63  # noqa: E402,F401  (patches gen52icons.icon)
import gen52icons as gi  # noqa: E402
import gen68 as g68  # noqa: E402
from data49 import board  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
N, GOLD, W = '#0f1445', '#e8b800', '#fff'

SUITE_ICONS = {
    'S1': ('People', f'<circle cx="43" cy="21" r="7.5" fill="{GOLD}"/><path d="M31 52v-2.5a12 12 0 0 1 24 0V52z" fill="{GOLD}"/>'
                     f'<circle cx="25" cy="24" r="9" fill="{N}"/><path d="M9 55v-3.5a16 16 0 0 1 32 0V55z" fill="{N}"/>'),
    'S2': ('ID badge', f'<rect x="13" y="11" width="38" height="46" rx="6" fill="{N}"/><rect x="26" y="6" width="12" height="9" rx="2.5" fill="{GOLD}"/>'
                       f'<circle cx="32" cy="29" r="7" fill="{GOLD}"/><path d="M22 43h20M25 49h14" stroke="{W}" stroke-width="3" stroke-linecap="round"/>'),
    'S3': ('Key', f'<circle cx="21" cy="32" r="13" fill="{N}"/><circle cx="21" cy="32" r="5" fill="{GOLD}"/>'
                  f'<rect x="31" y="28" width="27" height="8" rx="2" fill="{N}"/><rect x="48" y="35" width="6" height="9" rx="1.5" fill="{N}"/>'
                  f'<rect x="39" y="35" width="5" height="6" rx="1.5" fill="{N}"/>'),
    'S4': ('Controls', f'<path d="M10 18h44M10 32h44M10 46h44" stroke="{N}" stroke-width="5" stroke-linecap="round"/>'
                       f'<circle cx="24" cy="18" r="6.5" fill="{GOLD}"/><circle cx="42" cy="32" r="6.5" fill="{N}"/><circle cx="42" cy="32" r="2.5" fill="{W}"/>'
                       f'<circle cx="28" cy="46" r="6.5" fill="{N}"/><circle cx="28" cy="46" r="2.5" fill="{W}"/>'),
    'S5': ('Team tree', f'<path d="M32 20v8M14 28h36M14 28v8M32 28v8M50 28v8" stroke="{N}" stroke-width="3" fill="none" stroke-linecap="round"/>'
                        f'<rect x="23" y="7" width="18" height="14" rx="3.5" fill="{N}"/><rect x="5" y="36" width="18" height="14" rx="3.5" fill="{N}"/>'
                        f'<rect x="23" y="36" width="18" height="14" rx="3.5" fill="{GOLD}"/><rect x="41" y="36" width="18" height="14" rx="3.5" fill="{N}"/>'),
}
PICK = 'S5'
_icon = gi.icon


def suite_icon(key, size):
    return f'<svg class="ai" width="{size}" height="{size}" viewBox="0 0 64 64" aria-hidden="true">{SUITE_ICONS[key][1]}</svg>'


def icon(kind, code, size, dark):
    return suite_icon(PICK, size) if code == 'Suite' else _icon(kind, code, size, dark)


gi.icon = icon

EXTRA = ('.t1 .nm{font-size:11.5px!important;letter-spacing:.02em!important}'
         '.t1 .rl .ct{color:#5b6779;font-weight:500}')


def person(first, full, ini, systems, suite, what):
    if suite:
        covers = [c for c, r in systems if r == 'Admin'] or ['BMS', 'VMMS', 'VRMS']
        scope = 'For ' + (', '.join(covers[:-1]) + ' and ' + covers[-1] if len(covers) > 1 else covers[0])
        suite = (suite[0], scope)
    css, html = g68.page(full, ini, systems, suite, 3)
    html = html.replace('<b>Suite</b>', '<b>Suite management</b>')
    return f'{full} ({what}) · 3 to a row', css + EXTRA, html


for first, full, ini, systems, suite, what in g68.PEOPLE:
    BOARDS[f'R69{first}'] = (lambda a=(first, full, ini, systems, suite, what): person(*a))


def icons_board():
    """Five Suite management tiles side by side, one per icon."""
    css, html = person(*g68.PEOPLE[3])[1:]
    tile = html[html.find('<a class="t1"', html.find('Suite management') - 600):]
    start = html.rfind('<a class="t1"', 0, html.find('<b>Suite management</b>'))
    end = html.find('</a>', start) + 4
    tile = html[start:end]
    cells = ''
    for k, (label, _) in SUITE_ICONS.items():
        t = tile.replace(tile[tile.find('<svg class="ai"'):tile.find('</svg>', tile.find('<svg class="ai"')) + 6], suite_icon(k, 52))
        cells += f'<div class="cell"><p class="gl" style="margin:0 0 8px">{k} · {label}</p>{t}</div>'
    grid = f'<div class="opts">{cells}</div>'
    body = html[:html.find('<div class="lay">')] + grid + html[html.find('</div>', html.find('<div class="lay">') + 10) + 6:]
    body = body.replace('<h2>Your systems</h2><span>2</span>', '<h2>Suite management: pick an icon</h2>')
    lay_end = body.find('<div class="ft"')
    return ('Suite management icon: S1 people, S2 ID badge, S3 key, S4 controls, S5 team tree',
            css + '.opts{display:grid;grid-template-columns:repeat(3,384px);gap:24px 24px}.opts .t1{display:flex}', body[:lay_end] + body[lay_end:])


BOARDS['R69SuiteIcons'] = icons_board


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

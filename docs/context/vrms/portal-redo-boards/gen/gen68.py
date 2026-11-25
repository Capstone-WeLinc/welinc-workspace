"""Round 68 (Nov 26): N3 picked (the full name as a small one line label, no description). The launcher three to a
row and four to a row, for each kind of person: one system as its admin, two systems, three systems, admin of two,
three systems plus admin of one, and a suite admin with no systems. (One system and no admin role skips the
launcher.) Launcher as picked: Q1, J1, P5, K3a, E1g. python3 -I gen68.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g51  # noqa: E402
import gen53 as g53  # noqa: E402
import gen56 as g56  # noqa: E402
import gen59 as g59  # noqa: E402
import gen60 as g60  # noqa: E402
import gen63 as g63  # noqa: E402
from data49 import board  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
NAVY = '15,20,69'
FULL = {'BMS': 'Booking Management System', 'VMMS': 'Vehicle Maintenance Management System', 'VRMS': 'Vehicle Repair Management System'}
N3 = ('.t1{height:212px}.t1 .ln{display:none}'
      '.t1 .nm{margin-top:10px;font:600 10px "IBM Plex Mono",monospace;letter-spacing:.01em;text-transform:uppercase;color:#5b6779;white-space:nowrap}')

PEOPLE = [
    ('Victor', 'Victor Ramos', 'VR', [('VRMS', 'Admin')], ('People, roles and access for VRMS', '2 to review'),
     'one system, its admin'),
    ('Danilo', 'Danilo Reyes', 'DR', [('VMMS', 'Operations'), ('VRMS', 'Mechanic')], None, 'two systems'),
    ('Corazon', 'Corazon Villareal', 'CV', [('BMS', 'Operations'), ('VMMS', 'Operations'), ('VRMS', 'Chief Mechanic')], None,
     'three systems'),
    ('Felicidad', 'Felicidad Roxas', 'FR', [('VMMS', 'Admin'), ('VRMS', 'Admin')], ('People, roles and access for VMMS and VRMS', '4 to review'),
     'admin of two systems'),
    ('Armando', 'Armando Cruz', 'AC', [('BMS', 'Admin'), ('VMMS', 'Operations'), ('VRMS', 'Chief Mechanic')],
     ('People, roles and access for BMS', '1 to review'), 'three systems, admin of one'),
    ('Leonora', 'Leonora Castillo', 'LC', [], ('People, roles and access for BMS, VMMS and VRMS', '5 to review'),
     'suite admin, no systems'),
]


def page(full, ini, systems, suite, cols):
    its = [dict(code=c, name=FULL[c], line='', role=r, count=None) for c, r in systems]
    if suite:
        its.append(dict(code='Suite', name='People, roles and access', line=suite[0], role=None, count=suite[1]))
    lcss, lhtml = g53.L1(its, 'plain')
    lhtml = g59.numbered(lhtml.replace(g53.HINT, ''))
    css = ''
    n = len(systems)
    if cols == 3:
        css += '.lay{grid-template-columns:repeat(3,384px)}'
        if n == 3 and suite:  # Suite management wraps to its own row, under its own label
            css += ('.lay>a{grid-row:auto}.lay>.gl:first-of-type{grid-column:1/4!important;grid-row:1}'
                    '.lay>a:not(:last-of-type){grid-row:2}.lay>.gl:nth-of-type(2){grid-column:1/4!important;grid-row:3;margin-top:12px}'
                    '.lay>a:last-of-type{grid-row:4;grid-column:1}')
    if n == 0:  # a suite admin with no systems: no group labels, the heading names the area
        lhtml = lhtml.replace('<p class="gl" style="grid-column:1/1">Systems</p>', '').replace('<p class="gl" style="grid-column:1/2">Admin</p>', '')
        lhtml = lhtml.replace('<h2>Your systems</h2><span>0</span>', '<h2>Suite management</h2>')
    boxes = ''.join(g63.box(*b, detail=False) for b in g63.PYRAMID)
    art = f'<svg class="bx" viewBox="-2 48 488 332" fill="none" stroke-width="2" stroke-linejoin="round" aria-hidden="true">{boxes}</svg>'
    foot = f'<div class="ft" aria-hidden="true">{art}<div class="hl"></div><span class="est">EST. 2018</span></div>'
    top = g59.TOP_HTML.replace('Corazon Villareal', full).replace('>CV<', f'>{ini}<')
    html = f'<div class="pg">{top}<div class="w below">{lhtml}</div>{foot}<span class="co"><b>WeLinc Logistics</b></span></div>'
    k3a = '.ft .bx{right:calc(50% - 600px);height:200px}' + g63.ink(f'rgba({NAVY},.12)', 'rgba(232,184,0,.16)', 'rgba(232,184,0,.3)')
    return (g51.CSS + g53.COMMON + g56.TOP + g59.Q1 + lcss + g59.P5 + g60.BASE + g63.FOOT_CSS + k3a + N3 + css
            + '.li{width:52px;height:52px;display:flex;align-items:center;color:#0f1445}'), html


for first, full, ini, systems, suite, what in PEOPLE:
    for cols in (3, 4):
        key = f'R68{first}{cols}'
        t = f'{full} ({what}) · {cols} to a row'
        BOARDS[key] = (lambda t=t, full=full, ini=ini, systems=systems, suite=suite, cols=cols: (t, *page(full, ini, systems, suite, cols)))


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

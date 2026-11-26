"""Round 52, the icon spot: what sits where the navy squares were. Each board shows the same three systems
as G1 tiles (plus the navy Suite management tile, so the icon is seen on dark too) and as G2 cards.
python3 -I gen52icons.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g  # noqa: E402
from data49 import board, CORAZON, I, ic  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
NAVY, GOLD = '#0f1445', '#e8b800'
SUITE = dict(code='Suite', name='Suite management', line='People, roles and access for your systems', role='4 to review')


def svg(inner, size):
    return f'<svg class="ai" width="{size}" height="{size}" viewBox="0 0 64 64" aria-hidden="true">{inner}</svg>'


def scaled(code, fg, hole, k=.86):
    o = 32 * (1 - k)
    return f'<g transform="translate({o} {o}) scale({k})">{g.glyph(code, fg, GOLD, hole)}</g>'


def vehicle(code, fg, bg):
    s = f'fill="none" stroke="{fg}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"'
    wheel = lambda x, y: f'<circle cx="{x}" cy="{y}" r="4.5" fill="{bg}" stroke="{fg}" stroke-width="2.4"/>'  # noqa: E731
    if code == 'BMS':  # wing van with a drop pin
        return (f'<path d="M5 24h33v19H5zM38 29h11l8 8v6H38z" {s}/><path d="M41 32h7l4 4h-11z" {s}/>'
                f'{wheel(14, 45)}{wheel(29, 45)}{wheel(49, 45)}'
                f'<path d="M21 5a6 6 0 0 0-6 6c0 5 6 9 6 9s6-4 6-9a6 6 0 0 0-6-6z" fill="{GOLD}"/><circle cx="21" cy="11" r="2" fill="{bg}"/>')
    if code == 'VMMS':  # L300 with its service check done
        return (f'<path d="M5 25h35l12 10v8H5z" {s}/><path d="M37 28l9 7h-9z" {s}/>{wheel(16, 45)}{wheel(43, 45)}'
                f'<circle cx="51" cy="13" r="8" fill="{GOLD}"/><path d="m47 13 3 3 5-6" fill="none" stroke="{bg}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>')
    if code == 'VRMS':  # van raised on the lift
        return (f'<path d="M7 14h30v18H7zM37 19h10l8 8v5H37z" {s}/>{wheel(16, 35)}{wheel(46, 35)}'
                f'<path d="M3 44h58" stroke="{GOLD}" stroke-width="3.5" stroke-linecap="round"/>'
                f'<path d="M10 44v14M54 44v14" {s}/>')
    return (f'<path d="M32 9c5 4 11 6 17 6v14c0 12-7 19-17 23-10-4-17-11-17-23V15c6 0 12-2 17-6z" {s}/>'
            f'<path d="m25 31 5 5 10-11" fill="none" stroke="{GOLD}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')


LUCIDE = {'BMS': I['cal'], 'VMMS': I['truck'], 'VRMS': I['wrench'], 'Suite': I['shield']}


def icon(kind, code, size, dark):
    fg = '#fff' if dark else NAVY
    bg = NAVY if dark else '#fff'
    if kind == 'plain':
        return svg(g.glyph(code, fg, GOLD, bg), size)
    if kind == 'frame':
        line = 'rgba(255,255,255,.28)' if dark else '#d5dbe7'
        return svg(f'<rect x="1" y="1" width="62" height="62" rx="17" fill="none" stroke="{line}" stroke-width="1.5"/>{scaled(code, fg, bg)}', size)
    if kind == 'disc':
        disc = 'rgba(255,255,255,.1)' if dark else '#fbf1c7'
        return svg(f'<circle cx="32" cy="32" r="32" fill="{disc}"/>{scaled(code, fg, "#fbf1c7" if not dark else NAVY)}', size)
    if kind == 'vehicle':
        return svg(vehicle(code, fg, bg), size)
    if kind == 'line':
        return f'<span class="li">{ic(LUCIDE[code], 30, 1.75)}</span>'
    return '<span class="rule"></span>'


OPTS = [
    ('R52IconPlain', 'plain', 'I1 · The drawn mark alone, navy and gold, no square behind it'),
    ('R52IconFrame', 'frame', 'I2 · The drawn mark in a thin outlined frame (no fill)'),
    ('R52IconDisc', 'disc', 'I3 · The drawn mark on a soft gold disc'),
    ('R52IconVehicle', 'vehicle', 'I4 · A line drawn vehicle per system (wing van, L300, van on the lift), gold detail'),
    ('R52IconLine', 'line', 'I5 · Standard line icons (calendar, truck, wrench, shield), the most conventional'),
    ('R52IconNone', 'none', 'I6 · No icon: a short gold rule, the system code is the mark'),
]

CSS = '''.pg{height:580px;min-height:580px;padding:44px 120px 0}
.tl{height:256px}
.tl.su{background:#0f1445;box-shadow:0 14px 30px -12px rgba(15,20,69,.5)}
.tl.su b,.tl.su .nm{color:#fff}.tl.su .ln,.tl.su .rl{color:rgba(255,255,255,.7)}.tl.su .rl strong{color:#e8b800}
.li{width:52px;height:52px;display:flex;align-items:center;color:#0f1445}
.su .li{color:#fff}.su .li svg :last-child{color:#e8b800}
.ac .li{width:64px;height:64px;justify-content:center;grid-row:span 3}
.rule{display:block;width:28px;height:4px;border-radius:2px;background:#e8b800;margin-top:6px}
.ac .rule{grid-row:span 3;margin-top:12px}
.none .tl b{font-size:34px;margin-top:20px}.none .ac{grid-template-columns:40px 1fr}
.row2{margin-top:32px}'''


def build(kind, title):
    gcss, _ = g.G2()
    tiles = ''
    for s in CORAZON + [SUITE]:
        su = s is SUITE
        rl = '<strong>4 to review</strong>' if su else f'Your role: <strong>{s["role"]}</strong>'
        tiles += (f'<a class="tl{" su" if su else ""}" href="#">{icon(kind, s["code"], 58, su)}<b>{s["code"]}</b>'
                  f'<span class="nm">{s["name"]}</span><span class="ln">{s["line"]}</span><span class="rl">{rl}</span></a>')
    cards = ''.join(f'<a class="ac" href="#">{icon(kind, s["code"], 64, False)}<span class="t"><b>{s["code"]}</b><span>{s["role"]}</span></span>'
                    f'<span class="nm">{s["name"]}</span><span class="ln">{s["line"]}</span></a>' for s in CORAZON)
    body = (f'<div class="pg {kind}"><div class="hd"><h2>G1 tiles</h2><span>with Suite management for an admin</span></div><div class="tiles">{tiles}</div>'
            f'<div class="hd row2"><h2>G2 cards</h2></div><div class="cards">{cards}</div></div>')
    return title, g.CSS + gcss + CSS, body


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, kind, title in OPTS:
        if ONLY and name not in ONLY:
            continue
        t, css, body = build(kind, title)
        (OUT / f'{name}.dc.html').write_text(board(t, css, body, h=580))
        print(name, t)


if __name__ == '__main__':
    main()

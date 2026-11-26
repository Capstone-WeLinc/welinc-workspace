"""Round 59 (Nov 26): new ideas, not tweaks of the mark. The 88px band (Q1) gets a surface or a job of its own;
the footer gets something other than the company name. "Open one to start..." is gone from the heading row.
L1 tiles, I1 icons. python3 -I gen59.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g  # noqa: E402
import gen53 as g53  # noqa: E402
import gen56 as g56  # noqa: E402
from data49 import board, CORAZON  # noqa: E402
from parts import V_L300, V_VAN, V_WING  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
NAME = 'WeLinc Logistics'
Q1 = '.tp{height:88px}.tp .row{height:88px}.tp .mk{top:-110px;height:300px}.below{padding-top:36px}'
NOMARK = '.tp .mk{display:none}'
LINE_CSS = '.co{font-size:13px;color:#5b6779}.co b{color:#0f172a;font-weight:700}'
LINE = f'<span class="co"><b>{NAME}</b> · Since 2018</span>'
PLAIN_CSS = '.fl0{position:absolute;left:0;right:0;bottom:20px}'
PLAIN = f'<div class="fl0"><div class="w">{LINE}</div></div>'


# ---------------------------------------------------------------- drawings
def depot(stroke, sw=1.5):
    """Line drawing of a depot: a sawtooth roof warehouse with three roller doors, the office, a gabled shed."""
    doors = ''.join(f'<rect x="{x}" y="50" width="50" height="37"/>' + ''.join(
        f'<path d="M{x} {y}h50"/>' for y in range(56, 87, 6)) for x in (60, 150, 240))
    saw = 'M40 87V30' + ''.join(f'L{x + 40} 12V30' for x in range(40, 300, 40)) + 'V87'
    win = ''.join(f'<rect x="{x}" y="{y}" width="14" height="10"/>' for x in (334, 360, 386) for y in (54, 70))
    shed = 'M440 87V40L540 18L640 40V87'
    sdoors = '<rect x="462" y="52" width="60" height="35"/><rect x="558" y="52" width="60" height="35"/>'
    return (f'<g fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round">'
            f'<path d="M0 87.2H680"/><path d="{saw}"/>{doors}<rect x="320" y="42" width="100" height="45"/>{win}'
            f'<path d="{shed}"/>{sdoors}</g>')


def header(deco='', mid='', mark=False):
    mk = g56.MK if mark else ''
    return f'<header class="tp">{mk}{deco}<div class="w"><div class="row">{g56.LOCK}{mid}{g56.TOOLS}</div></div></header>'


def page(title, top_css, top_html, foot_css=PLAIN_CSS, foot_html=PLAIN):
    lcss, lhtml = g53.L1(g53.items(CORAZON, False), 'plain')
    lhtml = lhtml.replace(g53.HINT, '')
    body = f'<div class="pg">{top_html}<div class="w below">{lhtml}</div>{foot_html}</div>'
    return title, g.CSS + g53.COMMON + g56.TOP + Q1 + top_css + lcss + LINE_CSS + foot_css, body


# ---------------------------------------------------------------- the band (88px, the bar is the whole band)
def A2():
    """Container siding: the band ribbed like a shipping container wall, lit from the right."""
    css = NOMARK + '''.tp:before{content:"";position:absolute;inset:0;z-index:0;
background:repeating-linear-gradient(90deg,rgba(255,255,255,.06) 0 3px,rgba(255,255,255,.02) 3px 9px,rgba(0,0,0,.22) 9px 11px,transparent 11px 18px);
-webkit-mask:linear-gradient(90deg,transparent 30%,#000 85%);mask:linear-gradient(90deg,transparent 30%,#000 85%)}'''
    return css, header()


def A3():
    """The depot skyline: a faint line drawing of our depot standing on the band's bottom edge, right side."""
    css = NOMARK + '.tp .dp{position:absolute;left:calc(50% - 220px);bottom:0;height:70px;z-index:0}'
    return css, header(f'<svg class="dp" viewBox="0 0 680 88" aria-hidden="true">{depot("rgba(255,255,255,.16)")}</svg>')


def A4():
    """Dispatch board: a fine ruled grid like the planning board in the dispatch office, fading in from the left."""
    css = NOMARK + '''.tp:before{content:"";position:absolute;inset:0;z-index:0;
background:linear-gradient(rgba(255,255,255,.07) 1px,transparent 1px) 0 0/22px 22px,
linear-gradient(90deg,rgba(255,255,255,.07) 1px,transparent 1px) 0 0/22px 22px;
-webkit-mask:linear-gradient(90deg,transparent 25%,#000 90%);mask:linear-gradient(90deg,transparent 25%,#000 90%)}'''
    return css, header()


def A5():
    """The band gets a job: a status pill for the three systems. Green when all run; amber names the one that doesn't."""
    css = '''.tp .stt{order:2;border:0;cursor:pointer;font-family:inherit;display:flex;align-items:center;gap:10px;height:36px;padding:0 14px 0 12px;
border-radius:999px;background:rgba(255,255,255,.07);box-shadow:inset 0 0 0 1px rgba(255,255,255,.1);font-size:13px;font-weight:500;color:rgba(255,255,255,.85)}
.tp .stt i{width:8px;height:8px;border-radius:50%;background:#4ade80;box-shadow:0 0 0 3px rgba(74,222,128,.18)}
.tp .row .sp{order:1}.tp .row .hb{order:3}.tp .row .me{order:4}'''
    mid = '<button class="stt" type="button"><i></i>All systems running</button>'
    return css, header(mid=mid, mark=True)


def A6():
    """Livery pinstripes: a gold and a white pinstripe run the band's bottom and kick up on the mark's slant at the right."""
    css = NOMARK + '.tp .ps{position:absolute;inset:0;width:100%;height:100%;z-index:0}'
    svg = ('<svg class="ps" viewBox="0 0 1440 88" aria-hidden="true" fill="none">'
           '<path d="M0 74H1346L1382 0" stroke="#e8b800" stroke-width="3"/>'
           '<path d="M0 81H1360L1400 0" stroke="rgba(255,255,255,.35)" stroke-width="1.5"/></svg>')
    return css, header(svg)


for key, t, fn in [
    ('R59A1', 'A1 · Container siding: the band ribbed like a container wall, lit from the right', A2),
    ('R59A2', 'A2 · Depot skyline: our depot as a faint line drawing on the band\'s bottom edge', A3),
    ('R59A3', 'A3 · Dispatch board: a fine ruled grid, like the planning board in dispatch', A4),
    ('R59A4', 'A4 · The band gets a job: a status pill for the three systems', A5),
    ('R59A5', 'A5 · Livery pinstripes: gold and white, kicking up on the mark\'s slant at the right', A6),
]:
    BOARDS[key] = (lambda t=t, fn=fn: page(t, *fn()))


# ---------------------------------------------------------------- footers (on the page, not the company name)
TOP_CSS, TOP_HTML = '', header(mark=True)


def F1():
    """The fleet parked along the floor: the L300, the closed van and the wing van, quiet and still."""
    css = '''.ff{position:absolute;left:0;right:0;bottom:0;height:200px}
.ff .fl{position:absolute;left:0;right:0;bottom:44px;height:1px;background:#d9dee8}
.ff svg{position:absolute;right:calc(50% - 600px);bottom:44px;height:118px;}
.ff .co{position:absolute;left:calc(50% - 600px);bottom:16px}'''
    svg = (f'<svg viewBox="0 0 560 70" aria-hidden="true"><defs>{V_L300}{V_VAN}{V_WING}</defs>'
           '<use href="#l300" x="0" y="22" width="96" height="50"/><use href="#van" x="120" y="14" width="138" height="56"/>'
           '<use href="#wing" x="290" y="6" width="172" height="64"/></svg>')
    return css, f'<div class="ff"><div class="fl"></div>{svg}{LINE}</div>'


def F2():
    """The depot at the end of the page: the same building as a navy line drawing, the company line beside it."""
    css = '''.ff{position:absolute;left:0;right:0;bottom:0;height:220px}
.ff svg{position:absolute;right:calc(50% - 680px);bottom:-1px;height:128px}
.ff .co{position:absolute;left:calc(50% - 600px);bottom:22px}'''
    return css, f'<div class="ff"><svg viewBox="0 0 680 88" aria-hidden="true">{depot("rgba(15,20,69,.16)", 0.9)}</svg>{LINE}</div>'


PIN = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
       '<path d="M20 10c0 5-8 12-8 12s-8-7-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>')


def F3():
    """Our branches: Marikina, Sta. Rosa and Pulilan in a row, each with its town; the company line under them."""
    br = [('Marikina', 'Marikina City, Metro Manila'), ('Sta. Rosa', 'Sta. Rosa, Laguna'), ('Pulilan', 'Pulilan, Bulacan')]
    css = '''.ff{position:absolute;left:0;right:0;bottom:0;height:190px;border-top:1px solid #e3e7ef}
.ff .w{display:flex;flex-direction:column;height:190px;padding:28px 0 20px}
.ff h3{margin:0 0 14px;font:600 11px "IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase;color:#7a8597}
.ff .bs{display:grid;grid-template-columns:repeat(3,282px);gap:24px}
.ff .b{display:flex;gap:10px;color:#0f1445}.ff .b b{display:block;font-size:14px;font-weight:700}
.ff .b span{display:block;margin-top:2px;font-size:13px;color:#5b6779}
.ff .co{margin-top:auto}'''
    cols = ''.join(f'<div class="b">{PIN}<div><b>{n}</b><span>{t}</span></div></div>' for n, t in br)
    return css, f'<div class="ff"><div class="w"><h3>Our branches</h3><div class="bs">{cols}</div>{LINE}</div></div>'


def F4():
    """Your account at a glance: when you last signed in, and what to do if that wasn't you."""
    css = '''.ff{position:absolute;left:0;right:0;bottom:0;height:120px;border-top:1px solid #e3e7ef}
.ff .w{height:120px;display:flex;align-items:center;gap:14px}
.ff .ic{width:40px;height:40px;border-radius:12px;background:#fff;box-shadow:0 0 0 1px #e3e7ef;display:grid;place-items:center;color:#0f1445}
.ff .t{font-size:14px;color:#0f172a}.ff .t span{display:block;margin-top:2px;font-size:13px;color:#5b6779}
.ff .t a{color:#0f1445;font-weight:600;text-decoration:underline;text-underline-offset:3px}
.ff .co{margin-left:auto}'''
    shield = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
              '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
              '<path d="m9 12 2 2 4-4"/></svg>')
    return css, (f'<div class="ff"><div class="w"><span class="ic">{shield}</span><p class="t" style="margin:0">Last signed in Tuesday, Nov 25 at 9:14 AM'
                 f'<span>Not you? <a href="#">Change your password</a></span></p>{LINE}</div></div>')


def F5():
    """Help where people get stuck: a missing system, and how the suite works. Two quiet rows, the company line under."""
    css = '''.ff{position:absolute;left:0;right:0;bottom:0;height:170px}
.ff .w{height:170px;display:flex;flex-direction:column;padding-bottom:20px}
.ff .hs{display:grid;grid-template-columns:repeat(2,1fr);gap:24px;padding-top:4px}
.ff .h{display:flex;gap:14px;align-items:flex-start;padding:18px 20px;border-radius:16px;box-shadow:inset 0 0 0 1px #e3e7ef}
.ff .h svg{flex:none;color:#0f1445;margin-top:1px}
.ff .h b{display:block;font-size:14px;color:#0f172a}.ff .h span{display:block;margin-top:3px;font-size:13px;color:#5b6779}
.ff .co{margin-top:auto}'''
    key = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
           '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6M15.5 7.5l3 3L22 7l-3-3"/></svg>')
    book = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
            '<path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2zM22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z"/></svg>')
    return css, (f'<div class="ff"><div class="w"><div class="hs">'
                 f'<div class="h">{key}<div><b>Missing a system?</b><span>Your system admin can give you access. You\'ll see it here once they do.</span></div></div>'
                 f'<div class="h">{book}<div><b>New to the suite?</b><span>One sign in opens every system you have. <a href="#" style="color:#0f1445;font-weight:600;text-decoration:underline;text-underline-offset:3px">How it works</a></span></div></div>'
                 f'</div>{LINE}</div></div>')


def F6():
    """Loading bay floor: the tile columns carry on as painted bay lines, a stop line across, bay numbers on the floor."""
    xs = [108, 414, 720, 1026, 1332]
    lines = ''.join(f'<i style="left:{x - 1}px"></i>' for x in xs)
    nums = ''.join(f'<em style="left:{x + 12}px">BAY 0{n + 1}</em>' for n, x in enumerate(xs[:4]))
    css = '''.ff{position:absolute;left:0;right:0;bottom:0;height:250px}
.ff .stop{position:absolute;left:96px;right:96px;top:0;height:3px;background:repeating-linear-gradient(90deg,rgba(232,184,0,.55) 0 30px,transparent 30px 44px)}
.ff i{position:absolute;top:0;bottom:0;width:3px;background:rgba(232,184,0,.45)}
.ff em{position:absolute;top:22px;width:258px;text-align:center;font:600 24px "IBM Plex Mono",monospace;font-style:normal;letter-spacing:.12em;color:#e3e7ef}
.ff .co{position:absolute;left:120px;bottom:20px}'''
    return css, f'<div class="ff"><div class="stop"></div>{lines}<span aria-hidden="true">{nums}</span>{LINE}</div>'


for key, t, fn in [
    ('R59F1', 'F1 · The fleet parked along the floor: L300, closed van, wing van in their livery', F1),
    ('R59F2', 'F2 · The depot at the end of the page, a navy line drawing', F2),
    ('R59F3', 'F3 · Our branches: Marikina, Sta. Rosa and Pulilan with their towns', F3),
    ('R59F4', 'F4 · Your account: when you last signed in, and "Not you?"', F4),
    ('R59F5', 'F5 · Help where people get stuck: a missing system, how the suite works', F5),
    ('R59F6', 'F6 · Loading bay floor: the tile columns carry on as painted bay lines', F6),
]:
    BOARDS[key] = (lambda t=t, fn=fn: page(t, TOP_CSS, TOP_HTML, *fn()))

# ---------------------------------------------------------------- the page itself (Q1 top as picked, plain company line)
def body(title, css, edit=lambda h: h):
    lcss, lhtml = g53.L1(g53.items(CORAZON, False), 'plain')
    lhtml = edit(lhtml.replace(g53.HINT, ''))
    b = f'<div class="pg">{TOP_HTML}<div class="w below">{lhtml}</div>{PLAIN}</div>'
    return title, g.CSS + g53.COMMON + g56.TOP + Q1 + lcss + LINE_CSS + PLAIN_CSS + css, b


P1 = '''.lay{grid-template-columns:repeat(3,1fr)}.t1{height:300px;padding:30px}.t1 b{margin-top:24px;font-size:32px}
.t1 .nm{font-size:16px}.t1 .ln{font-size:14px}.t1 .rl{font-size:14px}'''
P2 = '''.below{position:absolute;left:50%;top:88px;bottom:64px;transform:translateX(-50%);display:flex;flex-direction:column;justify-content:center;padding:0 0 40px}
.lay{grid-template-columns:repeat(3,282px);justify-content:center}.hd{justify-content:center}'''
P3 = '''.gh{height:256px;padding:22px;border-radius:20px;border:1.5px dashed #cdd3df;display:flex;flex-direction:column;justify-content:flex-end;gap:6px;color:#5b6779}
.gh svg{margin-bottom:auto;color:#7a8597}.gh b{font-size:15px;color:#0f172a}.gh span{font-size:13px;line-height:1.45}'''
P4 = '''.lay{position:relative;z-index:0}
.lay:before{content:"";position:absolute;left:-13.5px;right:-13.5px;top:-18px;bottom:-44px;z-index:-1;
background:repeating-linear-gradient(90deg,rgba(232,184,0,.55) 0 3px,transparent 3px 306px)}
.lay:after{content:"";position:absolute;left:-13.5px;right:-13.5px;bottom:-44px;height:3px;z-index:-1;
background:repeating-linear-gradient(90deg,rgba(232,184,0,.55) 0 26px,transparent 26px 40px)}'''
P5 = '''.t1{position:relative}
.t1 kbd{position:absolute;top:20px;right:20px;min-width:26px;height:26px;padding:0 7px;border-radius:7px;display:grid;place-items:center;
font:600 12px "IBM Plex Mono",monospace;color:#5b6779;background:#f3f5f9;box-shadow:inset 0 0 0 1px #dfe3ec,inset 0 -2px 0 #dfe3ec}'''

GHOST = ('<div class="gh"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
         '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6M15.5 7.5l3 3L22 7l-3-3"/></svg>'
         '<b>Missing a system?</b><span>Your system admin can give you access. It shows up here once they do.</span></div>')


def ghost(h):
    """Put the dashed tile in the grid's empty slot (the grid div is the last element)."""
    return h[:-6] + GHOST + h[-6:]


def numbered(h):
    n = 0
    while '<a class="t1" href="#">' in h:
        n += 1
        h = h.replace('<a class="t1" href="#">', f'<a class="t1" href="#" data-key="{n}"><kbd aria-hidden="true">{n}</kbd>', 1)
    return h


for key, t, css, edit in [
    ('R59P1', 'P1 · Three systems share the full width, no empty fourth slot', P1, None),
    ('R59P2', 'P2 · The tiles sit in the middle of the page, not stuck under the band', P2, None),
    ('R59P3', 'P3 · The empty slot explains itself: a dashed "Missing a system?" tile', P3, ghost),
    ('R59P4', 'P4 · The tiles parked in bays: gold bay lines and a stop line on the page floor', P4, None),
    ('R59P5', 'P5 · Keyboard first: each tile carries its number key (1, 2, 3)', P5, numbered),
]:
    BOARDS[key] = (lambda t=t, css=css, edit=edit: body(t, css, edit or (lambda h: h)))


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

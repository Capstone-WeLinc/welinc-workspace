"""Round 54 (Nov 25, late night): L1 and M1 are picked. Bottom designs that carry "WeLinc Logistics · Since 2018",
and ways to tell the navbar from the blue band under it.
python3 -I gen54.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g  # noqa: E402
import gen53 as g53  # noqa: E402
from data49 import board, CORAZON  # noqa: E402
from parts import LOGO_POLY  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
MARK = f'<svg viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>'
NAME = 'WeLinc Logistics'


# ---------------------------------------------------------------- bottoms (each carries the company line)
def D1():
    """The name as huge type, cropped by the bottom edge; the company line above it."""
    css = '''.d1{position:absolute;left:0;right:0;bottom:0;height:250px;overflow:hidden;border-top:1px solid #e3e7ef}
.d1 .w{position:static}
.d1 .ln{position:absolute;left:50%;width:1200px;margin-left:-600px;top:22px;display:flex;justify-content:space-between;font-size:13px;color:#5b6779}
.d1 .ln b{color:#0f172a;font-weight:700}
.d1 .big{position:absolute;left:50%;transform:translateX(-50%);bottom:-36px;white-space:nowrap;font-size:150px;line-height:1;font-weight:800;font-style:italic;letter-spacing:-.045em;color:#e6e9f0}'''
    return css, (f'<div class="d1"><div class="ln"><span><b>{NAME}</b> · Since 2018</span><span>Privacy · Terms</span></div>'
                 f'<div class="big" aria-hidden="true">{NAME}</div></div>')


def D2():
    """A navy strip with the mark's slant repeated across it, the company line in white."""
    css = '''.d2{position:absolute;left:0;right:0;bottom:0;height:92px;background:#0f1445;color:#fff;overflow:hidden}
.d2:before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(113deg,rgba(255,255,255,.045) 0 30px,transparent 30px 60px)}
.d2 .w{height:92px;display:flex;align-items:center;gap:12px;font-size:13px;color:rgba(255,255,255,.7)}
.d2 svg{height:16px;fill:#e8b800}.d2 b{color:#fff}.d2 .r{margin-left:auto}'''
    return css, f'<div class="d2"><div class="w">{MARK}<span><b>{NAME}</b> · Since 2018</span><span class="r">Privacy · Terms</span></div></div>'


def D3():
    """A navy band that mirrors the top one: M1's mark, faint and cropped, now on the left."""
    css = '''.d3{position:absolute;left:0;right:0;bottom:0;height:150px;background:#0f1445;color:#fff;overflow:hidden}
.d3 .mk{position:absolute;left:calc(50% - 720px);bottom:-50px;height:260px;fill:rgba(255,255,255,.045)}
.d3 .w{height:150px;display:flex;align-items:flex-end;padding-bottom:26px;gap:12px}
.d3 .co{display:flex;flex-direction:column;gap:4px}.d3 .co b{font-size:16px;font-weight:800;font-style:italic}
.d3 .co span{font:600 11px "IBM Plex Mono",monospace;letter-spacing:.08em;color:#e8b800}
.d3 .r{margin-left:auto;font-size:12.5px;color:rgba(255,255,255,.6)}'''
    return css, (f'<div class="d3"><svg class="mk" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>'
                 f'<div class="w"><div class="co"><b>{NAME}</b><span>SINCE 2018</span></div><span class="r">IT desk, local 214 · Privacy · Terms</span></div></div>')


def D4():
    """A company seal, like a dispatch stamp: the mark in the middle, the name and year around it."""
    ring = (f'{NAME.upper()} · SINCE 2018 · MARIKINA · STA. ROSA · PULILAN · ')
    css = '''.d4{position:absolute;left:0;right:0;bottom:0;height:200px}
.d4 .w{height:200px;display:flex;align-items:flex-end;padding-bottom:22px}
.d4 .ln{font-size:13px;color:#5b6779}.d4 .ln b{color:#0f172a}
.d4 .seal{position:absolute;right:0;bottom:26px;width:156px;height:156px;transform:rotate(-12deg);opacity:.85}
.d4 .r{margin-left:24px;font-size:12.5px;color:#7a8597}'''
    seal = (f'<svg class="seal" viewBox="0 0 160 160" aria-hidden="true"><defs><path id="ring" d="M80 80m-60 0a60 60 0 1 1 120 0a60 60 0 1 1-120 0"/></defs>'
            f'<circle cx="80" cy="80" r="76" fill="none" stroke="#0f1445" stroke-width="2"/><circle cx="80" cy="80" r="47" fill="none" stroke="#0f1445" stroke-width="1.2"/>'
            f'<text font-family="IBM Plex Mono,monospace" font-size="10.4" font-weight="600" letter-spacing="1.2" fill="#0f1445"><textPath href="#ring">{ring}</textPath></text>'
            f'<g transform="translate(56 66) scale(.146)" fill="#e8b800">{LOGO_POLY}</g></svg>')
    return css, f'<div class="d4"><div class="w"><span class="ln"><b>{NAME}</b> · Since 2018</span><span class="r">Privacy · Terms</span>{seal}</div></div>'


def D5():
    """A small ornament: the gold mark between two hairlines, the company line under it."""
    css = '''.d5{position:absolute;left:0;right:0;bottom:0;height:150px}
.d5 .orn{display:flex;align-items:center;gap:20px;padding-top:44px}
.d5 .orn i{flex:1;height:1px;background:#dfe3ec}
.d5 .orn svg{height:22px;fill:#e8b800}
.d5 .ln{margin-top:18px;display:flex;justify-content:center;gap:10px;font-size:13px;color:#5b6779}
.d5 .ln b{color:#0f172a}'''
    return css, (f'<div class="d5"><div class="w"><div class="orn"><i></i>{MARK}<i></i></div>'
                 f'<div class="ln"><span><b>{NAME}</b> · Since 2018</span><span>·</span><span>Privacy · Terms</span></div></div></div>')


def D6():
    """Livery band: a navy strip whose right end carries the three gold slashes, full height, bleeding off."""
    css = '''.d6{position:absolute;left:0;right:0;bottom:0;height:110px;background:#0f1445;color:#fff;overflow:hidden}
.d6 .sl{position:absolute;right:calc(50% - 760px);top:-6px;height:122px;fill:#e8b800}
.d6 .w{height:110px;display:flex;align-items:center;gap:24px;font-size:13px;color:rgba(255,255,255,.7)}
.d6 b{color:#fff;font-size:15px;font-style:italic;font-weight:800}'''
    return css, (f'<div class="d6"><svg class="sl" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>'
                 f'<div class="w"><b>{NAME}</b><span>Since 2018</span><span>Privacy · Terms</span></div></div>')


# ---------------------------------------------------------------- navbar vs band (on M1)
SEP = {
    'T1': '',
    'T2': '.nd3:before{content:"";position:absolute;left:0;right:0;top:64px;height:1px;background:rgba(255,255,255,.12);z-index:2}',
    'T3': '.nd3:before{content:"";position:absolute;left:0;right:0;top:0;height:64px;background:#0a0d33;z-index:1}',
    'T4': ('.nd3:before{content:"";position:absolute;left:0;right:0;top:0;height:64px;background:#0a0d33;z-index:1;'
           'box-shadow:0 2px 0 #e8b800}'),
    'T5': ('.nd3:before{content:"";position:absolute;left:0;right:0;top:0;height:64px;background:rgba(255,255,255,.06);z-index:1;'
           '-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);box-shadow:inset 0 -1px 0 rgba(255,255,255,.1)}'),
    'T6': ('.nd3:before{content:"";position:absolute;left:0;right:0;top:0;height:64px;background:#0f1445;z-index:1;'
           'box-shadow:0 14px 30px -4px rgba(0,0,0,.7),0 1px 0 rgba(255,255,255,.06)}'),
}


def foot_line():
    """The plain company line, for the navbar boards."""
    css = '''.fl0{position:absolute;left:0;right:0;bottom:20px;font-size:13px;color:#5b6779}.fl0 .w{display:flex;justify-content:space-between}.fl0 b{color:#0f172a}'''
    return css, f'<div class="fl0"><div class="w"><span><b>{NAME}</b> · Since 2018</span><span>Privacy · Terms</span></div></div>'


def compose(title, bottom, sep='T1'):
    ncss, nhtml = g53.nav(g53.M1, 'Corazon', 'Corazon Villareal', 'CV')
    lcss, lhtml = g53.L1(g53.items(CORAZON, False), 'plain')
    bcss, bhtml = bottom()
    body = f'<div class="pg">{nhtml}{lhtml}</div>{bhtml}</div>'
    css = (g.CSS + g53.COMMON + ncss + '.nd3 .mk{z-index:0}' + SEP[sep] + lcss + bcss
           + '.li{width:52px;height:52px;display:flex;align-items:center;color:#0f1445}')
    return title, css, body


def add(key, title, **kw):
    BOARDS[key] = lambda: compose(title, **kw)


add('R54D1', 'D1 · The name as huge type, cropped by the bottom edge', bottom=D1)
add('R54D2', 'D2 · A navy strip with the mark\'s slant repeated across it', bottom=D2)
add('R54D3', 'D3 · A navy band mirroring the top: the faint mark, now on the left', bottom=D3)
add('R54D4', 'D4 · A company seal like a dispatch stamp, bottom right', bottom=D4)
add('R54D5', 'D5 · A small ornament: the gold mark between two hairlines, the line under it', bottom=D5)
add('R54D6', 'D6 · Livery band: the three gold slashes at the right end of a navy strip', bottom=D6)

add('R54T1', 'T1 · No separation (M1 as picked)', bottom=foot_line, sep='T1')
add('R54T2', 'T2 · A hairline under the navbar, across the full width', bottom=foot_line, sep='T2')
add('R54T3', 'T3 · The navbar a shade deeper than the band', bottom=foot_line, sep='T3')
add('R54T4', 'T4 · Deeper navbar with a gold line under it', bottom=foot_line, sep='T4')
add('R54T5', 'T5 · The navbar as frosted glass, the mark blurred behind it', bottom=foot_line, sep='T5')
add('R54T6', 'T6 · The navbar lifted: a soft shadow falls onto the band', bottom=foot_line, sep='T6')


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

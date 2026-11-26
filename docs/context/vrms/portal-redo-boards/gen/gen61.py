"""Round 61 (Nov 26): no animation. E1 kept as a still hairline across the bottom (the fallback), plus options
around that line. Q1 band, P5 number keys. python3 -I gen61.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen60 as g60  # noqa: E402
from data49 import board  # noqa: E402
from parts import LOGO_POLY  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
MARK = f'<svg class="m" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>'
HL = '.ft .hl{position:absolute;left:0;right:0;bottom:56px;height:1px;background:#e1e5ee}'

OPTS = [
    ('R61E1', 'E1 · The line as it is: a hairline across the full width (the fallback)', HL, '<div class="hl"></div>'),
    ('R61E1a', 'E1a · The line only as wide as the content, lined up with the tiles',
     HL + '.ft .hl{left:calc(50% - 600px);right:calc(50% - 600px)}', '<div class="hl"></div>'),
    ('R61E1b', 'E1b · The line fades out at both ends',
     HL + '.ft .hl{background:linear-gradient(90deg,rgba(208,214,226,0),#d6dbe6 20%,#d6dbe6 80%,rgba(208,214,226,0))}', '<div class="hl"></div>'),
    ('R61E1c', 'E1c · A short gold start: the line begins with 48px of gold over the company line',
     HL + '.ft .hl i{position:absolute;left:calc(50% - 600px);top:-1px;width:48px;height:3px;border-radius:2px;background:#e8b800}',
     '<div class="hl"><i></i></div>'),
    ('R61E1d', 'E1d · A pinstripe pair: the grey line with a thin gold one 3px under it',
     HL + '.ft .hl:after{content:"";position:absolute;left:0;right:0;top:4px;height:1.5px;background:#e8b800}', '<div class="hl"></div>'),
    ('R61E1e', 'E1e · A lane marking: the line dashed, long dashes like paint on a depot floor',
     HL + '.ft .hl{height:2px;background:repeating-linear-gradient(90deg,#dce1ea 0 28px,transparent 28px 44px)}', '<div class="hl"></div>'),
    ('R61E1f', 'E1f · The small gold mark leads the line, at the left edge of the content',
     HL + '''.ft .hl{left:calc(50% - 600px + 34px)}
.ft .m{position:absolute;left:calc(50% - 600px);bottom:50px;height:13px;fill:#e8b800}''', f'{MARK}<div class="hl"></div>'),
    ('R61E1g', 'E1g · Split: the company line on the left, "EST. 2018" small on the right, under the line',
     HL, '<div class="hl"></div><span class="est">EST. 2018</span>'),
]
EST_CSS = '''.ft .est{position:absolute;right:calc(50% - 600px);bottom:22px;font:600 11px "IBM Plex Mono",monospace;letter-spacing:.1em;color:#7a8597}'''


def make(t, css, foot, key):
    title, c, body = g60.page(t, css + (EST_CSS if key == 'R61E1g' else ''), foot)
    if key == 'R61E1g':
        body = body.replace(' · Since 2018</span>', '</span>')
    return title, c, body


for key, t, css, foot in OPTS:
    BOARDS[key] = (lambda t=t, css=css, foot=foot, key=key: make(t, css, foot, key))


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

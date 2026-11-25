"""Round 53 (Nov 25, late night): G1 style layouts, more bottoms, N3b variations.
Your calls: no "Your role:" label, Suite management is a white tile like the rest (not inverted), icons I1 or I2.
python3 -I gen53.py <project dir> [Board,Board]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen51 as g  # noqa: E402
import gen52 as g52  # noqa: E402
import gen52icons as gi  # noqa: E402
from data49 import board, CORAZON, FELICIDAD, I, ic  # noqa: E402
from parts import LOGO_POLY  # noqa: E402

OUT = Path(sys.argv[1])
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
BOARDS = {}
NAVY, GOLD = '#0f1445', '#e8b800'
HINT = g52.HINT


def items(people, suite):
    out = [dict(code=s['code'], name=s['name'], line=s['line'], role=s['role'], count=None) for s in people]
    if suite:
        out.append(dict(code='Suite', name='Suite management', line='People, roles and access for VMMS and VRMS', role=None, count='4 to review'))
    return out


def role_of(it):
    return f'<span class="ct">{it["count"]}</span>' if it['count'] else it['role']


def head(its):
    n = len([i for i in its if i['role']])
    return f'<div class="hd"><h2>Your systems</h2><span>{n}</span>{HINT}</div>'


def labels(its, cols):
    """Group labels over the tiles when Suite management is there (it sits after the systems)."""
    n = len([i for i in its if i['role']])
    if n == len(its):
        return ''
    return (f'<p class="gl" style="grid-column:1/{n + 1}">Systems</p>'
            f'<p class="gl" style="grid-column:{n + 1}/{n + 2}">Admin</p>')


COMMON = '''.ct{color:#7a5f00;font-weight:600}
.gl{grid-row:1;margin:0 0 -8px;font:600 11px "IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase;color:#7a8597}
.lay>a{grid-row:2}
.lay:not(:has(.gl))>a{grid-row:auto}
.lay a{transition:transform .2s cubic-bezier(.2,.8,.2,1),box-shadow .2s}
.lay a:hover{transform:translateY(-3px)}
.lay a:focus-visible{outline:3px solid #e8b800;outline-offset:3px}'''


# ---------------------------------------------------------------- G1 style layouts
def L1(its, ik):
    """Classic: icon, code, name, line; the role sits alone at the bottom, no label."""
    css = '''.lay{display:grid;grid-template-columns:repeat(4,282px);gap:24px}
.t1{height:256px;padding:22px;border-radius:20px;background:#fff;display:flex;flex-direction:column;box-shadow:0 0 0 1px #e3e7ef}
.t1:hover{box-shadow:0 0 0 1px #d5dbe7,0 14px 30px rgba(15,23,42,.10)}
.t1 b{margin-top:18px;font-size:26px;line-height:1;font-weight:800;letter-spacing:-.03em;color:#0f1445}
.t1 .nm{margin-top:8px;font-size:14px;font-weight:600;line-height:1.35}
.t1 .ln{margin-top:4px;font-size:13px;line-height:1.45;color:#5b6779}
.t1 .rl{margin-top:auto;font-size:13px;font-weight:600;color:#0f172a}'''
    t = ''.join(f'<a class="t1" href="#">{gi.icon(ik, i["code"], 52, False)}<b>{i["code"]}</b><span class="nm">{i["name"]}</span>'
                f'<span class="ln">{i["line"]}</span><span class="rl">{role_of(i)}</span></a>' for i in its)
    return css, head(its) + f'<div class="lay">{labels(its, 4)}{t}</div>'


def L2(its, ik):
    """Head row: icon and code side by side, the role in small caps at the top right."""
    css = '''.lay{display:grid;grid-template-columns:repeat(4,282px);gap:24px}
.t2{height:220px;padding:20px 22px;border-radius:20px;background:#fff;display:flex;flex-direction:column;box-shadow:0 0 0 1px #e3e7ef}
.t2:hover{box-shadow:0 0 0 1px #d5dbe7,0 14px 30px rgba(15,23,42,.10)}
.t2 .hr{display:flex;align-items:center;gap:12px}
.t2 b{font-size:24px;font-weight:800;letter-spacing:-.025em;color:#0f1445}
.t2 .rl{margin-left:auto;align-self:flex-start;font:600 10.5px "IBM Plex Mono",monospace;letter-spacing:.07em;text-transform:uppercase;color:#5b6779;text-align:right;max-width:90px;line-height:1.35}
.t2 .rl .ct{color:#7a5f00}
.t2 .nm{margin-top:auto;font-size:14px;font-weight:600;line-height:1.35}
.t2 .ln{margin-top:4px;font-size:13px;line-height:1.45;color:#5b6779;min-height:38px}'''
    t = ''.join(f'<a class="t2" href="#"><span class="hr">{gi.icon(ik, i["code"], 44, False)}<b>{i["code"]}</b><span class="rl">{role_of(i)}</span></span>'
                f'<span class="nm">{i["name"]}</span><span class="ln">{i["line"]}</span></a>' for i in its)
    return css, head(its) + f'<div class="lay">{labels(its, 4)}{t}</div>'


def L3(its, ik):
    """Footer row: a taller tile, the role in its own footer under a hairline."""
    css = '''.lay{display:grid;grid-template-columns:repeat(4,282px);gap:24px}
.t3{height:290px;border-radius:20px;background:#fff;display:flex;flex-direction:column;box-shadow:0 0 0 1px #e3e7ef;overflow:hidden}
.t3:hover{box-shadow:0 0 0 1px #d5dbe7,0 14px 30px rgba(15,23,42,.10)}
.t3 .bd{flex:1;padding:24px 22px 0;display:flex;flex-direction:column}
.t3 b{margin-top:20px;font-size:28px;line-height:1;font-weight:800;letter-spacing:-.03em;color:#0f1445}
.t3 .nm{margin-top:10px;font-size:14px;font-weight:600;line-height:1.35}
.t3 .ln{margin-top:4px;font-size:13px;line-height:1.45;color:#5b6779}
.t3 .ft{height:52px;padding:0 22px;display:flex;align-items:center;gap:8px;border-top:1px solid #eef1f6;background:#fafbfd;font-size:13px;font-weight:600;color:#0f172a}
.t3 .ft svg{color:#7a8597}'''
    person = ic(I['users'], 15, 2)
    t = ''.join(f'<a class="t3" href="#"><span class="bd">{gi.icon(ik, i["code"], 60, False)}<b>{i["code"]}</b><span class="nm">{i["name"]}</span>'
                f'<span class="ln">{i["line"]}</span></span><span class="ft">{"" if i["count"] else person}{role_of(i)}</span></a>' for i in its)
    return css, head(its) + f'<div class="lay">{labels(its, 4)}{t}</div>'


def L4(its, ik):
    """Small tiles, five to a row (a launchpad); everything a size smaller."""
    css = '''.lay{display:grid;grid-template-columns:repeat(5,220px);gap:25px}
.t4{height:236px;padding:20px;border-radius:18px;background:#fff;display:flex;flex-direction:column;box-shadow:0 0 0 1px #e3e7ef}
.t4:hover{box-shadow:0 0 0 1px #d5dbe7,0 12px 26px rgba(15,23,42,.10)}
.t4 b{margin-top:16px;font-size:22px;line-height:1;font-weight:800;letter-spacing:-.025em;color:#0f1445}
.t4 .nm{margin-top:8px;font-size:13px;font-weight:600;line-height:1.35}
.t4 .ln{margin-top:4px;font-size:12.5px;line-height:1.45;color:#5b6779}
.t4 .rl{margin-top:auto;font-size:12.5px;font-weight:600;color:#0f172a}'''
    t = ''.join(f'<a class="t4" href="#">{gi.icon(ik, i["code"], 44, False)}<b>{i["code"]}</b><span class="nm">{i["name"]}</span>'
                f'<span class="ln">{i["line"]}</span><span class="rl">{role_of(i)}</span></a>' for i in its)
    return css, head(its) + f'<div class="lay">{labels(its, 5)}{t}</div>'


def L5(its, ik):
    """Wide tiles, two to a row: the icon large on the left, the role at the top right."""
    css = '''.lay{display:grid;grid-template-columns:repeat(2,588px);gap:24px}
.t5{height:150px;padding:24px 26px;border-radius:20px;background:#fff;display:grid;grid-template-columns:72px 1fr auto;column-gap:22px;align-items:start;box-shadow:0 0 0 1px #e3e7ef}
.t5:hover{box-shadow:0 0 0 1px #d5dbe7,0 14px 30px rgba(15,23,42,.10)}
.t5 .ai,.t5 .li,.t5 .rule{grid-row:span 3}
.t5 b{font-size:26px;line-height:1;font-weight:800;letter-spacing:-.03em;color:#0f1445}
.t5 .rl{font-size:13px;font-weight:600;color:#0f172a}
.t5 .nm{grid-column:2/4;margin-top:10px;font-size:14px;font-weight:600}
.t5 .ln{grid-column:2/4;margin-top:3px;font-size:13px;color:#5b6779}
.lay .gl{display:none}.lay>a{grid-row:auto}'''
    t = ''.join(f'<a class="t5" href="#">{gi.icon(ik, i["code"], 72, False)}<b>{i["code"]}</b><span class="rl">{role_of(i)}</span>'
                f'<span class="nm">{i["name"]}</span><span class="ln">{i["line"]}</span></a>' for i in its)
    return css, head(its) + f'<div class="lay">{t}</div>'


def L6(its, ik):
    """Joined: one white panel split by hairlines, no gaps and no shadows; four cells."""
    css = '''.lay{display:grid;grid-template-columns:repeat(4,1fr);border-radius:20px;background:#fff;box-shadow:0 0 0 1px #e3e7ef;overflow:hidden}
.t6{height:250px;padding:24px;display:flex;flex-direction:column;border-right:1px solid #eef1f6}
.t6:hover{background:#f8f9fc;transform:none!important}
.t6 b{margin-top:18px;font-size:26px;line-height:1;font-weight:800;letter-spacing:-.03em;color:#0f1445}
.t6 .nm{margin-top:8px;font-size:14px;font-weight:600;line-height:1.35}
.t6 .ln{margin-top:4px;font-size:13px;line-height:1.45;color:#5b6779}
.t6 .rl{margin-top:auto;font-size:13px;font-weight:600;color:#0f172a}
.t6.empty{border-right:0;display:flex;align-items:flex-start;justify-content:flex-end;color:#99a2b3;font-size:13px}
.lay .gl{display:none}.lay>a{grid-row:auto}'''
    t = ''.join(f'<a class="t6" href="#">{gi.icon(ik, i["code"], 52, False)}<b>{i["code"]}</b><span class="nm">{i["name"]}</span>'
                f'<span class="ln">{i["line"]}</span><span class="rl">{role_of(i)}</span></a>' for i in its)
    t += '<div class="t6 empty"></div>' * (4 - len(its))
    return css, head(its) + f'<div class="lay">{t}</div>'


# ---------------------------------------------------------------- bottoms
FT = '<div class="ftl"><div class="w"><span>WeLinc Logistics · Since 2018</span><span>Privacy · Terms</span></div></div>'
FT_CSS = '''.ftl{position:absolute;left:0;right:0;bottom:16px;font-size:12px;color:#7a8597}.ftl .w{display:flex;justify-content:space-between}'''
HELP = lambda name: [(I['shield'], 'Signed in as ' + name, 'Last sign in: Tuesday, Nov 24, 6:12 PM, Chrome on Windows.'),  # noqa: E731
                     (I['key'], 'Missing a system?', 'Each system\'s admin gives its roles. Ask them, then sign in again.'),
                     (I['users'], 'Need help?', 'IT desk, local 214. Monday to Saturday, 7 AM to 7 PM.')]


def B1(name):
    css = g52.BOTTOM_CSS['panel']
    return css, g52.bottom('panel', name)


def B3(name):
    """Help cards right under the systems, in the flow of the page."""
    css = '''.hc{margin-top:40px}.hc h2{margin:0 0 14px;font-size:15px;font-weight:700}
.hc .cs{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.hc .c{display:flex;gap:14px;padding:18px 20px;border-radius:16px;background:#e9ecf3}
.hc .c svg{flex:none;color:#0f1445;margin-top:2px}
.hc strong{display:block;font-size:13.5px;color:#0f172a}.hc p{margin:4px 0 0;font-size:13px;line-height:1.5;color:#5b6779}''' + FT_CSS
    cs = ''.join(f'<div class="c">{ic(i, 18, 2)}<div><strong>{h}</strong><p>{t}</p></div></div>' for i, h, t in HELP(name))
    return css, ('inflow', f'<div class="hc"><h2>Help and account</h2><div class="cs">{cs}</div></div>', FT)


def B4(name):
    """A navy footer that mirrors the band: the page is held between two navy edges."""
    css = '''.nf{position:absolute;left:0;right:0;bottom:0;height:176px;background:#0f1445;color:#fff;overflow:hidden}
.nf .mk{position:absolute;right:calc(50% - 700px);bottom:-60px;height:240px;fill:rgba(255,255,255,.04)}
.nf .cols{position:relative;display:grid;grid-template-columns:repeat(3,1fr);gap:48px;padding-top:30px}
.nf strong{display:flex;align-items:center;gap:8px;font-size:13px}.nf strong svg{color:#e8b800}
.nf p{margin:6px 0 0;font-size:13px;line-height:1.55;color:rgba(255,255,255,.66)}
.nf .w{position:static}
.nf .fl{position:absolute;left:50%;width:1200px;margin-left:-600px;bottom:16px;display:flex;justify-content:space-between;font-size:12px;color:rgba(255,255,255,.5)}'''
    cs = ''.join(f'<div><strong>{ic(i, 16, 2)}{h}</strong><p>{t}</p></div>' for i, h, t in HELP(name))
    return css, (f'<div class="nf"><svg class="mk" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg><div class="w"><div class="cols">{cs}</div>'
                 f'<div class="fl"><span>WeLinc Logistics · Since 2018</span><span>Privacy · Terms</span></div></div></div>')


def B5(name):
    """The WeLinc mark, huge and faint, in the bottom right of the light page."""
    css = '''.wm{position:absolute;right:-90px;bottom:-70px;height:420px;fill:#0f1445;opacity:.035}''' + FT_CSS
    return css, f'<svg class="wm" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>{FT}'


def B6(name):
    """A dotted floor, like a depot's marked concrete, fading up from the bottom."""
    css = '''.fl6{position:absolute;left:0;right:0;bottom:0;height:300px;
background-image:radial-gradient(circle,rgba(15,20,69,.16) 1.2px,transparent 1.6px);background-size:22px 22px;
-webkit-mask-image:linear-gradient(transparent,#000 85%);mask-image:linear-gradient(transparent,#000 85%)}
.fl6:after{content:"";position:absolute;left:0;right:0;bottom:44px;height:4px;background:repeating-linear-gradient(90deg,#e8b800 0 40px,transparent 40px 64px);opacity:.55}''' + FT_CSS
    return css, f'<div class="fl6"></div>{FT}'


def B7(name):
    """Our garages: the three garages by town, a quiet company footer."""
    css = '''.gf{position:absolute;left:0;right:0;bottom:0;background:#e9ecf3;border-top:1px solid #dfe3ec}
.gf h3{margin:0;padding-top:24px;font:600 11px "IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase;color:#7a8597}
.gf .cols{display:grid;grid-template-columns:repeat(3,1fr);gap:48px;padding:14px 0 20px}
.gf .g{display:flex;gap:14px;align-items:flex-start}
.gf svg{flex:none}
.gf strong{display:block;font-size:14px;color:#0f172a}.gf p{margin:3px 0 0;font-size:13px;color:#5b6779}
.gf .fl{display:flex;justify-content:space-between;padding:12px 0 16px;border-top:1px solid #dfe3ec;font-size:12px;color:#7a8597}'''
    gar = ('<svg width="40" height="32" viewBox="0 0 40 32" aria-hidden="true"><path d="M2 31V11L20 3l18 8v20" fill="none" stroke="#0f1445" stroke-width="1.8" stroke-linejoin="round"/>'
           '<path d="M10 31V17h20v14M10 21h20M10 25h20" fill="none" stroke="#0f1445" stroke-width="1.5"/><path d="M2 31h36" stroke="#e8b800" stroke-width="2"/></svg>')
    cs = ''.join(f'<div class="g">{gar}<div><strong>{n}</strong><p>{t}</p></div></div>' for n, t in
                 [('Marikina', 'Marikina City, Metro Manila'), ('Sta. Rosa', 'Sta. Rosa, Laguna'), ('Pulilan', 'Pulilan, Bulacan')])
    return css, (f'<div class="gf"><div class="w"><h3>Our garages</h3><div class="cols">{cs}</div>'
                 f'<div class="fl"><span>WeLinc Logistics · Since 2018 · IT desk, local 214</span><span>Privacy · Terms</span></div></div></div>')


# ---------------------------------------------------------------- N3b variations (the band with the WeLinc mark)
MK = f'<svg class="mk" viewBox="0 0 330 185" aria-hidden="true">{LOGO_POLY}</svg>'


def M1():
    return ('.nd3 .mk{position:absolute;right:calc(50% - 720px);top:-40px;height:300px;fill:rgba(255,255,255,.045)}', MK, 184)


def M2():
    return ('.nd3 .mk{position:absolute;left:calc(50% - 760px);top:-170px;height:560px;fill:rgba(255,255,255,.035)}', MK, 184)


def M3():
    return ('.nd3 .mk{position:absolute;right:calc(50% - 640px);top:-24px;height:250px;fill:none;stroke:rgba(232,184,0,.38);stroke-width:1.4;vector-effect:non-scaling-stroke}'
            '.nd3 .mk polygon{vector-effect:non-scaling-stroke}', MK, 184)


def M4():
    return ('.nd3 .mk{position:absolute;right:calc(50% - 680px);bottom:-110px;height:330px;fill:rgba(232,184,0,.10)}'
            '.nd3 .gr{padding-top:44px}', MK, 232)


def M5():
    css = ('.nd3 .stp{position:absolute;right:0;top:0;bottom:0;width:58%;'
           'background:repeating-linear-gradient(113deg,rgba(255,255,255,.04) 0 46px,transparent 46px 92px);'
           '-webkit-mask-image:linear-gradient(90deg,transparent,#000 60%);mask-image:linear-gradient(90deg,transparent,#000 60%)}'
           '.nd3 .mk{position:absolute;right:calc(50% - 600px);bottom:30px;height:34px;fill:#e8b800}')
    return css, '<span class="stp"></span>' + MK, 184


def M6():
    css = ('.nd3 .cut{position:absolute;right:0;top:0;bottom:0;width:40%;background:#141a55;clip-path:polygon(78px 0,100% 0,100% 100%,0 100%)}'
           '.nd3 .edge{position:absolute;right:0;top:0;bottom:0;width:calc(40% + 6px);background:#e8b800;clip-path:polygon(78px 0,84px 0,6px 100%,0 100%)}'
           '.nd3 .mk{position:absolute;right:calc(50% - 600px);top:72px;height:62px;fill:#e8b800}')
    return css, '<span class="edge"></span><span class="cut"></span>' + MK, 184


def nav(variant, first, name, ini):
    mcss, art, h = variant()
    css = g52.BAND.replace('height:184px', f'height:{h}px') + mcss
    html = g52.band(first, art).replace('{ROW}', g.nav_row(name, ini))
    return css, html


# ---------------------------------------------------------------- compose
def compose(title, lay=L1, bot=B1, mark=M1, ik='plain', person='C'):
    first, name, ini, people, suite = (('Corazon', 'Corazon Villareal', 'CV', CORAZON, False) if person == 'C'
                                       else ('Felicidad', 'Felicidad Roxas', 'FR', FELICIDAD, True))
    ncss, nhtml = nav(mark, first, name, ini)
    lcss, lhtml = lay(items(people, suite), ik)
    bcss, b = bot(name)
    if isinstance(b, tuple):  # in the page flow, plus a footer line
        _, inflow, tail = b
        body = f'<div class="pg">{nhtml}{lhtml}{inflow}</div>{tail}</div>'
    else:
        body = f'<div class="pg">{nhtml}{lhtml}</div>{b}</div>'
    css = g.CSS + COMMON + ncss + lcss + bcss + '.li{width:52px;height:52px;display:flex;align-items:center;color:#0f1445}'
    return title, css, body


def add(key, title, **kw):
    BOARDS[key] = lambda: compose(title, **kw)


# page 1: G1 style layouts (I1 icons; L1 also with I2 and the admin case)
add('R53L1', 'L1 · Classic tile; the role alone at the bottom, no label (I1)', lay=L1)
add('R53L2', 'L2 · Head row: icon and code together, the role small at the top right (I1)', lay=L2)
add('R53L3', 'L3 · Taller tile, the role in its own footer under a hairline (I2)', lay=L3, ik='frame')
add('R53L4', 'L4 · Small tiles, five to a row, a size smaller (I1)', lay=L4)
add('R53L5', 'L5 · Wide tiles, two to a row, the icon large on the left (I2)', lay=L5, ik='frame')
add('R53L6', 'L6 · Joined: one panel split by hairlines, no gaps or shadows (I1)', lay=L6)
add('R53L1Admin', 'L1 admin · Felicidad: Suite management is a white tile like the rest, after her systems (I2)', lay=L1, ik='frame', person='F')
add('R53L2Admin', 'L2 admin · Felicidad, Suite management white (I1)', lay=L2, person='F')
add('R53L6Admin', 'L6 admin · Felicidad, Suite management white (I1)', lay=L6, person='F')

# page 2: bottoms (L1, I1, M1)
add('R53B1', 'B1 · Help and account panel, pinned to the bottom (from Round 52)', bot=B1)
add('R53B3', 'B3 · Help and account as three cards right under the systems', bot=B3)
add('R53B4', 'B4 · A navy footer that mirrors the band, the mark faint in it', bot=B4)
add('R53B5', 'B5 · The WeLinc mark, huge and faint, in the bottom right', bot=B5)
add('R53B6', 'B6 · A dotted floor with a gold lane line, fading up from the bottom', bot=B6)
add('R53B7', 'B7 · Our garages: Marikina, Sta. Rosa and Pulilan by town', bot=B7)

# page 3: N3b variations (L1, I1, B1)
add('R53M1', 'M1 · The mark oversized and faint, cropped on the right (Round 52 N3b)', mark=M1)
add('R53M2', 'M2 · The mark huge and very faint behind the greeting', mark=M2)
add('R53M3', 'M3 · The mark drawn as a thin gold outline on the right', mark=M3)
add('R53M4', 'M4 · A taller band, the mark in faint gold sinking off the bottom right', mark=M4)
add('R53M5', 'M5 · The mark\'s slant as faint stripes on the right, a small gold mark', mark=M5)
add('R53M6', 'M6 · The band cut on the mark\'s slant with a gold edge, the mark in gold', mark=M6)


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

#!/usr/bin/env python3
"""Draw a simple illustration per cocktail -> website/cocktail-art/<id>.svg  (run before build_site.py)"""
from pathlib import Path
OUT = Path(__file__).resolve().parent / "cocktail-art"
OUT.mkdir(exist_ok=True)

# ---------- glasses: (outline path, liquid clip, liquid top y, stem/base svg) ----------
GLASS = {
 "martini": dict(
    bowl="M100,70 L300,70 L200,178 Z", top=84,
    base='<path d="M200,178 L200,246" stroke="{g}" stroke-width="5" fill="none"/><ellipse cx="200" cy="250" rx="52" ry="8" fill="{g}" fill-opacity=".55" stroke="{g}" stroke-width="2"/>',
    rim=(100,300,70)),
 "coupe": dict(
    bowl="M96,92 C96,152 146,186 200,186 C254,186 304,152 304,92 Z", top=106,
    base='<path d="M200,186 L200,248" stroke="{g}" stroke-width="5" fill="none"/><ellipse cx="200" cy="252" rx="52" ry="8" fill="{g}" fill-opacity=".55" stroke="{g}" stroke-width="2"/>',
    rim=(96,304,92)),
 "small-coupe": dict(
    bowl="M122,112 C122,160 160,188 200,188 C240,188 278,160 278,112 Z", top=124,
    base='<path d="M200,188 L200,246" stroke="{g}" stroke-width="5" fill="none"/><ellipse cx="200" cy="250" rx="44" ry="7" fill="{g}" fill-opacity=".55" stroke="{g}" stroke-width="2"/>',
    rim=(122,278,112)),
 "rocks": dict(
    bowl="M126,104 L274,104 L266,232 Q265,244 254,244 L146,244 Q135,244 134,232 Z", top=134, base="", rim=(126,274,104)),
 "pitcher": dict(
    bowl="M104,58 Q114,74 130,78 L138,238 Q139,252 152,252 L248,252 Q261,252 262,238 L272,64 L272,58 Z", top=108,
    base='<path d="M270,92 C328,86 332,214 258,228" fill="none" stroke="#5b4636" stroke-opacity=".28" stroke-width="14" stroke-linecap="round"/><path d="M270,92 C328,86 332,214 258,228" fill="none" stroke="{g}" stroke-width="8.5" stroke-linecap="round" stroke-opacity=".95"/>',
    rim=(104,272,58)),
 "double-rocks": dict(
    bowl="M112,92 L288,92 L278,236 Q277,248 265,248 L135,248 Q123,248 122,236 Z", top=126, base="", rim=(112,288,92)),
}

def glass_svg(kind, liquid, extra_in="", extra_top="", g="#ffffff", alpha=.28, layers=None):
    d = GLASS[kind]; cid = f"c-{kind}"
    lq = ""
    if layers:   # list of (fraction_from_top_start, color)
        for y, h, col in layers: lq += f'<rect x="0" y="{y}" width="400" height="{h}" fill="{col}"/>'
    else:
        lq = f'<rect x="0" y="{d["top"]}" width="400" height="200" fill="url(#liq)"/>'
    base = d["base"].format(g=g)
    return f'''
  <clipPath id="{cid}"><path d="{d['bowl']}"/></clipPath>
  {base}
  <path d="{d['bowl']}" fill="{g}" fill-opacity=".12"/>
  <g clip-path="url(#{cid})">{lq}{extra_in}
    <path d="{d['bowl']}" fill="url(#shine)"/>
  </g>
  <path d="{d['bowl']}" fill="none" stroke="#5b4636" stroke-opacity=".28" stroke-width="7" stroke-linejoin="round"/>
  <path d="{d['bowl']}" fill="none" stroke="{g}" stroke-width="3.5" stroke-linejoin="round" stroke-opacity=".95"/>
  {extra_top}'''

# ---------- garnishes ----------
def orange_wheel(cx, cy, r=26, rot=0, col="#f59a23"):
    segs = "".join(f'<path d="M0,0 L{r*.78:.1f},0" stroke="#fff3d6" stroke-width="2.2" transform="rotate({a})"/>' for a in range(0, 360, 45))
    return f'<g transform="translate({cx},{cy}) rotate({rot})"><circle r="{r}" fill="{col}"/><circle r="{r-4}" fill="#ffc861"/>{segs}</g>'
def cherry(cx, cy, r=11):
    return f'<path d="M{cx},{cy-r} Q{cx+6},{cy-r-22} {cx+20},{cy-r-30}" stroke="#4d7a2b" stroke-width="2.5" fill="none"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="#b3122b"/><circle cx="{cx-4}" cy="{cy-4}" r="3" fill="#fff" fill-opacity=".55"/>'
def twist(cx, cy, col="#f2c230", rot=0):
    return f'<g transform="translate({cx},{cy}) rotate({rot})" fill="none" stroke="{col}" stroke-width="5" stroke-linecap="round"><path d="M0,0 C18,-14 -6,-26 14,-38 C30,-48 8,-58 26,-68"/></g>'
def olive(cx, cy):
    return f'<line x1="{cx-30}" y1="{cy+34}" x2="{cx+34}" y2="{cy-38}" stroke="#c8a064" stroke-width="3" stroke-linecap="round"/><ellipse cx="{cx}" cy="{cy}" rx="15" ry="11" fill="#8aa13a" transform="rotate(-35 {cx} {cy})"/><circle cx="{cx+4}" cy="{cy-3}" r="4.5" fill="#d1432b"/>'
def cinnamon(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#7a4220" stroke-width="9" stroke-linecap="round"/><line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#a8693a" stroke-width="3" stroke-linecap="round"/>'
def dots(x1, x2, y, n, col, r=1.6, spread=5):
    import random; rnd = random.Random(int(x1*7+y))
    return "".join(f'<circle cx="{rnd.uniform(x1,x2):.1f}" cy="{y+rnd.uniform(-spread/2,spread):.1f}" r="{rnd.uniform(r*.6,r*1.4):.1f}" fill="{col}"/>' for _ in range(n))
def apple_cube(x, y, s=16, rot=0):
    return f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="3" fill="#f6ecc0" stroke="#c43a3a" stroke-width="2.5" transform="rotate({rot} {x+s/2} {y+s/2})"/>'

def ice(cubes):
    return "".join(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="6" fill="#ffffff" fill-opacity=".38" stroke="#fff" stroke-opacity=".7" stroke-width="2" transform="rotate({r} {x+s/2} {y+s/2})"/>' for x, y, s, r in cubes)
def sugar_rim(x1, x2, y):
    import random; rnd = random.Random(7)
    band = f'<rect x="{x1-3}" y="{y-7}" width="{x2-x1+6}" height="12" rx="5" fill="#fffdf6" stroke="#b98d4b" stroke-width="1.6"/>'
    cr = ""
    for _ in range(60):
        cx = rnd.uniform(x1, x2); cy = rnd.uniform(y-9, y+2); r = rnd.uniform(1.6, 3.2)
        cr += f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{r*1.6:.1f}" height="{r*1.6:.1f}" rx=".8" fill="#ffffff" stroke="#b98d4b" stroke-width=".9" transform="rotate({rnd.uniform(0,90):.0f} {cx:.1f} {cy:.1f})"/>'
    return band + cr
def shavings(cx, y, col="#3b2013"):
    return "".join(f'<path d="M{cx+dx},{y+dy} q5,-9 11,-2 q-4,6 -11,2" fill="{col}"/>' for dx, dy in [(-30,0),(-8,-5),(14,1),(34,-4),(-18,8),(8,6)])

# ---------- the drinks ----------
def d(bg1, bg2, liquid, kind, **kw): return dict(bg=(bg1, bg2), liquid=liquid, kind=kind, **kw)
DRINKS = {
 "sangria": d("#fbe9e1", "#f3c9bd", ("#a1182f", "#6e0f20"), "pitcher",
     inside=lambda: ice([(148,128,30,-8),(214,150,28,10),(160,214,28,4)]) + orange_wheel(196, 176, 20, 10) + orange_wheel(236, 126, 17, -20) + orange_wheel(176, 138, 16, 30, "#f2d33a") + apple_cube(222, 206, 16, 14) + apple_cube(150, 176, 15, -12) + apple_cube(206, 228, 14, 30),
     top=lambda: cinnamon(206, 40, 232, 122)),
 "brandy-alexander": d("#f6ebdc", "#e6cba8", ("#e2bf98", "#b98a5b"), "coupe",
     inside=lambda: "",
     top=lambda: dots(140, 262, 108, 70, "#6f3f1c", 1.7, 7)),
 "brandy-flip": d("#f6eee0", "#e8d6b6", ("#f0e0bf", "#d3b57f"), "small-coupe",
     inside=lambda: '<ellipse cx="200" cy="126" rx="80" ry="8" fill="#fff9ea" fill-opacity=".9"/>',
     top=lambda: dots(148, 252, 122, 55, "#7a4a22", 1.6, 6)),
 "sidecar": d("#fdf1db", "#f4d9a4", ("#f6c25a", "#e08a1f"), "coupe",
     inside=lambda: "",
     top=lambda: sugar_rim(96, 304, 92) + twist(300, 86, "#f2c230", 18)),
 "vieux-carre": d("#f6e7d8", "#e3bf98", ("#c97a35", "#8f4a17"), "rocks",
     inside=lambda: ice([(160,126,64,-6)]),
     top=lambda: twist(150, 112, "#f2b21b", -10) + cherry(256, 118)),
 "wisconsin-old-fashioned": d("#f8e8d4", "#ecc99a", ("#d8873a", "#a35a1c"), "double-rocks",
     inside=lambda: ice([(150,120,48,-8),(206,128,52,9),(176,176,46,3)]),
     top=lambda: orange_wheel(262, 100, 28, 15) + cherry(160, 96)),
 "chocolate-martini": d("#efe3dc", "#d6b9a8", ("#5a3020", "#2b140b"), "martini",
     inside=lambda: '<path d="M120,96 q40,18 80,0 t80,6" stroke="#b9805a" stroke-width="5" fill="none" stroke-opacity=".6"/>',
     top=lambda: shavings(200, 86)),
 "grasshopper": d("#e9f4e6", "#bfe0bb", ("#b4e6b6", "#76c79b"), "coupe",
     inside=lambda: "",
     top=lambda: shavings(200, 100, "#4a2a18")),
 "tiramisu-cocktail": d("#f3e8de", "#dcc2a9", ("#8c5836", "#4e2b17"), "small-coupe",
     inside=lambda: '<rect x="0" y="124" width="400" height="26" fill="#f3e3c8"/>',
     top=lambda: dots(140, 260, 122, 80, "#4a2a18", 1.7, 7)),
 "toffee-cocktail": d("#f9ebd8", "#ebca98", ("#e0a560", "#b4732f"), "martini",
     inside=lambda: '<path d="M118,92 q30,22 60,0 t60,4 t40,-4" stroke="#8a4c14" stroke-width="5" fill="none" stroke-opacity=".7"/>',
     top=lambda: shavings(200, 86)),
 "aviation": d("#eeeaf6", "#d4cdea", ("#d9d4f0", "#aaa0d6"), "coupe",
     inside=lambda: "",
     top=lambda: twist(300, 86, "#f2c230", 18) + cherry(150, 100, 10)),
 "bees-knees": d("#fdf3d6", "#f4dd9c", ("#f8e394", "#e9b84a"), "coupe",
     inside=lambda: "",
     top=lambda: twist(300, 86, "#f2c230", 18)),
 "martini": d("#e8f0f3", "#c6d9e0", ("#f3f9fb", "#cfe3ea"), "martini",
     inside=lambda: "",
     top=lambda: olive(214, 70)),
}

def svg(did, c):
    b1, b2 = c["bg"]; l1, l2 = c["liquid"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" role="img" aria-label="{did}">
<defs>
  <radialGradient id="bg" cx="50%" cy="38%" r="75%"><stop offset="0" stop-color="{b1}"/><stop offset="1" stop-color="{b2}"/></radialGradient>
  <linearGradient id="liq" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{l1}"/><stop offset="1" stop-color="{l2}"/></linearGradient>
  <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity=".38"/><stop offset=".22" stop-color="#fff" stop-opacity="0"/><stop offset=".85" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".15"/></linearGradient>
</defs>
<rect width="400" height="300" fill="url(#bg)"/>
<ellipse cx="200" cy="262" rx="130" ry="14" fill="#000" fill-opacity=".10"/>
{glass_svg(c["kind"], None, c["inside"](), c["top"]())}
</svg>'''

if __name__ == "__main__":
    for did, c in DRINKS.items():
        (OUT / f"{did}.svg").write_text(svg(did, c), encoding="utf-8")
    print(len(DRINKS), "illustrations ->", OUT)

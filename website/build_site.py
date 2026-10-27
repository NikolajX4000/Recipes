#!/usr/bin/env python3
"""Parse the .tex recipes and generate a static, searchable website in ./site

Usage (from anywhere):  python3 website/build_site.py
Then open website/site/index.html  (or serve it:  python3 -m http.server -d website/site)
"""
import json, re, shutil, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent      # the recipes folder
OUT = Path(__file__).resolve().parent / "site"

CATEGORY_LABELS = {
    "apetizers": "Appetizers", "main-dishes": "Main dishes", "desserts": "Desserts",
    "sides": "Sides", "drinks": "Drinks", "lunch": "Lunch", "snacks": "Snacks",
}

# ---------- LaTeX helpers ----------
def strip_comments(s):
    return re.sub(r"(?<!\\)%.*", "", s)

def match_brace(s, i):
    """s[i] == '{' -> index of matching '}'"""
    depth = 0
    for j in range(i, len(s)):
        c = s[j]
        if c == "\\":
            continue
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return j
    return len(s) - 1

def get_arg(s, macro, opt=False):
    m = re.search(r"\\" + macro + r"\b", s)
    if not m: return None
    i = m.end()
    if opt:
        m2 = re.match(r"\s*\[[^\]]*\]", s[i:])
        if m2: i += m2.end()
    while i < len(s) and s[i] in " \n\t": i += 1
    if i >= len(s) or s[i] != "{": return None
    return s[i + 1:match_brace(s, i)]

def index_terms(s, name="ingredient"):
    return re.findall(r"\\index\[" + name + r"\]\{([^{}]*)\}", s)

def clean(s):
    s = re.sub(r"\\index(\[[^\]]*\])?\{[^{}]*\}", "", s)
    s = s.replace("$\\times$", "×").replace("\\footnote{", " – ").replace("\\footnote", " – ")
    s = s.replace("\\%", "%").replace("\\&", "&").replace("\\_", "_").replace("\\$", "$")
    s = s.replace("\\degree", "°").replace("\\textdegree", "°").replace("\\xspace", "")
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"<b>\1</b>", s)
    s = re.sub(r"\\(?:textit|emph)\{([^{}]*)\}", r"<i>\1</i>", s)
    s = re.sub(r"\\(?:LARGE|Large|large|normalsize|small|footnotesize|noindent|raggedleft|hrule|vfill|newpage|clearpage)\b", "", s)
    s = re.sub(r"\\v?space\*?\{[^{}]*\}", "", s)
    s = s.replace("---", "—").replace("--", "–").replace("\\\\", " ")
    s = s.replace("``", "“").replace("''", "”").replace("~", " ")
    s = re.sub(r"\\[,;! ]", " ", s)
    s = re.sub(r"[{}]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def items(block):
    parts = re.split(r"\\item\b", block)[1:]
    return [(clean(p), index_terms(p)) for p in parts if clean(p)]

def slugify(s):
    s = unicodedata.normalize("NFKD", s.lower().replace("ø", "o").replace("æ", "ae").replace("å", "a"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def minutes(s):
    m = re.search(r"\d+", s or "")
    return int(m.group()) if m else None

# ---------- recipe (food) parser ----------
def parse_food(src, path, category, subcat=None):
    src = strip_comments(src)
    title = clean(get_arg(src, "title") or path.stem)
    type_raw = get_arg(src, "TypeCooking") or ""
    r = {
        "id": slugify(path.stem), "title": title, "kind": "food", "category": category,
        "type": clean(type_raw), "servings": minutes(get_arg(src, "NbPerson")),
        "prep": minutes(get_arg(src, "PrepTime")), "cook": minutes(get_arg(src, "CookingTime")),
        "temp": clean(get_arg(src, "CookingTempe") or ""),
    }
    if subcat: r["subcategory"] = subcat
    img = get_arg(src, "Image")
    if img is not None:
        m = re.search(r"\{([^{}]*)\}\s*$", src[src.index("\\Image"):].split("\n")[0])
        if m: r["image"] = m.group(1)

    # ingredients
    ing = re.search(r"\\begin\{ingredient\}(.*?)\\end\{ingredient\}", src, re.S)
    groups, keys = [], []
    if ing:
        body = ing.group(1)
        subs = list(re.finditer(r"\\begin\{subingredient\}\{([^{}]*)\}(.*?)\\end\{subingredient\}", body, re.S))
        sub_names = {clean(m.group(1)).lower() for m in subs}
        main = re.search(r"\\begin\{main\}(.*?)\\end\{main\}", body, re.S)
        main_items = items(main.group(1)) if main else []
        main_items = [(t, k) for t, k in main_items if not (subs and t.lower() in sub_names)]
        if main_items:
            groups.append({"name": None, "items": [t for t, _ in main_items]})
            for _, k in main_items: keys += k
        for m in subs:
            its = items(m.group(2))
            groups.append({"name": clean(m.group(1)), "items": [t for t, _ in its]})
            for _, k in its: keys += k
    r["ingredients"] = groups
    r["ingredientKeys"] = sorted(set(keys))

    # steps
    rec = re.search(r"\\begin\{recipe\}(.*?)\\end\{recipe\}", src, re.S)
    steps = []
    if rec:
        body = rec.group(1)
        pos = 0
        while True:
            m = re.compile(r"\\(step|substep)\b").search(body, pos)
            if not m: break
            i = m.end(); label = None
            mo = re.match(r"\s*\[([^\]]*)\]", body[i:])
            if mo: label = clean(mo.group(1)); i += mo.end()
            while i < len(body) and body[i].isspace(): i += 1
            if i >= len(body) or body[i] != "{":
                pos = i; continue
            j = match_brace(body, i)
            text = clean(body[i + 1:j]); pos = j + 1
            if m.group(1) == "step":
                steps.append({"text": text, "subs": []})
            else:
                if not steps: steps.append({"text": "", "subs": []})
                steps[-1]["subs"].append({"label": label, "text": text})
    r["steps"] = steps
    note = re.search(r"\\begin\{notes\}(.*?)\\end\{notes\}", src, re.S)
    r["notes"] = clean(note.group(1)) if note else ""
    return r

# ---------- cocktail parser ----------
def parse_drink(src, path):
    src = strip_comments(src)
    title = clean(get_arg(src, "subsubsection") or path.stem)
    base = ""
    mb = re.search(r"\\textbf\{\\large ([^{}]*)\}\\\\", src)
    if mb: base = clean(mb.group(1))
    g = re.search(r"\\sweettartguage\{(-?[\d.]+)\}", src)
    pos = float(g.group(1)) if g else None   # -1 sweet .. +1 tart
    def section(name, nxt=r"\\vspace|\\hrule|\\end\{minipage\}"):
        m = re.search(r"\\textbf\{\\large " + name + r":?\}:?(.*?)(?=" + nxt + r"|\Z)", src, re.S)
        return m
    flavors = index_terms(src, "flavor-profile")
    hist = re.search(r"\\textbf\{\\large History:\}(.*?)\\vspace", src, re.S)
    tip = re.search(r"\\textbf\{\\large (?:Fun|Helpful) Tip:\}(.*?)(?:\\newpage|\\clearpage|\Z)", src, re.S)
    def itemize_after(name):
        m = re.search(r"\\textbf\{\\large " + name + r"\}\s*\\begin\{itemize\}(.*?)\\end\{itemize\}", src, re.S)
        return items(m.group(1)) if m else []
    ings = itemize_after("Ingredients")
    keys = []
    for _, k in ings: keys += k
    garnish = itemize_after("Garnish")
    for _, k in garnish: keys += k
    return {
        "id": slugify(path.stem), "title": title, "kind": "drink", "category": "Cocktails",
        "subcategory": base, "type": base, "sweetTart": pos,
        "flavors": [clean(f) for f in flavors],
        "history": clean(hist.group(1)) if hist else "",
        "ingredients": [{"name": None, "items": [t for t, _ in ings]}] if ings else [],
        "garnish": [t for t, _ in garnish],
        "tools": [t for t, _ in itemize_after(r"Tools/Glassware")],
        "glass": sorted(set(clean(x) for x in index_terms(src, "glass"))),
        "ingredientKeys": sorted(set(keys)),
        "steps": [{"text": t, "subs": []} for t, _ in itemize_after("Instructions")],
        "notes": clean(tip.group(1)) if tip else "",
    }

def translatable(r):
    out = [r["title"], r.get("type", ""), r.get("notes", ""), r.get("history", "")]
    for g in r["ingredients"]:
        out.append(g["name"] or ""); out += g["items"]
    for k in ("garnish", "tools", "glass", "flavors"): out += r.get(k, [])
    for st in r["steps"]:
        out.append(st["text"])
        for x in st["subs"]: out += [x["label"] or "", x["text"]]
    return [x for x in out if x]

# ---------- main ----------
def main():
    recipes = []
    paths_in_order = []
    def read(p): return p.read_text(encoding="utf-8")
    for p in sorted((ROOT / "recipes").glob("*/*.tex")):
        s = read(p)
        if s.strip(): recipes.append(parse_food(s, p, CATEGORY_LABELS.get(p.parent.name, p.parent.name.title()))); paths_in_order.append(p)
    for p in sorted((ROOT / "nemlig").glob("*/*.tex")):
        s = read(p)
        if s.strip():
            sub = p.parent.name.replace("-", " ").capitalize()
            r = parse_food(s, p, "Nemlig", sub)
            r["type"] = r["type"] or sub
            recipes.append(r); paths_in_order.append(p)
    for p in sorted((ROOT / "cocktail-cards").glob("*/*.tex")):
        s = read(p)
        if s.strip(): recipes.append(parse_drink(s, p)); paths_in_order.append(p)

    # sections: keep recipes / nemlig / cocktail-cards separate
    for r in recipes:
        if r["kind"] == "drink":
            r["section"], r["group"] = "Cocktail cards", r["subcategory"] or "Other"
        elif r["category"] == "Nemlig":
            r["section"], r["group"] = "Nemlig", r["type"] or r.get("subcategory", "Other")
        else:
            r["section"], r["group"] = "Recipes", r["category"]

    for r in recipes:
        r["lang"] = "en" if r["kind"] == "drink" else "da"   # language the .tex is written in

    # unique ids
    seen = {}
    for r in recipes:
        n = seen.get(r["id"], 0); seen[r["id"]] = n + 1
        if n: r["id"] += f"-{n+1}"

    # images -> site/images
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    for r in recipes:
        if r.get("image"):
            src = ROOT / r["image"]
            if src.exists():
                dst = OUT / "images" / (slugify(src.stem) + src.suffix.lower())
                shutil.copy2(src, dst)
                r["image"] = "images/" + dst.name
            else:
                print("missing image:", r["image"], "for", r["title"]); r.pop("image")

    # cocktail illustrations (website/cocktail-art/<id>.svg, made by make_cocktail_art.py)
    art = Path(__file__).resolve().parent / "cocktail-art"
    for r in recipes:
        a = art / f"{r['id']}.svg"
        if r["kind"] == "drink" and not r.get("image") and a.exists():
            (OUT / "images" / "cocktails").mkdir(parents=True, exist_ok=True)
            shutil.copy2(a, OUT / "images" / "cocktails" / a.name)
            r["image"] = f"images/cocktails/{a.name}"; r["art"] = True
    # cocktails: which base spirit(s) appear in the ingredient list (a drink can be in several)
    # only the spirit itself counts for the spirit chips; liqueurs (Kahlua, Baileys, ...) have their own "Liqueurs" chip
    SPIRITS = [("Vodka", r"\bvodka\b"),
               ("Gin", r"\b(gin|genever)\b"),
               ("Whiskey", r"\b(whiske?y|bourbon|rye|scotch)\b"),
               ("Rum", r"\b(rum|rhum|cacha[cç]a)\b"),
               ("Agave spirits", r"\b(tequila|mezcal|sotol)\b"),
               ("Cognac/Brandy", r"\b(cognac|brandy|armagnac|calvados|pisco)\b"),
               ("Wine/Sparkling", r"\b(wine|prosecco|champagne|cava|sparkling|sherry|port|madeira)\b"),
               ("Amaro/Aperitif", r"\b(campari|aperol|amaro|amari|fernet|cynar|lillet|suze|averna|montenegro|vermouth|j[aä]germeister)\b"),
               ("Liqueurs", r"(liqueur|kahl[uú]a|baileys|amaretto|disaronno|cr[eè]me de|cointreau|triple sec|cura[cç]ao|maraschino(?! cherr)|chambord|b[eé]n[eé]dictine|grand marnier|pimm|st[.-]? ?germain|midori|frangelico|limoncello|galliano|chartreuse|drambuie|j[aä]germeister)")]
    for r in recipes:
        if r["kind"] == "drink":
            ings = " | ".join(i for g in r["ingredients"] for i in g["items"])
            r["spirits"] = [name for name, rx in SPIRITS if re.search(rx, ings, re.I)]
    # order of the PDF book: follow the \\input{...} chain from recipes.tex
    visited = []
    def walk(rel):
        path = (ROOT / rel).with_suffix(".tex") if not str(rel).endswith(".tex") else ROOT / rel
        if not path.exists() or path in visited: return
        visited.append(path)
        for line in read(path).splitlines():
            if line.lstrip().startswith("%"): continue
            m = re.search(r"\\input\{\./([^}]+)\}", line)
            if m: walk(m.group(1))
    walk("recipes.tex")
    pos = {p.resolve(): i for i, p in enumerate(visited)}
    for r, p in zip(recipes, paths_in_order):
        r["order"] = pos.get(p.resolve(), 99999)
    # glass drawn in each cocktail illustration (used by the "sort by glass" option)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from make_cocktail_art import DRINKS
    GLASS_GROUP = {"coupe": "Coupe", "small-coupe": "Coupe", "martini": "Martini Glass", "rocks": "Rocks Glass", "double-rocks": "Rocks Glass", "pitcher": "Pitcher"}
    for r in recipes:
        if r["kind"] == "drink" and r["id"] in DRINKS:
            r["glassGroup"] = GLASS_GROUP[DRINKS[r["id"]]["kind"]]
    OUT.mkdir(exist_ok=True)
    # translations.json: {"en": {danish source string: english}, "da": {english source string: danish}}
    tfile = Path(__file__).resolve().parent / "translations.json"
    trans = json.loads(tfile.read_text(encoding="utf-8")) if tfile.exists() else {"en": {}, "da": {}}
    missing = []
    for r in recipes:
        target = "da" if r["lang"] == "en" else "en"
        for t in translatable(r):
            if t not in trans[target]: missing.append((r["title"], t))
    if missing:
        print(f"  {len(missing)} strings have no translation yet (shown untranslated). Add them to translations.json:")
        for title, t in missing[:15]: print("   -", title, "|", t[:70])
    shutil.copy2(Path(__file__).resolve().parent / "index.template.html", OUT / "index.html")
    (OUT / "recipes.json").write_text(json.dumps(recipes, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "data.js").write_text("window.RECIPES = " + json.dumps(recipes, ensure_ascii=False) + ";\nwindow.TRANS = " + json.dumps(trans, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"{len(recipes)} recipes -> {OUT}")
    for r in recipes:
        warn = []
        if not r["ingredients"]: warn.append("no ingredients")
        if not r["steps"]: warn.append("no steps")
        if warn: print("  WARN", r["title"], warn)

if __name__ == "__main__":
    main()

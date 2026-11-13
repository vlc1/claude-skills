"""Build a Slides deck: render LaTeX equations to inline SVG and assemble slide files.

Usage: python3 build.py [--deck-json]
Sources: eqs.py, src/order.txt, src/slides/<id>.html, config.json. Output: root/project/.
"""
import hashlib, html, json, re, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from eqs import EQS, SCALE  # noqa: E402

CACHE = HERE / "cache"
OUT = HERE / "root" / "project"
DEFAULT_SCALE = 4.4  # px per TeX pt: 10 pt math ~ 44 px, reads level with 32 px body text

# XeLaTeX: \text in TT Norms Pro (the deck's face); no-math keeps \mathbf, \mathrm in Computer Modern.
PREAMBLE = r"""\documentclass[preview,border=0pt]{standalone}
\usepackage{amsmath,amssymb,cancel,xcolor}
\usepackage[no-math]{fontspec}
\setmainfont{TTNormsPro-Regular.otf}[Path=""" + str(HERE / "fonts") + r"""/, BoldFont=TTNormsPro-Bold.otf]
\definecolor{noir}{HTML}{0F273B}\definecolor{bleu}{HTML}{2F2A85}
\definecolor{rose}{HTML}{E83583}\definecolor{vert}{HTML}{00936E}\definecolor{violet}{HTML}{8B4A97}
\newcommand{\cb}[1]{{\color{bleu}#1}}\newcommand{\crs}[1]{{\color{rose}#1}}
\newcommand{\cv}[1]{{\color{vert}#1}}\newcommand{\cvi}[1]{{\color{violet}#1}}
\begin{document}\color{noir}$\displaystyle %s$\end{document}
"""


def round_numbers(svg):
    """Round path coordinates to 0.01 pt; every number gets an explicit separator."""
    def num(m):
        v = f"{float(m.group(0)):.2f}".rstrip("0").rstrip(".")
        return " " + ("0" if v in ("-0", "") else v)
    return re.sub(r"\bd='([^']*)'", lambda m: "d='" + re.sub(r"-?\d*\.?\d+", num, m.group(1)).strip() + "'", svg)


STRUT = r"\vphantom{\dfrac{\partial \phi}{\partial t}}"


def braces(tex):
    """Each \\underbrace{A}_{B} becomes an ordinary term with a common depth, so labels share a baseline
    and a following + keeps its binary spacing."""
    def group(s, i):  # s[i] == "{": return index after the matching brace
        depth = 0
        for j in range(i, len(s)):
            depth += {"{": 1, "}": -1}.get(s[j], 0)
            if depth == 0:
                return j + 1
        raise ValueError("unbalanced braces")
    out, i, key = [], 0, r"\underbrace{"
    while (k := tex.find(key, i)) >= 0:
        a_end = group(tex, k + len(key) - 1)
        if not tex.startswith("_{", a_end):
            raise ValueError("underbrace without a label")
        b_end = group(tex, a_end + 1)
        inner = braces(tex[k + len(key): a_end - 1])
        out += [tex[i:k], "{\\underbrace{", STRUT, inner, "}_{", tex[a_end + 2: b_end - 1], "}}"]
        i = b_end
    return "".join(out) + tex[i:]


def render(eid):
    tex, scale = EQS[eid], SCALE.get(eid, DEFAULT_SCALE)
    src = PREAMBLE % braces(tex)
    if scale > 3.2:  # words in display equations stay at body-text size (32 px) whatever the equation's scale
        f = 32 / scale
        src = src.replace(r"\begin{document}", r"\let\oldtext\text\renewcommand{\text}[1]{\oldtext{\fontsize{%.2fpt}{%.2fpt}\selectfont #1}}\begin{document}" % (f, 1.2 * f), 1)
    key = hashlib.sha1(src.encode()).hexdigest()[:16]
    raw_path = CACHE / f"{eid}-{key}.svg"
    if not raw_path.exists():
        CACHE.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "e.tex").write_text(src)
            r = subprocess.run(["xelatex", "-no-pdf", "-interaction=nonstopmode", "-halt-on-error", "e.tex"],
                               cwd=tmp, capture_output=True, text=True)
            if r.returncode:
                err = [l for l in r.stdout.splitlines() if l.startswith("!")]
                sys.exit(f"LaTeX error in {eid}: {err}")
            subprocess.run(["dvisvgm", "--no-fonts", "--exact-bbox", "-o", "e.svg", "e.xdv"],
                           cwd=tmp, capture_output=True, check=True)
            raw_path.write_text((Path(tmp) / "e.svg").read_text())
    raw = raw_path.read_text()
    x, y, w, h = map(float, re.search(r"viewBox='([^']+)'", raw).group(1).split())
    W, H = round(w * scale), round(h * scale)
    body = raw[raw.index(">", raw.index("<svg")) + 1: raw.rindex("</svg>")]
    body = body.replace("xlink:href", "href")
    body = re.sub(r"id='([^']+)'", lambda m: f"id='{eid}-{m.group(1)}'", body)
    body = re.sub(r"href='#([^']+)'", lambda m: f"href='#{eid}-{m.group(1)}'", body)
    body = round_numbers(re.sub(r"\s*\n\s*", "", body))
    label = html.escape(re.sub(r"\\c(b|rs|v|vi)\{", "{", tex), quote=True)
    sx, sy = W / w, H / h
    return (f'<svg xmlns="http://www.w3.org/2000/svg" aria-label="{label}" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}" style="width:{W}px;height:{H}px">'
            f'<g transform="scale({sx:.4f} {sy:.4f}) translate({-x:.3f} {-y:.3f})">{body}</g></svg>')


ALLOWED_TAGS = set("section h1 h2 h3 p ul ol li br b i u a span div img table tr th td svg hr "
                   "x-shape x-icon x-connector x-embed aside".split())


# Math must be LaTeX SVG only: no symbols in visible text (speaker notes are exempt).
MATH_CHARS = re.compile(r"[Ͱ-Ͽ⁰-₟ᴀ-ᶿ←-⇿∀-⋿℀-⅏"
                        r"⅐-⅟±²³¹×÷=<>~^_]")
MATH_TOKENS = re.compile(r"(?<![\w’'])(Re|Pe|Pr|Ra|Gr|Ma|Kn|St|Nu|[B-Zb-xz])(?![\w’'])")


def math_in_text(flat):
    """Return snippets of visible text that hold symbols instead of LaTeX SVG."""
    vis = re.sub(r"<aside>.*?</aside>", "", flat, flags=re.S)
    hits = ["<i>"] * vis.count("<i>")
    words = html.unescape(re.sub(r"<[^>]+>", " ", vis))
    for m in list(MATH_CHARS.finditer(words)) + list(MATH_TOKENS.finditer(words)):
        hits.append(words[max(0, m.start() - 12): m.end() + 12].strip())
    return hits


def check_slide(sid, text):
    errs = []
    if len(re.findall(r"<section\b", text)) != 1 or not text.startswith(f'<section id="{sid}"'):
        errs.append("must be exactly one <section> with matching id")
    svgs = re.findall(r"<svg\b.*?</svg>", text, re.S)
    embeds = re.findall(r"<x-embed\b.*?</x-embed>", text, re.S)
    flat = re.sub(r"<svg\b.*?</svg>|<x-embed\b.*?</x-embed>", "<svg/>", text, flags=re.S)
    for s in svgs:
        if len(s.encode()) > 52_000:
            errs.append(f"svg over 52 KB ({len(s.encode())} B)")
        if "<text" in s:
            errs.append("svg holds <text>")
    ids = re.findall(r"\bid=['\"]([^'\"]+)['\"]", "".join(svgs))
    if len(ids) != len(set(ids)):
        errs.append("duplicate svg ids")
    if len(embeds) > 8 or any(len(e.encode()) > 16_000 for e in embeds):
        errs.append("embed limits exceeded")
    for style in re.findall(r'style="([^"]*)"', flat):
        if re.search(r"margin|var\(|\d(\.\d+)?r?em\b", style):
            errs.append(f"forbidden css: {style[:60]}")
        for fs in re.findall(r"font-size:\s*([\d.]+)px", style):
            if float(fs) < 24:
                errs.append(f"font-size {fs}px < 24")
    hits = math_in_text(flat)
    if hits:
        errs.append(f"{len(hits)} symbols outside SVG, e.g. {hits[:3]}")
    bad = set(re.findall(r"<([a-zA-Z][\w-]*)", flat)) - ALLOWED_TAGS
    if bad:
        errs.append(f"tags outside the subset: {sorted(bad)}")
    if "class=" in flat:
        errs.append("class attribute")
    n = len(re.findall(r"<[a-zA-Z]", flat))
    if n > 200:
        errs.append(f"{n} elements > 200")
    m = re.search(r"<aside>(.*?)</aside>\s*</section>\s*$", text, re.S)
    if not m or len(m.group(1)) > 4000:
        errs.append("needs one <aside> (≤4000 chars) as last child")
    for ph in re.findall(r"\{\{[^}]*\}\}", flat):
        errs.append(f"unresolved placeholder {ph}")
    return errs


def read_order():
    order, sections = [], {}
    pending = None
    for line in (HERE / "src" / "order.txt").read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("##"):
            pending = line[2:].strip()
        else:
            if pending:
                sections[f"s{len(sections)}"] = {"description": pending, "start": line}
                pending = None
            order.append(line)
    return order, sections


def place(m):
    """{{eq:id}} flows; {{eq:id@x,y}} pins the SVG at (x, y) in its positioned parent."""
    svg = render(m.group(1))
    if m.group(2):
        svg = svg.replace('style="', f'style="position:absolute;left:{m.group(2)}px;top:{m.group(3)}px;', 1)
    else:  # a long sibling paragraph must not shrink the equation in a flex row
        svg = svg.replace('style="', 'style="flex:none;', 1)
    return svg


def selftest():
    assert braces(r"a + \underbrace{x}_{l} + b") == r"a + {\underbrace{" + STRUT + r"x}_{l}} + b"
    assert braces(r"\underbrace{\underbrace{y}_{1}}_{2}").count(r"\underbrace") == 2
    ok = "<p>01 · Cinématique et conservation, il y a l’eau à 2D</p><p>4 / 54</p><aside>ρ = ∇·u</aside>"
    assert math_in_text(ok) == [], math_in_text(ok)
    for bad in ["<p>la masse <i>volumique</i></p>", "<p>avec ρ constant</p>", "<p>Re grand</p>",
                "<p>inconnues u, v, p</p>", "<p>Kn &lt; 0,01</p>", "<p>Δt ~ Δx²</p>", "<p>uₙ nul</p>"]:
        assert math_in_text(bad), bad
    print("selftest OK")


def main():
    if "--selftest" in sys.argv:
        return selftest()
    cfg = json.loads((HERE / "config.json").read_text())
    order, sections = read_order()
    (OUT / "slides").mkdir(parents=True, exist_ok=True)
    footer_tpl = (HERE / "src" / "footer.html").read_text().strip()
    failed, missing = False, []
    for n, sid in enumerate(order, 1):
        p = HERE / "src" / "slides" / f"{sid}.html"
        if not p.exists():
            missing.append(sid)
            continue
        text = p.read_text().strip()
        if "{{footer}}" in text:  # content slides: a two-line title block, so content starts at the same height
            text = re.sub(r"(\{\{h2\}\}.*?</h2>)", r'<div style="height:141px;display:flex;flex-direction:column">\1</div>', text, count=1, flags=re.S)
        text = text.replace("{{footer}}", footer_tpl.replace("{{n}}", str(n)).replace("{{N}}", str(len(order))))
        for k, v in cfg["subst"].items():
            text = text.replace("{{" + k + "}}", v)
        text = re.sub(r"\{\{eq:([\w-]+)(?:@(\d+),(\d+))?\}\}", place, text) + "\n"
        errs = check_slide(sid, text)
        if errs:
            failed = True
            print(f"FAIL {sid}: " + "; ".join(errs))
        (OUT / "slides" / f"{sid}.html").write_text(text)
    if missing:
        print(f"{len(missing)} slides without source yet")
    if "--deck-json" in sys.argv:
        deck = dict(cfg["deck"], order=order, sections=sections)
        (OUT / "deck.json").write_text(json.dumps(deck, ensure_ascii=False, indent=2) + "\n")
    if "--all-eqs" in sys.argv:
        sizes = {e: len(render(e).encode()) for e in EQS}
        big = max(sizes, key=sizes.get)
        print(f"{len(sizes)} equations rendered; largest {big} = {sizes[big]} B")
        assert all(s <= 52_000 for s in sizes.values())
    print("FAILED" if failed else "OK")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

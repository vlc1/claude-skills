---
name: qmd-to-slides
description: Turn a Quarto lecture chapter (.qmd, revealjs, LaTeX math) into a polished Claude Slides artifact in the UGE (Université Gustave Eiffel) design system, with every equation rendered by XeLaTeX to inline SVG. Use when the user asks to make slides, a deck or a Slides artifact from a chapter or a .qmd file, to convert the next chapter "like Ch01", or to fix math display, alignment, footer or divider layout in such a deck.
---

# Quarto chapter → UGE Slides artifact

Learned on Ch01 « Modélisation des milieux continus » (5t-tp4 course, 54 slides,
https://claude.ai/artifact/Ehk147dyEiaPZ3q11ng4S1). The first deck took 23
publishes; every rule below fixes one of them. Worked example: the repo's
`slides/ch01_continuum/` (same kit, full `eqs.py` and 54 slide sources).
Ch02 « Modélisation de la turbulence » (61 slides,
https://claude.ai/artifact/HKxKhCKxfCPry3NpMJDyPb, `slides/ch02_turbulence/`)
added the embed, publishing, review and terminology rules.

## Workflow

1. Read `SYLLABUS.qmd` and the chapter. Outline one idea per slide: fix errors,
   split dense slides, add no topics. Six parts maximum, each opened by a divider.
2. Ask once, upfront (asked for Ch01; defaults in brackets): language [French],
   math [XeLaTeX SVG], widgets [auto-animated `<x-embed>`], scope [fix + split],
   contact email on the final slide [vincent.le-chenadec@univ-eiffel.fr].
3. Copy `kit/` to `slides/chNN_<slug>/` in the course repo. Copy the two TT Norms
   Pro `.otf` into its `fonts/` (from Ch01's `fonts/`, or from the UGE design
   system `project/fonts/`). Set the chapter title in `config.json` (`deck.title`)
   and `src/footer.html`.
4. Write `eqs.py` (LaTeX per id, size via `LEVELS`) and `src/slides/<id>.html`
   (placeholders below), list ids and section descriptions in `src/order.txt`.
5. Loop until clean: `python3 build.py --selftest`, `python3 build.py --deck-json`,
   `python3 preview.py`, `python3 audit.py`, then look at every `pv-NN.png`.
   Chained after the build, `preview.py` sometimes left old PNGs and an old
   `preview.html` without any error: run it on its own, expect "N slides
   rendered", and check the PNG timestamps before trusting a montage or the audit.
6. Create the deck: Artifact `quickstart` (slides), then publish with the Slides
   `type_url` (https://claude.ai/artifact/8jTsAFQMFDb2oA8MsPJ2eL), `title`, and
   `auto_open: "after_first_write"`. Read the type's instructions it returns.
7. First content publish, `root` = `<kit>/root`, `file_path` = `root/project/deck.json`,
   `files` = slides plus server-side copies from the UGE design system
   (https://claude.ai/artifact/CEgGQsZVhRekV6dcfMoTyd):
   `project/ds/uge/tokens.json` ← `project/tokens.json`,
   `project/ds/uge/fonts/TTNormsPro-{Regular,Bold}.otf` ← `project/fonts/…`.
   Copy the two logos into the deck's asset store with `asset: true`,
   `from_url` = Gabarit deck https://claude.ai/artifact/HJ9cJ3LGYTAi5Q7e4zKphH,
   `asset_ids` `34c1e63b3c9743e34de62266cd5b78bf`, `e1cbdd48d635d2f356bcbcc79d736816`;
   put the returned `/_blob/…` urls in `config.json` `logo_c` (colour) and `logo_w`
   (white), rebuild. `deck.json` keeps the `designSystems` UGE record.
8. Later publishes: same `url`, `root`, one changed slide as `file_path`, the rest
   in `files`. A publish with only `files` is refused. A publish touching files
   not read or listed in this session is refused too: `list` with
   `scope: "files"` counts as seeing them. Footers bake in "n / N", so adding or
   removing a slide changes every slide: republish all slides plus `deck.json`
   (new `order`), and remove a slide with `null` in the `files` map.
9. External review by a subagent (brief below), apply, rebuild, audit, publish.
   Then a terminology pass and, when the owner provides one, a scientific audit
   (briefs below).
10. Owner comments arrive as artifact comment threads: read with ArtifactComments,
    fix, publish, reply and resolve each thread.
11. Sync the kit to the repo; never commit the fonts (licensed); propose a commit.

## Kit (`kit/`)

- `build.py`: renders `eqs.py` with XeLaTeX `-no-pdf` → `dvisvgm --no-fonts
  --exact-bbox`, prefixes SVG ids per equation, rounds paths, caches in `cache/`,
  substitutes `config.json` snippets and `{{footer}}`, writes `root/project/`.
  Fails a slide on: Slides format subset (tags, `margin`, `em`, `var(`, `class`,
  font-size < 24, > 200 elements, SVG > 52 KB or with `<text>`, embed > 16 KB,
  missing last `<aside>`), and on any math symbol in visible text.
- `preview.py`: headless Chrome render with TT Norms Pro, 9 slides per shot
  (one tall shot fails past ~10), writes `pv-NN.png` and `preview.html`.
- `audit.py`: on `preview.html`, flags unequal `flex:1` columns (content pushed a
  column wider), content past 120 px side margins, content into the footer band.
- `review_pack.py`: `review/equations.tsv` (slide, id, scale, size, placement,
  LaTeX) for the reviewer.
- Placeholders: `{{eq:id}}` flowing (gets `flex:none`), `{{eq:id@x,y}}` pinned
  (diagram labels), `{{sec}}` content slide, `{{div}}` divider, `{{eyeb}}`,
  `{{h2}}`, `{{h3}}`, `{{p}}` 32 px, `{{small}}` 28 px, `{{lbl}}`, `{{row}}`,
  `{{eqc}}` centring wrapper, `{{B}}` bold face, `{{divider-art}}`, `{{footer}}`.
- Sample slides: `cover`, `partie-1`, `continuite` (two-column content), `fin`.

## Math display (owner requirement: no mismatch between symbols and equations)

- Every symbol is LaTeX SVG: none in prose, titles (words only), labels, legends,
  table cells (tables are LaTeX or text-only). `<i>` in text counts as math.
  Unicode math is allowed only in speaker notes (`<aside>`). The build enforces it;
  a single capital letter in text (even a placeholder "N") trips it, and so do
  initials (« S. B. Pope »: write first names in full) and k, ε, y⁺ in a
  sentence (write « énergie cinétique turbulente », « dissipation »).
- Later corrections go in an override block appended at the end of `eqs.py`
  (`EQS.update({...})`, plus `SCALE.update` for new ids): the last assignment
  wins, so always edit the effective definition, not the first one.
- A long `\text` label silently wraps into a stretched, broken line: split it
  over two lines with `aligned`, or shorten it.
- XeLaTeX with `fontspec[no-math]` loading TT Norms Pro by file path, so `\text`
  matches the slide text and `\mathbf` stays Computer Modern. `\text` is capped
  at 32 px whatever the equation's scale.
- One size per role (scale = px per TeX pt), via `LEVELS` in `eqs.py`:
  H 5.0 key result · D 4.4 standard display · C 4.0 display in a column ·
  T 3.2 / 2.8 / 2.4 inline with 32 / 28 / 24 px text · L 2.8 label in a diagram.
  Same role on one slide, same size. Quote slide equation may exceed (7).
- `\underbrace{A}_{B}` gets a common strut (`build.braces`): labels share a
  baseline, a following `+` keeps binary spacing. Write "= 0" under a brace,
  not a strike-through.
- Colour macros `\cb` bleu, `\crs` rose (`\cr` clashes with a TeX primitive),
  `\cv` vert, `\cvi` violet. A colour keeps one meaning across the deck
  (e.g. elliptic/pressure = vert); words inside equations are rare, put them in
  a text label beside the equation instead.
- Centre an equation alone in a column or cell (`{{eqc}}` or `align-items:center`);
  keep left-aligned ones that share a row with a label, captions, list-like legends.
  First-order or key equations on their own line.
- Uppercase labels (`{{lbl}}`, `{{eyeb}}`) never contain equations: they would be
  uppercased.

## Layout

- Content slide: padding `128px 128px 136px`, gap 32, eyebrow « 0N · Partie »,
  title as a full sentence stating the conclusion (64 px, fixed 141 px block, added
  by the build), body 32 px, 28 px only for legends and tables.
- Footer row at bottom 64 px (deck title, n / N, colour logo); nothing may enter
  the 136 px band: shorten text or move detail to speaker notes.
- Dividers: the viewer ignored multi-value `padding` on dividers (text stuck to
  the left edge). Use single `padding:128px` + a `<div style="height:120px">`
  spacer, as in `partie-1.html`. Cover and fin use `padding:128px` too.
- Equal columns: `flex:1` siblings; a wide equation silently widens its column,
  so scale it to level C or split. Decorative rules (column top borders) bleu
  unless the colour encodes meaning; one tint opacity for all tinted blocks.
- Diagrams: inline SVG in UGE palette, no `<text>` (labels as pinned `<p>` or
  `{{eq:id@x,y}}`); flowing SVGs need `flex:none` (the build adds it).
- Animations: `<x-embed>` ≤ 16 KB, system fonts, labels ≥ 24 px, on an
  equal-width grid of label slots. The embed must be a direct child of the
  `<section>`, pinned with `position:absolute` in slide coordinates
  (`left:128px; top:…`); nested in a positioned `div` it renders locally but
  the viewer shows an error. Reserve its place in the flow with a `flex:none`
  spacer `div` of the same height.
- Reference-book figures are allowed as images with one credit line
  (« D'après Prénom Nom, « Titre », éditeur, année, figure N »): render the PDF
  page with Ghostscript at 400 dpi, crop the caption off, upload with
  `asset: true`, measure axis ticks in pixels to place overlays. The local
  preview shows a grey box for `/_blob/` images: check overlays on a local
  render that uses the cropped PNG.
- Removing a slide: grep the other slides and notes for its id and for
  « diapositive suivante/précédente », and check the table of contents, the
  divider notes and the synthesis; move any content worth keeping into a
  neighbour's notes.

## Owner preferences (Ch01 and Ch02 comments)

- No references to TD/TP, other chapters or bibliography on slides (a book
  figure's credit line is the one exception).
- No software-specific trivia that dates quickly (e.g. Fluent operating density).
- Name the method or person behind a result (Buckingham Π for the dimensionless
  groups; Prandtl 1904 for the boundary layer). A part on wall turbulence opens
  with a picture of the boundary layer itself.
- Famous quotations stay in their original language (Richardson's « Big whorls »
  in English), with the French translation in the notes.
- Terminology rulings: « masse volumique » (not « densité »); dissipation goes
  to « énergie interne » (« chaleur » only for heat flux); « tenseur des
  contraintes de Reynolds » (never « tensions de Reynolds »); diagonal entries
  « composantes normales », −ρ⟨u′v′⟩ « contrainte turbulente de cisaillement »;
  « modèles au second ordre (RSM) »; « l'approche RANS » (not « la RANS »);
  « gradient de pression défavorable »; « taille de la première maille »;
  « grands tourbillons »; « forme non conservative »; « advection » for u·∇φ in
  Ch01, « convection » in Ch02 (owner's choice, ask for a new chapter).
- Define every symbol used (Nusselt: define n* or write with q_w).
- Wording: « faible » not « petit »; avoid « mais » in titles and equations.
- Physical sketches must be right (streamlines orthogonal to an outlet).
- Requested colour words are rendered in that colour (« Jaune » in yellow), even
  if a reviewer prefers a swatch.

## External review brief (subagent, read-only)

Give it: `pv-NN.png` (or 1440 px renders), `review/equations.tsv`, `eqs.py`,
`src/slides/`, `config.json`. State the fixed constraints (math rules, centring
rule, size levels, UGE palette, margins, ≥ 24 px, content frozen). Ask for:
A. deck-wide rules violated, with offending slides and eq ids, especially the
size hierarchy computed from `equations.tsv`; B. per-slide findings with concrete
fixes; C. ten highest-impact changes; under 1500 words, no praise. Apply, then
report what was skipped and why.

## Terminology pass and scientific audit

- Terminology brief (read-only subagent): every term not quite accurate in
  French scientific usage, in visible text, notes and `\text{}` labels; compare
  with standard French textbooks; give the owner rulings above as the bar.
  Output: table slide | file:line | current | proposed | reason | confidence,
  every location found by grep; deck-wide inconsistencies; split-usage items.
  Show the owner every row, low-confidence ones included, and let them choose.
- A scientific audit report (e.g. Codex, `slides/REPORT.md`) is a handoff, not
  permission: re-read current sources first, apply short visible fixes, put
  qualifications in notes, add no slides, preserve the verified formulas it lists.
- Apply findings with one scratch script of exact-once replacements: fail on 0
  or several matches; let a space in a pattern also match NBSP and narrow NBSP
  (French text has a narrow NBSP before « : » and « ; »). Then rebuild, audit,
  and fix overflows by moving text to the notes.

## Checks before reporting

- `build.py --selftest`, `audit.py --selftest`, build "OK", audit "no layout
  problems found", every `pv-NN.png` looked at.
- The local preview is not the viewer: say so, and ask the owner to check the
  cover, a divider, one dense slide and every animation in the real deck.

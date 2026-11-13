# Chapter deck (UGE Slides artifact)

Sources of a Claude Slides artifact built from a Quarto chapter. Process and rules: skill `qmd-to-slides`.

- `eqs.py`: every equation, label and table cell, in LaTeX, with its scale (px per TeX pt).
- `src/slides/<id>.html`: one slide each, with `{{eq:id}}` (flowing) or `{{eq:id@x,y}}` (pinned) placeholders.
- `src/order.txt`: slide order and section descriptions; `src/footer.html`, `config.json`: shared snippets and the deck index.
- `build.py`: renders equations (XeLaTeX, `dvisvgm --no-fonts`) to inline SVG and writes `root/project/`.
- `preview.py`: local headless-Chrome render of the slides, for layout checks.
- `audit.py`: on the preview page, flags equal-share columns pushed wider by their content, and content past the side margins or into the footer band.
- `review_pack.py`: `review/equations.tsv` for the external design review.

## Requirements

- TeX Live with `xelatex`, `fontspec`, `amsmath`, `cancel`, `xcolor`; `dvisvgm`.
- The TT Norms Pro font files `TTNormsPro-Regular.otf` and `TTNormsPro-Bold.otf` in `fonts/`.
  They are the university's licensed fonts and are not committed: copy them from the UGE design
  system (https://claude.ai/artifact/CEgGQsZVhRekV6dcfMoTyd, `project/fonts/`).
- For `preview.py` and `audit.py`: Google Chrome; ImageMagick for `preview.py`.

## Usage

```sh
python3 build.py --selftest     # checks the symbol detector
python3 build.py --deck-json    # builds slides and project/deck.json into root/
python3 preview.py [ids...]     # renders pv-NN.png for the given slides (all by default)
python3 audit.py [--selftest]   # layout audit of preview.html (run preview.py with no ids first)
```

The build fails on any slide that breaks the Slides format subset or that shows a mathematical
symbol outside a LaTeX SVG (speaker notes excepted). Publish `root/project/` with the Artifact tool,
`root` set to `root/`.

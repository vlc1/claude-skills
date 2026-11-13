"""Write review/equations.tsv (every equation use, its scale and size) for the external design review.
Run after build.py --deck-json and preview.py; the reviewer reads pv-NN.png and this table."""
import re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build import DEFAULT_SCALE, read_order, render  # noqa: E402
from eqs import EQS, SCALE  # noqa: E402

rows = ["slide\tslide_id\teq_id\tscale\twidth_px\theight_px\tplacement\tlatex"]
for n, sid in enumerate(read_order()[0], 1):
    p = HERE / "src" / "slides" / f"{sid}.html"
    src = p.read_text() if p.exists() else ""
    for m in re.finditer(r"\{\{eq:([\w-]+)(@\d+,\d+)?\}\}", src):
        w, h = re.search(r'width="(\d+)" height="(\d+)"', render(m.group(1))).groups()
        rows.append("\t".join([str(n), sid, m.group(1), str(SCALE.get(m.group(1), DEFAULT_SCALE)), w, h,
                               "pinned" if m.group(2) else "flow", EQS[m.group(1)].replace("\t", " ")]))
(HERE / "review").mkdir(exist_ok=True)
(HERE / "review" / "equations.tsv").write_text("\n".join(rows) + "\n")
print(len(rows) - 1, "equation uses written to review/equations.tsv")

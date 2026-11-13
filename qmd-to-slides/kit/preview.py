"""Local approximation of the slide canvas, to spot overflow before publishing."""
import json, re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ids = sys.argv[1:] or json.loads((HERE / "root/project/deck.json").read_text())["order"]
ids = [i for i in ids if (HERE / f"root/project/slides/{i}.html").exists()]
css = f"""@font-face{{font-family:'TT Norms Pro';src:url({HERE}/fonts/TTNormsPro-Regular.otf)}}
@font-face{{font-family:'TT Norms Pro Bold';src:url({HERE}/fonts/TTNormsPro-Bold.otf)}}
body{{margin:0}}section{{width:1920px;height:1080px;box-sizing:border-box;position:relative;overflow:hidden;outline:2px solid red}}
h1,h2,h3,p,ul{{margin:0}}ul{{padding-left:40px}}aside{{display:none}}x-embed{{display:block;background:#eee}}
img{{background:#ccc}}"""
pages = [ids[i:i + 9] for i in range(0, len(ids), 9)]  # one tall screenshot fails past ~10 slides
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for k, page in enumerate(pages):
    body = "".join(re.sub(r"/_blob/\w+", "", (HERE / f"root/project/slides/{i}.html").read_text()) for i in page)
    (HERE / "preview.html").write_text(f"<!doctype html><meta charset=utf-8><style>{css}</style>{body}")
    subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars", f"--window-size=1920,{1080*len(page)}",
                    f"--screenshot={HERE}/preview.png", f"file://{HERE}/preview.html"], capture_output=True, check=True)
    subprocess.run(["magick", str(HERE / "preview.png"), "-crop", "1920x1080", "+repage", "-resize", "960x540",
                    "-scene", str(9 * k), str(HERE / "pv-%02d.png")], check=True)
# audit.py reads the whole deck from preview.html
body = "".join(re.sub(r"/_blob/\w+", "", (HERE / f"root/project/slides/{i}.html").read_text()) for i in ids)
(HERE / "preview.html").write_text(f"<!doctype html><meta charset=utf-8><style>{css}</style>{body}")
print(len(ids), "slides rendered")

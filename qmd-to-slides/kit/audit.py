"""Layout audit on preview.html: equal-share columns that grew, content past the side margins or into the footer band."""
import pathlib, re, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
JS = """<script>window.onload=()=>{const out=[];document.querySelectorAll('section').forEach(sec=>{const sr=sec.getBoundingClientRect();
sec.querySelectorAll('div').forEach(row=>{const kids=[...row.children].filter(k=>k.tagName==='DIV'&&k.style.flex.startsWith('1'));
if(kids.length>1){const w=kids.map(k=>k.getBoundingClientRect().width);if(Math.max(...w)>1.03*Math.min(...w))out.push(sec.id+': unequal columns '+w.map(Math.round).join('/'));}});
sec.querySelectorAll('svg,p,h2,h3,div').forEach(e=>{if(e.style.position==='absolute')return;const r=e.getBoundingClientRect();
if(r.right>sr.right-120||r.left<sr.left+120)out.push(sec.id+': past margin <'+e.tagName.toLowerCase()+'> '+Math.round(r.left)+'-'+Math.round(r.right));
const lim=sr.bottom-parseFloat(getComputedStyle(sec).paddingBottom)+2;if(!e.closest('[style*=absolute]')&&r.height>0&&r.bottom>lim&&sec.querySelector('[style*="bottom:64px"]'))out.push(sec.id+': into footer band, bottom '+Math.round(r.bottom-sr.top)+' > '+Math.round(lim-sr.top));});});
const pre=document.createElement('pre');pre.id='out';pre.textContent=[...new Set(out)].join('\\n');document.body.appendChild(pre);};</script>"""
def audit(html):
    page = HERE / "audit.html"
    page.write_text(html.replace("</style>", "</style>" + JS, 1))
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    r = subprocess.run([chrome, "--headless", "--disable-gpu", "--virtual-time-budget=3000", "--window-size=1920,1080",
                        "--dump-dom", f"file://{page}"], capture_output=True, text=True)
    page.unlink()
    m = re.search(r'<pre id="out">(.*?)</pre>', r.stdout, re.S)
    assert m, "audit did not run"
    return [l for l in m.group(1).splitlines() if l]
html = (HERE / "preview.html").read_text()
if "--selftest" in sys.argv:
    bad = ('<section id="sanity" style="width:1920px;padding:128px"><div style="display:flex;flex-direction:row;gap:64px">'
           '<div style="flex:1"><svg width="1200" height="50" style="flex:none;width:1200px;height:50px"></svg></div>'
           '<div style="flex:1"></div></div></section>')
    hits = audit(html.replace("<section ", bad + "<section ", 1))
    assert any(h.startswith("sanity: unequal") for h in hits), hits
    print("audit selftest OK")
else:
    print("\n".join(audit(html)) or "no layout problems found")

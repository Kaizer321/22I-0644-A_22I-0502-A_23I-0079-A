import re, sys, pathlib, subprocess, markdown, pypdf
D = pathlib.Path(__file__).parent
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
sys.stdout.reconfigure(encoding="utf-8")
src = (D / "report.md").read_text(encoding="utf-8")
head, rest = src.split("### Abstract", 1)
conv = lambda s: markdown.markdown(s, extensions=["tables", "fenced_code"])
body = '<div class="title">' + conv(head.replace(chr(10), "  " + chr(10))) + "</div>" + conv("### Abstract" + rest)
body = re.sub(r"<p>(<img [^>]*>)\s*(?:</p>\s*<p>)?<em>(.*?)</em></p>", r'<div class="fig">\1<div class="cap">\2</div></div>', body, flags=re.S)

def build(pt, mm, img):
    css = f"""@page{{size:A4;margin:{mm}mm;@bottom-center{{content:counter(page);font:9pt sans-serif}}}}
body{{font:{pt}pt/1.3 Georgia,'Times New Roman',serif;margin:0;text-align:justify}}
h1,h2,h3,h4{{font-family:'Segoe UI',Arial,sans-serif;text-align:left;margin:.9em 0 .3em;break-after:avoid}}
h3{{font-size:1.25em}}h4{{font-size:1.05em}}p{{margin:.4em 0}}
.title{{text-align:center;margin-bottom:1em}}.title h1{{text-align:center;font-size:1.9em;margin:.3em 0}}.title h2{{text-align:center;font-size:1.3em;margin:.2em 0 .8em;font-weight:normal}}
table{{border-collapse:collapse;width:100%;font-size:.88em;break-inside:avoid;margin:.5em 0;text-align:left}}
th,td{{border:.4pt solid #888;padding:2pt 4pt;vertical-align:top}}th{{background:#e8e8e8}}
pre{{background:#f2f2f2;padding:6pt;font:8.5pt/1.25 Consolas,'Courier New',monospace;white-space:pre-wrap;break-inside:avoid;text-align:left}}
code{{font-family:Consolas,'Courier New',monospace;font-size:.9em}}pre code{{font-size:inherit}}
.fig{{break-inside:avoid;text-align:center;margin:.7em 0}}.fig img{{display:block;margin:0 auto;width:{img}%;height:auto;max-width:100%}}.cap{{font-size:.9em;margin-top:.2em}}"""
    h = D / "report.html"
    h.write_text(f"<!doctype html><meta charset=utf-8><style>{css}</style>{body}", encoding="utf-8")
    pdf = D.parent / "report.pdf"
    pdf.unlink(missing_ok=True)
    subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", h.as_uri()], check=True, timeout=180)
    return pdf, pypdf.PdfReader(pdf)

pt, mm, img = float(sys.argv[1]) if len(sys.argv) > 1 else 10.5, 16, 80
pdf, r = build(pt, mm, img)
print(f"pages={len(r.pages)} font={pt}pt margin={mm}mm img={img}%")
print(repr(r.pages[0].extract_text()[:400]))
for n in range(1, 11):
    print(f"Figure {n}: pages", [i for i, p in enumerate(r.pages, 1) if re.search(rf"Figure {n} —", p.extract_text())])

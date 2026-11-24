"""Build the A4 project report from its Markdown source and local figures."""
import argparse
import re
import subprocess
import tempfile
from pathlib import Path

import markdown


DOCS = Path(__file__).resolve().parent
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

COVER = """
<section class="cover">
  <img class="logo" src="figures/fast-nuces-islamabad.png" alt="FAST-NUCES Islamabad logo">
  <div class="university">FAST-NUCES Islamabad</div>
  <div class="department">BS Data Science and Artificial Intelligence</div>
  <div class="project-label">Design and Analysis of Algorithms · Final Project Report</div>
  <h1>LIFELINE</h1>
  <div class="subtitle">Algorithmic Relief-Command Engine</div>
  <div class="members">
    <h2>Group 69 <span>Section AI-A</span></h2>
    <div><strong>Muhammad Umar</strong><span>22I-0644</span></div>
    <div><strong>Haider Ali</strong><span>22I-0502</span></div>
    <div><strong>Awwab Ahmed</strong><span>23I-0079</span></div>
  </div>
</section>
"""

CSS = """
@page { size: A4; margin: 16mm 17mm 17mm; @bottom-center {
  content: counter(page); color: #455b6c; font: 9pt 'Segoe UI', Arial, sans-serif;
} }
@page cover { @bottom-center { content: none; } }
body { margin: 0; color: #192a37; font: 10.5pt/1.29 Georgia, serif; }
h3, h4 { font-family: 'Segoe UI', Arial, sans-serif; break-after: avoid; color: #10476b; }
h3 { font-size: 15pt; margin: .85em 0 .32em; border-bottom: 1px solid #cedde7; padding-bottom: .12em; }
h4 { font-size: 11pt; margin: .75em 0 .25em; }
p { margin: .36em 0; orphans: 2; widows: 2; }
li { margin: .2em 0; }
.cover { page: cover; break-after: page; text-align: center; font-family: 'Segoe UI', Arial, sans-serif;
  border-top: 4px solid #10476b; padding-top: 24mm; }
.logo { width: 30mm; height: 30mm; object-fit: contain; }
.university { font-size: 19pt; font-weight: 700; margin-top: 4mm; color: #10476b; }
.department { font-size: 11pt; color: #455b6c; }
.project-label { margin-top: 30mm; color: #455b6c; font-size: 10pt; }
.cover h1 { font: bold 52pt/1 'Segoe UI', Arial, sans-serif; letter-spacing: .025em;
  color: #10476b; margin: 3mm 0; }
.subtitle { font-size: 19pt; }
.members { margin: 27mm auto 0; width: 107mm; text-align: left; }
.members h2, .members div { display: flex; justify-content: space-between; align-items: baseline; }
.members h2 { font-size: 13pt; color: #10476b; border-bottom: 2px solid #10476b;
  margin: 0; padding: 0 0 2mm; }
.members div { border-bottom: 1px solid #cedde7; padding: 3mm 0; font-size: 11pt; }
.members span { font-size: 10pt; font-weight: 400; color: #455b6c; }
table { border-collapse: collapse; width: 100%; font-size: .85em; margin: .42em 0 .6em; break-inside: avoid; }
th, td { border: .45pt solid #b8cad6; padding: 3pt 4pt; text-align: left; vertical-align: top; }
th { background: #eaf2f7; color: #10476b; }
tbody tr:nth-child(even) { background: #f6f9fb; }
pre { background: #f0f5f8; padding: 7pt; font: 8pt/1.3 Consolas, monospace;
  white-space: pre-wrap; break-inside: avoid; }
code { font-family: Consolas, monospace; font-size: .9em; }
pre code { font-size: inherit; }
.fig { break-inside: avoid; text-align: center; margin: .6em 0 .8em; }
.fig img { display: block; width: auto; max-width: 78%; max-height: 102mm; margin: auto; }
.cap { color: #344e60; font-size: .89em; margin-top: .25em; }
p:has(+ table) { break-after: avoid; }
h3:has(+ p + ul) + p { break-after: avoid; }
"""


def build(browser, output, browser_flags):
    source = (DOCS / "report.md").read_text(encoding="utf-8")
    _, abstract = source.split("### Abstract", 1)
    body = markdown.markdown("### Abstract" + abstract, extensions=["tables", "fenced_code"])
    body = re.sub(
        r"<p>(<img [^>]*>)\s*(?:</p>\s*<p>)?<em>(.*?)</em></p>",
        r'<figure class="fig">\1<figcaption class="cap">\2</figcaption></figure>',
        body,
        flags=re.S,
    )
    html = DOCS / "report.html"
    html.write_text(
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<title>LIFELINE Final Project Report</title><style>{CSS}</style></head>'
        f'<body>{COVER}<main>{body}</main></body></html>',
        encoding="utf-8",
    )
    with tempfile.TemporaryDirectory(prefix="report-browser-", ignore_cleanup_errors=True) as profile:
        subprocess.run(
            [browser, "--headless", "--disable-gpu", "--no-pdf-header-footer", *browser_flags,
             "--no-first-run", f"--user-data-dir={profile}",
             f"--print-to-pdf={output.resolve()}", html.as_uri()],
            check=True,
            timeout=180,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", default=EDGE)
    parser.add_argument("--browser-flag", action="append", default=[])
    parser.add_argument("--output", type=Path, default=DOCS.parent / "report.pdf")
    args = parser.parse_args()
    build(args.browser, args.output, args.browser_flag)

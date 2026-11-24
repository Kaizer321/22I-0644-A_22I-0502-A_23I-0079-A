"""Render real program output as terminal-style PNGs. Usage: make_screens.py out.png "title" textfile first last (1-based, inclusive; last=0 means end)."""
import sys, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

out, title, src, a, b = sys.argv[1:6]
L = open(src, encoding="utf-8", errors="replace").read().splitlines()
L = L[int(a) - 1 : int(b) or None]
L = [l if len(l) <= 110 else l[:109] + "…" for l in L]
lh = 0.19
fig = plt.figure(figsize=(30, (len(L) + 2) * lh + 0.3), dpi=150, facecolor="#1e1e1e")
t1 = fig.text(0.2 / 30, 0.97, "$ " + title, color="#ffffff", family="monospace", size=9, weight="bold", va="top")
t2 = fig.text(0.2 / 30, 0.97 - 2 * lh / fig.get_figheight(), chr(10).join(L), color="#d4d4d4", family="monospace", size=9, va="top", linespacing=1.25)
# size the canvas from the measured text extent, not a guessed char width
r = fig.canvas.get_renderer()
w = max(t.get_window_extent(r).x1 for t in (t1, t2)) / fig.dpi + 0.3
fig.set_size_inches(w, fig.get_figheight())  # fig.text is in figure fractions: re-place at fixed inch offsets
h = fig.get_figheight()
t1.set_position((0.2 / w, 1 - 0.2 / h)); t2.set_position((0.2 / w, 1 - (0.2 + 2 * lh) / h))
fig.savefig(out, facecolor=fig.get_facecolor())

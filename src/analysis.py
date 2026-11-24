import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent / "results"
# two-sided 0.975 t critical values, df = 1..30
T = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145, 2.131,
     2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]
XLABEL = {"A1": "input size n (crates)", "A2": "W (capacity units)", "B1": "V (locations)", "C1": "n (windows)", "D1": "m (alarms)"}
DESC = {"A1": "knapsack, vary n, pooled M+L crates, W = 0.4 x total weight", "A2": "knapsack, vary W, first 4000 pooled crates",
        "B1": "shortest paths, synthetic maps with E = 2.5V", "B2": "shortest paths, 12 real L-sample maps",
        "C1": "window scheduling, pooled M+L windows", "D1": "alarm queues, pooled M+L alarms"}
FIT_COLS = ["experiment", "algorithm", "metric", "k_points", "slope", "ci_low", "ci_high", "r2", "holdout_size", "holdout_rel_error", "predicted_missing"]


def fit(size, y):
    """Least squares of log10(y) on log10(size); slope, 95% CI, R², intercept."""
    x, y = np.log10(size), np.log10(y)
    b, a = np.polyfit(x, y, 1)
    r = y - (a + b * x)
    se = np.sqrt(r @ r / (len(x) - 2) / ((x - x.mean()) ** 2).sum())
    sst = ((y - y.mean()) ** 2).sum()
    t = T[len(x) - 3]
    return {"slope": b, "ci_low": b - t * se, "ci_high": b + t * se, "r2": 1 - r @ r / sst if sst else 1.0, "a": a}


def fits(rows):
    by, sizes, dnf = defaultdict(list), defaultdict(set), set()
    for r in rows:
        sizes[r["experiment"]].add(float(r["size"]))
        if r["status"] == "DNF":
            dnf.add((r["experiment"], r["algorithm"]))
        if r["status"] == "OK" and r["experiment"] != "B2":
            by[r["experiment"], r["algorithm"]].append((float(r["size"]), float(r["time_s"]), float(r["ops"])))
    out = []
    for (e, alg), pts in by.items():
        pts.sort()
        for metric, col in (("time", 1), ("ops", 2)):
            p = [q for q in pts if q[col] > 0]
            if len(p) < 5:
                continue
            s, y = [q[0] for q in p], [q[col] for q in p]
            f, h = fit(s, y), fit(s[:-1], y[:-1])
            pred = 10 ** (h["a"] + h["slope"] * np.log10(s[-1]))
            miss = sorted(sizes[e] - set(s)) if metric == "time" and (e, alg) in dnf else []
            out.append({"experiment": e, "algorithm": alg, "metric": metric, "k_points": len(p), "slope": f["slope"], "ci_low": f["ci_low"],
                        "ci_high": f["ci_high"], "r2": f["r2"], "holdout_size": int(s[-1]), "holdout_rel_error": abs(pred - y[-1]) / y[-1],
                        "predicted_missing": ";".join(f"{int(m)}:{10 ** (f['a'] + f['slope'] * np.log10(m)):.4g}" for m in miss)})
    return out


def caption(exp, env, what):
    hw = f"{env.get('cpu', '?')}, {env.get('ram', '?')}, Windows/Python {env.get('python', '?')}"
    return f"Experiment {exp}: {DESC[exp]}. Hardware: {hw}. {what}"


def plot_series(exp, rows, col, ylabel, cap, path, bars):
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for alg, m in zip(dict.fromkeys(r["algorithm"] for r in rows), "osd^v"):
        p = sorted((float(r["size"]), float(r[col]), float(r["time_iqr_s"] or 0)) for r in rows if r["algorithm"] == alg)
        ax.errorbar([q[0] for q in p], [q[1] for q in p], yerr=[q[2] / 2 for q in p] if bars else None, marker=m, capsize=3, label=alg)
    ax.set(xscale="log", yscale="log", xlabel=XLABEL[exp], ylabel=ylabel, title=f"{exp}: {DESC[exp]}")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.text(0.5, 0.01, cap, ha="center", va="bottom", wrap=True, fontsize=8)
    fig.subplots_adjust(bottom=0.22)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_b2(rows, cap, path):
    t = defaultdict(dict)
    for r in rows:
        t[r["instance"], int(r["size"])][r["algorithm"]] = float(r["time_s"])
    k = sorted((k for k, v in t.items() if len(v) == 2 and v["dijkstra"] > 0), key=lambda k: k[1])
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.bar(range(len(k)), [t[x]["bellman_ford"] / t[x]["dijkstra"] for x in k])
    ax.set_xticks(range(len(k)), [f"{c}\nV={v}" for c, v in k], rotation=60, fontsize=7)
    ax.set(yscale="log", xlabel="case_id (V locations)", ylabel="Bellman-Ford / Dijkstra time ratio (x)", title="B2: Bellman-Ford vs Dijkstra on real maps")
    ax.axhline(1, color="k", lw=0.8)
    fig.text(0.5, 0.01, cap, ha="center", va="bottom", wrap=True, fontsize=8)
    fig.subplots_adjust(bottom=0.3)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv)
    base = ROOT / "smoke" if a.smoke else ROOT
    plots = base / "plots" if a.smoke else ROOT / "plots"
    plots.mkdir(parents=True, exist_ok=True)
    with open(base / "results.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    env = {}
    if (base / "environment.txt").exists():
        env = dict(l.split(": ", 1) for l in (base / "environment.txt").read_text().splitlines() if ": " in l)
    with open(base / "fits.csv", "w", newline="") as f:
        w = csv.DictWriter(f, FIT_COLS)
        w.writeheader()
        w.writerows(fits(rows))
    tail = "SMOKE: 1 run, no warm-up, error bars = IQR" if a.smoke else "median of 5 runs after 1 warm-up, error bars = IQR"
    for e in dict.fromkeys(r["experiment"] for r in rows):
        ok = [r for r in rows if r["experiment"] == e and r["status"] == "OK"]
        if not ok:
            continue
        if e == "B2":
            plot_b2(ok, caption(e, env, tail), plots / "B2_ratio.png")
            continue
        plot_series(e, ok, "time_s", "median time (s)", caption(e, env, tail), plots / f"{e}_time.png", True)
        plot_series(e, ok, "ops", "operations (count)", caption(e, env, "operation counters of one deterministic run (excluding pre_*)."), plots / f"{e}_ops.png", False)


if __name__ == "__main__":
    main()

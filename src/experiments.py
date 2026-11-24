import argparse
import csv
import datetime
import functools
import multiprocessing as mp
import platform
import queue
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

from src import alarms, inventory, loader, routes, scheduling

TIMEOUT = 300  # seconds to wait for each message of a child (rulebook 6.3)
ROOT = Path(__file__).resolve().parent.parent / "results"
COLS = ["module", "experiment", "algorithm", "instance", "size", "size2", "time_s", "time_iqr_s", "ops", "mem_bytes", "status", "note"]


def _worker(q, fn, args, mode, runs):
    try:
        if mode == "mem":
            tracemalloc.start()  # the instance already exists in this child
            fn(*args)
            q.put(("mem", tracemalloc.get_traced_memory()[1]))
            return
        ops = {}
        res = fn(*args, ops=ops)  # counted run doubles as the discarded warm-up
        q.put(("ops", ops, res))
        for _ in range(runs):
            t = time.perf_counter()
            fn(*args)
            q.put(("t", time.perf_counter() - t))
    except Exception as e:
        q.put(("err", repr(e)))


def run_child(fn, args, mode="time", runs=5):
    """-> ("OK", info) | ("DNF", None) | ("FAIL", reason); info has ops/res/times or mem."""
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=_worker, args=(q, fn, args, mode, runs))
    p.start()
    info = {"times": []}
    try:
        for _ in range(1 if mode == "mem" else 1 + runs):
            m = q.get(timeout=TIMEOUT)
            if m[0] == "err":
                return "FAIL", m[1]
            if m[0] == "ops":
                info["ops"], info["res"] = m[1], m[2]
            elif m[0] == "t":
                info["times"].append(m[1])
            else:
                info["mem"] = m[1]
        return "OK", info
    except queue.Empty:
        return "DNF", None
    finally:
        if p.is_alive():
            p.terminate()
        p.join()


@functools.cache
def _groups(table):
    ids = loader.sample("M") + loader.sample("L")
    d = loader.load(ids, [table])[table]
    return [d[c] for c in ids]


@functools.cache
def _maps():
    ids = loader.sample("L")
    d = loader.load(ids, ["locations", "roads"])
    maps = sorted(((len(d["locations"][c]), c) for c in ids))
    pick = [maps[round(i * (len(maps) - 1) / 11)] for i in range(12)] if len(maps) > 12 else maps
    out = []
    for V, c in dict.fromkeys(pick):
        roads = [(r["road_no"], r["u"], r["v"], r["minutes"]) for r in d["roads"][c]]
        out.append((c, V, roads, [r["penalty"] for r in d["locations"][c]]))
    return out


def _a1(n):
    items = loader.pool_crates(_groups("crates"), n)
    W = sum(w for _, w, _ in items) * 2 // 5
    return f"pool:M+L:n={n}", n, W, (items, W)


def _a2(W):
    return "pool:M+L:n=4000", W, 4000, (loader.pool_crates(_groups("crates"), 4000), W)


def _b(V, roads, penalty):
    return (V, routes.build_adj(V, roads, penalty), 0), len(roads)


def _b1(V):
    args, E = _b(*loader.synthetic_network(V, f"69-synth-{V}"))
    return f"synth:69-synth-{V}", V, E, args


def _b2(key):
    c, V, roads, penalty = key
    args, E = _b(V, roads, penalty)
    return c, V, E, args


def _c1(n):
    return f"pool:M+L:n={n}", n, None, (loader.pool_windows(_groups("windows"), n),)


def _d1(m):
    return f"pool:M+L:m={m}", m, None, (loader.pool_alarms(_groups("incidents"), m),)


def _geo(a, n):
    return [a * 2**i for i in range(n)]


def _chk_a1(r):
    return None if r["knapsack_dp"][0] >= r["ratio_greedy"][0] else "knapsack_dp value < ratio_greedy value"


def _chk_b(r):
    return None if r["dijkstra"][0] == r["bellman_ford"][0] else "dijkstra dist != bellman_ford dist"


def _chk_d1(r):
    v = list(r.values())
    return None if all(x == v[0] for x in v) else "alarm release orders differ"


# name: (module, algorithms, sizes(), build, check)
EXPS = {
    "A1": ("A", [inventory.knapsack_dp, inventory.ratio_greedy], lambda: _geo(100, 7), _a1, _chk_a1),
    "A2": ("A", [inventory.knapsack_dp], lambda: _geo(1000, 6), _a2, None),
    "B1": ("B", [routes.dijkstra, routes.bellman_ford, routes.bfs_fewest], lambda: _geo(500, 7), _b1, _chk_b),
    "B2": ("B", [routes.dijkstra, routes.bellman_ford], _maps, _b2, _chk_b),
    "C1": ("C", [scheduling.eff_count, scheduling.weighted_dp, scheduling.value_greedy], lambda: _geo(250, 8), _c1, None),
    "D1": ("D", [alarms.release_heap, alarms.release_sorted_list, alarms.release_buckets], lambda: _geo(500, 8), _d1, _chk_d1),
}


def write_rows(path, exps, rows):
    keep = []
    if path.exists():
        with open(path, newline="") as f:
            keep = [r for r in csv.DictReader(f) if r["experiment"] not in exps]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        w.writerows(keep + rows)


def measure(fn, args, runs):
    st, info = run_child(fn, args, "time", runs)
    if st != "OK":
        return {"status": st, "note": info or "timeout"}
    t = info["times"]
    out = {"status": "OK", "res": info["res"], "time_s": statistics.median(t),
           "time_iqr_s": (lambda q: q[2] - q[0])(statistics.quantiles(t, n=4)) if len(t) > 1 else 0.0,
           "ops": sum(v for k, v in info["ops"].items() if not k.startswith("pre_")),
           "note": ";".join(f"{k}={v}" for k, v in info["ops"].items())}
    st, m = run_child(fn, args, "mem")
    if st == "OK":
        out["mem_bytes"] = m["mem"]
    else:
        out["note"] += f";mem:{st}"
        if st == "FAIL":
            out["status"] = "FAIL"
            out["note"] += f": {m}"
    return out


def run_experiment(name, smoke):
    module, fns, sizes, build, check = EXPS[name]
    sizes = sizes()[:2 if smoke else None]
    dnf, rows = set(), []
    for s in sizes:
        inst, size, size2, args = build(s)
        pts = {}
        for fn in fns:
            if fn.__name__ in dnf:
                continue
            p = measure(fn, args, 1 if smoke else 5)
            if p["status"] == "DNF":
                dnf.add(fn.__name__)
            pts[fn.__name__] = p
        reason = None
        if check and all(p["status"] == "OK" for p in pts.values()) and len(pts) == len(fns):
            try:
                reason = check({k: p["res"] for k, p in pts.items()})
            except Exception as e:
                reason = repr(e)
        for alg, p in pts.items():
            p.pop("res", None)
            if reason:
                p["status"], p["note"] = "FAIL", f"{reason};{p.get('note', '')}"
            rows.append({"module": module, "experiment": name, "algorithm": alg, "instance": inst, "size": size, "size2": size2, **p})
            print(f"{name} {alg} {inst} size={size} {p['status']} t={p.get('time_s')} ops={p.get('ops')} mem={p.get('mem_bytes')}", flush=True)
    return rows


def write_environment(out):
    cpu = platform.processor()
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
            cpu = winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
    except (ImportError, OSError):
        pass
    try:
        import psutil
        ram = f"{psutil.virtual_memory().total / 2**30:.1f} GB"
    except ImportError:
        ram = "unknown (psutil not installed)"
    lines = [f"platform: {platform.platform()}", f"python: {platform.python_version()}", f"cpu: {cpu}", f"ram: {ram}",
             f"datetime: {datetime.datetime.now().isoformat(timespec='seconds')}", f"master_release: {loader.RELEASE}"]
    (out / "environment.txt").write_text("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("exps", nargs="*")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv)
    ap.error(f"unknown experiment in {a.exps}") if set(a.exps) - set(EXPS) else None
    out = ROOT / "smoke" if a.smoke else ROOT
    out.mkdir(parents=True, exist_ok=True)
    write_environment(out)
    failed = False
    for name in a.exps or EXPS:
        rows = run_experiment(name, a.smoke)
        write_rows(out / "results.csv", {name}, rows)
        failed |= any(row["status"] == "FAIL" for row in rows)
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())

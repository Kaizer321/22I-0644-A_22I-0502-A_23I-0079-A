import csv
import time
from collections import deque
from pathlib import Path

from src import alarms as al_, inventory, loader, routes, scheduling
from src import validation as valid

RES = Path(__file__).resolve().parent.parent / "results"
TABLES = ["cases", "crates", "locations", "roads", "waves", "windows", "incidents"]
DEFAULT = ["1-06", "1-26", "2-40", "2-48", "4-47"]
EVENTS = ["Normal", "Storm", "Food shortage", "Dangerous area", "Medical emergency", "Flood", "Evacuation"]
FIELDS = ("case_id tier day event destination reachable route_roads route_cost bf_cost fewest_route_cost capacity "
          "load_value_dp load_value_greedy load_weight_dp windows_available windows_count windows_value_dp "
          "windows_value_greedy alarms mean_wait max_wait max_wait_p9 peak_queue checks_failed note").split()
MULT = {2: (3, 2), 3: (0, 2), 5: (2, 3)}  # day -> (crate category, integer multiplier)


def mins(day, m): return (3 * m + 1) // 2 if day == 2 else m
def pen(day, p): return 2 * p if day == 4 and p >= 2 else p
def crate_value(day, cat, v): return v * MULT[day][1] if day in MULT and cat == MULT[day][0] else v


def blocked_roads(day, waves):
    wnos = sorted({w["wave_no"] for w in waves})  # master cases number waves from 0 or from 1
    if day == 1 or not wnos:
        return set()
    return {w["road_no"] for w in waves if day > 5 or w["wave_no"] == wnos[(day - 2) % len(wnos)]}


def timed(f, *a):
    ops, t = {}, time.perf_counter()
    r = f(*a, ops=ops)
    return r, time.perf_counter() - t, ops


def alarm_check(al, rel):
    # independent of module D: per-priority FIFOs of admitted alarms, the head of the top non-empty one must be released
    info = {a[0]: a for a in al}
    if sorted(x[1] for x in rel) != sorted(info):
        return "not every alarm released exactly once"
    q, i, prev, size = {p: deque() for p in range(1, 11)}, 0, -1, 0
    for t, aid in rel:
        if t <= prev:
            return "more than one release per tick"
        if t > prev + 1 and size:
            return f"tick {prev + 1} idle with alarms waiting"
        while i < len(al) and al[i][1] <= t:
            q[al[i][2]].append(al[i][0])
            i, size = i + 1, size + 1
        if info[aid][1] > t:
            return f"alarm {aid} released before arrival"
        top = next((p for p in range(10, 0, -1) if q[p]), None)
        if top is None or q[top][0] != aid:
            return f"alarm {aid} released at {t} while a more urgent one waited"
        q[top].popleft()
        size, prev = size - 1, t
    return None


def run_case(cid, d):
    L = []
    p = L.append
    c = d["cases"][0]
    cap, targets = c["capacity"], [c["target_0"], c["target_1"], c["target_2"]]
    try:
        valid.check_crates(cid, d["crates"], cap)
        valid.check_network(cid, d["locations"], d["roads"], d["waves"], targets)
        valid.check_windows(cid, d["windows"])
        valid.check_alarms(cid, d["incidents"])
    except valid.InvalidInput as e:
        return f"{cid}: INVALID INPUT rule={e.rule} detail={e.detail} -> campaign stopped", []
    V, ends = len(d["locations"]), {r["road_no"]: (r["u"], r["v"]) for r in d["roads"]}
    rows = []
    p(f"=== case {cid} (tier {c['tier']}), capacity {cap}, targets {targets}")
    for day in range(1, 8):
        pn = [pen(day, x["penalty"]) for x in d["locations"]]
        roads = [(r["road_no"], r["u"], r["v"], mins(day, r["minutes"])) for r in d["roads"]]
        rm = {no: m for no, _, _, m in roads}
        blocked = blocked_roads(day, d["waves"])
        dst = targets[(day - 1) % 3]
        crates = [(r["crate_id"], r["weight"], crate_value(day, r["cat"], r["value"])) for r in d["crates"]]
        al = [(r["alarm_id"], r["tick"], r["priority"]) for r in d["incidents"]]
        if day in (2, 5):  # ASSUMPTION: the extra alarm exists on its day only
            al = sorted(al + [(max((a[0] for a in al), default=0) + 1, 0, 9 if day == 2 else 10)], key=lambda a: (a[1], a[0]))
        wins = [(r["window_id"], r["start"], r["finish"], r["value"]) for r in d["windows"] if (r["window_id"] + day) % 5]
        changes = {1: "none", 2: "minutes x1.5 (ceil), tool crates x2, alarm p9 at tick 0", 3: "food crates x2",
                   4: "penalties >= 2 doubled", 5: "medicine crates x3, alarm p10 at tick 0", 6: "none", 7: "no loading"}[day]
        row = dict.fromkeys(FIELDS) | dict(case_id=cid, tier=c["tier"], day=day, event=EVENTS[day - 1], destination=dst, capacity=cap,
                   windows_available=len(wins), alarms=len(al))
        checks, note = [], ""
        p(f"--- Day {day}: {EVENTS[day - 1]}")
        p(f"input: destination {dst}, blocked roads {len(blocked)}, crates {len(crates)}, windows {len(wins)} available "
          f"of {len(d['windows'])}, alarms {len(al)}; changes: {changes}")

        def walk(path):  # independent re-cost of a road list from HQ; None when invalid
            u, tot = 0, 0
            for no in path:
                if no in blocked or u not in ends[no]:
                    return None
                u = ends[no][1] if u == ends[no][0] else ends[no][0]
                tot += rm[no] + pn[u]
            return tot if u == dst else None

        adj = routes.build_adj(V, roads, pn, blocked)
        (hops, bpar), tb, ob = timed(routes.bfs_fewest, V, adj, 0)
        row["reachable"] = reach = hops[dst] is not None
        if reach:
            (dist, par), td, od = timed(routes.dijkstra, V, adj, 0)
            (bf, _), tf, of = timed(routes.bellman_ford, V, adj, 0)
            path, fewest = routes.path(par, 0, dst), routes.path(bpar, 0, dst)
            fcost = routes.route_cost(adj, 0, fewest)
            row.update(route_roads=len(path), route_cost=dist[dst], bf_cost=bf[dst], fewest_route_cost=fcost)
            checks += [("route", walk(path) == dist[dst] and walk(fewest) == fcost, "path invalid or cost does not re-sum"),
                       ("bellman_ford == dijkstra", bf[dst] == dist[dst], f"{bf[dst]} != {dist[dst]}")]
            p(f"route: {len(path)} roads, cost {dist[dst]}")
            p(f"  baseline: bellman_ford cost {bf[dst]}; fewest-roads route {len(fewest)} roads, cost {fcost} (gap {fcost - dist[dst]})")
            p(f"  time/ops: dijkstra {td * 1e3:.2f}ms {od}; bellman_ford {tf * 1e3:.2f}ms {of}; bfs {tb * 1e3:.2f}ms {ob}")
            if day < 7:
                (dv, di), td, od = timed(inventory.knapsack_dp, crates, cap)
                (gv, gi), tg, og = timed(inventory.ratio_greedy, crates, cap)
                cm = {i: (w, v) for i, w, v in crates}

                def load_ok(v, ids):
                    return len(set(ids)) == len(ids) and all(i in cm for i in ids) and \
                        sum(cm[i][0] for i in ids) <= cap and sum(cm[i][1] for i in ids) == v

                checks.append(("load", load_ok(dv, di) and load_ok(gv, gi), "weight over capacity, duplicate id or value does not re-sum"))
                row.update(load_value_dp=dv, load_value_greedy=gv, load_weight_dp=sum(cm[i][0] for i in di))
                p(f"load: {len(di)} crates, value {dv}, weight {row['load_weight_dp']}/{cap}")
                p(f"  baseline: ratio_greedy value {gv} (gap {dv - gv})")
                p(f"  time/ops: knapsack_dp {td * 1e3:.2f}ms {od}; ratio_greedy {tg * 1e3:.2f}ms {og}")
            else:
                note = "evacuation, no loading"
                p("load: none (evacuation)")
        else:
            note = "no route"
            p("route: no route, trip skipped (no loading)")
        # windows and alarms run every day, trip or not
        ec, te, oe = timed(scheduling.eff_count, wins)
        (wv, wi), tw, ow = timed(scheduling.weighted_dp, wins)
        (gv, gi), tg, og = timed(scheduling.value_greedy, wins)
        wm = {i: (s, f, v) for i, s, f, v in wins}

        def win_ok(ids):
            ss = sorted(wm[i][:2] for i in ids if i in wm)
            return len(ss) == len(ids) and all(a[1] <= b[0] for a, b in zip(ss, ss[1:]))

        checks.append(("windows", all(map(win_ok, (ec, wi, gi))) and sum(wm[i][2] for i in wi) == wv and sum(wm[i][2] for i in gi) == gv,
                       "overlap, unavailable window or value does not re-sum"))
        row.update(windows_count=len(ec), windows_value_dp=wv, windows_value_greedy=gv)
        p(f"windows: {len(ec)} by earliest finish, DP value {wv} ({len(wi)} windows)")
        p(f"  baseline: value_greedy value {gv} (gap {wv - gv})")
        p(f"  time/ops: eff_count {te * 1e3:.2f}ms {oe}; weighted_dp {tw * 1e3:.2f}ms {ow}; value_greedy {tg * 1e3:.2f}ms {og}")
        rel, th, oh = timed(al_.release_heap, al)
        rs, ts, os_ = timed(al_.release_sorted_list, al)
        rb, tk, ok = timed(al_.release_buckets, al)
        arr = {a[0]: a for a in al}
        waits = [t - arr[i][1] for t, i in rel]
        w9 = [t - arr[i][1] for t, i in rel if arr[i][2] >= 9]
        peak, k = 0, 0
        for n, (t, _) in enumerate(rel):
            while k < len(al) and al[k][1] <= t:
                k += 1
            peak = max(peak, k - n)
        bad = alarm_check(al, rel)
        checks += [("alarm queues identical", rel == rs == rb, "release orders differ"), ("alarms", bad is None, bad)]
        row.update(mean_wait=f"{sum(waits) / len(waits):.2f}" if waits else 0, max_wait=max(waits, default=0),
                   max_wait_p9=max(w9) if w9 else "", peak_queue=peak)
        p(f"alarms: {len(al)} released, mean wait {row['mean_wait']}, max wait {row['max_wait']}, "
          f"max wait priority>=9 {'n/a' if row['max_wait_p9'] == '' else row['max_wait_p9']}, peak queue {peak}")
        p(f"  baselines: sorted_list and bucket queue release order identical: {rel == rs == rb}")
        p(f"  time/ops: heap {th * 1e3:.2f}ms {oh}; sorted_list {ts * 1e3:.2f}ms {os_}; buckets {tk * 1e3:.2f}ms {ok}")
        p("constraints: " + "; ".join(f"{n} {'OK' if ok else 'FAIL (' + str(m) + ')'}" for n, ok, m in checks))
        row.update(checks_failed=sum(not ok for _, ok, _ in checks), note=note)
        p(f"outcome: {'trip made' if reach else 'no route, trip skipped'}; checks failed {row['checks_failed']}")
        rows.append(row)
    p(f"SUMMARY {cid}: tier {c['tier']}, skipped trips {sum(not r['reachable'] for r in rows)}, "
      f"checks failed {sum(r['checks_failed'] for r in rows)}")
    return "\n".join(L), rows


def difficult(rows):
    L = ["=== deliberately difficult scenarios"]
    for cid, what, num, den, days in (("4-47", "greedy/DP load value", "load_value_greedy", "load_value_dp", range(1, 7)),
                                      ("2-48", "fewest-roads/Dijkstra route cost", "fewest_route_cost", "route_cost", range(1, 8))):
        for r in rows:
            if r["case_id"] == cid and r["day"] in days and r["reachable"] and r[den]:
                L.append(f"{cid} day {r['day']}: {what} = {r[num]}/{r[den]} = {r[num] / r[den]:.3f}")
    skipped = [f"{r['case_id']} day {r['day']}" for r in rows if not r["reachable"]]
    L.append("skipped trips (no route): " + (", ".join(skipped) or "none"))
    return "\n".join(L)


def campaign(case_ids=None):
    ids = case_ids or DEFAULT
    data, rows, bad = loader.load(ids, TABLES), [], 0
    RES.mkdir(exist_ok=True)
    for cid in ids:
        d = {t: data[t][cid] for t in TABLES}
        text, r = run_case(cid, d) if d["cases"] else (f"{cid}: INVALID INPUT rule=case.unknown detail=not in cases.csv", [])
        print(text)
        (RES / f"campaign_{cid}.txt").write_text(text + "\n", encoding="utf-8")
        rows += r
        bad += (not r) + sum(x["checks_failed"] for x in r)
    with open(RES / "campaign_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(difficult(rows))
    return bad

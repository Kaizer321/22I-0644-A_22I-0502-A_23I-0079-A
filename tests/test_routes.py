import random
import time
from collections import deque

import pytest

from src import loader
from src.routes import bellman_ford, bfs_fewest, build_adj, dijkstra, path, route_cost
from src.validation import InvalidInput, check_network

INF = float("inf")


def rand_graph(rng):
    V = rng.randint(2, 30)
    pairs = {tuple(sorted(rng.sample(range(V), 2))) for _ in range(rng.randint(0, 2 * V))}
    roads = [(k, u, v, rng.randint(1, 20)) for k, (u, v) in enumerate(sorted(pairs))]
    return V, roads, [rng.choice([0, 1, 2, 4, 6]) for _ in range(V)]


def floyd(V, roads, pen):
    d = [[0 if i == j else INF for j in range(V)] for i in range(V)]
    for _, u, v, m in roads:
        d[u][v], d[v][u] = min(d[u][v], m + pen[v]), min(d[v][u], m + pen[u])
    for k in range(V):
        for i in range(V):
            for j in range(V):
                d[i][j] = min(d[i][j], d[i][k] + d[k][j])
    return d


def ref_hops(V, roads, src):
    nb = [[] for _ in range(V)]
    for _, u, v, _ in roads:
        nb[u].append(v)
        nb[v].append(u)
    h, q = {src: 0}, deque([src])
    while q:
        u = q.popleft()
        for v in nb[u]:
            if v not in h:
                h[v] = h[u] + 1
                q.append(v)
    return [h.get(x) for x in range(V)]


def test_random_graphs():
    rng = random.Random(69)
    for _ in range(200):
        V, roads, pen = rand_graph(rng)
        adj = build_adj(V, roads, pen)
        src = rng.randrange(V)
        fw = floyd(V, roads, pen)[src]
        dd, dp = dijkstra(V, adj, src)
        bd, _ = bellman_ford(V, adj, src)
        hops, _ = bfs_fewest(V, adj, src)
        assert dd == bd == [None if x == INF else x for x in fw]
        assert hops == ref_hops(V, roads, src)
        for t in range(V):
            p = path(dp, src, t)
            assert (p is None) == (dd[t] is None)
            if p is not None:
                assert route_cost(adj, src, p) == dd[t]


def test_directed_asymmetry():
    adj = build_adj(2, [(0, 0, 1, 5)], [0, 3])
    assert dijkstra(2, adj, 0)[0][1] == 8 and dijkstra(2, adj, 1)[0][0] == 5


def test_blocked_and_self():
    adj = build_adj(2, [(7, 0, 1, 5)], [0, 0], blocked=[7])
    d, p = dijkstra(2, adj, 0)
    assert d[1] is None and path(p, 0, 1) is None and path(p, 0, 0) == []


def test_route_cost_rejects_bad_road():
    with pytest.raises(ValueError):
        route_cost(build_adj(2, [(0, 0, 1, 5)], [0, 0]), 0, [9])


def test_bfs_tie_rule():
    roads = [(0, 0, 2, 1), (1, 0, 1, 1), (2, 2, 3, 1), (3, 1, 3, 1)]
    adj = build_adj(4, roads, [0] * 4)
    _, par = bfs_fewest(4, adj, 0)
    assert path(par, 0, 3) == [1, 3]  # via node 1, not 2


def test_validation_rejects_endpoint_ge_V():
    locs = [{"loc_id": i, "penalty": 0} for i in range(3)]
    with pytest.raises(InvalidInput):
        check_network("c", locs, [{"road_no": 0, "u": 0, "v": 3, "minutes": 1}], [], [1])


def run_master(ids, bf):
    t = loader.load(ids, ["cases", "locations", "roads"])
    trap = []
    for c in ids:
        cs, locs, rds = t["cases"][c][0], t["locations"][c], t["roads"][c]
        V, pen = len(locs), [r["penalty"] for r in locs]
        adj = build_adj(V, [(r["road_no"], r["u"], r["v"], r["minutes"]) for r in rds], pen)
        dd, dp = dijkstra(V, adj, 0)
        if bf:
            assert dd == bellman_ford(V, adj, 0)[0]
        _, bp = bfs_fewest(V, adj, 0)
        ratios = []
        for k in range(3):
            tg = cs[f"target_{k}"]
            if dd[tg] is None:
                continue
            bc = route_cost(adj, 0, path(bp, 0, tg))
            assert dd[tg] <= bc
            ratios.append(2 * bc >= 3 * dd[tg])
        if cs["case_no"] == 48:
            trap.append(any(ratios))
    return trap


def test_master_S():
    run_master(loader.sample("S"), True)


def test_master_trap_48():
    cases = {c["case_id"]: c["case_no"] for c in loader.read_cases()}
    ids = [c for c in loader.sample("X") if cases[c] == 48]
    assert ids
    assert all(run_master(ids, False))


def test_synth_timing(capsys):
    V, roads, pen = loader.synthetic_network(4000, "69-synth-4000")
    adj = build_adj(V, roads, pen)
    res = []
    for f in (dijkstra, bellman_ford):
        ops, t0 = {}, time.perf_counter()
        d, _ = f(V, adj, 0, ops)
        res.append((d, f.__name__, time.perf_counter() - t0, ops))
    assert res[0][0] == res[1][0]
    with capsys.disabled():
        for _, n, t, o in res:
            print(f"\n{n}: {t:.3f}s {o}")

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

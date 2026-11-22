from collections import deque

from src.heap import MinHeap, inc
from src.sorting import merge_sort


def build_adj(V, roads, penalty, blocked=(), ops=None):
    blocked, adj = set(blocked), [[] for _ in range(V)]
    for no, u, v, m in roads:
        if no not in blocked:
            adj[u].append((v, m + penalty[v], no))
            adj[v].append((u, m + penalty[u], no))
    return [merge_sort(a, lambda e: (e[0], e[2]), ops, "pre_") for a in adj]


def dijkstra(V, adj, src, ops=None):
    dist, parent, h = [None] * V, [None] * V, MinHeap(ops=ops)
    dist[src] = 0
    h.push((0, src))
    while h:
        d, u = h.pop()
        if d > dist[u]:  # stale entry (lazy deletion)
            continue
        inc(ops, "nodes")
        for v, c, no in adj[u]:
            inc(ops, "edges")
            inc(ops, "relax")  # ASSUMPTION: relax counts every attempted relaxation, i.e. every examined edge
            if dist[v] is None or d + c < dist[v]:
                dist[v], parent[v] = d + c, (u, no)
                h.push((d + c, v))
    return dist, parent


def bellman_ford(V, adj, src, ops=None):
    dist, parent = [None] * V, [None] * V
    dist[src] = 0
    for _ in range(V - 1):
        inc(ops, "rounds")
        changed = False
        for u in range(V):
            if dist[u] is None:
                continue
            for v, c, no in adj[u]:
                inc(ops, "edges")
                inc(ops, "relax")
                if dist[v] is None or dist[u] + c < dist[v]:
                    dist[v], parent[v] = dist[u] + c, (u, no)
                    changed = True
        if not changed:
            break
    return dist, parent


def bfs_fewest(V, adj, src, ops=None):
    hops, parent, q = [None] * V, [None] * V, deque([src])
    hops[src] = 0
    while q:
        u = q.popleft()
        inc(ops, "nodes")
        for v, _, no in adj[u]:
            inc(ops, "edges")
            if hops[v] is None:  # first discovery wins = lowest-id tie rule
                hops[v], parent[v] = hops[u] + 1, (u, no)
                q.append(v)
    return hops, parent


def path(parent, src, dst):
    if dst != src and parent[dst] is None:
        return None
    out = []
    while dst != src:
        dst, no = parent[dst]
        out.append(no)
    return out[::-1]


def route_cost(adj, src, roads_used):
    total, u = 0, src
    for no in roads_used:
        for v, c, n in adj[u]:
            if n == no:
                total, u = total + c, v
                break
        else:
            raise ValueError(f"road {no} not usable from node {u}")
    return total

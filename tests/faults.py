# Deliberately faulty copies of production functions; used only through LIFELINE_FAULT (see conftest.py).
from src import alarms, routes
from src.heap import MinHeap, inc
from src.sorting import merge_sort

_real_build_adj = routes.build_adj  # bound before conftest patches routes.build_adj


def eff_count(windows, ops=None):
    chosen, last = [], None
    for wid, s, f, _ in merge_sort(windows, lambda w: (w[2], w[0])):
        inc(ops, "items")
        if last is None or s > last:  # BUG: touching windows rejected
            chosen.append(wid)
            last = f
    return chosen


def weighted_dp(windows, ops=None):
    ws = merge_sort(windows, lambda w: (w[2], w[0]))
    n = len(ws)
    p, dp, take = [0] * (n + 1), [0] * (n + 1), [False] * (n + 1)
    for j in range(1, n + 1):
        s, v = ws[j - 1][1], ws[j - 1][3]
        lo = 0
        inc(ops, "probe")
        while lo < n and ws[lo][2] < s:  # BUG: < instead of <=
            lo += 1
        inc(ops, "cells")
        p[j], dp[j] = lo, dp[j - 1]
        if dp[lo] + v > dp[j]:
            dp[j], take[j] = dp[lo] + v, True
    chosen, j = [], n
    while j > 0:
        if take[j]:
            chosen.append(ws[j - 1][0])
            j = p[j]
        else:
            j -= 1
    return dp[n], chosen[::-1]


def release_heap(alarms_in, ops=None):
    h = MinHeap(lambda a: (-a[2], a[0]), ops)  # BUG: ignores tick
    return alarms._run(alarms_in, ops, h.push, lambda: h.pop()[0])


def build_adj(V, roads, penalty, blocked=(), ops=None):
    return _real_build_adj(V, roads, penalty, (), ops)  # BUG: blocked ignored


def knapsack_dp(items, cap, ops=None):
    dp, keeps = [0] * (cap + 1), []
    for _, w, v in items:
        keep = [False] * (cap + 1)
        inc(ops, "items")
        inc(ops, "cells", max(cap - w + 1, 0))
        for c in range(w, cap + 1):  # BUG: upward loop reuses the item
            if dp[c - w] + v > dp[c]:
                dp[c], keep[c] = dp[c - w] + v, True
        keeps.append(keep)
    chosen, c = [], cap
    for (i, w, _), keep in zip(reversed(items), reversed(keeps)):
        while keep[c]:
            chosen.append(i)
            c -= w
    return dp[cap], chosen[::-1]


FAULTS = {
    "touching": {"eff_count": eff_count, "weighted_dp": weighted_dp},
    "tie_rule": {"release_heap": release_heap},
    "blocked": {"build_adj": build_adj},
    "unbounded": {"knapsack_dp": knapsack_dp},
}

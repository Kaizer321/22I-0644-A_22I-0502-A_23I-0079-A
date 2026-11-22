from src.heap import inc
from src.sorting import merge_sort


def eff_count(windows, ops=None):
    chosen, last = [], None
    for wid, s, f, _ in merge_sort(windows, lambda w: (w[2], w[0]), ops):
        inc(ops, "items")
        if last is None or s >= last:
            chosen.append(wid)
            last = f
    return chosen


def weighted_dp(windows, ops=None):
    # ASSUMPTION: the sort is preprocessing here, so it is counted as pre_cmp/pre_move
    ws = merge_sort(windows, lambda w: (w[2], w[0]), ops, "pre_")
    n = len(ws)
    p, dp, take = [0] * (n + 1), [0] * (n + 1), [False] * (n + 1)
    for j in range(1, n + 1):
        _, s, _, v = ws[j - 1]
        lo, hi = 0, n  # first index whose finish > s
        while lo < hi:
            inc(ops, "probe")
            mid = (lo + hi) // 2
            if ws[mid][2] <= s:
                lo = mid + 1
            else:
                hi = mid
        p[j] = lo
        inc(ops, "cells")
        dp[j] = dp[j - 1]
        if dp[lo] + v > dp[j]:  # strict: ties do not take
            dp[j], take[j] = dp[lo] + v, True
    chosen, j = [], n
    while j > 0:
        if take[j]:
            chosen.append(ws[j - 1][0])
            j = p[j]
        else:
            j -= 1
    return dp[n], chosen[::-1]


def value_greedy(windows, ops=None):
    kept, total = [], 0  # kept: chosen windows ordered by start
    for w in merge_sort(windows, lambda w: (-w[3], w[0]), ops):
        inc(ops, "items")
        lo, hi = 0, len(kept)  # first kept window starting after w
        while lo < hi:
            inc(ops, "probe")
            mid = (lo + hi) // 2
            if kept[mid][1] <= w[1]:
                lo = mid + 1
            else:
                hi = mid
        if (lo > 0 and kept[lo - 1][2] > w[1]) or (lo < len(kept) and kept[lo][1] < w[2]):
            continue
        inc(ops, "shift", len(kept) - lo)
        kept.insert(lo, w)
        total += w[3]
    return total, [w[0] for w in kept]

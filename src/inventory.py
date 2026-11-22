from fractions import Fraction

from src.heap import inc
from src.sorting import merge_sort


def knapsack_dp(items, cap, ops=None):
    # shortcut: keep-rows cost n*(cap+1) bytes, switch to divide-and-conquer reconstruction if memory binds
    dp, keeps = [0] * (cap + 1), []
    for _, w, v in items:
        inc(ops, "items")
        if w > cap:
            keeps.append(b"")
            continue
        inc(ops, "cells", cap - w + 1)
        cand = [x + v for x in dp[: cap - w + 1]]
        take = [c > o for c, o in zip(cand, dp[w:])]  # strict: ties keep the item out
        dp[w:] = [c if t else o for c, o, t in zip(cand, dp[w:], take)]
        keeps.append(bytes(take))
    chosen, c = [], cap
    for (i, w, _), k in zip(reversed(items), reversed(keeps)):
        if k and c >= w and k[c - w]:
            chosen.append(i)
            c -= w
    return dp[cap], chosen[::-1]


def ratio_greedy(items, cap, ops=None):
    order = merge_sort(items, lambda t: (-Fraction(t[2], t[1]), t[0]), ops)
    total, left, chosen = 0, cap, []
    for i, w, v in order:
        inc(ops, "items")
        if w <= left:
            left -= w
            total += v
            chosen.append(i)
    return total, chosen

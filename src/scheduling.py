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

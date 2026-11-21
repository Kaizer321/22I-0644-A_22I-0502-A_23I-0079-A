from src.heap import inc


def merge_sort(seq, key, ops=None, prefix=""):
    a, buf = list(seq), list(seq)
    c, m = prefix + "cmp", prefix + "move"

    def rec(lo, hi):  # sorts a[lo:hi]; recursion depth is log n
        if hi - lo < 2:
            return
        mid = (lo + hi) // 2
        rec(lo, mid)
        rec(mid, hi)
        i, j, k = lo, mid, lo
        while i < mid and j < hi:
            inc(ops, c)
            if key(a[j]) < key(a[i]):  # strict: equal keys take the left one first (stable)
                buf[k] = a[j]
                j += 1
            else:
                buf[k] = a[i]
                i += 1
            k += 1
        while i < mid:
            buf[k] = a[i]
            i += 1
            k += 1
        while j < hi:
            buf[k] = a[j]
            j += 1
            k += 1
        inc(ops, m, hi - lo)
        a[lo:hi] = buf[lo:hi]

    rec(0, len(a))
    return a

from collections import deque

from .heap import MinHeap, inc


def _run(alarms, ops, push, pop):
    out, i, t, n, size = [], 0, 0, len(alarms), 0
    while i < n or size:
        if not size and t < alarms[i][1]:
            t = alarms[i][1]  # idle jump: nothing waiting, nothing released
        while i < n and alarms[i][1] <= t:
            inc(ops, "items")
            push(alarms[i])
            i, size = i + 1, size + 1
        out.append((t, pop()))
        t, size = t + 1, size - 1
    return out


def release_heap(alarms, ops=None):
    h = MinHeap(lambda a: (-a[2], a[1], a[0]), ops)
    return _run(alarms, ops, h.push, lambda: h.pop()[0])


def release_sorted_list(alarms, ops=None):
    a = []  # ascending by (priority, -tick, -id): most urgent last

    def push(x):
        k, lo, hi = (x[2], -x[1], -x[0]), 0, len(a)
        while lo < hi:
            mid = (lo + hi) // 2
            inc(ops, "probe")
            inc(ops, "cmp")
            if a[mid] < k:
                lo = mid + 1
            else:
                hi = mid
        inc(ops, "shift", len(a) - lo)
        a.insert(lo, k)

    return _run(alarms, ops, push, lambda: -a.pop()[2])


def release_buckets(alarms, ops=None):
    q = [deque() for _ in range(11)]  # index = priority; input order is already (tick, id)

    def push(x):
        inc(ops, "bucket")
        q[x[2]].append(x[0])

    def pop():
        p = 10
        while True:
            inc(ops, "bucket")
            if q[p]:
                break
            p -= 1
        inc(ops, "bucket")
        return q[p].popleft()

    return _run(alarms, ops, push, pop)

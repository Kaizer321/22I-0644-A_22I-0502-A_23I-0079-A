def inc(ops, key, n=1):
    if ops is not None:
        ops[key] = ops.get(key, 0) + n


class MinHeap:
    def __init__(self, key=None, ops=None):
        self.a, self.key, self.ops = [], key or (lambda x: x), ops

    def __len__(self):
        return len(self.a)

    def __bool__(self):
        return bool(self.a)

    def peek(self):
        return self.a[0]

    def push(self, x):
        a, key, ops = self.a, self.key, self.ops
        inc(ops, "pq")
        a.append(x)
        i, kx = len(a) - 1, key(x)
        while i:
            p = (i - 1) // 2
            inc(ops, "cmp")
            if not kx < key(a[p]):
                break
            a[i] = a[p]
            inc(ops, "move")
            i = p
        a[i] = x
        inc(ops, "move")

    def pop(self):
        a, key, ops = self.a, self.key, self.ops
        if not a:
            raise IndexError("pop from empty MinHeap")
        inc(ops, "pq")
        top, x = a[0], a.pop()
        if not a:
            return top
        n, i, kx = len(a), 0, key(x)
        while 2 * i + 1 < n:
            c = 2 * i + 1
            if c + 1 < n:
                inc(ops, "cmp")
                if key(a[c + 1]) < key(a[c]):
                    c += 1
            inc(ops, "cmp")
            if not key(a[c]) < kx:
                break
            a[i] = a[c]
            inc(ops, "move")
            i = c
        a[i] = x
        inc(ops, "move")
        return top

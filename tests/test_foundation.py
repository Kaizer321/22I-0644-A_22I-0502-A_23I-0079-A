import math
import random

import pytest

from src import loader
from src.heap import MinHeap
from src.sorting import merge_sort
from src.validation import (InvalidInput, check_alarms, check_crates,
                            check_network, check_windows)


def test_heap_order_and_key():
    rng = random.Random(1)
    xs = [rng.randrange(50) for _ in range(500)]
    h = MinHeap()
    for x in xs:
        h.push(x)
    assert len(h) == 500 and h.peek() == min(xs)
    assert [h.pop() for _ in xs] == sorted(xs) and not h
    ts = [(rng.randrange(5), rng.randrange(5)) for _ in range(200)]
    h = MinHeap(key=lambda t: (-t[0], t[1]))
    for t in ts:
        h.push(t)
    assert [h.pop() for _ in ts] == sorted(ts, key=lambda t: (-t[0], t[1]))


def test_heap_empty_and_ops():
    with pytest.raises(IndexError):
        MinHeap().pop()
    ops = {}
    h = MinHeap(ops=ops)
    for x in (3, 1, 2):
        h.push(x)
    h.pop()
    assert ops["pq"] == 4 and ops["cmp"] > 0 and ops["move"] > 0


def test_merge_sort_stable():
    rng = random.Random(2)
    xs = [(rng.randrange(10), i) for i in range(1000)]
    assert merge_sort(xs, key=lambda t: t[0]) == sorted(xs, key=lambda t: t[0])
    assert merge_sort([], key=lambda t: t) == []


@pytest.mark.parametrize("xs", [list(range(4096)), list(range(4096, 0, -1))])
def test_merge_sort_monotone(xs):
    ops = {}
    assert merge_sort(xs, key=lambda x: x, ops=ops, prefix="pre_") == sorted(xs)
    assert ops["pre_cmp"] <= 4096 * math.log2(4096) and ops["pre_move"] > 0

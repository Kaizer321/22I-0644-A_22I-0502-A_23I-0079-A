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


def test_loader_sample_and_load():
    assert loader.sample("S")[:3] == ["1-06", "1-13", "2-00"]
    assert [len(loader.sample(t)) for t in "SMLX"] == [204, 208, 62, 41]
    rows = loader.load(["69-00"], ["crates"])["crates"]["69-00"]
    assert rows and all(isinstance(r["weight"], int) and isinstance(r["value"], int) for r in rows)
    assert rows[0]["crate_id"] == 1 and rows[0]["case_id"] == "69-00"


def test_pooling():
    c = [[{"weight": 2, "value": 3}] * 3, [{"weight": 5, "value": 6}] * 4]
    assert loader.pool_crates(c, 5) == [(1, 2, 3), (2, 2, 3), (3, 2, 3), (4, 5, 6), (5, 5, 6)]
    with pytest.raises(ValueError):
        loader.pool_crates(c, 8)
    w = [[{"start": 1, "finish": 2, "value": 9}], [{"start": 1, "finish": 2, "value": 9}]]
    assert loader.pool_windows(w, 2) == [(1, 1, 2, 9), (2, 1441, 1442, 9)]
    with pytest.raises(ValueError):
        loader.pool_windows(w, 3)
    a = [[{"tick": 0, "priority": 1}, {"tick": 4, "priority": 2}], [{"tick": 0, "priority": 3}, {"tick": 2, "priority": 4}]]
    got = loader.pool_alarms(a, 4)
    assert [g[1] for g in got] == [0, 4, 5, 7] and [g[0] for g in got] == [1, 2, 3, 4]
    assert len(loader.pool_alarms(a, 3)) == 3
    with pytest.raises(ValueError):
        loader.pool_alarms(a, 5)


def test_synthetic_network():
    V, roads, pen = loader.synthetic_network(200, "seed-x")
    assert len(roads) == 500 and pen[0] == 0 and set(pen) <= {0, 1, 2, 4, 6}
    assert all(u < v and 1 <= m <= 60 for _, u, v, m in roads)
    adj = {i: [] for i in range(V)}
    for _, u, v, _ in roads:
        adj[u].append(v)
        adj[v].append(u)
    seen, stack = {0}, [0]
    while stack:
        for y in adj[stack.pop()]:
            if y not in seen:
                seen.add(y)
                stack.append(y)
    assert len(seen) == V
    assert loader.synthetic_network(200, "seed-x") == (V, roads, pen)


def test_validation():
    ok = [{"crate_id": 1, "weight": 2, "value": 0}]
    check_crates("c", ok, 0)
    check_crates("c", [], 5)
    for rows, cap, rule in [([{"crate_id": 1, "weight": 0, "value": 0}], 1, "crates.weight"),
                            (ok, -1, "crates.capacity"),
                            (ok + ok, 1, "crates.id")]:
        with pytest.raises(InvalidInput) as e:
            check_crates("c", rows, cap)
        assert e.value.rule == rule and e.value.case_id == "c" and "c" in str(e.value)

    locs = [{"loc_id": i, "penalty": 0} for i in range(3)]
    roads = [{"road_no": 0, "u": 0, "v": 1, "minutes": 5}, {"road_no": 1, "u": 1, "v": 2, "minutes": 5}]
    check_network("c", locs, roads, [{"road_no": 1}], [2])
    for args, rule in [((locs, roads, [{"road_no": 9}], [2]), "network.wave_road"),
                       ((locs, roads, [], [0]), "network.target"),
                       ((locs, [{"road_no": 0, "u": 2, "v": 1, "minutes": 5}], [], [2]), "network.road_ends"),
                       ((locs, [{"road_no": 0, "u": 0, "v": 1, "minutes": 0}], [], [2]), "network.minutes"),
                       (([{"loc_id": 1, "penalty": 0}], [], [], []), "network.loc_id")]:
        with pytest.raises(InvalidInput) as e:
            check_network("c", *args)
        assert e.value.rule == rule

    check_windows("c", [{"window_id": 1, "start": 0, "finish": 1, "value": 0}])
    with pytest.raises(InvalidInput) as e:
        check_windows("c", [{"window_id": 1, "start": 3, "finish": 3, "value": 0}])
    assert e.value.rule == "windows.span"

    check_alarms("c", [{"alarm_id": 1, "tick": 0, "priority": 1}, {"alarm_id": 2, "tick": 0, "priority": 10}])
    with pytest.raises(InvalidInput) as e:
        check_alarms("c", [{"alarm_id": 1, "tick": 2, "priority": 1}, {"alarm_id": 2, "tick": 1, "priority": 1}])
    assert e.value.rule == "alarms.tick"
    with pytest.raises(InvalidInput) as e:
        check_alarms("c", [{"alarm_id": 1, "tick": 0, "priority": 11}])
    assert e.value.rule == "alarms.priority"


def test_checksums():
    sums = loader.verify_checksums()
    assert "cases.csv" in sums and len(sums) == 20

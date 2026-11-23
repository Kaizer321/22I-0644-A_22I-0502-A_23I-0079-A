import random

import pytest

from src import loader
from src.alarms import release_buckets, release_heap, release_sorted_list
from src.validation import InvalidInput, check_alarms

IMPLS = [release_heap, release_sorted_list, release_buckets]


def urgency(a):
    return (-a[2], a[1], a[0])


def reference(alarms):
    todo, wait, out, t = list(alarms), [], [], 0
    while todo or wait:
        if not wait:
            t = max(t, todo[0][1])
        while todo and todo[0][1] <= t:
            wait.append(todo.pop(0))
        best = min(wait, key=urgency)
        wait.remove(best)
        out.append((t, best[0]))
        t += 1
    return out


def check_invariants(alarms, out):
    by_id = {a[0]: a for a in alarms}
    assert sorted(i for _, i in out) == sorted(by_id)
    assert all(t > u for (t, _), (u, _) in zip(out[1:], out))
    released = set()
    for t, i in out:
        assert t >= by_id[i][1]
        best = min((a for a in alarms if a[1] <= t and a[0] not in released), key=urgency)
        assert best[0] == i
        released.add(i)


def rand_instance(rng):
    n, t, rows = rng.randint(0, 200), 0, []
    for i in range(1, n + 1):
        t += rng.choice([0, 0, 0, 1, 2, 10])
        rows.append((i, t, rng.choice([rng.randint(1, 10), rng.randint(4, 6)])))
    return rows


def test_random_instances():
    rng = random.Random(69)
    for _ in range(300):
        rows = rand_instance(rng)
        want = reference(rows)
        check_invariants(rows, want)
        for f in IMPLS:
            assert f(rows) == want


@pytest.mark.parametrize("f", IMPLS)
def test_edges_and_ties(f):
    assert f([]) == []
    assert f([(1, 50, 3)]) == [(50, 1)]
    assert f([(1, 0, 5), (2, 0, 5), (3, 0, 5)]) == [(0, 1), (1, 2), (2, 3)]  # id breaks tie at same tick
    assert f([(1, 0, 5), (2, 1, 5), (3, 2, 5)]) == [(0, 1), (1, 2), (2, 3)]
    assert f([(1, 0, 5), (2, 0, 5), (3, 1, 5)]) == [(0, 1), (1, 2), (2, 3)]  # earlier tick before later id
    assert f([(1, 0, 3), (2, 0, 3), (3, 1, 3), (4, 1, 9)]) == [(0, 1), (1, 4), (2, 2), (3, 3)]


def test_campaign_insertion():
    rows = rand_instance(random.Random(7))
    new = max(a[0] for a in rows) + 1
    rows = sorted(rows + [(new, 0, 10)], key=lambda a: (a[1], a[0]))
    for f in IMPLS:
        assert (0, new) in f(rows)


def test_master_data():
    for tier, k in (("M", 20), ("L", 5)):
        ids = loader.sample(tier)[:k]
        data = loader.load(ids, ["incidents"])["incidents"]
        for c in ids:
            rows = [(r["alarm_id"], r["tick"], r["priority"]) for r in data[c]]
            outs = [f(rows) for f in IMPLS]
            assert outs[0] == outs[1] == outs[2]
            check_invariants(rows, outs[0])


def test_validation_layer():
    row = lambda i, t, p: {"alarm_id": i, "tick": t, "priority": p}
    for rows in ([row(1, 3, 5), row(2, 2, 5)], [row(1, 0, 5), row(2, 1, 11)]):
        with pytest.raises(InvalidInput):
            check_alarms("x", rows)

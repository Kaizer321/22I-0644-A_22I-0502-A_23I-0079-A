import math
import random
from itertools import combinations

import pytest

from src import loader
from src.scheduling import eff_count, value_greedy, weighted_dp
from src.validation import InvalidInput, check_windows


def ok(ws):
    return all(a[2] <= b[1] or b[2] <= a[1] for a, b in combinations(ws, 2))


def brute(ws):
    best_c = best_v = 0
    for r in range(len(ws) + 1):
        for sub in combinations(ws, r):
            if ok(sub):
                best_c = max(best_c, r)
                best_v = max(best_v, sum(w[3] for w in sub))
    return best_c, best_v


def rand_instance(rng):
    ws = []
    for i in range(1, rng.randint(0, 12) + 1):
        s = rng.choice([rng.randint(0, 99), rng.randrange(0, 100, 10)])
        ws.append((i, s, min(100, s + rng.choice([1, 10, 10, 20, rng.randint(1, 40)])), rng.randint(0, 50)))
    return [w for w in ws if w[1] < w[2]]


def test_random_vs_brute_force():
    rng = random.Random(69)
    for _ in range(300):
        ws = rand_instance(rng)
        by = {w[0]: w for w in ws}
        c, v = brute(ws)
        ids = eff_count(ws)
        assert len(ids) == c and ok([by[i] for i in ids])
        dv, dids = weighted_dp(ws)
        assert dv == v and ok([by[i] for i in dids]) and sum(by[i][3] for i in dids) == dv
        gv, gids = value_greedy(ws)
        assert gv <= dv and ok([by[i] for i in gids]) and sum(by[i][3] for i in gids) == gv


def test_touching_and_overlap():
    for f in (eff_count, lambda w: weighted_dp(w)[1], lambda w: value_greedy(w)[1]):
        assert sorted(f([(1, 0, 10, 5), (2, 10, 20, 5)])) == [1, 2]
        assert len(f([(1, 0, 10, 5), (2, 9, 20, 5)])) == 1
    assert (weighted_dp([]), eff_count([]), value_greedy([])) == ((0, []), [], (0, []))


def test_reference_tier_s():
    ids = loader.sample("S")
    assert len(ids) == 204
    d = loader.load(ids, ["windows", "claims"])
    for c in ids:
        ws = [(r["window_id"], r["start"], r["finish"], r["value"]) for r in d["windows"][c]]
        claim = d["claims"][c][0]
        assert len(eff_count(ws)) == claim["window_count_opt"], c
        assert weighted_dp(ws)[0] == claim["window_value_opt"], c


def test_ops_sanity():
    ws = [(i, i, i + 3, 1) for i in range(1, 50)]
    ops = {}
    weighted_dp(ws, ops)
    n = len(ws)
    assert ops["cells"] == n and ops["probe"] <= n * (math.ceil(math.log2(n + 1)) + 1)


def test_validation_rejects_empty_span():
    with pytest.raises(InvalidInput):
        check_windows("x", [{"window_id": 1, "start": 5, "finish": 5, "value": 1}])

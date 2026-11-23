import itertools
import random

import pytest

from src import loader
from src.inventory import knapsack_dp, ratio_greedy
from src.validation import InvalidInput, check_crates


def brute(items, cap):
    best = 0
    for r in range(len(items) + 1):
        for s in itertools.combinations(items, r):
            if sum(w for _, w, _ in s) <= cap:
                best = max(best, sum(v for _, _, v in s))
    return best


def test_random_vs_brute():
    rng = random.Random(69)
    for _ in range(300):
        items = [(i, rng.randint(1, 15), rng.randint(0, 40)) for i in range(1, rng.randint(0, 12) + 1)]
        cap = rng.randint(0, 50)
        val, ids = knapsack_dp(items, cap)
        by = {i: (w, v) for i, w, v in items}
        assert val == brute(items, cap)
        assert sum(by[i][0] for i in ids) <= cap and sum(by[i][1] for i in ids) == val
        assert len(set(ids)) == len(ids) and ids == sorted(ids)
        assert ratio_greedy(items, cap)[0] <= val


def test_edges_and_ties():
    assert knapsack_dp([], 5) == (0, []) and ratio_greedy([], 5) == (0, [])
    assert knapsack_dp([(1, 1, 9)], 0) == (0, []) and ratio_greedy([(1, 1, 9)], 0) == (0, [])
    assert knapsack_dp([(1, 5, 9)], 4) == (0, []) and ratio_greedy([(1, 5, 9)], 4) == (0, [])
    assert ratio_greedy([(7, 2, 4), (3, 1, 2)], 2) == (2, [3])  # equal ratio: lower crate_id first


def test_greedy_suboptimal():
    items = [(1, 1, 3), (2, 3, 8)]  # ratio 3 beats 2.67, then 2 no longer fits
    assert ratio_greedy(items, 3)[0] == 3 and knapsack_dp(items, 3)[0] == 8


def test_ops_cells():
    ops, items = {}, [(1, 3, 5), (2, 7, 1), (3, 12, 2)]
    knapsack_dp(items, 10, ops)
    assert ops == {"items": 3, "cells": 8 + 4 + 0}


def test_reference_tier_s():
    ids = loader.sample("S")
    assert len(ids) == 204
    d = loader.load(ids, ["crates", "cases", "claims"])
    for c in ids:
        items = [(r["crate_id"], r["weight"], r["value"]) for r in d["crates"][c]]
        assert knapsack_dp(items, d["cases"][c][0]["capacity"])[0] == d["claims"][c][0]["cargo_opt"], c


def test_trap_case_47():
    ids = [c["case_id"] for c in loader.read_cases() if c["case_no"] == 47 and c["case_id"] in set(loader.sample("X"))]
    assert ids
    d = loader.load(ids, ["crates", "cases"])
    for c in ids:
        items = [(r["crate_id"], r["weight"], r["value"]) for r in d["crates"][c]]
        cap = d["cases"][c][0]["capacity"]
        assert ratio_greedy(items, cap)[0] * 10 <= knapsack_dp(items, cap)[0] * 6, c


def test_validation_rejects_zero_weight():
    with pytest.raises(InvalidInput) as e:
        check_crates("x", [{"crate_id": 1, "weight": 0, "value": 1}], 5)
    assert "weight" in e.value.rule

from ast import literal_eval

from src import campaign, loader
from src.alarms import release_buckets, release_heap, release_sorted_list

TABLES = campaign.TABLES


def case(cid):
    d = loader.load([cid], TABLES)
    return {t: d[t][cid] for t in TABLES}


def test_end_to_end_1_06():
    text, rows = campaign.run_case("1-06", case("1-06"))
    assert [r["day"] for r in rows] == list(range(1, 8))
    assert sum(r["checks_failed"] for r in rows) == 0 and "FAIL" not in text
    assert rows[6]["load_value_dp"] is None and rows[6]["note"] in ("evacuation, no loading", "no route")
    for output, row in zip(text.split("--- Day ")[1:], rows, strict=True):
        selections = {
            label.strip(): literal_eval(ids)
            for line in output.splitlines() if line.startswith("  selected ")
            for label, ids in [line.split(": ", 1)]
        }
        roads = selections.get("selected road IDs (HQ to destination)")
        crates = selections.get("selected crate IDs (knapsack DP)")
        assert (roads is not None) == row["reachable"]
        if roads is not None:
            assert len(roads) == row["route_roads"]
        assert (crates is not None) == (row["load_value_dp"] is not None)
        assert len(selections["selected rescue-window IDs (earliest finish)"]) == row["windows_count"]
        assert "selected rescue-window IDs (weighted DP)" in selections
    # ASSUMPTION: "released at tick 0" cannot hold in 1-06 (a p10 alarm also arrives at tick 0), so: at tick 0 admitted, released right after the p>=9 alarms of tick 0
    al = [(r["alarm_id"], r["tick"], r["priority"]) for r in case("1-06")["incidents"]]
    new = max(a[0] for a in al) + 1
    rel = release_heap(sorted(al + [(new, 0, 9)], key=lambda a: (a[1], a[0])))
    assert (sum(a[1] == 0 and a[2] >= 9 for a in al), new) in rel


def test_tie_rule_uses_tick_before_id():
    # same priority, earlier tick has the larger id: only a key that includes the tick gets this right
    stream = [(7, 0, 5), (8, 0, 9), (1, 1, 5)]
    for f in (release_heap, release_sorted_list, release_buckets):
        assert f(stream) == [(0, 8), (1, 7), (2, 1)]


def test_skipped_trip():
    ids = (loader.sample("S") + loader.sample("M"))[:60]
    data = loader.load(ids, TABLES)
    for cid in ids:
        _, rows = campaign.run_case(cid, {t: data[t][cid] for t in TABLES})
        if rows and not rows[5]["reachable"]:
            r = rows[5]
            assert r["load_value_dp"] is None and r["route_cost"] is None and r["note"] == "no route"
            return
    raise AssertionError("no skipped Day 6 in 60 cases")  # path taken: found in the sample (1-06 is one)


def test_day_transformations():
    assert campaign.mins(2, 7) == 11 and campaign.mins(1, 7) == 7
    assert campaign.pen(4, 6) == 12 and campaign.pen(4, 1) == 1 and campaign.pen(4, 2) == 4 and campaign.pen(3, 6) == 6
    assert campaign.crate_value(3, 0, 37) == 74 and campaign.crate_value(3, 1, 37) == 37
    assert campaign.crate_value(2, 3, 5) == 10 and campaign.crate_value(5, 2, 5) == 15


def test_invalid_input_reported_not_raised():
    d = case("1-06")
    d["crates"][0]["weight"] = 0
    text, rows = campaign.run_case("1-06", d)
    assert rows == [] and "INVALID INPUT" in text and "crates.weight" in text


def test_waves_numbered_from_one():
    waves = case("3-00")["waves"]
    ids = {n: {w["road_no"] for w in waves if w["wave_no"] == n} for n in (1, 2, 3)}
    assert {w["wave_no"] for w in waves} == {1, 2, 3}
    got = [campaign.blocked_roads(d, waves) for d in range(1, 8)]
    assert got == [set(), ids[1], ids[2], ids[3], ids[1], ids[1] | ids[2] | ids[3], ids[1] | ids[2] | ids[3]]

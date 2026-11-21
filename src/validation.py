class InvalidInput(Exception):
    def __init__(self, case_id, rule, detail):
        super().__init__(f"{case_id}: {rule}: {detail}")
        self.case_id, self.rule, self.detail = case_id, rule, detail


def _req(ok, case_id, rule, detail):
    if not ok:
        raise InvalidInput(case_id, rule, detail)


def _int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _unique(case_id, rule, ids):
    _req(len(set(ids)) == len(ids), case_id, rule, "duplicate id")


def check_crates(case_id, rows, capacity):
    _req(_int(capacity) and capacity >= 0, case_id, "crates.capacity", f"capacity={capacity!r}")
    _unique(case_id, "crates.id", [r["crate_id"] for r in rows])
    for r in rows:
        _req(_int(r["crate_id"]) and r["crate_id"] > 0, case_id, "crates.id", f"crate_id={r['crate_id']!r}")
        _req(_int(r["weight"]) and r["weight"] >= 1, case_id, "crates.weight", f"crate {r['crate_id']}: weight={r['weight']!r}")
        _req(_int(r["value"]) and r["value"] >= 0, case_id, "crates.value", f"crate {r['crate_id']}: value={r['value']!r}")


def check_network(case_id, locations, roads, waves, targets):
    V = len(locations)
    _req([r["loc_id"] for r in locations] == list(range(V)), case_id, "network.loc_id", "loc_id not 0..V-1 consecutive")
    for r in locations:
        _req(_int(r["penalty"]) and r["penalty"] >= 0, case_id, "network.penalty", f"loc {r['loc_id']}: penalty={r['penalty']!r}")
    _unique(case_id, "network.road_no", [r["road_no"] for r in roads])
    for r in roads:
        _req(_int(r["u"]) and _int(r["v"]) and 0 <= r["u"] < r["v"] < V, case_id, "network.road_ends", f"road {r['road_no']}: u={r['u']!r} v={r['v']!r}")
        _req(_int(r["minutes"]) and r["minutes"] >= 1, case_id, "network.minutes", f"road {r['road_no']}: minutes={r['minutes']!r}")
    known = {r["road_no"] for r in roads}
    for w in waves:
        _req(w["road_no"] in known, case_id, "network.wave_road", f"wave road {w['road_no']!r} not in roads")
    for t in targets:
        _req(_int(t) and 0 < t < V, case_id, "network.target", f"target={t!r}")


def check_windows(case_id, rows):
    _unique(case_id, "windows.id", [r["window_id"] for r in rows])
    for r in rows:
        _req(_int(r["start"]) and _int(r["finish"]) and 0 <= r["start"] < r["finish"], case_id, "windows.span", f"window {r['window_id']}: {r['start']!r}..{r['finish']!r}")
        _req(_int(r["value"]) and r["value"] >= 0, case_id, "windows.value", f"window {r['window_id']}: value={r['value']!r}")


def check_alarms(case_id, rows):
    _unique(case_id, "alarms.id", [r["alarm_id"] for r in rows])
    prev = 0
    for r in rows:
        _req(_int(r["tick"]) and r["tick"] >= prev, case_id, "alarms.tick", f"alarm {r['alarm_id']}: tick={r['tick']!r} (prev {prev})")
        prev = r["tick"]
        _req(_int(r["priority"]) and 1 <= r["priority"] <= 10, case_id, "alarms.priority", f"alarm {r['alarm_id']}: priority={r['priority']!r}")

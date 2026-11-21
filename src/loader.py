import csv
import hashlib
import random
from pathlib import Path

RELEASE = "master_release_v1"
MASTER = Path(__file__).resolve().parent.parent / "Master Dataset" / "archive"
TEXT = {"case_id", "tier", "type", "text", "pattern", "report_a", "report_b", "group_no", "orig_case_id"}


def verify_checksums():
    out = {}
    for line in (MASTER / "CHECKSUMS.txt").read_text().splitlines():
        if not line.strip():
            continue
        want, name = line.split(None, 1)
        name = name.strip().lstrip("*")
        h = hashlib.sha256()
        with open(MASTER / name, "rb") as f:
            while chunk := f.read(1 << 20):
                h.update(chunk)
        if h.hexdigest() != want:
            raise RuntimeError(f"checksum mismatch: {name}")
        out[name] = want
    return out


def _rows(table):
    with open(MASTER / f"{table}.csv", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        head = next(r)
        conv = [h not in TEXT for h in head]
        for row in r:
            yield head, conv, row


def _dict(head, conv, row):
    return {h: int(v) if c else v for h, c, v in zip(head, conv, row)}


def read_cases():
    return [_dict(*x) for x in _rows("cases")]


def sample(tier, s=69):
    ids = [c["case_id"] for c in read_cases() if c["tier"] == tier]
    return ids[s % 7::7]


def load(case_ids, tables):
    want = set(case_ids)
    out = {}
    for t in tables:
        d = out[t] = {c: [] for c in case_ids}
        for head, conv, row in _rows(t):
            if row[0] in want:
                d[row[0]].append(_dict(head, conv, row))
    return out


def _take(items, n, what):
    out = []
    for x in items:
        if len(out) == n:
            break
        out.append(x)
    if len(out) < n:
        raise ValueError(f"not enough {what}: {len(out)} < {n}")
    return out


def pool_crates(groups, n):
    rows = _take((r for g in groups for r in g), n, "crates")
    return [(i, r["weight"], r["value"]) for i, r in enumerate(rows, 1)]


def pool_windows(groups, n):
    rows = _take(((r, 1440 * i) for i, g in enumerate(groups) for r in g), n, "windows")
    return [(k, r["start"] + o, r["finish"] + o, r["value"]) for k, (r, o) in enumerate(rows, 1)]


def pool_alarms(groups, n):
    seq, off = [], 0
    for g in groups:
        if g:
            seq += [(r, off) for r in g]
            off += g[-1]["tick"] + 1  # ASSUMPTION: rows of a case are in tick order, so g[-1] is the last tick
    rows = _take(seq, n, "alarms")
    return [(k, r["tick"] + o, r["priority"]) for k, (r, o) in enumerate(rows, 1)]


def synthetic_network(V, seed):
    rng = random.Random(seed)
    pairs = {(rng.randrange(i), i) for i in range(1, V)}
    E = int(2.5 * V)
    assert E <= V * (V - 1) // 2, "V too small for E = floor(2.5V)"
    while len(pairs) < E:
        u, v = rng.sample(range(V), 2)
        pairs.add((min(u, v), max(u, v)))
    roads = [(k, u, v, rng.randint(1, 60)) for k, (u, v) in enumerate(sorted(pairs))]  # sorted: set order is not seed-stable
    penalty = [0] + [rng.choice([0, 1, 2, 4, 6]) for _ in range(V - 1)]
    return V, roads, penalty

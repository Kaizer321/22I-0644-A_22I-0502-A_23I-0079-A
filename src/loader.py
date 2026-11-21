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

import csv
import time

import pytest

from src import analysis, experiments, main


def test_fit_recovers_slope_two():
    x = [100 * 2**i for i in range(6)]
    f = analysis.fit(x, [3 * v**2 for v in x])
    assert f["slope"] == pytest.approx(2, abs=0.01) and f["r2"] == pytest.approx(1)


def test_write_rows_keeps_other_experiments(tmp_path):
    p = tmp_path / "r.csv"
    row = lambda e, s: {"experiment": e, "algorithm": "f", "size": s, "status": "OK"}
    experiments.write_rows(p, {"A1"}, [row("A1", 1), row("B1", 2)])
    experiments.write_rows(p, {"A1"}, [row("A1", 9)])
    got = [(r["experiment"], r["size"]) for r in csv.DictReader(open(p))]
    assert sorted(got) == [("A1", "9"), ("B1", "2")]
    assert next(csv.reader(open(p))) == experiments.COLS


def _trivial(x, ops=None):
    return x


def _slow(ops=None):
    time.sleep(5)


def test_run_child_five_times():
    st, info = experiments.run_child(_trivial, (7,))
    assert st == "OK" and len(info["times"]) == 5 and info["res"] == 7


def test_run_child_dnf(monkeypatch):
    monkeypatch.setattr(experiments, "TIMEOUT", 1)
    assert experiments.run_child(_slow, ())[0] == "DNF"


@pytest.mark.parametrize(("status", "exit_code"), [("OK", 0), ("DNF", 0), ("FAIL", 1)])
def test_experiment_cli_writes_status_and_returns_exit_code(tmp_path, monkeypatch, status, exit_code):
    monkeypatch.setattr(experiments, "ROOT", tmp_path)
    monkeypatch.setattr(experiments, "run_experiment", lambda name, smoke: [
        {"experiment": name, "algorithm": "test_algorithm", "status": status}
    ])

    assert main.main(["experiments", "A1"]) == exit_code
    with (tmp_path / "results.csv").open(newline="") as results:
        assert next(csv.DictReader(results))["status"] == status

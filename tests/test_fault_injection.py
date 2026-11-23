import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RUNS = {  # fault -> (what is broken, test files that must catch it)
    "touching": ("eff_count / weighted_dp reject touching windows (< instead of <=)", ["tests/test_scheduling.py"]),
    "tie_rule": ("release_heap key (-priority, alarm_id) ignores tick", ["tests/test_alarms.py", "tests/test_campaign.py::test_tie_rule_uses_tick_before_id"]),
    "blocked": ("build_adj ignores the blocked roads", ["tests/test_routes.py"]),
    "unbounded": ("knapsack_dp reuses items (capacity loop upward)", ["tests/test_inventory.py"]),
}
pytestmark = pytest.mark.skipif("LIFELINE_FAULT" in os.environ, reason="no recursion")


def test_every_fault_is_caught():
    out = ["Fault injection: each faulty copy is patched in (tests/conftest.py) and must make the suite fail.\n"]
    for name, (desc, files) in RUNS.items():
        p = subprocess.run([sys.executable, "-m", "pytest", *files, "-q", "-p", "no:cacheprovider", "-rf"], cwd=ROOT,
                           env={**os.environ, "LIFELINE_FAULT": name}, capture_output=True, text=True)
        failed = sorted(set(re.findall(r"^FAILED (\S+)", p.stdout, re.M)))
        out.append(f"[{name}] {desc}\n  test files: {' '.join(files)}\n  return code: {p.returncode}\n  failing tests ({len(failed)}):\n    " + "\n    ".join(failed) + "\n")
        assert p.returncode != 0 and failed, f"fault {name} was NOT caught"
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "fault_injection.txt").write_text("\n".join(out), encoding="utf-8")

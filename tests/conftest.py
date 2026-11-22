import os
import sys

from src import alarms, inventory, routes, scheduling  # noqa: F401  (must be imported for the sweep to find them)
from tests.faults import FAULTS

# Runs at collection start, before test modules do `from src.x import f`; the sweep also fixes modules already imported.
for name, fake in FAULTS.get(os.environ.get("LIFELINE_FAULT"), {}).items():
    originals = {m: getattr(m, name) for m in list(sys.modules.values()) if m and m.__name__.startswith("src.") and hasattr(m, name)}
    for m, orig in originals.items():
        setattr(m, name, fake)
        for other in list(sys.modules.values()):
            if other and other.__name__.startswith(("src.", "tests.")) and getattr(other, name, None) is orig:
                setattr(other, name, fake)

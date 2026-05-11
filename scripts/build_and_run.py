"""
Przebudowuje i odpala cały projekt:
  1. Testy jednostkowe
  2. Wizualizacje (oryginalne + relabeled + syntetyczne)
  3. Eksperymenty (wszystkie algorytmy, DLG1–DLG4)
"""

import subprocess
import sys
import time
from pathlib import Path

PYTHON = sys.executable
ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
OK  = "[OK]"
ERR = "[BLAD]"

steps = [
    ("Testy jednostkowe",
     [PYTHON, "-m", "pytest", "tests/", "-v", "--tb=short"]),

    ("Wizualizacje oryginalne (UUID, 18 grafow)",
     [PYTHON, str(SCRIPTS / "visualize_graphs.py")]),

    ("Wizualizacje z etykietami",
     [PYTHON, str(ROOT / "docs" / "relabeled_graphs" / "generate_relabeled_viz.py")]),

    ("Syntetyczne scenariusze broken lineage",
     [PYTHON, str(ROOT / "docs" / "synthetic_schema" / "generate_schema_viz.py")]),

    ("Eksperymenty — wszystkie algorytmy na DLG1–DLG4",
     [PYTHON, str(SCRIPTS / "run_experiments.py")]),
]

results = []
t_total = time.time()

for name, cmd in steps:
    print(f"\n{'='*60}")
    print(f">>> {name}")
    print('='*60)
    t0 = time.time()
    ret = subprocess.run(cmd, cwd=str(ROOT))
    elapsed = time.time() - t0
    status = OK if ret.returncode == 0 else ERR
    results.append((name, status, elapsed))
    print(f"\n{status}  ({elapsed:.1f}s)")

print(f"\n{'='*60}")
print("PODSUMOWANIE")
print('='*60)
for name, status, elapsed in results:
    print(f"  {status}  {elapsed:5.1f}s  {name}")
print(f"\nLaczny czas: {time.time() - t_total:.1f}s")

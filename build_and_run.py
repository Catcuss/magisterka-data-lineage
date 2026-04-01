"""
Przebudowuje i odpala cały projekt:
  1. Testy jednostkowe
  2. Wizualizacje (oryginalne + relabeled + syntetyczne)
  3. Eksperymenty (wszystkie algorytmy, DLG1–DLG4)
"""

import subprocess
import sys
import time

PYTHON = sys.executable
OK  = "[OK]"
ERR = "[BLAD]"

steps = [
    ("Testy jednostkowe",
     [PYTHON, "-m", "pytest", "tests/", "-v", "--tb=short"]),

    ("Wizualizacje oryginalne (UUID, 18 grafow)",
     [PYTHON, "visualize_graphs.py"]),

    ("Wizualizacje z etykietami",
     [PYTHON, "docs/relabeled_graphs/generate_relabeled_viz.py"]),

    ("Syntetyczne scenariusze broken lineage",
     [PYTHON, "docs/synthetic_schema/generate_schema_viz.py"]),

    ("Eksperymenty — wszystkie algorytmy na DLG1–DLG4",
     [PYTHON, "run_experiments.py"]),
]

results = []
t_total = time.time()

for name, cmd in steps:
    print(f"\n{'='*60}")
    print(f">>> {name}")
    print('='*60)
    t0 = time.time()
    ret = subprocess.run(cmd, cwd="C:/Users/Maria/Desktop/MAGISTERKA")
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

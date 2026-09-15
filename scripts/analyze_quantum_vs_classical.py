"""
Deep analysis: does the quantum walk beat classical methods
at the actual scientific task (HOMO site classification)?
"""
import json
import numpy as np
from pathlib import Path

RESULTS = Path("D:/Molecule-App/quantum_vs_classical_results.json")
LITERATURE_HOMO = {
    "caffeine":        "heteroatom",
    "theobromine":     "heteroatom",
    "theophylline":    "heteroatom",
    "aspirin":         "conjugated_c",
    "acetaminophen":   "conjugated_c",
    "benzene":         "conjugated_c",
    "naphthalene":     "conjugated_c",
    "adrenaline":      "conjugated_c",
    "dopamine":        "conjugated_c",
    "serotonin":       "conjugated_c",
    "glucose":         "heteroatom",
    "sucrose":         "heteroatom",
    "chloroquine":     "conjugated_c",
    "morphine":        "conjugated_c",
    "nicotine":        "heteroatom",
    "methane":         "conjugated_c",
    "ethene":          "conjugated_c",
}

with open(RESULTS) as f:
    results = json.load(f)

def element_type(el):
    if el == "C": return "conjugated_c"
    if el in ("O", "N", "S", "Cl"): return "heteroatom"
    return "other"

def classify(top_el):
    return element_type(top_el)

print("=" * 130)
print("HOMO SITE CLASSIFICATION ACCURACY — QUANTUM vs CLASSICAL vs EIGENVECTOR")
print("=" * 130)
print(f"{'Molecule':<18} {'Literature':<15} {'Q-Top1':>8} {'Cl-Top1':>8} {'Eig-Top1':>8} "
      f"{'Q✓':>4} {'Cl✓':>4} {'Eig✓':>4}  Notes")
print("-" * 130)

q_hits = cl_hits = eig_hits = 0
total = 0

for r in results:
    if r.get("error"):
        continue
    name = r["name"].lower()
    lit = LITERATURE_HOMO.get(name, "?")
    if lit == "?":
        continue
    total += 1

    q_top = r["quantum_top3_elements"][0]
    cl_top = r["classical_top3_elements"][0]
    eig_top = r["eigenvector_top3_elements"][0]

    q_type = element_type(q_top)
    cl_type = element_type(cl_top)
    eig_type = element_type(eig_top)

    q_ok = 1 if q_type == lit else 0
    cl_ok = 1 if cl_type == lit else 0
    eig_ok = 1 if eig_type == lit else 0

    q_hits += q_ok
    cl_hits += cl_ok
    eig_hits += eig_ok

    # Notes
    note = ""
    if q_ok and not cl_ok:
        note = "Q wins"
    elif cl_ok and not q_ok:
        note = "Cl wins"
    elif q_ok and cl_ok:
        note = "both"
    else:
        note = "both wrong"

    print(f"{r['name']:<18} {lit:<15} {q_top:>5}({q_type[:3]}) {cl_top:>5}({cl_type[:3]}) {eig_top:>5}({eig_type[:3]}) "
          f"{'✓' if q_ok else '✗':>4} {'✓' if cl_ok else '✗':>4} {'✓' if eig_ok else '✗':>4}  {note}")

print("-" * 130)
print(f"\nACCURACY AT DOMINANT ELEMENT TYPE CLASSIFICATION:")
print(f"  Quantum walk:        {q_hits}/{total} = {100*q_hits/total:.1f}%")
print(f"  Classical RW:        {cl_hits}/{total} = {100*cl_hits/total:.1f}%")
print(f"  Eigenvector centr.:  {eig_hits}/{total} = {100*eig_hits/total:.1f}%")

# Now: does quantum beat classical INDIVIDUALLY?
print(f"\n\nHEAD-TO-HEAD (per molecule):")
print(f"{'Molecule':<18} {'Q':>4} {'Cl':>4} {'Winner'}")
print("-" * 50)
wins = {1: 0, 0: 0, 2: 0}  # quantum, classical, tie
for r in results:
    if r.get("error"):
        continue
    name = r["name"].lower()
    lit = LITERATURE_HOMO.get(name, "?")
    if lit == "?":
        continue
    q_top = element_type(r["quantum_top3_elements"][0])
    cl_top = element_type(r["classical_top3_elements"][0])
    q_ok = 1 if q_top == lit else 0
    cl_ok = 1 if cl_top == lit else 0
    if q_ok > cl_ok:
        winner = "Q"
        wins[1] += 1
    elif cl_ok > q_ok:
        winner = "Cl"
        wins[0] += 1
    else:
        winner = "tie"
        wins[2] += 1
    print(f"{r['name']:<18} {'✓' if q_ok else '✗':>4} {'✓' if cl_ok else '✗':>4}  {winner}")
print("-" * 50)
print(f"Quantum wins: {wins[1]}, Classical wins: {wins[0]}, Ties: {wins[2]}")

print(f"\n\nWHY QUANTUM AND CLASSICAL DIVERGE — ROOT CAUSE ANALYSIS:")
print("=" * 130)
print("\nClassical RW top sites — what's happening at node 0?")
for r in results:
    if r.get("error"):
        continue
    name = r["name"].lower()
    cl_top = r["methods"]["classical_rw"]["top1"]
    q_top = r["methods"]["quantum_walk"]["top1"]
    atoms_cl = r["classical_top3_elements"]
    atoms_q = r["quantum_top3_elements"]
    print(f"  {r['name']:<18}  node0→Cl-top={cl_top}({atoms_cl[0]})  Q-top={q_top}({atoms_q[0]})")

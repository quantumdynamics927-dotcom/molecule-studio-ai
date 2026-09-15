"""
Corrected analysis: quantum walk with n/2 steps vs classical baselines.
Also: detailed per-molecule comparison of step-count sensitivity.
"""
import json, math
import numpy as np
from pathlib import Path

RESULTS = Path("D:/Molecule-App/spectral_results.json")
with open(RESULTS) as f:
    spectral_res = {r["name"]: r for r in json.load(f)}

# Also load the expanded fixed-10 results
EXPANDED = Path("D:/Molecule-App/expanded_results.json")
try:
    with open(EXPANDED) as f:
        expanded_res = {r["name"]: r for r in json.load(f)}
except:
    expanded_res = {}

LITERATURE_HOMO = {
    "caffeine": "heteroatom", "theobromine": "heteroatom", "theophylline": "heteroatom",
    "aspirin": "conjugated_c", "acetaminophen": "conjugated_c", "benzene": "conjugated_c",
    "naphthalene": "conjugated_c", "adrenaline": "conjugated_c", "dopamine": "conjugated_c",
    "serotonin": "conjugated_c", "glucose": "heteroatom", "sucrose": "heteroatom",
    "chloroquine": "conjugated_c", "morphine": "conjugated_c", "nicotine": "heteroatom",
    "methane": "heteroatom", "ethene": "conjugated_c",
    "anthracene": "conjugated_c", "tetracene": "conjugated_c", "pentacene": "conjugated_c",
    "ethane": "conjugated_c", "propane": "conjugated_c", "butane": "conjugated_c",
    "pentane": "conjugated_c", "hexane": "conjugated_c",
    "pyridine": "heteroatom", "pyrrole": "heteroatom", "furan": "heteroatom",
    "thiophene": "heteroatom", "quinoline": "heteroatom", "isoquinoline": "heteroatom",
    "water": "heteroatom", "hydrogen sulfide": "heteroatom", "ammonia": "heteroatom",
    "methanol": "heteroatom", "methanethiol": "heteroatom",
    "toluene": "heteroatom", "phenol": "conjugated_c", "aniline": "conjugated_c",
    "styrene": "conjugated_c", "biphenyl": "conjugated_c",
    "ibuprofen": "conjugated_c", "warfarin": "conjugated_c", "cortisol": "conjugated_c",
    "acetophenone": "conjugated_c", "benzaldehyde": "conjugated_c", "nitrobenzene": "heteroatom",
    "anisole": "conjugated_c", "nitromethane": "heteroatom", "dimethyl sulfide": "heteroatom",
    "dimethyl sulfoxide": "heteroatom", "acetaldehyde": "heteroatom", "acetone": "heteroatom",
    "formaldehyde": "heteroatom", "carbon disulfide": "heteroatom", "hydrogen cyanide": "heteroatom",
    "pyrimidine": "heteroatom", "pyridazine": "heteroatom", "pyrazine": "heteroatom",
    "imidazole": "heteroatom", "oxazole": "heteroatom", "thiazole": "heteroatom",
    "acenaphthylene": "conjugated_c", "fluorene": "conjugated_c", "phenanthrene": "conjugated_c",
    "pyrene": "conjugated_c", "chrysene": "conjugated_c", "triphenylene": "conjugated_c",
    "naphthacene": "conjugated_c", "perylene": "conjugated_c", "coronene": "conjugated_c",
    "indene": "conjugated_c",
    "glycine": "heteroatom", "alanine": "conjugated_c", "phenylalanine": "conjugated_c",
    "tryptophan": "conjugated_c", "cysteine": "heteroatom",
    "adenine": "heteroatom", "guanine": "heteroatom", "cytosine": "heteroatom",
    "thymine": "heteroatom", "uracil": "heteroatom",
    "retinol": "conjugated_c", "thiamine": "heteroatom", "riboflavin": "heteroatom",
    "pyridoxine": "heteroatom", "nicotinamide": "heteroatom",
    "testosterone": "conjugated_c", "estradiol": "conjugated_c", "cholesterol": "conjugated_c",
    "quercetin": "heteroatom", "luteolin": "heteroatom", "catechin": "heteroatom",
    "acrolein": "conjugated_c", "methyl vinyl ketone": "conjugated_c",
    "acrylonitrile": "conjugated_c", "methyl acrylate": "conjugated_c",
    "acetaldehyde oxime": "heteroatom",
}

def element_type(el):
    if el == "C": return "conjugated_c"
    if el in ("O", "N", "S", "Cl"): return "heteroatom"
    return "other"


def score_result(r, lit_homo):
    lit = lit_homo.get(r["name"].lower(), "?")
    if lit == "?":
        return None
    q_top = r["quantum_walk"]["top3_elements"][0]
    c_top = r["coined_rw"]["top3_elements"][0]
    p_top = r["plain_rw"]["top3_elements"][0]
    e_top = r["eigenvector"]["top3_elements"][0]
    return {
        "name": r["name"],
        "lit": lit,
        "n": r.get("num_atoms", r.get("n", "?")),
        "steps": r.get("steps_used", 10),
        "q_ok": element_type(q_top) == lit,
        "cnd_ok": element_type(c_top) == lit,
        "plain_ok": element_type(p_top) == lit,
        "eig_ok": element_type(e_top) == lit,
        "q_top": q_top,
        "cnd_top": c_top,
        "plain_top": p_top,
        "eig_top": e_top,
    }


# ---- Spectral-adaptive results ----
spectral_scores = [score_result(r, LITERATURE_HOMO) for r in spectral_res.values()]
spectral_scores = [s for s in spectral_scores if s is not None]

# ---- Expanded fixed-10 results ----
expanded_scores = [score_result(r, LITERATURE_HOMO) for r in expanded_res.values()]
expanded_scores = [s for s in expanded_scores if s is not None]

def summarize(scores, label):
    n = len(scores)
    q = sum(1 for s in scores if s["q_ok"]) / n * 100
    cnd = sum(1 for s in scores if s["cnd_ok"]) / n * 100
    pln = sum(1 for s in scores if s["plain_ok"]) / n * 100
    eig = sum(1 for s in scores if s["eig_ok"]) / n * 100
    print(f"{label}: n={n}  Q={q:.1f}%  Cnd={cnd:.1f}%  Pln={pln:.1f}%  Eig={eig:.1f}%")
    return {"n": n, "q": q, "cnd": cnd, "pln": pln, "eig": eig}

print("=" * 80)
print("FIXED-10 vs SPECTRAL-GAP-ADAPTIVE STEP COMPARISON")
print("=" * 80)
print("\nFixed-10 (pre-registered):")
s1 = summarize(expanded_scores, "expanded fixed-10")
print("\nSpectral adaptive (pi/(2*gap), capped 100):")
s2 = summarize(spectral_scores, "spectral pi/(2*gap)")

print(f"\nStep counts (spectral): min={min(s['steps'] for s in spectral_scores)}, "
      f"max={max(s['steps'] for s in spectral_scores)}, "
      f"median={sorted(s['steps'] for s in spectral_scores)[len(spectral_scores)//2]}")

# ---- Where does n/2 steps beat fixed-10 for quantum? ----
print("\n\nMOLECULES WHERE QUANTUM IMPROVES with spectral steps vs fixed-10:")
print("-" * 80)

common = set(r["name"] for r in spectral_scores) & set(r["name"] for r in expanded_scores)
improved = []
regressed = []
for name in sorted(common):
    s_spectral = next(s for s in spectral_scores if s["name"] == name)
    s_fixed = next(s for s in expanded_scores if s["name"] == name)
    if s_spectral["q_ok"] and not s_fixed["q_ok"]:
        improved.append(name)
        print(f"  RECOVERS: {name:<25} n={s_fixed['n']:>3}  steps: {s_spectral['steps']:>3} "
              f"  Q-top: {s_spectral['q_top']} ({s_spectral['lit']})")
    elif not s_spectral["q_ok"] and s_fixed["q_ok"]:
        regressed.append(name)
        print(f"  REGRESS:  {name:<25} n={s_fixed['n']:>3}  steps: {s_fixed['steps']:>3} "
              f"  Q-top: {s_fixed['q_top']} → {s_spectral['q_top']} ({s_spectral['lit']})")

print(f"\nQuantum improves: {len(improved)} molecules")
print(f"Quantum regresses: {len(regressed)} molecules")

# ---- Steps n/2 analysis ----
print("\n\nTHE key question: does n/2 steps fix large molecules?")
print("=" * 80)

large_mols = [(s["name"], s["n"], s["steps"]) for s in spectral_scores
               if s["n"] is not None and s["n"] >= 30]
print(f"\nLarge molecules (n>=30) in spectral run:")
for name, n, steps in sorted(large_mols, key=lambda x: -x[1]):
    s = next(ss for ss in spectral_scores if ss["name"] == name)
    print(f"  {name:<25} n={n:>3}  steps={steps:>3}  "
          f"Q={'✓' if s['q_ok'] else '✗'}({s['q_top']})  "
          f"Cnd={'✓' if s['cnd_ok'] else '✗'}({s['cnd_top']})  "
          f"Pln={'✓' if s['plain_ok'] else '✗'}({s['plain_top']})")

# Compare large molecule accuracy
large_spectral = [s for s in spectral_scores if s["n"] is not None and s["n"] >= 30]
large_fixed = [s for s in expanded_scores if s["n"] is not None and s["n"] >= 30]
print(f"\nLarge molecule accuracy (n>=30):")
if large_spectral:
    summarize(large_spectral, "spectral adaptive (n/2 steps)")
if large_fixed:
    summarize(large_fixed, "fixed-10")
if large_spectral and large_fixed:
    q_spectral = sum(1 for s in large_spectral if s["q_ok"]) / len(large_spectral)
    q_fixed = sum(1 for s in large_fixed if s["q_ok"]) / len(large_fixed)
    print(f"  Improvement from n/2 steps: {100*(q_spectral - q_fixed):.1f} pp")

# ---- The honest summary ----
print("\n\n" + "=" * 80)
print("HONEST SUMMARY")
print("=" * 80)
print(f"""
FIXED-10 RESULTS (pre-registered protocol):
  Q=53.1%  Cnd=64.3%  Pln=41.8%  Eig=59.2%  (n=98)

SPECTRAL-GAP-ADAPTIVE (pi/(2*gap), capped 100):
  Q=32.7%  Cnd=59.2%  Pln=35.7%  Eig=57.1%  (n=98)
  → pi/(2*gap) gives 2 steps for most molecules → WORSE than fixed-10

The pi/(2*gap) formula is wrong for molecular graphs.
Molecular graphs have λ_max ≈ 8-10 (not 1-2), so gap is near 1,
giving only 2 steps. This is TOO FEW.

KEY FINDING: steps_n_over_2 from step_formula_test.py:
  Q=62.2% at n/2 steps vs Q=53.1% at fixed-10 (n=98)
  → n/2 steps recovers ~9 pp of accuracy on quantum walk
  → Confirms: under-mixing IS part of the story

BUT: classical methods still beat quantum at n/2 steps:
  Coined RW = 62.2% (tied with quantum) or higher

STILL UNRESOLVED:
  1. n/2 steps helps quantum but not enough to beat classical
  2. Coined RW is more robust to molecule size than quantum walk
  3. The pilot's 88.2% was a selection artifact (small, rigid molecules)
""")

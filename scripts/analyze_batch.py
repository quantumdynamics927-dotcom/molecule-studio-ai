"""
Analyze batch results: check which molecules are fully mixed at step 10,
and what the ranking tells us at different mix states.
"""

import json, re
from pathlib import Path

RESULTS_FILE = Path(__file__).parent.parent / "batch_results.json"

with open(RESULTS_FILE) as f:
    results = json.load(f)

def count_c(formula):
    matches = re.findall(r"C(\d*)", formula)
    return sum(int(m) if m else 1 for m in matches)

def role(el):
    if el == "H": return "H (terminal)"
    if el in ("O", "N", "S", "Cl"): return f"{el} hetero"
    if el == "C": return "C (conjugated)"
    return f"{el} other"

print("=" * 120)
print("BATCH ANALYSIS: STABILITY, MIXING STATE, AND DOMINANT SITE TYPE")
print("=" * 120)

total = 0
localized = 0  # PR < 0.5 (not fully mixed)
partial = 0    # 0.5 <= PR < 0.9
full = 0       # PR >= 0.9 (fully mixed)

# Site type stats
c_dominant = 0   # conjugated carbon in top 3
hetero_dominant = 0  # heteroatom in top 3
h_dominant = 0     # hydrogen in top 3

print(f"\n{'Molecule':<18} {'Formula':<12} {'Stab':>6} {'PR':>6} {'Mix State':<18} {'#1 Site':>12} {'p1':>7} {'Top3 Element Types'}")
print("-" * 120)

for r in results:
    if r.get("error"):
        continue
    total += 1

    pr = r["participation_ratio"]
    stab = r["stability_score"]
    t1_el = r["top_site_1"][0]

    if pr < 0.5:
        mix = "LOCALIZED"
        localized += 1
    elif pr < 0.9:
        mix = "PARTIAL MIX"
        partial += 1
    else:
        mix = "FULL MIX"
        full += 1

    t1_el = r["top_site_1"][0]
    t2_el = r["top_site_2"][0]
    t3_el = r["top_site_3"][0]

    # Top3 element types
    top3_types = [r["top_site_1"][0], r["top_site_2"][0], r["top_site_3"][0]]
    c_in_top3 = top3_types.count("C")
    h_in_top3 = top3_types.count("H")
    hetero_in_top3 = sum(1 for e in top3_types if e in ("O", "N", "S", "Cl"))

    if c_in_top3 >= 2:
        dominant = "C-dominant"
    elif hetero_in_top3 >= 2:
        dominant = "hetero-dominant"
    elif c_in_top3 == 1:
        dominant = "C-mixed"
    else:
        dominant = "other"

    t1_str = f"{r['top_site_1'][0]}{r['top_site_1'][1]}"
    print(f"{r['name']:<18} {r['formula']:<12} {stab:>6.4f} {pr:>6.4f} {mix:<18} {t1_str:>12} {r['top_site_1'][2]:>7.4f}  C={c_in_top3} H={h_in_top3} hetero={hetero_in_top3}  [{dominant}]")

print("-" * 120)
print(f"\nMIX STATE DISTRIBUTION (step 10):")
print(f"  Fully mixed (PR>=0.9):  {full}/{total} = {100*full/total:.0f}%")
print(f"  Partial mix:             {partial}/{total} = {100*partial/total:.0f}%")
print(f"  Still localized:          {localized}/{total} = {100*localized/total:.0f}%")

# Now look at only localized/partial molecules
print(f"\n\nDETAILED: LOCALIZED/PARTIAL MOLECULES (where ranking MEANS something):")
print("=" * 120)
print(f"{'Molecule':<18} {'Stab':>6} {'PR':>6} {'Mix':<10} {'#1':>8} {'p1':>7} {'#2':>8} {'p2':>7} {'#3':>8} {'p3':>7} {'Interpretation'}")
print("-" * 120)

for r in results:
    if r.get("error"):
        continue
    pr = r["participation_ratio"]
    if pr >= 0.9:
        continue  # skip fully mixed

    t1_el, t1_i, t1_p = r["top_site_1"]
    t2_el, t2_i, t2_p = r["top_site_2"]
    t3_el, t3_i, t3_p = r["top_site_3"]

    t1_str = f"{t1_el}{t1_i}"
    t2_str = f"{t2_el}{t2_i}"
    t3_str = f"{t3_el}{t3_i}"

    # Interpretation
    formula = r["formula"]
    c_count = count_c(formula)

    if t1_el in ("O", "N"):
        interp = "HOMO on heteroatom (lone pair)"
    elif t1_el == "C":
        interp = "HOMO on conjugated C"
    else:
        interp = ""

    print(f"{r['name']:<18} {r['stability_score']:>6.4f} {pr:>6.4f} {'LOCALIZED' if pr < 0.5 else 'PARTIAL':<10} {t1_str:>8} {t1_p:>7.4f} {t2_str:>8} {t2_p:>7.4f} {t3_str:>8} {t3_p:>7.4f}  {interp}")

"""
Diagnostic analysis: where is the quantum walk failing,
and is the drop from 88% to 53% a selection artifact or a real effect?
"""
import json
import numpy as np
from pathlib import Path

RESULTS = Path("D:/Molecule-App/expanded_results.json")

# Load if exists, else recreate
try:
    with open(RESULTS) as f:
        results = json.load(f)
except FileNotFoundError:
    print("Run expanded_batch.py first")
    raise SystemExit()

LITERATURE_HOMO = {
    # --- Pilot (17) ---
    "caffeine": "heteroatom", "theobromine": "heteroatom", "theophylline": "heteroatom",
    "aspirin": "conjugated_c", "acetaminophen": "conjugated_c", "benzene": "conjugated_c",
    "naphthalene": "conjugated_c", "adrenaline": "conjugated_c", "dopamine": "conjugated_c",
    "serotonin": "conjugated_c", "glucose": "heteroatom", "sucrose": "heteroatom",
    "chloroquine": "conjugated_c", "morphine": "conjugated_c", "nicotine": "heteroatom",
    "methane": "conjugated_c", "ethene": "conjugated_c",
    # --- PAH series (5) ---
    "anthracene": "conjugated_c", "tetracene": "conjugated_c", "pentacene": "conjugated_c",
    # --- Alkanes (6) ---
    "ethane": "conjugated_c", "propane": "conjugated_c", "butane": "conjugated_c",
    "pentane": "conjugated_c", "hexane": "conjugated_c",
    # --- Heterocycles (6) ---
    "pyridine": "heteroatom", "pyrrole": "heteroatom", "furan": "heteroatom",
    "thiophene": "heteroatom", "quinoline": "heteroatom", "isoquinoline": "heteroatom",
    # --- Small heteroatom-dominant (5) ---
    "water": "heteroatom", "hydrogen sulfide": "heteroatom", "ammonia": "heteroatom",
    "methanol": "heteroatom", "methanethiol": "heteroatom",
    # --- Additional aromatics (5) ---
    "toluene": "conjugated_c", "phenol": "conjugated_c", "aniline": "conjugated_c",
    "styrene": "conjugated_c", "biphenyl": "conjugated_c",
    # --- More drugs / bioactive ---
    "ibuprofen": "conjugated_c", "warfarin": "conjugated_c", "cortisol": "conjugated_c",
    "acetophenone": "conjugated_c", "benzaldehyde": "conjugated_c", "nitrobenzene": "heteroatom",
    "anisole": "conjugated_c", "nitromethane": "heteroatom", "dimethyl sulfide": "heteroatom",
    "dimethyl sulfoxide": "heteroatom", "acetaldehyde": "heteroatom", "acetone": "heteroatom",
    "formaldehyde": "heteroatom", "carbon disulfide": "heteroatom", "hydrogen cyanide": "heteroatom",
    # --- More heterocycles (6) ---
    "pyrimidine": "heteroatom", "pyridazine": "heteroatom", "pyrazine": "heteroatom",
    "imidazole": "heteroatom", "oxazole": "heteroatom", "thiazole": "heteroatom",
    # --- Extended aromatics (10) ---
    "acenaphthylene": "conjugated_c", "fluorene": "conjugated_c", "phenanthrene": "conjugated_c",
    "pyrene": "conjugated_c", "chrysene": "conjugated_c", "triphenylene": "conjugated_c",
    "naphthacene": "conjugated_c", "perylene": "conjugated_c", "coronene": "conjugated_c",
    "indene": "conjugated_c",
    # --- Amino acids (5) ---
    "glycine": "heteroatom", "alanine": "conjugated_c", "phenylalanine": "conjugated_c",
    "tryptophan": "conjugated_c", "cysteine": "heteroatom",
    # --- Nucleobases (5) ---
    "adenine": "heteroatom", "guanine": "heteroatom", "cytosine": "heteroatom",
    "thymine": "heteroatom", "uracil": "heteroatom",
    # --- Vitamins / cofactors (5) ---
    "retinol": "conjugated_c", "thiamine": "heteroatom", "riboflavin": "heteroatom",
    "pyridoxine": "heteroatom", "nicotinamide": "heteroatom",
    # --- Steroids (3) ---
    "testosterone": "conjugated_c", "estradiol": "conjugated_c", "cholesterol": "conjugated_c",
    # --- Flavonoids (3) ---
    "quercetin": "heteroatom", "luteolin": "heteroatom", "catechin": "heteroatom",
    # --- Simple oxohydrocarbons (5) ---
    "acrolein": "conjugated_c", "methyl vinyl ketone": "conjugated_c",
    "acrylonitrile": "conjugated_c", "methyl acrylate": "conjugated_c",
    "acetaldehyde oxime": "heteroatom",
}

def element_type(el):
    if el == "C": return "conjugated_c"
    if el in ("O", "N", "S", "Cl"): return "heteroatom"
    return "other"

def q_correct(r):
    lit = LITERATURE_HOMO.get(r["name"].lower(), "?")
    if lit == "?": return None
    q_top = r["quantum_walk"]["top3_elements"][0]
    return element_type(q_top) == lit

def pln_correct(r):
    lit = LITERATURE_HOMO.get(r["name"].lower(), "?")
    if lit == "?": return None
    top = r["plain_rw"]["top3_elements"][0]
    return element_type(top) == lit

def cnd_correct(r):
    lit = LITERATURE_HOMO.get(r["name"].lower(), "?")
    if lit == "?": return None
    top = r["coined_rw"]["top3_elements"][0]
    return element_type(top) == lit

# Segment analysis
print("=" * 100)
print("SEGMENT ANALYSIS: Where does quantum walk succeed / fail?")
print("=" * 100)

segments = {
    "Pilot (17)": [],
    "PAH series": [],
    "Alkanes": [],
    "Simple heterocycles (5-member)": [],
    "Quinoline/isoquinoline": [],
    "Small heteroatom H2O/NH3/etc": [],
    "Additional aromatics (toluene/phenol)": [],
    "Extended PAHs (pyrene/chrysene)": [],
    "Nucleobases": [],
    "Amino acids": [],
    "Steroids": [],
    "Flavonoids": [],
    "Vitamins/cofactors": [],
    "Carbonyls/ketones": [],
    "Nitriles/cyanides": [],
    "Sulfides/thiols": [],
}

for r in results:
    n = r["name"].lower()
    if n in ["caffeine","theobromine","theophylline","aspirin","acetaminophen","benzene",
             "naphthalene","adrenaline","dopamine","serotonin","glucose","sucrose",
             "chloroquine","morphine","nicotine","methane","ethene"]:
        seg = "Pilot (17)"
    elif n in ["anthracene","tetracene","pentacene"]:
        seg = "PAH series"
    elif n in ["ethane","propane","butane","pentane","hexane"]:
        seg = "Alkanes"
    elif n in ["pyridine","pyrrole","furan","thiophene"]:
        seg = "Simple heterocycles (5-member)"
    elif n in ["quinoline","isoquinoline"]:
        seg = "Quinoline/isoquinoline"
    elif n in ["water","hydrogen sulfide","ammonia","methanol","methanethiol"]:
        seg = "Small heteroatom H2O/NH3/etc"
    elif n in ["toluene","phenol","aniline","styrene","biphenyl"]:
        seg = "Additional aromatics (toluene/phenol)"
    elif n in ["pyrene","chrysene","triphenylene","naphthacene","perylene","coronene",
               "acenaphthylene","fluorene","phenanthrene","indene"]:
        seg = "Extended PAHs (pyrene/chrysene)"
    elif n in ["adenine","guanine","cytosine","thymine","uracil"]:
        seg = "Nucleobases"
    elif n in ["glycine","alanine","phenylalanine","tryptophan","cysteine"]:
        seg = "Amino acids"
    elif n in ["testosterone","estradiol","cholesterol"]:
        seg = "Steroids"
    elif n in ["quercetin","luteolin","catechin"]:
        seg = "Flavonoids"
    elif n in ["retinol","thiamine","riboflavin","pyridoxine","nicotinamide"]:
        seg = "Vitamins/cofactors"
    elif n in ["acetone","acetaldehyde","formaldehyde","acetophenone","benzaldehyde",
               "acrolein","methyl vinyl ketone","methyl acrylate"]:
        seg = "Carbonyls/ketones"
    elif n in ["acrylonitrile","hydrogen cyanide","nitrobenzene","nitromethane"]:
        seg = "Nitriles/cyanides"
    elif n in ["dimethyl sulfide","dimethyl sulfoxide","methanethiol","carbon disulfide",
               "acetaldehyde oxime"]:
        seg = "Sulfides/thiols"
    else:
        seg = None
    if seg:
        segments[seg].append(r)

print(f"\n{'Segment':<35} {'n':>4}  {'Q%':>6} {'Cnd%':>6} {'Pln%':>6}  Q>C  Q<C  tie")
print("-" * 100)

all_q = all_cnd = all_pln = 0
all_n = 0

for seg, rs in sorted(segments.items(), key=lambda x: -len(x[1])):
    if not rs:
        continue
    n = len(rs)
    q_ok = sum(1 for r in rs if q_correct(r) == True)
    c_ok = sum(1 for r in rs if cnd_correct(r) == True)
    p_ok = sum(1 for r in rs if pln_correct(r) == True)
    all_q += q_ok; all_cnd += c_ok; all_pln += p_ok; all_n += n

    q_pct = q_ok/n*100
    c_pct = c_ok/n*100
    p_pct = p_ok/n*100

    # Count head-to-head wins
    q_wins = sum(1 for r in rs if q_correct(r) == True and cnd_correct(r) == False and pln_correct(r) == False)
    c_wins = sum(1 for r in rs if cnd_correct(r) == True and q_correct(r) == False and pln_correct(r) == False)
    ties   = sum(1 for r in rs if q_correct(r) == cnd_correct(r) and (cnd_correct(r) == pln_correct(r)))

    print(f"{seg:<35} {n:>4}  {q_pct:>5.0f}% {c_pct:>5.0f}% {p_pct:>5.0f}%  {q_wins:>4} {c_wins:>4} {ties:>4}")

print("-" * 100)
print(f"{'TOTAL':<35} {all_n:>4}  {all_q/all_n*100:>5.0f}% {all_cnd/all_n*100:>5.0f}% {all_pln/all_n*100:>5.0f}%")

# Key question: which molecules does QUANTUM get wrong but COINED gets right?
print("\n\nMOLECULES WHERE COINED RW IS CORRECT BUT QUANTUM IS WRONG:")
print("=" * 80)
for r in results:
    if (q_correct(r) == False and cnd_correct(r) == True):
        lit = LITERATURE_HOMO.get(r["name"].lower(), "?")
        q_top = r["quantum_walk"]["top3_elements"][0]
        c_top = r["coined_rw"]["top3_elements"][0]
        p_top = r["plain_rw"]["top3_elements"][0]
        print(f"  {r['name']:<25} lit={lit:<15} Q={q_top:>4}  Cnd={c_top:>4}  Pln={p_top:>4}")

print("\n\nMOLECULES WHERE QUANTUM IS CORRECT BUT COINED RW IS WRONG:")
print("=" * 80)
for r in results:
    if (q_correct(r) == True and cnd_correct(r) == False):
        lit = LITERATURE_HOMO.get(r["name"].lower(), "?")
        q_top = r["quantum_walk"]["top3_elements"][0]
        c_top = r["coined_rw"]["top3_elements"][0]
        p_top = r["plain_rw"]["top3_elements"][0]
        print(f"  {r['name']:<25} lit={lit:<15} Q={q_top:>4}  Cnd={c_top:>4}  Pln={p_top:>4}")

# Where BOTH get H as top site
print("\n\nMOLECULES WHERE ALL METHODS GET H (neither Q nor classical works):")
print("=" * 80)
for r in results:
    lit = LITERATURE_HOMO.get(r["name"].lower(), "?")
    if lit == "?": continue
    q_top = r["quantum_walk"]["top3_elements"][0]
    c_top = r["coined_rw"]["top3_elements"][0]
    p_top = r["plain_rw"]["top3_elements"][0]
    if q_top == "H" and c_top == "H" and p_top == "H":
        print(f"  {r['name']:<25} lit={lit:<15} all-H  Q={r['quantum_walk']['top1']:>3}  Cnd={r['coined_rw']['top1']:>3}  Pln={r['plain_rw']['top1']:>3}")

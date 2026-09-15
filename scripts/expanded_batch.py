"""
Expanded batch: quantum vs classical walk on 120+ molecules.
============================================================
Same protocol as the pre-registered PROTOCOL.md.
"""

from __future__ import annotations
import json, sys, time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fetch_molecule import fetch_molecule
from molecular_fractal_bridge import (
    build_molecular_adjacency, MoleculeInput, run_fractal_analysis,
)
from coined_vs_quantum import plain_random_walk, coined_classical_walk, eigenvector_centrality

LITERATURE_HOMO = {
    # --- Pilot (17) ---
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
    # --- PAH series (5) ---
    "anthracene":      "conjugated_c",
    "tetracene":       "conjugated_c",
    "pentacene":       "conjugated_c",
    # --- Alkanes (6) ---
    "ethane":          "conjugated_c",
    "propane":        "conjugated_c",
    "butane":         "conjugated_c",
    "pentane":        "conjugated_c",
    "hexane":         "conjugated_c",
    # --- Heterocycles (6) ---
    "pyridine":       "heteroatom",
    "pyrrole":        "heteroatom",
    "furan":          "heteroatom",
    "thiophene":      "heteroatom",
    "quinoline":      "heteroatom",
    "isoquinoline":   "heteroatom",
    # --- Small heteroatom-dominant (5) ---
    "water":          "heteroatom",
    "hydrogen sulfide": "heteroatom",
    "ammonia":        "heteroatom",
    "methanol":       "heteroatom",
    "methanethiol":   "heteroatom",
    # --- Additional aromatics (5) ---
    "toluene":        "conjugated_c",
    "phenol":         "conjugated_c",
    "aniline":        "conjugated_c",
    "styrene":        "conjugated_c",
    "biphenyl":       "conjugated_c",
    # --- More drugs / bioactive (15) ---
    "ibuprofen":      "conjugated_c",
    "warfarin":       "conjugated_c",
    "cortisol":       "conjugated_c",
    "acetophenone":   "conjugated_c",
    "benzaldehyde":   "conjugated_c",
    "nitrobenzene":   "heteroatom",
    "anisole":        "conjugated_c",
    "nitromethane":   "heteroatom",
    "dimethyl sulfide": "heteroatom",
    "dimethyl sulfoxide": "heteroatom",
    "acetaldehyde":   "heteroatom",
    "acetone":        "heteroatom",
    "formaldehyde":   "heteroatom",
    "carbon disulfide": "heteroatom",
    "hydrogen cyanide": "heteroatom",
    # --- More heterocycles (6) ---
    "pyrimidine":     "heteroatom",
    "pyridazine":     "heteroatom",
    "pyrazine":       "heteroatom",
    "imidazole":      "heteroatom",
    "oxazole":        "heteroatom",
    "thiazole":       "heteroatom",
    # --- Extended aromatics (10) ---
    "acenaphthylene": "conjugated_c",
    "fluorene":       "conjugated_c",
    "phenanthrene":   "conjugated_c",
    "pyrene":         "conjugated_c",
    "chrysene":       "conjugated_c",
    "triphenylene":   "conjugated_c",
    "naphthacene":    "conjugated_c",
    "perylene":       "conjugated_c",
    "coronene":       "conjugated_c",
    "indene":         "conjugated_c",
    # --- Amino acids (5) ---
    "glycine":        "heteroatom",
    "alanine":        "conjugated_c",
    "phenylalanine":  "conjugated_c",
    "tryptophan":     "conjugated_c",
    "cysteine":       "heteroatom",
    # --- Nucleobases (5) ---
    "adenine":        "heteroatom",
    "guanine":        "heteroatom",
    "cytosine":       "heteroatom",
    "thymine":        "heteroatom",
    "uracil":         "heteroatom",
    # --- Vitamins / cofactors (5) ---
    "retinol":        "conjugated_c",
    "thiamine":       "heteroatom",
    "riboflavin":     "heteroatom",
    "pyridoxine":     "heteroatom",
    "nicotinamide":   "heteroatom",
    # --- Steroids (3) ---
    "testosterone":   "conjugated_c",
    "estradiol":      "conjugated_c",
    "cholesterol":    "conjugated_c",
    # --- Flavonoids (3) ---
    "quercetin":     "heteroatom",
    "luteolin":      "heteroatom",
    "catechin":      "heteroatom",
    # --- Simple oxohydrocarbons (5) ---
    "acrolein":      "conjugated_c",
    "methyl vinyl ketone": "conjugated_c",
    "acrylonitrile":  "conjugated_c",
    "methyl acrylate": "conjugated_c",
    "acetaldehyde oxime": "heteroatom",
}


def element_type(el):
    if el == "C": return "conjugated_c"
    if el in ("O", "N", "S", "Cl"): return "heteroatom"
    return "other"


def compare_one(name, atoms, bonds, steps=10, initial_node=0):
    """Run all methods on one molecule."""
    adj = build_molecular_adjacency(atoms, bonds)

    # Quantum walk
    mol = MoleculeInput(name=name, formula="?", atoms=atoms, bonds=bonds)
    q_result = run_fractal_analysis(
        molecule_data=mol, fractal="sierpinski", level=3,
        route="ifs", walk_steps=steps, initial_node=initial_node,
    )
    q_rank = [loc.atom_index for loc in q_result.localization]

    # Classical walks
    _, plain_rank = plain_random_walk(adj, steps=steps, initial_node=initial_node)
    _, coined_rank = coined_classical_walk(adj, steps=steps, initial_node=initial_node)

    # Eigenvector centrality
    eig_vec = eigenvector_centrality(adj)
    eig_rank = list(np.argsort(eig_vec)[::-1])

    def top_el(rank_list):
        return [atoms[i]["element"] for i in rank_list[:3]]

    return {
        "name": name,
        "num_atoms": len(atoms),
        "steps": steps,
        "initial_node": initial_node,
        "lit_expected": LITERATURE_HOMO.get(name.lower(), "?"),
        "quantum_walk": {"top1": q_rank[0], "top3": q_rank[:3],
                         "top3_elements": top_el(q_rank)},
        "plain_rw":      {"top1": plain_rank[0], "top3": plain_rank[:3],
                          "top3_elements": top_el(plain_rank)},
        "coined_rw":     {"top1": coined_rank[0], "top3": coined_rank[:3],
                          "top3_elements": top_el(coined_rank)},
        "eigenvector":   {"top1": eig_rank[0], "top3": eig_rank[:3],
                          "top3_elements": top_el(eig_rank)},
        "stability_score": getattr(q_result, "stability_score", None),
        "participation_ratio": getattr(q_result, "participation_ratio", None),
        "topological_entropy": getattr(q_result, "topological_entropy", None),
    }


def run_batch(names, steps=10, initial_node=0):
    results = []
    for i, name in enumerate(names):
        print(f"[{i+1}/{len(names)}] {name}...", end=" ", flush=True)
        r = fetch_molecule(name)
        if not r:
            print("FETCH FAILED")
            continue
        try:
            result = compare_one(name, r["atoms"], r["bonds"],
                               steps=steps, initial_node=initial_node)
            results.append(result)
            print(f"OK  ({result['num_atoms']} atoms)")
        except Exception as e:
            print(f"ERROR: {e}")
    return results


def score_results(results):
    """Score all methods against literature."""
    q_hits = plain_hits = coined_hits = eig_hits = 0
    valid = 0
    for r in results:
        lit = r["lit_expected"]
        if lit == "?" or r.get("error"):
            continue
        valid += 1

        q_type  = element_type(r["quantum_walk"]["top3_elements"][0])
        pln_type = element_type(r["plain_rw"]["top3_elements"][0])
        cnd_type = element_type(r["coined_rw"]["top3_elements"][0])
        eig_type = element_type(r["eigenvector"]["top3_elements"][0])

        if q_type == lit:  q_hits  += 1
        if pln_type == lit: plain_hits += 1
        if cnd_type == lit: coined_hits += 1
        if eig_type == lit: eig_hits += 1

    return {
        "n_valid": valid,
        "q_accuracy":  q_hits/valid if valid else 0,
        "plain_accuracy": plain_hits/valid if valid else 0,
        "coined_accuracy": coined_hits/valid if valid else 0,
        "eig_accuracy":  eig_hits/valid if valid else 0,
    }


def print_summary(results):
    scores = score_results(results)

    print("\n" + "=" * 120)
    print(f"EXPANDED BATCH RESULTS — {scores['n_valid']} VALIDATED MOLECULES")
    print("=" * 120)
    print(f"{'Molecule':<22} {'Lit':<10} "
          f"{'Q-Type':>10} {'Pln-Type':>10} {'Cnd-Type':>10} {'Eig-Type':>10}  "
          f"{'Q':>3} {'Pln':>4} {'Cnd':>4} {'Eig':>4}")
    print("-" * 120)

    for r in results:
        lit = r.get("lit_expected", "?")
        if lit == "?":
            continue
        q_el  = r["quantum_walk"]["top3_elements"][0]
        pln_el = r["plain_rw"]["top3_elements"][0]
        cnd_el = r["coined_rw"]["top3_elements"][0]
        eig_el = r["eigenvector"]["top3_elements"][0]

        q_ok   = element_type(q_el)  == lit
        pln_ok = element_type(pln_el) == lit
        cnd_ok = element_type(cnd_el) == lit
        eig_ok = element_type(eig_el) == lit

        print(f"{r['name']:<22} {lit:<10} "
              f"{q_el:>10} {pln_el:>10} {cnd_el:>10} {eig_el:>10}  "
              f"{'✓' if q_ok else '✗':>3} "
              f"{'✓' if pln_ok else '✗':>4} "
              f"{'✓' if cnd_ok else '✗':>4} "
              f"{'✓' if eig_ok else '✗':>4}")

    print("-" * 120)
    print(f"\nACCURACY SUMMARY:")
    print(f"  Quantum walk:        {scores['q_accuracy']:.1%}")
    print(f"  Coined RW:           {scores['coined_accuracy']:.1%}")
    print(f"  Plain RW:            {scores['plain_accuracy']:.1%}")
    print(f"  Eigenvector:         {scores['eig_accuracy']:.1%}")
    print(f"\n  Accuracy gap (Q − Coined RW): {scores['q_accuracy']-scores['coined_accuracy']:.1%}")
    print(f"  Accuracy gap (Q − Plain RW):   {scores['q_accuracy']-scores['plain_accuracy']:.1%}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", "-s", type=int, default=10)
    parser.add_argument("--node", "-n", type=int, default=0)
    parser.add_argument("--output", "-o", type=str, default="D:/Molecule-App/expanded_results.json")
    args = parser.parse_args()

    # All molecules in the planned set
    ALL_NAMES = list(LITERATURE_HOMO.keys())
    print(f"Fetching {len(ALL_NAMES)} molecules...")
    results = run_batch(ALL_NAMES, steps=args.steps, initial_node=args.node)
    print(f"\nCollected {len(results)} results")

    print_summary(results)

    # Fix numpy int64 serialization
    def make_serializable(obj):
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(v) for v in obj]
        elif hasattr(obj, 'item'):  # numpy types
            return obj.item()
        else:
            return obj

    with open(args.output, "w") as f:
        json.dump(make_serializable(results), f, indent=2)
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()

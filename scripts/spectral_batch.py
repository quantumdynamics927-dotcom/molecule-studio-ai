"""
Spectral gap analysis for step count derivation.
=============================================
For a continuous-time quantum walk on a graph, the mixing/spreading time
is governed by the spectral gap of the (normalized) Laplacian:

  L_norm = I - D^{-1/2} A D^{-1/2}
  spectral_gap = 1 - λ_2(L_norm)   [algebraic connectivity]

For the staggered quantum walk, the relevant scale is the inverse of the
spectral gap:  steps ≈ π / (2 * spectral_gap)  (first crossing time)

We use: steps = ceil(π / (2 * gap)) as the理论基础-derived step count.

We also test: steps = ceil(1 / gap) and steps = ceil(π / gap).
"""
from __future__ import annotations
import json, sys, math
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fetch_molecule import fetch_molecule
from molecular_fractal_bridge import build_molecular_adjacency, MoleculeInput, run_fractal_analysis
from coined_vs_quantum import plain_random_walk, coined_classical_walk, eigenvector_centrality

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
    "toluene": "conjugated_c", "phenol": "conjugated_c", "aniline": "conjugated_c",
    "styrene": "conjugated_c", "biphenyl": "conjugated_c",
    "ibuprofen": "conjugated_c", "warfarin": "conjugated_c", "cortisol": "conjugated_c",
    "acetophenone": "conjugated_c", "benzaldehyde": "heteroatom", "nitrobenzene": "heteroatom",
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


def spectral_gap(adj: np.ndarray) -> float:
    """
    Compute the normalized Laplacian spectral gap for a weighted graph.

    L_norm = I - D^{-1/2} A D^{-1/2}
    spectral_gap = 1 - λ_2(L_norm)
                   = smallest non-zero eigenvalue of L_norm

    For a fully connected graph (all eigenvalues = 1): gap = 0
    For a disconnected graph: gap = 0 (there are zero eigenvalues)

    Returns: spectral gap in (0, 1], or np.nan if indeterminate.
    """
    n = adj.shape[0]
    if n <= 1:
        return np.nan

    # Build normalized Laplacian
    degree = adj.sum(axis=1)
    # Avoid division by zero
    degree_safe = np.where(degree > 0, degree, 1.0)
    D_inv_sqrt = np.diag(1.0 / np.sqrt(degree_safe))
    L = np.eye(n) - D_inv_sqrt @ adj @ D_inv_sqrt

    # Eigenvalues of normalized Laplacian: 0 = λ_0 ≤ λ_1 ≤ ... ≤ λ_{n-1} ≤ 2
    eigenvalues = np.linalg.eigvalsh(L)
    eigenvalues = np.sort(eigenvalues)

    # λ_0 should be 0 (or very close); λ_1 is the algebraic connectivity
    # spectral_gap = λ_1 (for connected) or 1 - λ_1 for normalized
    # More precisely: gap = 1 - λ_1 (since λ_0 = 0, λ_1 is second smallest)
    # But for our purposes, use λ_1 directly as the connectivity measure
    algebraic_connectivity = eigenvalues[1]  # λ_1 ≥ 0

    # Normalized spectral gap: 1 - λ_1 (for normalized Laplacian, λ_1 ∈ [0,1])
    # For disconnected graphs, λ_1 = 0 exactly
    if algebraic_connectivity < 1e-10:
        return np.nan  # disconnected or poorly connected

    spectral_gap = 1 - algebraic_connectivity
    return spectral_gap


def steps_from_gap(spectral_gap: float, formula: str = "pi_over_2") -> int:
    """
    Derive step count from spectral gap.

    Formulas tested:
    - 'pi_over_2': steps = ceil(π / (2 * gap))   [first crossing time]
    - 'pi':         steps = ceil(π / gap)          [full period]
    - 'inverse':    steps = ceil(1 / gap)           [simple inverse]
    - 'log_n_over_gap': steps = ceil(math.log(1 + 1/gap))  [log-scaled]
    """
    if np.isnan(spectral_gap) or spectral_gap <= 0:
        return 10  # fallback

    if formula == "pi_over_2":
        steps = math.pi / (2 * spectral_gap)
    elif formula == "pi":
        steps = math.pi / spectral_gap
    elif formula == "inverse":
        steps = 1.0 / spectral_gap
    elif formula == "log_n_over_gap":
        steps = math.log(1.0 + 1.0 / spectral_gap)
    else:
        steps = math.pi / (2 * spectral_gap)

    return max(2, int(math.ceil(steps)))


def compare_one(name, atoms, bonds, steps, initial_node=0):
    """Run all methods on one molecule with given step count."""
    adj = build_molecular_adjacency(atoms, bonds)
    n = len(atoms)

    # Spectral gap
    gap = spectral_gap(adj)
    derived_steps = steps_from_gap(gap, "pi_over_2")

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
        "num_atoms": n,
        "steps_used": steps,
        "spectral_gap": gap,
        "theoretical_steps": derived_steps,
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
    }


def run_batch(names, steps_formula="pi_over_2", cap_steps=100):
    """Run batch with spectral-gap-derived step counts."""
    results = []
    for i, name in enumerate(names):
        print(f"[{i+1}/{len(names)}] {name}...", end=" ", flush=True)
        mol = fetch_molecule(name)
        if not mol:
            print("FETCH FAILED")
            continue
        atoms, bonds = mol["atoms"], mol["bonds"]
        adj = build_molecular_adjacency(atoms, bonds)
        gap = spectral_gap(adj)
        steps = steps_from_gap(gap, steps_formula)
        steps = min(steps, cap_steps)

        try:
            result = compare_one(name, atoms, bonds, steps)
            results.append(result)
            print(f"OK  n={len(atoms):2d}  gap={gap:.4f}  steps={steps:3d}  (derived from gap)")
        except Exception as e:
            print(f"ERROR: {e}")
    return results


def score_results(results, lit_homo):
    q_hits = plain_hits = coined_hits = eig_hits = 0
    valid = 0
    for r in results:
        lit = r.get("lit_expected", "?")
        if lit == "?":
            continue
        valid += 1
        q_type = element_type(r["quantum_walk"]["top3_elements"][0])
        pln_type = element_type(r["plain_rw"]["top3_elements"][0])
        cnd_type = element_type(r["coined_rw"]["top3_elements"][0])
        eig_type = element_type(r["eigenvector"]["top3_elements"][0])
        if q_type == lit: q_hits += 1
        if pln_type == lit: plain_hits += 1
        if cnd_type == lit: coined_hits += 1
        if eig_type == lit: eig_hits += 1
    return {
        "n": valid,
        "q": q_hits/valid if valid else 0,
        "plain": plain_hits/valid if valid else 0,
        "coined": coined_hits/valid if valid else 0,
        "eig": eig_hits/valid if valid else 0,
    }


def print_comparison(results, label):
    scores = score_results(results, LITERATURE_HOMO)
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")
    print(f"Molecules: {scores['n']}")
    print(f"Quantum walk:       {scores['q']:.1%}")
    print(f"Coined RW:         {scores['coined']:.1%}")
    print(f"Plain RW:          {scores['plain']:.1%}")
    print(f"Eigenvector:       {scores['eig']:.1%}")
    return scores


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--formula", "-f", choices=["pi_over_2", "pi", "inverse", "log_n_over_gap"],
                        default="pi_over_2")
    parser.add_argument("--cap", "-c", type=int, default=100)
    parser.add_argument("--output", "-o", type=str, default="D:/Molecule-App/spectral_results.json")
    args = parser.parse_args()

    names = list(LITERATURE_HOMO.keys())
    print(f"Running spectral-gap-adaptive batch (formula={args.formula}, cap={args.cap})...")
    print(f"Molecules: {len(names)}")

    results = run_batch(names, steps_formula=args.formula, cap_steps=args.cap)
    print(f"\nCollected {len(results)} results")

    scores = print_comparison(results, f"SPECTRAL-GAP-ADAPTIVE STEPS (formula={args.formula})")

    # Save
    def make_serializable(obj):
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(v) for v in obj]
        elif hasattr(obj, 'item'):
            return obj.item()
        else:
            return obj

    with open(args.output, "w") as f:
        json.dump(make_serializable(results), f, indent=2)
    print(f"Saved to {args.output}")

    # Print step distribution
    steps_list = [r["steps_used"] for r in results if "steps_used" in r]
    print(f"\nStep distribution: min={min(steps_list)}, max={max(steps_list)}, "
          f"median={sorted(steps_list)[len(steps_list)//2]}")


if __name__ == "__main__":
    main()

"""
Corrected spectral step formula for molecular graphs.
===================================================
The π/(2*gap) formula was wrong because molecular graphs are well-connected
(normalized gap ≈ 1) giving tiny step counts.

The correct formula for quantum walk spreading/completion time uses:
  t_walk ~ π / (2 * sqrt(λ_max))

where λ_max is the largest non-zero eigenvalue of the (non-normalized) graph Laplacian.

For a d-regular graph: λ_max ≈ 2d
For molecular graphs: approximate via average degree <d>

But since we're computing the actual Laplacian, we can use the eigenvalues directly.

Alternative: use a mixing-time inspired formula
  steps = ceil(2 * n / (1 - λ_2/λ_max))

Or just: steps = ceil(n / 2) as a proven heuristic for graph search.
Let's test several formulas and compare to fixed-10.
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


def laplacian_eigenvalues(adj):
    """Compute eigenvalues of the non-normalized graph Laplacian."""
    n = adj.shape[0]
    degree = adj.sum(axis=1)
    D = np.diag(degree)
    L = D - adj
    return np.linalg.eigvalsh(L)


def compute_step_formulas(adj, n):
    """
    Compute step count from several formulas and return all of them.
    """
    eigenvalues = laplacian_eigenvalues(adj)
    eigenvalues = np.sort(eigenvalues)

    # λ_0 = 0 (always), λ_1 = algebraic connectivity, λ_max = largest eigenvalue
    lambda_1 = eigenvalues[1]  # algebraic connectivity (smallest non-zero)
    lambda_max = eigenvalues[-1]  # largest eigenvalue

    # Average degree
    avg_degree = adj.sum(axis=1).mean()

    results = {
        "n": n,
        "avg_degree": avg_degree,
        "lambda_1": lambda_1,
        "lambda_max": lambda_max,
    }

    # Formula 1: π / (2 * sqrt(λ_max)) — spreading time for regular graphs
    if lambda_max > 0:
        t_spread = math.pi / (2 * math.sqrt(lambda_max))
        results["steps_pi_sqrt"] = max(2, int(math.ceil(t_spread)))

    # Formula 2: π / (2 * sqrt(λ_1)) — mixing time (slower mode)
    if lambda_1 > 1e-10:
        t_mix = math.pi / (2 * math.sqrt(lambda_1))
        results["steps_pi_sqrt_l1"] = max(2, int(math.ceil(t_mix)))

    # Formula 3: n / 2 — graph diameter heuristic (O(n) bound for path)
    results["steps_n_over_2"] = max(2, int(math.ceil(n / 2)))

    # Formula 4: n / 4 — tighter heuristic
    results["steps_n_over_4"] = max(2, int(math.ceil(n / 4)))

    # Formula 5: π * n / λ_max — period-based
    if lambda_max > 0:
        t_period = math.pi * n / lambda_max
        results["steps_pi_n_over_lambda"] = max(2, int(math.ceil(t_period)))

    # Formula 6: max(10, n // 2) — fallback heuristic that worked for pilot
    results["steps_max10_n_over2"] = max(10, n // 2)

    return results


def run_all_step_formulas(names):
    """
    For each molecule, compute steps from all formulas and run quantum walk
    at each step count, then compare accuracies.
    """
    # Step formulas to test
    FORMULAS = [
        "steps_pi_sqrt",
        "steps_pi_sqrt_l1",
        "steps_n_over_2",
        "steps_n_over_4",
        "steps_pi_n_over_lambda",
        "steps_max10_n_over2",
        "steps_fixed_10",
    ]

    # Collect results: formula -> {q_hits, plain_hits, coined_hits, eig_hits, n}
    formula_scores = {f: {"q": 0, "plain": 0, "coined": 0, "eig": 0, "n": 0} for f in FORMULAS}
    # Also store per-molecule results
    molecule_results = []

    for i, name in enumerate(names):
        print(f"[{i+1}/{len(names)}] {name}...", end=" ", flush=True)
        mol = fetch_molecule(name)
        if not mol:
            print("FETCH FAILED")
            continue
        atoms, bonds = mol["atoms"], mol["bonds"]
        adj = build_molecular_adjacency(atoms, bonds)
        n = len(atoms)

        formulas = compute_step_formulas(adj, n)

        # Reference results at fixed 10 steps for comparison
        mol = MoleculeInput(name=name, formula="?", atoms=atoms, bonds=bonds)
        q10_result = run_fractal_analysis(
            molecule_data=mol, fractal="sierpinski", level=3,
            route="ifs", walk_steps=10, initial_node=0,
        )
        q10_rank = [loc.atom_index for loc in q10_result.localization]
        _, plain10_rank = plain_random_walk(adj, steps=10, initial_node=0)
        _, coined10_rank = coined_classical_walk(adj, steps=10, initial_node=0)
        eig_vec = eigenvector_centrality(adj)
        eig10_rank = list(np.argsort(eig_vec)[::-1])

        def top_el(rank_list):
            return [atoms[i]["element"] for i in rank_list[:3]]

        lit = LITERATURE_HOMO.get(name.lower(), "?")
        mol_result = {"name": name, "lit": lit, "n": n}

        for f in FORMULAS:
            steps = formulas.get(f, 10) if f != "steps_fixed_10" else 10

            # Run quantum walk at this step count
            mol2 = MoleculeInput(name=name, formula="?", atoms=atoms, bonds=bonds)
            qr = run_fractal_analysis(
                molecule_data=mol2, fractal="sierpinski", level=3,
                route="ifs", walk_steps=steps, initial_node=0,
            )
            q_rank = [loc.atom_index for loc in qr.localization]

            # Classical at same steps
            _, plain_rank = plain_random_walk(adj, steps=steps, initial_node=0)
            _, coined_rank = coined_classical_walk(adj, steps=steps, initial_node=0)

            # Score
            if lit != "?":
                formula_scores[f]["n"] += 1
                q_type = element_type(top_el(q_rank)[0])
                pln_type = element_type(top_el(plain_rank)[0])
                cnd_type = element_type(top_el(coined_rank)[0])

                if q_type == lit: formula_scores[f]["q"] += 1
                if pln_type == lit: formula_scores[f]["plain"] += 1
                if cnd_type == lit: formula_scores[f]["coined"] += 1

        print(f"n={n}  λ_max={formulas['lambda_max']:.2f}  "
              f"n/2={formulas['steps_n_over_2']}  n/4={formulas['steps_n_over_4']}  "
              f"π/√λ_max={formulas.get('steps_pi_sqrt','?')}")

    return formula_scores, molecule_results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", type=str, default="D:/Molecule-App/step_formula_results.json")
    args = parser.parse_args()

    names = list(LITERATURE_HOMO.keys())
    print(f"Testing step formulas on {len(names)} molecules...\n")

    formula_scores, molecule_results = run_all_step_formulas(names)

    # Print summary
    print("\n" + "=" * 90)
    print("STEP FORMULA COMPARISON — QUANTUM WALK ACCURACY")
    print("=" * 90)
    print(f"{'Formula':<35} {'n':>5}  {'Q%':>7} {'Cnd%':>7} {'Pln%':>7} {'Eig%':>7}")
    print("-" * 90)

    for f in sorted(formula_scores.keys()):
        s = formula_scores[f]
        n = s["n"]
        if n == 0:
            continue
        q_pct = s["q"]/n*100
        cnd_pct = s["coined"]/n*100
        pln_pct = s["plain"]/n*100
        eig_pct = s["eig"]/n*100
        print(f"{f:<35} {n:>5}  {q_pct:>6.1f}% {cnd_pct:>6.1f}% {pln_pct:>6.1f}% {eig_pct:>6.1f}%")

    print("=" * 90)
    print("\nNote: The fixed-10 baseline is the pre-registered protocol.")
    print("Formulas with >10 steps may improve accuracy on large molecules.")


if __name__ == "__main__":
    main()

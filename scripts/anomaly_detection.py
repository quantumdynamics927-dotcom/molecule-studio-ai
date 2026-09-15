"""
Structural Anomaly Detection via Quantum Walk on Molecular Graphs.
================================================================
Tests whether a staggered quantum walk can detect where a molecule
has been structurally perturbed — purely from the graph structure.

Setup:
  1. Reference molecule (e.g., benzene)
  2. Systematic single-atom substitutions at each position
  3. Run quantum walk and classical walks on each variant
  4. Ask: does the localization signature reliably identify
     WHICH position was substituted?

Self-verifying: we control the ground truth, no literature needed.
"""
from __future__ import annotations
import json, sys, math
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from molecular_fractal_bridge import build_molecular_adjacency, MoleculeInput, run_fractal_analysis
from coined_vs_quantum import plain_random_walk, coined_classical_walk, eigenvector_centrality

ELEMENT_MASS = {"H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999,
                "F": 18.998, "Cl": 35.45, "Br": 79.904, "I": 126.90,
                "S": 32.06, "P": 30.974}


def substitute_atom(atoms: list, bonds: list, position: int, new_element: str) -> tuple[list, list]:
    """
    Replace the atom at `position` with new_element and update bonds.
    The new atom inherits the old atom's connections.
    Returns new atoms and new bonds (both deep copies).
    """
    import copy
    new_atoms = copy.deepcopy(atoms)
    new_bonds = copy.deepcopy(bonds)

    # Update the element
    new_atoms[position]["element"] = new_element

    return new_atoms, new_bonds


def run_walks_on_molecule(atoms, bonds, steps=10, initial_node=0):
    """
    Run all methods and return localization signatures.
    Returns dict with per-method top-3 atoms and probabilities.
    """
    # Normalize bonds: accept either [{"atoms": [i,j], ...}] or [[i,j], ...] or [[i,j,order], ...]
    normalized_bonds = []
    for b in bonds:
        if isinstance(b, dict) and "atoms" in b:
            normalized_bonds.append([b["atoms"][0], b["atoms"][1]])
        elif isinstance(b, (list, tuple)) and len(b) >= 2:
            normalized_bonds.append([b[0], b[1]])

    adj = build_molecular_adjacency(atoms, normalized_bonds)

    # Quantum walk
    mol = MoleculeInput(name="?", formula="?", atoms=atoms, bonds=bonds)
    q_result = run_fractal_analysis(
        molecule_data=mol, fractal="sierpinski", level=3,
        route="ifs", walk_steps=steps, initial_node=initial_node,
    )
    q_rank = [(loc.atom_index, loc.visit_probability) for loc in q_result.localization]

    # Classical walks
    _, plain_rank = plain_random_walk(adj, steps=steps, initial_node=initial_node)
    _, coined_rank = coined_classical_walk(adj, steps=steps, initial_node=initial_node)

    # Eigenvector centrality
    eig_vec = eigenvector_centrality(adj)
    eig_rank = list(np.argsort(eig_vec)[::-1])

    def top3_with_prob(rank_list):
        if isinstance(rank_list, list) and len(rank_list) > 0:
            if isinstance(rank_list[0], tuple):
                return rank_list[:3]
            else:
                return [(i, adj[i].sum()) for i in rank_list[:3]]
        return []

    def rank_to_probs(rank_list, adj):
        probs = []
        for atom_idx in rank_list[:3]:
            if atom_idx < len(atoms):
                probs.append((atom_idx, atoms[atom_idx]["element"]))
        return probs

    return {
        "quantum": q_rank[:5],
        "classical": rank_to_probs(plain_rank, adj),
        "coined": rank_to_probs(coined_rank, adj),
        "eigenvector": [(i, atoms[i]["element"]) for i in eig_rank[:5]],
    }


def compute_signature_vector(walks_result, atoms):
    """
    Build a signature vector from walk results that can be compared across variants.
    Format: [avg_mass_top3, mass_spread_top3, hetero_in_top3, top1_mass, top1_degree]
    """
    def avg_mass(rank):
        if not rank:
            return 0.0
        masses = [ELEMENT_MASS.get(atoms[i]["element"], 0) for i, _ in rank[:3] if i < len(atoms)]
        return sum(masses) / len(masses) if masses else 0.0

    def hetero_count(rank):
        return sum(1 for i, _ in rank[:3] if i < len(atoms) and atoms[i]["element"] not in ("C", "H"))

    def top1_mass(rank):
        if not rank or rank[0][0] >= len(atoms):
            return 0.0
        return ELEMENT_MASS.get(atoms[rank[0][0]]["element"], 0)

    def mass_spread(rank):
        if len(rank) < 2:
            return 0.0
        masses = [ELEMENT_MASS.get(atoms[i]["element"], 0) for i, _ in rank[:3] if i < len(atoms)]
        if len(masses) < 2:
            return 0.0
        return max(masses) - min(masses)

    return {
        "avg_mass_top3": avg_mass(walks_result["quantum"]),
        "mass_spread": mass_spread(walks_result["quantum"]),
        "hetero_count": hetero_count(walks_result["quantum"]),
        "top1_mass": top1_mass(walks_result["quantum"]),
        "q_top1_idx": walks_result["quantum"][0][0] if walks_result["quantum"] else -1,
        "q_top1_el": atoms[walks_result["quantum"][0][0]]["element"] if walks_result["quantum"] else "?",
    }


def detect_substituted_position(reference_sig, variant_sigs, method="quantum"):
    """
    Given reference signature and a dictionary of variant signatures,
    find which variant is most different from reference.
    Returns the position with the largest signature change.
    """
    max_diff = -1
    detected_pos = None

    for pos, sig in variant_sigs.items():
        diff = (
            abs(sig["avg_mass_top3"] - reference_sig["avg_mass_top3"]) +
            abs(sig["top1_mass"] - reference_sig["top1_mass"]) +
            abs(sig["mass_spread"] - reference_sig["mass_spread"]) * 0.5 +
            abs(sig["hetero_count"] - reference_sig["hetero_count"]) * 5.0
        )
        if diff > max_diff:
            max_diff = diff
            detected_pos = pos

    return detected_pos, max_diff


def benzene_substitution_series():
    """
    Generate all substitution variants of benzene.
    Positions: 0-5 (all equivalent by symmetry, but substituents break it)
    Substituents: F, Cl, OH, NH2, CH3, NO2
    """
    # Benzene structure from PubChem (standard canonical ordering):
    # C0-C1-C2-C3-C4-C5 in a ring, with H's attached
    # Bonds: alternating double/single around the ring
    benzene_atoms = [
        {"element": "C",  "id": 0, "x": 0.0, "y": 1.4,  "z": 0.0},
        {"element": "C",  "id": 1, "x": 1.21, "y": 0.7,  "z": 0.0},
        {"element": "C",  "id": 2, "x": 1.21, "y": -0.7, "z": 0.0},
        {"element": "C",  "id": 3, "x": 0.0,  "y": -1.4, "z": 0.0},
        {"element": "C",  "id": 4, "x": -1.21,"y": -0.7, "z": 0.0},
        {"element": "C",  "id": 5, "x": -1.21,"y": 0.7,  "z": 0.0},
        {"element": "H",  "id": 6, "x": 0.0,  "y": 2.47, "z": 0.0},
        {"element": "H",  "id": 7, "x": 2.12, "y": 1.23, "z": 0.0},
        {"element": "H",  "id": 8, "x": 2.12, "y": -1.23,"z": 0.0},
        {"element": "H",  "id": 9, "x": 0.0,  "y": -2.47,"z": 0.0},
        {"element": "H",  "id": 10,"x": -2.12,"y": -1.23,"z": 0.0},
        {"element": "H",  "id": 11,"x": -2.12,"y": 1.23, "z": 0.0},
    ]
    # Ring bonds (alternating double/single)
    benzene_bonds = [
        {"atoms": [0, 1],  "order": 2.0},
        {"atoms": [1, 2],  "order": 1.0},
        {"atoms": [2, 3],  "order": 2.0},
        {"atoms": [3, 4],  "order": 1.0},
        {"atoms": [4, 5],  "order": 2.0},
        {"atoms": [5, 0],  "order": 1.0},
        # C-H bonds
        {"atoms": [0, 6],  "order": 1.0},
        {"atoms": [1, 7],  "order": 1.0},
        {"atoms": [2, 8],  "order": 1.0},
        {"atoms": [3, 9],  "order": 1.0},
        {"atoms": [4, 10], "order": 1.0},
        {"atoms": [5, 11], "order": 1.0},
    ]
    return benzene_atoms, benzene_bonds


def pyridine_substitution_series():
    """
    Pyridine: benzene with one C replaced by N.
    Standard ordering: N at position 0, then C around the ring.
    """
    pyridine_atoms = [
        {"element": "N",  "id": 0,  "x": 0.0,  "y": 1.4,  "z": 0.0},
        {"element": "C",  "id": 1,  "x": 1.21, "y": 0.7,  "z": 0.0},
        {"element": "C",  "id": 2,  "x": 1.21, "y": -0.7, "z": 0.0},
        {"element": "C",  "id": 3,  "x": 0.0,  "y": -1.4, "z": 0.0},
        {"element": "C",  "id": 4,  "x": -1.21,"y": -0.7, "z": 0.0},
        {"element": "C",  "id": 5,  "x": -1.21,"y": 0.7,  "z": 0.0},
        {"element": "H",  "id": 6,  "x": 0.0,  "y": 2.47, "z": 0.0},
        {"element": "H",  "id": 7,  "x": 2.12, "y": 1.23, "z": 0.0},
        {"element": "H",  "id": 8,  "x": 2.12, "y": -1.23,"z": 0.0},
        {"element": "H",  "id": 9,  "x": 0.0,  "y": -2.47,"z": 0.0},
        {"element": "H",  "id": 10,"x": -2.12,"y": -1.23,"z": 0.0},
    ]
    pyridine_bonds = [
        {"atoms": [0, 1],  "order": 2.0},  # C=N
        {"atoms": [1, 2],  "order": 1.0},
        {"atoms": [2, 3],  "order": 2.0},
        {"atoms": [3, 4],  "order": 1.0},
        {"atoms": [4, 5],  "order": 2.0},
        {"atoms": [5, 0],  "order": 1.0},
        {"atoms": [0, 6],  "order": 1.0},
        {"atoms": [1, 7],  "order": 1.0},
        {"atoms": [2, 8],  "order": 1.0},
        {"atoms": [3, 9],  "order": 1.0},
        {"atoms": [4, 10], "order": 1.0},
    ]
    return pyridine_atoms, pyridine_bonds


def naphthalene_substitution_series():
    """
    Naphthalene: two fused benzene rings.
    Ordering: C0-C1-C2-C3-C4-C5-C6-C7-C8-C9 with fusion bond C4-C5.
    Alpha positions: C0, C1, C4, C5, C8, C9
    Beta positions: C2, C3, C6, C7
    """
    naphthalene_atoms = [
        {"element": "C",  "id": 0,  "x": 0.0,   "y": 1.4,   "z": 0.0},
        {"element": "C",  "id": 1,  "x": 1.21,  "y": 0.7,   "z": 0.0},
        {"element": "C",  "id": 2,  "x": 2.42,  "y": 1.4,   "z": 0.0},
        {"element": "C",  "id": 3,  "x": 3.63,  "y": 0.7,   "z": 0.0},
        {"element": "C",  "id": 4,  "x": 3.63,  "y": -0.7,  "z": 0.0},
        {"element": "C",  "id": 5,  "x": 2.42,  "y": -1.4,  "z": 0.0},
        {"element": "C",  "id": 6,  "x": 1.21,  "y": -0.7,  "z": 0.0},
        {"element": "C",  "id": 7,  "x": -1.21, "y": -0.7,  "z": 0.0},
        {"element": "C",  "id": 8,  "x": -2.42, "y": 0.7,   "z": 0.0},
        {"element": "C",  "id": 9,  "x": -1.21, "y": 1.4,   "z": 0.0},
        {"element": "H",  "id": 10, "x": 0.0,   "y": 2.47,  "z": 0.0},
        {"element": "H",  "id": 11, "x": 4.55,  "y": 1.23,  "z": 0.0},
        {"element": "H",  "id": 12, "x": 4.55,  "y": -1.23, "z": 0.0},
        {"element": "H",  "id": 13, "x": 2.42,  "y": -2.47, "z": 0.0},
        {"element": "H",  "id": 14, "x": -2.42, "y": -1.4,  "z": 0.0},
        {"element": "H",  "id": 15, "x": -3.45, "y": 1.23,  "z": 0.0},
        {"element": "H",  "id": 16, "x": -2.42, "y": 2.47,  "z": 0.0},
    ]
    naphthalene_bonds = [
        # Ring 1
        {"atoms": [0, 1],  "order": 2.0},
        {"atoms": [1, 2],  "order": 1.0},
        {"atoms": [2, 3],  "order": 2.0},
        {"atoms": [3, 4],  "order": 1.0},
        # Ring 2 (fused)
        {"atoms": [4, 5],  "order": 2.0},
        {"atoms": [5, 6],  "order": 1.0},
        {"atoms": [6, 7],  "order": 2.0},
        {"atoms": [7, 8],  "order": 1.0},
        {"atoms": [8, 9],  "order": 2.0},
        {"atoms": [9, 0],  "order": 1.0},
        # Fusion bond
        {"atoms": [2, 7],  "order": 1.5},  # shared edge
        # C-H
        {"atoms": [0, 10], "order": 1.0},
        {"atoms": [3, 11], "order": 1.0},
        {"atoms": [4, 12], "order": 1.0},
        {"atoms": [5, 13], "order": 1.0},
        {"atoms": [7, 14], "order": 1.0},
        {"atoms": [8, 15], "order": 1.0},
        {"atoms": [9, 16], "order": 1.0},
    ]
    return naphthalene_atoms, naphthalene_bonds


def run_substitution_series(base_atoms, base_bonds, carbon_positions, substituents,
                           steps=10, initial_node=0):
    """
    Run the full substitution series experiment.

    Args:
        base_atoms, base_bonds: reference molecular structure
        carbon_positions: list of atom indices to substitute (the C atoms in the ring)
        substituents: list of element symbols to substitute
        steps: walk steps
        initial_node: starting node for walk

    Returns dict: {substitution: {position: {sig, walks_result}}}
    """
    results = {}

    # Reference run
    ref_walks = run_walks_on_molecule(base_atoms, base_bonds, steps=steps, initial_node=initial_node)
    ref_sig = compute_signature_vector(ref_walks, base_atoms)

    print(f"\n  Reference: top1={ref_sig['q_top1_el']}(idx={ref_sig['q_top1_idx']})  "
          f"avg_mass={ref_sig['avg_mass_top3']:.2f}  "
          f"hetero={ref_sig['hetero_count']}")

    for substituent in substituents:
        results[substituent] = {}
        print(f"\n  Substituent: {substituent}")

        for pos in carbon_positions:
            new_atoms, new_bonds = substitute_atom(base_atoms, base_bonds, pos, substituent)
            walks = run_walks_on_molecule(new_atoms, new_bonds, steps=steps, initial_node=initial_node)
            sig = compute_signature_vector(walks, new_atoms)

            # Compare to reference
            diff = (
                abs(sig["avg_mass_top3"] - ref_sig["avg_mass_top3"]) +
                abs(sig["top1_mass"] - ref_sig["top1_mass"]) +
                abs(sig["hetero_count"] - ref_sig["hetero_count"]) * 10.0
            )

            results[substituent][pos] = {
                "sig": sig,
                "walks": walks,
                "diff_from_ref": diff,
            }

            print(f"    pos={pos}: top1={sig['q_top1_el']}(idx={sig['q_top1_idx']})  "
                  f"avg_mass={sig['avg_mass_top3']:.2f}  "
                  f"hetero={sig['hetero_count']}  diff={diff:.2f}")

    return {"reference": ref_walks, "reference_sig": ref_sig, "results": results}


def print_detection_table(all_series_results):
    """
    For each substitution variant, print whether the walk correctly
    identifies WHICH position was substituted.
    """
    print("\n" + "=" * 100)
    print("ANOMALY DETECTION RESULTS: Can the walk identify the substituted position?")
    print("=" * 100)

    for series_name, series_data in all_series_results.items():
        ref_sig = series_data["reference_sig"]
        results = series_data["results"]

        print(f"\n--- {series_name} ---")
        print(f"Reference top1: {ref_sig['q_top1_el']}(idx={ref_sig['q_top1_idx']})  "
              f"avg_mass={ref_sig['avg_mass_top3']:.2f}")

        # For each substituent × position, compute which position "stands out most"
        for substituent, pos_results in results.items():
            print(f"\n  Substituent: {substituent}")

            # Find the position with maximum signature change
            max_diff = -1
            max_pos = None
            for pos, data in pos_results.items():
                if data["diff_from_ref"] > max_diff:
                    max_diff = data["diff_from_ref"]
                    max_pos = pos

            # Check if the max-diff position is actually substituted (it is, by definition)
            # The real question: does the walk concentrate on/near the substitution site?
            for pos, data in pos_results.items():
                sig = data["sig"]
                is_max = " ← MAX DIFF" if pos == max_pos else ""
                print(f"    pos={pos}: top1={sig['q_top1_el']}(idx={sig['q_top1_idx']:2d})  "
                      f"diff={data['diff_from_ref']:6.2f}  "
                      f"q_top1_near_subst={abs(sig['q_top1_idx']-pos)<=1}{is_max}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Structural anomaly detection via quantum walk")
    parser.add_argument("--steps", "-s", type=int, default=10)
    parser.add_argument("--output", "-o", type=str, default="D:/Molecule-App/anomaly_results.json")
    args = parser.parse_args()

    all_results = {}

    # ---- 1. Benzene substitution series ----
    print("\n" + "=" * 80)
    print("BENZENE SUBSTITUTION SERIES")
    print("=" * 80)
    print("Question: Can the quantum walk distinguish which ring position was substituted?")
    print("Carbon positions in benzene ring: 0, 1, 2, 3, 4, 5")
    print("Substituents: F, Cl, OH, NH2, CH3, NO2")

    benzene_atoms, benzene_bonds = benzene_substitution_series()
    carbon_positions = [0, 1, 2, 3, 4, 5]  # all 6 ring carbons

    benzene_results = run_substitution_series(
        benzene_atoms, benzene_bonds,
        carbon_positions=carbon_positions,
        substituents=["F", "Cl", "OH", "NH2", "CH3", "NO2"],
        steps=args.steps,
        initial_node=0,
    )
    all_results["benzene"] = benzene_results

    # ---- 2. Naphthalene substitution series ----
    print("\n\n" + "=" * 80)
    print("NAPHTHALENE SUBSTITUTION SERIES")
    print("=" * 80)
    print("Question: Alpha (positions 0,1,4,5,8,9) vs Beta (positions 2,3,6,7) substitution")
    print("Can the walk distinguish alpha vs beta substitution?")

    naphthalene_atoms, naphthalene_bonds = naphthalene_substitution_series()
    alpha_pos = [0, 1, 4, 5, 8, 9]  # alpha carbons
    beta_pos = [2, 3, 6, 7]           # beta carbons

    naph_results = run_substitution_series(
        naphthalene_atoms, naphthalene_bonds,
        carbon_positions=[0, 1, 2, 3],  # test 4 representative positions
        substituents=["F", "Cl", "OH"],
        steps=args.steps,
        initial_node=0,
    )
    all_results["naphthalene"] = naph_results

    # ---- Detection analysis ----
    print_detection_table(all_results)

    # ---- Save ----
    def make_serializable(obj):
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(v) for v in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif hasattr(obj, 'item'):
            return obj.item()
        return obj

    with open(args.output, "w") as f:
        json.dump(make_serializable(all_results), f, indent=2)
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()

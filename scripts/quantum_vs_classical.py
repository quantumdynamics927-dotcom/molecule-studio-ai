"""
Classical Random Walk vs Quantum Walk comparison on molecular graphs.
============================================================
This is the control experiment that tells us whether the quantum walk
is finding something beyond what a classical random walk can find.

The test: same molecular graphs, same starting node, same number of steps.
Compare: do quantum and classical walks produce the same dominant site rankings?

If YES → quantum walk is a re-expression of classical transport centrality
If NO → the difference is where quantum interference contributes

Also computes classical topological indices (degree, eigenvector centrality)
to check if classical graph theory already predicts the same rankings.
"""

from __future__ import annotations

import json
import math
import sys
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from fetch_molecule import fetch_molecule
from molecular_fractal_bridge import (
    build_molecular_adjacency, _build_graph_model, MoleculeInput,
    run_fractal_analysis,
)


# ---------------------------------------------------------------------------
# Classical continuous-time random walk
# ---------------------------------------------------------------------------

def classical_random_walk(
    adj: np.ndarray,
    steps: int = 10,
    initial_node: int = 0,
) -> tuple[np.ndarray, list[int]]:
    """
    Continuous-time classical random walk on weighted graph.

    Transition matrix: P = D^{-1} * A
    State evolves as: p(t+1) = P @ p(t)

    Returns:
        final_probs: probability distribution after `steps` steps
        rank_order: atom indices sorted by probability (highest first)
    """
    n = adj.shape[0]
    degree = adj.sum(axis=1)
    # Avoid division by zero for isolated nodes
    degree_safe = np.where(degree > 0, degree, 1.0)
    P = adj / degree_safe[:, np.newaxis]  # row-stochastic

    p = np.zeros(n)
    p[initial_node] = 1.0

    for _ in range(steps):
        p = P @ p

    rank = np.argsort(p)[::-1]
    return p, rank.tolist()


def eigenvector_centrality(adj: np.ndarray) -> np.ndarray:
    """
    Compute eigenvector centrality of a graph.
    c_i = (1/λ) * Σ_j A_ij * c_j
    The leading eigenvector of A gives the most central nodes.
    """
    n = adj.shape[0]
    eigenvalues, eigenvectors = np.linalg.eigh(adj)
    # Leading eigenvalue = max eigenvalue (last after sort)
    leading_vec = eigenvectors[:, -1]
    leading_vec = leading_vec / leading_vec.sum()  # normalize
    leading_vec = np.abs(leading_vec)  # signs don't matter for centrality
    return leading_vec


def degree_centrality(adj: np.ndarray) -> np.ndarray:
    """Simple degree centrality: degree[i] / max_degree"""
    d = adj.sum(axis=1)
    max_d = d.max()
    if max_d == 0:
        return np.ones(n) / n
    return d / max_d


def pagerank(adj: np.ndarray, alpha: float = 0.85, steps: int = 100) -> np.ndarray:
    """
    PageRank on the molecular graph.
    """
    n = adj.shape[0]
    degree = adj.sum(axis=1)
    degree_safe = np.where(degree > 0, degree, 1.0)
    # Column-stochastic form
    P = adj / degree_safe[:, np.newaxis]

    # Add damping
    J = np.ones((n, n)) / n
    P_teleport = alpha * P + (1 - alpha) * J

    p = np.ones(n) / n
    for _ in range(steps):
        p = P_teleport @ p

    return p


def compare_methods(
    mol_name: str,
    atoms: list,
    bonds: list,
    steps: int = 10,
    initial_node: int = 0,
) -> dict:
    """
    Run all methods on one molecule and compare rankings.
    """
    adj = build_molecular_adjacency(atoms, bonds)
    n = len(atoms)

    # --- Quantum walk ---
    mol = MoleculeInput(name=mol_name, formula="?", atoms=atoms, bonds=bonds)
    q_result = run_fractal_analysis(
        molecule_data=mol,
        fractal="sierpinski",
        level=3,
        route="ifs",
        walk_steps=steps,
        initial_node=initial_node,
    )

    # --- Classical random walk ---
    c_probs, c_rank = classical_random_walk(adj, steps=steps, initial_node=initial_node)

    # --- Classical indices ---
    eig_centrality = eigenvector_centrality(adj)
    deg_centrality = degree_centrality(adj)
    pr_scores = pagerank(adj)

    # --- Rankings ---
    # Quantum walk ranking
    q_rank = [loc.atom_index for loc in q_result.localization]

    # Classical random walk ranking
    cl_rank = c_rank

    # Eigenvector centrality ranking
    eig_rank = np.argsort(eig_centrality)[::-1].tolist()

    # Degree centrality ranking
    deg_rank = np.argsort(deg_centrality)[::-1].tolist()

    # PageRank ranking
    pr_rank = np.argsort(pr_scores)[::-1].tolist()

    # --- Top site comparison ---
    methods = {
        "quantum_walk": {"top1": q_rank[0] if len(q_rank) > 0 else -1,
                         "top3": q_rank[:3]},
        "classical_rw": {"top1": cl_rank[0] if len(cl_rank) > 0 else -1,
                         "top3": cl_rank[:3]},
        "eigenvector":  {"top1": eig_rank[0], "top3": eig_rank[:3]},
        "degree":       {"top1": deg_rank[0], "top3": deg_rank[:3]},
        "pagerank":     {"top1": pr_rank[0],  "top3": pr_rank[:3]},
    }

    # --- Agreements ---
    q_vs_cl_top1_match = methods["quantum_walk"]["top1"] == methods["classical_rw"]["top1"]
    q_vs_eig_top1_match = methods["quantum_walk"]["top1"] == methods["eigenvector"]["top1"]

    # Kendall's τ-like: rank correlation at top-3
    def topk_overlap(rank_a, rank_b, k=3):
        set_a = set(rank_a[:k])
        set_b = set(rank_b[:k])
        return len(set_a & set_b) / k

    q_cl_top3 = topk_overlap(q_rank, cl_rank)
    q_eig_top3 = topk_overlap(q_rank, eig_rank)

    return {
        "name": mol_name,
        "formula": getattr(q_result, "formula", "?"),
        "num_atoms": n,
        "steps": steps,
        "initial_node": initial_node,
        "methods": methods,
        "agreements": {
            "q_vs_cl_top1": q_vs_cl_top1_match,
            "q_vs_eig_top1": q_vs_eig_top1_match,
            "q_cl_top3_overlap": q_cl_top3,
            "q_eig_top3_overlap": q_eig_top3,
        },
        "quantum_top3_elements": [atoms[i]["element"] for i in q_rank[:3]],
        "classical_top3_elements": [atoms[i]["element"] for i in cl_rank[:3]],
        "eigenvector_top3_elements": [atoms[i]["element"] for i in eig_rank[:3]],
    }


def run_comparison_batch(
    molecules: list[dict],  # [{"name": str, "atoms": list, "bonds": list}]
    steps: int = 10,
    initial_node: int = 0,
) -> list[dict]:
    """Run comparison across a batch of molecules."""
    results = []
    for m in molecules:
        print(f"  {m['name']}...", end=" ", flush=True)
        try:
            r = compare_methods(
                m["name"], m["atoms"], m["bonds"],
                steps=steps, initial_node=initial_node,
            )
            results.append(r)
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"name": m["name"], "error": str(e)})
    return results


def print_comparison_table(results: list[dict]):
    """Print a formatted comparison table."""
    print("\n" + "=" * 130)
    print("QUANTUM vs CLASSICAL WALK — TOP SITE COMPARISON")
    print("=" * 130)
    print(f"{'Molecule':<18} {'Formula':<10} {'Q-Top1':>8} {'Cl-Top1':>8} "
          f"{'Eig-Top1':>8} {'Deg-Top1':>8} {'Q=Cl':>5} {'Q=Eig':>5} "
          f"{'Top3 overlap':>12} {'Q-Cl agreement'}")
    print("-" * 130)

    q_cl_agree = 0
    q_eig_agree = 0
    total = 0

    for r in results:
        if r.get("error"):
            continue
        total += 1

        m = r["methods"]
        agree = r["agreements"]

        q_top1_el = r["quantum_top3_elements"][0] if r["quantum_top3_elements"] else "?"
        cl_top1_el = r["classical_top3_elements"][0] if r["classical_top3_elements"] else "?"
        eig_top1_el = r["eigenvector_top3_elements"][0] if r["eigenvector_top3_elements"] else "?"

        q_match = "✓" if agree["q_vs_cl_top1"] else "✗"
        e_match = "✓" if agree["q_vs_eig_top1"] else "✗"
        if agree["q_vs_cl_top1"]:
            q_cl_agree += 1
        if agree["q_vs_eig_top1"]:
            q_eig_agree += 1

        ovlp = f"{agree['q_cl_top3_overlap']:.2f}"

        q_cl_agree_str = f"{q_match} ({q_top1_el}={cl_top1_el})"

        print(
            f"{r['name']:<18} {r.get('formula','?'):<10} "
            f"{m['quantum_walk']['top1']:>5}({q_top1_el}) "
            f"{m['classical_rw']['top1']:>5}({cl_top1_el}) "
            f"{m['eigenvector']['top1']:>5}({eig_top1_el}) "
            f"{m['degree']['top1']:>5} "
            f"{q_match:>5} {e_match:>5} "
            f"{ovlp:>12}  {q_cl_agree_str}"
        )

    print("-" * 130)
    print(f"Quantum=Classical top1: {q_cl_agree}/{total} = {100*q_cl_agree/max(total,1):.1f}%")
    print(f"Quantum=Eigenvector top1: {q_eig_agree}/{total} = {100*q_eig_agree/max(total,1):.1f}%")
    print("=" * 130)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Quantum vs Classical walk comparison")
    parser.add_argument("--steps", "-s", type=int, default=10)
    parser.add_argument("--node", "-n", type=int, default=0)
    parser.add_argument("--output", "-o", type=str, default=None)
    parser.add_argument("--molecules", nargs="*", default=None)
    args = parser.parse_args()

    # Load molecules from batch results
    batch_file = Path(__file__).parent.parent / "batch_results.json"
    with open(batch_file) as f:
        batch = json.load(f)

    # Reconstruct molecules from batch (atoms/bonds not in batch — fetch fresh)
    print(f"Fetching molecule structures...")
    molecules = []
    for r in batch:
        name = r["name"].lower()
        print(f"  Fetching {name}...", end=" ", flush=True)
        raw = fetch_molecule(name)
        if raw:
            molecules.append({
                "name": raw["name"],
                "atoms": raw["atoms"],
                "bonds": raw["bonds"],
            })
            print("OK")
        else:
            print("FAILED")

    print(f"\nRunning comparison on {len(molecules)} molecules...")
    results = run_comparison_batch(molecules, steps=args.steps, initial_node=args.node)
    print_comparison_table(results)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()

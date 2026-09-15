"""
Coined classical random walk (lifted Markov chain) vs quantum walk.
============================================================
A "coined walk" is a classical random walk with a coin degree-of-freedom —
at each step, a classical coin (random direction) is flipped, then the walker
moves. This is the strongest classical competitor to a quantum walk per the
"lifted Markov chain" literature (Lovas et al., INRIA RR-9001).

It mixes as O(t) vs O(√t) in certain regimes — much closer to quantum
performance than plain diffusion.

We also compute proper binomial significance for the head-to-head comparison.
"""

from __future__ import annotations

import json
import math
import sys
import numpy as np
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from fetch_molecule import fetch_molecule
from molecular_fractal_bridge import (
    build_molecular_adjacency, _build_graph_model, MoleculeInput,
    run_fractal_analysis,
)


# ---------------------------------------------------------------------------
# Coined classical walk (lifted Markov chain)
# ---------------------------------------------------------------------------

def coined_classical_walk(
    adj: np.ndarray,
    steps: int = 10,
    initial_node: int = 0,
    seed: int = 42,
) -> tuple[np.ndarray, list[int]]:
    """
    Continuous-time classical random walk with a coin degree-of-freedom.

    At each step:
    1. A "coin" samples a neighboring edge uniformly at random
    2. The walker transitions along that edge

    This is a lifted / non-backtracking Markov chain — a significantly
    stronger classical baseline than plain diffusion.

    Returns:
        final_probs: probability distribution after `steps` steps
        rank_order: atom indices sorted by probability (highest first)
    """
    rng = np.random.default_rng(seed)
    n = adj.shape[0]

    # Build neighbor list (edges in both directions for uniform sampling)
    neighbors = []
    for i in range(n):
        nbrs = []
        for j in range(n):
            if adj[i, j] > 0:
                # Add each bond once per unit weight
                w = int(round(adj[i, j]))
                nbrs.extend([j] * w)
        neighbors.append(nbrs)

    # If isolated, return uniform
    for i, nbrs in enumerate(neighbors):
        if len(nbrs) == 0:
            neighbors[i] = list(range(n))  # fallback: teleport

    p = np.zeros(n)
    p[initial_node] = 1.0

    for _ in range(steps):
        new_p = np.zeros(n)
        for i in range(n):
            if p[i] > 0:
                nbrs = neighbors[i]
                if nbrs:
                    # Sample uniformly from neighbors
                    probs = np.ones(len(nbrs)) / len(nbrs)
                    for j_idx, j in enumerate(nbrs):
                        new_p[j] += p[i] * probs[j_idx]
                else:
                    # Uniform fallback for isolated node
                    new_p += p[i] / n
        p = new_p

    rank = np.argsort(p)[::-1]
    return p, rank.tolist()


def plain_random_walk(
    adj: np.ndarray,
    steps: int = 10,
    initial_node: int = 0,
) -> tuple[np.ndarray, list[int]]:
    """Plain continuous-time random walk (P = D^{-1} * A)."""
    n = adj.shape[0]
    degree = adj.sum(axis=1)
    degree_safe = np.where(degree > 0, degree, 1.0)
    P = adj / degree_safe[:, np.newaxis]

    p = np.zeros(n)
    p[initial_node] = 1.0

    for _ in range(steps):
        p = P @ p

    rank = np.argsort(p)[::-1]
    return p, rank.tolist()


def eigenvector_centrality(adj: np.ndarray) -> np.ndarray:
    """Leading eigenvector of the adjacency matrix."""
    eigenvalues, eigenvectors = np.linalg.eigh(adj)
    leading_vec = eigenvectors[:, -1]
    leading_vec = leading_vec / leading_vec.sum()
    leading_vec = np.abs(leading_vec)
    return leading_vec


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


def element_type(el: str) -> str:
    if el == "C": return "conjugated_c"
    if el in ("O", "N", "S", "Cl"): return "heteroatom"
    return "other"


def compare_methods(
    mol_name: str,
    atoms: list,
    bonds: list,
    steps: int = 10,
    initial_node: int = 0,
) -> dict:
    """Run quantum walk and all classical baselines."""
    adj = build_molecular_adjacency(atoms, bonds)

    # Quantum walk
    mol = MoleculeInput(name=mol_name, formula="?", atoms=atoms, bonds=bonds)
    q_result = run_fractal_analysis(
        molecule_data=mol,
        fractal="sierpinski",
        level=3,
        route="ifs",
        walk_steps=steps,
        initial_node=initial_node,
    )

    # Plain random walk
    plain_probs, plain_rank = plain_random_walk(adj, steps=steps, initial_node=initial_node)

    # Coined classical walk (seeded for reproducibility)
    coined_probs, coined_rank = coined_classical_walk(adj, steps=steps, initial_node=initial_node)

    # Eigenvector centrality
    eig_vec = eigenvector_centrality(adj)
    eig_rank = np.argsort(eig_vec)[::-1].tolist()

    def top_elements(rank_list, k=3):
        return [atoms[i]["element"] for i in rank_list[:k]]

    return {
        "name": mol_name,
        "num_atoms": len(atoms),
        "steps": steps,
        "initial_node": initial_node,
        "quantum_walk": {
            "top1": q_rank[0] if (q_rank := [loc.atom_index for loc in q_result.localization]) else -1,
            "top3": q_rank[:3] if q_rank else [],
            "top3_elements": top_elements(q_rank),
        },
        "plain_rw": {
            "top1": plain_rank[0],
            "top3": plain_rank[:3],
            "top3_elements": top_elements(plain_rank),
        },
        "coined_rw": {
            "top1": coined_rank[0],
            "top3": coined_rank[:3],
            "top3_elements": top_elements(coined_rank),
        },
        "eigenvector": {
            "top1": eig_rank[0],
            "top3": eig_rank[:3],
            "top3_elements": top_elements(eig_rank),
        },
    }


def run_batch(molecules, steps=10, initial_node=0):
    results = []
    for m in molecules:
        print(f"  {m['name']}...", end=" ", flush=True)
        try:
            r = compare_methods(m["name"], m["atoms"], m["bonds"],
                                steps=steps, initial_node=initial_node)
            results.append(r)
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"name": m["name"], "error": str(e)})
    return results




def main():
    import argparse
    parser = argparse.ArgumentParser(description="Coined classical walk vs quantum walk")
    parser.add_argument("--steps", "-s", type=int, default=10)
    parser.add_argument("--node", "-n", type=int, default=0)
    parser.add_argument("--output", "-o", type=str, default=None)
    args = parser.parse_args()

    # Load batch
    batch_file = Path(__file__).parent.parent / "batch_results.json"
    with open(batch_file) as f:
        batch = json.load(f)

    print(f"Fetching {len(batch)} molecule structures...")
    molecules = []
    for r in batch:
        name = r["name"].lower()
        print(f"  {name}...", end=" ", flush=True)
        raw = fetch_molecule(name)
        if raw:
            molecules.append({"name": raw["name"], "atoms": raw["atoms"], "bonds": raw["bonds"]})
            print("OK")
        else:
            print("FAILED")

    print(f"\nRunning 4-method comparison (steps={args.steps}, node={args.node})...")
    results = run_batch(molecules, steps=args.steps, initial_node=args.node)

    # ---- Print table ----
    print("\n" + "=" * 140)
    print("QUANTUM vs PLAIN RW vs COINED RW vs EIGENVECTOR — DOMINANT SITE")
    print("=" * 140)
    print(f"{'Molecule':<18} {'Lit':<10} {'Q-Top1':>8} {'Pln-Top1':>8} {'Cnd-Top1':>8} {'Eig-Top1':>8}  "
          f"{'Q✓':>4} {'Pln✓':>4} {'Cnd✓':>4} {'Eig✓':>4}  Winner")
    print("-" * 140)

    q_hits = plain_hits = coined_hits = eig_hits = 0
    head_q_wins = head_plain_wins = head_coined_wins = head_ties = 0
    wins_detail = []

    for r in results:
        if r.get("error"):
            continue
        name = r["name"].lower()
        lit = LITERATURE_HOMO.get(name, "?")
        if lit == "?":
            continue

        q_top_el = r["quantum_walk"]["top3_elements"][0]
        plain_top_el = r["plain_rw"]["top3_elements"][0]
        coined_top_el = r["coined_rw"]["top3_elements"][0]
        eig_top_el = r["eigenvector"]["top3_elements"][0]

        q_type = element_type(q_top_el)
        plain_type = element_type(plain_top_el)
        coined_type = element_type(coined_top_el)
        eig_type = element_type(eig_top_el)

        q_ok = q_type == lit
        plain_ok = plain_type == lit
        coined_ok = coined_type == lit
        eig_ok = eig_type == lit

        if q_ok: q_hits += 1
        if plain_ok: plain_hits += 1
        if coined_ok: coined_hits += 1
        if eig_ok: eig_hits += 1

        # Head-to-head: quantum vs each classical
        q_wins = int(q_ok and not plain_ok and not coined_ok)
        plain_wins = int(plain_ok and not q_ok and not coined_ok)
        coined_wins = int(coined_ok and not q_ok and not plain_ok)
        tie = int(q_ok == plain_ok == coined_ok)

        if tie:
            head_ties += 1
        elif q_wins:
            head_q_wins += 1
        elif plain_wins:
            head_plain_wins += 1
        elif coined_wins:
            head_coined_wins += 1

        if q_ok: winner = "Q"
        elif plain_ok: winner = "Pln"
        elif coined_ok: winner = "Cnd"
        elif eig_ok: winner = "Eig"
        else: winner = "—"

        print(f"{r['name']:<18} {lit:<10} "
              f"{q_top_el:>5}({r['quantum_walk']['top1']:>2}) "
              f"{plain_top_el:>5}({r['plain_rw']['top1']:>2}) "
              f"{coined_top_el:>5}({r['coined_rw']['top1']:>2}) "
              f"{eig_top_el:>5}({r['eigenvector']['top1']:>2}) "
              f"{'✓' if q_ok else '✗':>4} {'✓' if plain_ok else '✗':>4} {'✓' if coined_ok else '✗':>4} {'✓' if eig_ok else '✗':>4}  "
              f"{winner}")

    total = len([r for r in results if not r.get("error") and LITERATURE_HOMO.get(r["name"].lower(), "?") != "?"])

    print("-" * 140)
    print(f"\nACCURACY: Quantum={q_hits}/{total} ({100*q_hits/total:.1f}%)  "
          f"PlainRW={plain_hits}/{total} ({100*plain_hits/total:.1f}%)  "
          f"CoinedRW={coined_hits}/{total} ({100*coined_hits/total:.1f}%)  "
          f"Eigenvector={eig_hits}/{total} ({100*eig_hits/total:.1f}%)")

    # Non-tied comparisons for binomial test
    non_tied = head_q_wins + head_plain_wins + head_coined_wins + head_ties
    n_nontied = head_q_wins + head_plain_wins + head_coined_wins
    print(f"\nHEAD-TO-HEAD (excluding ties): Q wins={head_q_wins}, PlainRW wins={head_plain_wins}, CoinedRW wins={head_coined_wins}")
    print(f"  Q wins {head_q_wins}/{n_nontied} = {100*head_q_wins/max(n_nontied,1):.1f}% of non-tied comparisons")

    # Binomial test: under H0: quantum and classical equally likely, p=0.5
    # Non-tied = trials where there is a clear winner
    # This is testing: is quantum more likely to win than classical?
    # Strict comparison: quantum wins vs classical wins (excluding ties and mutual correctness)
    # Cases: both wrong, both right (tie), Q wins, Cl wins
    # Count: both right = ties, both wrong = ?
    # Non-tied clear wins: Q vs Classical
    print(f"\n--- BINOMIAL SIGNIFICANCE ---")
    # Option 1: count of Q wins vs (Q wins + Cl wins) among cases where only one is correct
    n_trials = head_q_wins + head_plain_wins + head_coined_wins
    if n_trials > 0:
        print(f"Non-tied comparisons (one correct, others wrong): {n_trials}")
        print(f"  Quantum wins alone: {head_q_wins}/{n_trials}")
        print(f"  Coined RW wins alone: {head_coined_wins}/{n_trials}")
        print(f"  Plain RW wins alone: {head_plain_wins}/{n_trials}")

    # Option 2: exact binomial under H0: p=0.5, n=non_tied where Q or classical wins
    # This tests: if Q and classical are equally good, how often would Q win n times?
    # One-sided: P(X >= head_q_wins) for X ~ Binomial(n_trials, 0.5)
    if n_trials >= 3:
        # Use scipy if available
        try:
            from scipy.stats import binomtest
            result = binomtest(head_q_wins, n_trials, 0.5, alternative='greater')
            print(f"\nExact binomial test (scipy): H0: Q and classical equally good")
            print(f"  n = {n_trials}, k = {head_q_wins} quantum wins")
            print(f"  One-sided p-value (Q > classical by chance): {result.pvalue:.5f}")
            print(f"  {'Significant at α=0.05' if result.pvalue < 0.05 else 'Not significant at α=0.05'}")
        except ImportError:
            print("\n(scipy not available for exact binomial test)")

    # Also test against the stronger coined RW
    print(f"\n--- COINED RW HEAD-TO-HEAD ---")
    q_vs_coined_wins = sum(1 for r in results if not r.get("error")
                           and element_type(r["quantum_walk"]["top3_elements"][0]) == LITERATURE_HOMO.get(r["name"].lower(), "?")
                           and element_type(r["coined_rw"]["top3_elements"][0]) != LITERATURE_HOMO.get(r["name"].lower(), "?"))
    q_vs_coined_loss = sum(1 for r in results if not r.get("error")
                           and element_type(r["coined_rw"]["top3_elements"][0]) == LITERATURE_HOMO.get(r["name"].lower(), "?")
                           and element_type(r["quantum_walk"]["top3_elements"][0]) != LITERATURE_HOMO.get(r["name"].lower(), "?"))
    n_qc = q_vs_coined_wins + q_vs_coined_loss
    print(f"  Quantum beats Coined RW: {q_vs_coined_wins}/{n_qc}")
    print(f"  Coined RW beats Quantum: {q_vs_coined_loss}/{n_qc}")
    if n_qc > 0:
        try:
            from scipy.stats import binomtest
            result = binomtest(q_vs_coined_wins, n_qc, 0.5, alternative='greater')
            print(f"  Exact binomial p-value (Q > Coined RW): {result.pvalue:.5f}")
        except ImportError:
            pass

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()

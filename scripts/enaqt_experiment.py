"""
ENAQT (Environment-Assisted Quantum Transport) Experiment.
======================================================
Tests whether transport efficiency on molecular bond graphs shows
the characteristic ENAQT peak at intermediate dephasing.

The ENAQT hypothesis (Rebentrost, Mohseni, Aspuru-Guzik 2009):
  Moderate dephasing (intermediate noise) ENHANCES transport efficiency
  compared to both pure quantum (gamma=0) and purely classical (gamma=1).

Three-way comparison:
  gamma=0.0: Pure unitary quantum walk (no dephasing)
  gamma=1.0: Fully decohered -> classical random walk
  0<gamma<1: Intermediate dephasing -> ENAQT regime

The peak at intermediate gamma is the signature prediction.
If no peak: efficiency is monotonic -> molecular bond graphs behave
like the "classical FRET" limit in the skeptical FMO literature.

Readout: end-to-end transport efficiency.
For a conjugated chain: source = one end, sink = the other.
We use the spectral gap and graph structure to identify source/sink.
"""
from __future__ import annotations
import json, math, sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fetch_molecule import fetch_molecule
from molecular_fractal_bridge import build_molecular_adjacency, MoleculeInput


# ---------------------------------------------------------------------------
# ENAQT: Dephasing Quantum Walk
# ---------------------------------------------------------------------------

def quantum_walk_probabilities(adj: np.ndarray, steps: int, initial_node: int) -> np.ndarray:
    """
    Pure staggered quantum walk probabilities at each step.
    Uses the molecular adjacency matrix directly.
    For a continuous-time staggered walk on graph with adjacency A:
      p(t+1) = U @ p(t) where U encodes alternating coin-shift
    Simplified: use dispersing walk approximation: A @ p, then normalize.
    """
    n = adj.shape[0]
    A = adj
    p = np.zeros(n)
    p[initial_node] = 1.0
    probs_list = [p.copy()]

    for _ in range(steps):
        p_new = A @ p
        p_new = np.abs(p_new)
        norm = np.linalg.norm(p_new)
        if norm > 0:
            p_new = p_new / norm
        p = p_new
        probs_list.append(p.copy())

    return np.array(probs_list)


def classical_rw_probabilities(adj: np.ndarray, steps: int, initial_node: int) -> np.ndarray:
    """
    Classical continuous-time random walk probabilities at each step.
    Transition: p(t+1) = D^{-1} * A @ p(t)
    """
    n = adj.shape[0]
    degree = adj.sum(axis=1)
    degree_safe = np.where(degree > 0, degree, 1.0)
    P = adj / degree_safe[:, np.newaxis]

    p = np.zeros(n)
    p[initial_node] = 1.0
    probs_list = [p.copy()]

    for _ in range(steps):
        p = P @ p
        probs_list.append(p.copy())

    return np.array(probs_list)


def enaqt_probabilities(
    adj: np.ndarray,
    steps: int,
    initial_node: int,
    gamma: float,
) -> np.ndarray:
    """
    ENAQT: dephasing quantum walk at level gamma in [0, 1].

    At each step, mix quantum and classical distributions:
      p_mixed = (1 - gamma) * p_quantum + gamma * p_classical

    gamma = 0 -> pure quantum (unitary evolution)
    gamma = 1 -> pure classical (fully decohered)
    0 < gamma < 1 -> intermediate ENAQT regime
    """
    n = adj.shape[0]

    degree = adj.sum(axis=1)
    degree_safe = np.where(degree > 0, degree, 1.0)
    P = adj / degree_safe[:, np.newaxis]

    p = np.zeros(n)
    p[initial_node] = 1.0
    probs_list = [p.copy()]

    for _ in range(steps):
        # Quantum step (absolute-value dispersing walk approximation)
        p_q = adj @ p
        p_q = np.abs(p_q)
        norm_q = np.linalg.norm(p_q)
        if norm_q > 0:
            p_q = p_q / norm_q

        # Classical step
        p_c = P @ p

        # Mix
        p_new = (1 - gamma) * p_q + gamma * p_c

        norm = np.linalg.norm(p_new)
        if norm > 0:
            p_new = p_new / norm
        p = p_new
        probs_list.append(p.copy())

    return np.array(probs_list)


def transport_efficiency(probs_history: np.ndarray, source: int, sink: int) -> float:
    """
    Compute end-to-end transport efficiency as first-arrival probability at sink.

    Sums the incremental probability that arrives at the sink at each step,
    avoiding double-counting once the excitation has arrived.
    """
    sink_probs = probs_history[:, sink]
    cumulative = 0.0
    for t in range(1, len(sink_probs)):
        arriving = max(0.0, sink_probs[t] - sink_probs[t - 1])
        cumulative += arriving
    return min(1.0, cumulative)


# ---------------------------------------------------------------------------
# Source/Sink identification for conjugated chains
# ---------------------------------------------------------------------------

def identify_source_sink(adj: np.ndarray, atoms: list) -> tuple[int, int]:
    """
    Identify source and sink nodes for transport efficiency measurement.

    Source = highest-degree carbon node (initial excitation site).
    Sink = highest-degree carbon node not adjacent to source,
           chosen to maximize graph distance from source.
    """
    n = adj.shape[0]
    degrees = adj.sum(axis=1)

    carbon_indices = [i for i in range(n) if atoms[i]["element"] == "C"]
    if len(carbon_indices) < 2:
        carbon_indices = list(range(n))

    carbon_degrees = {i: degrees[i] for i in carbon_indices}

    source = max(carbon_indices, key=lambda i: carbon_degrees[i])

    candidates = [i for i in carbon_indices if i != source and adj[source, i] == 0]
    if not candidates:
        candidates = [i for i in carbon_indices if i != source]

    # BFS to find graph distances
    from collections import deque
    def bfs_dist(start, targets):
        dist = {start: 0}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            for nb in np.where(adj[cur] > 0)[0]:
                if nb not in dist:
                    dist[nb] = dist[cur] + 1
                    queue.append(nb)
        target_dist = max((dist.get(t, 9999) for t in targets), default=0)
        return target_dist

    sink = max(candidates, key=lambda i: bfs_dist(source, set(candidates) - {i}))

    return source, sink


# ---------------------------------------------------------------------------
# Run ENAQT sweep on a single molecule
# ---------------------------------------------------------------------------

def run_enaqt_sweep(
    atoms: list,
    bonds: list,
    steps: int | None = None,
    gamma_values: list[float] | None = None,
    initial_node: int | None = None,
) -> dict:
    """
    Run ENAQT experiment on one molecule.

    Sweeps gamma from 0 to 1 and computes transport efficiency at each point.
    """
    adj = build_molecular_adjacency(atoms, bonds)
    n = len(atoms)

    if gamma_values is None:
        gamma_values = [round(i * 0.05, 3) for i in range(21)]

    if steps is None:
        steps = max(5, (n + 1) // 2)

    source, sink = identify_source_sink(adj, atoms)
    if initial_node is not None:
        source = initial_node

    results = {
        "molecule": atoms[0].get("name", "?") if atoms else "?",
        "num_atoms": n,
        "steps": steps,
        "source": source,
        "sink": sink,
        "source_element": atoms[source]["element"],
        "sink_element": atoms[sink]["element"],
        "gamma_sweep": [],
    }

    for gamma in gamma_values:
        probs = enaqt_probabilities(adj, steps=steps, initial_node=source, gamma=gamma)
        eff = transport_efficiency(probs, source=source, sink=sink)
        results["gamma_sweep"].append({
            "gamma": gamma,
            "efficiency": float(eff),
            "sink_at_final": float(probs[-1, sink]),
        })

    return results


# ---------------------------------------------------------------------------
# PAH series
# ---------------------------------------------------------------------------

PAH_SERIES = ["benzene", "naphthalene", "anthracene", "tetracene", "pentacene"]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ENAQT experiment on PAH series")
    parser.add_argument("--steps", "-s", type=int, default=None)
    parser.add_argument("--output", "-o", type=str, default="D:/Molecule-App/enaqt_results.json")
    args = parser.parse_args()

    print("=" * 80)
    print("ENAQT EXPERIMENT: Transport Efficiency vs Dephasing on PAH Series")
    print("=" * 80)
    print("""
Hypothesis: ENAQT (Rebentrost, Mohseni, Aspuru-Guzik 2009)
  -> Intermediate dephasing (0 < gamma < 1) ENHANCES transport efficiency
  -> Efficiency-vs-gamma curve has a peak at intermediate gamma

Test molecules: Benzene -> Pentacene (increasing conjugation length)
  If ENAQT is real on molecular graphs: we should see the peak.
  If purely classical FRET limit: efficiency monotonically decreases with gamma.
  If purely quantum: efficiency monotonically increases with gamma (no peak).

Metric: End-to-end transport efficiency (first-arrival probability at sink)
""")

    gamma_values = [round(i * 0.05, 3) for i in range(21)]

    all_results = {}
    for name in PAH_SERIES:
        print(f"\n{name}...", end=" ", flush=True)
        mol = fetch_molecule(name)
        if not mol:
            print("FETCH FAILED")
            continue

        result = run_enaqt_sweep(
            atoms=mol["atoms"],
            bonds=mol["bonds"],
            steps=args.steps,
            gamma_values=gamma_values,
        )

        sweep = result["gamma_sweep"]
        # Build lookup by gamma value
        eff_by_g = {s["gamma"]: s["efficiency"] for s in sweep}

        eff_at_0 = eff_by_g.get(0.0, 0.0)
        eff_at_1 = eff_by_g.get(1.0, eff_by_g.get(0.95, 0.0))
        max_eff = max(eff_by_g.values())
        peak_gamma = max(eff_by_g, key=lambda g: eff_by_g[g])

        print(f"n={result['num_atoms']}  source={result['source']}({result['source_element']}) "
              f"sink={result['sink']}({result['sink_element']})  "
              f"eff(g=0)={eff_at_0:.4f}  eff(g=1)={eff_at_1:.4f}  "
              f"max_eff={max_eff:.4f} at g={peak_gamma:.2f}")

        all_results[name] = result

    # Print comparison table
    print("\n\n" + "=" * 80)
    print("ENAQT CURVE SUMMARY: Does efficiency peak at intermediate gamma?")
    print("=" * 80)
    header = f"{'Molecule':<15} {'n':>4} {'g=0.00':>8} {'g=0.25':>8} {'g=0.50':>8} {'g=0.75':>8} {'g=1.00':>8} {'Peak@':>7} {'Pattern'}"
    print(header)
    print("-" * len(header))

    for name, result in all_results.items():
        sweep = result["gamma_sweep"]
        eff_by_g = {s["gamma"]: s["efficiency"] for s in sweep}

        g0  = eff_by_g.get(0.0,   0.0)
        g25 = eff_by_g.get(0.25,  0.0)
        g50 = eff_by_g.get(0.50,  0.0)
        g75 = eff_by_g.get(0.75,  0.0)
        g100 = eff_by_g.get(1.0,  eff_by_g.get(0.95, 0.0))

        max_eff = max(eff_by_g.values())
        peak_g = max(eff_by_g, key=lambda g: eff_by_g[g])

        # Classify pattern
        if peak_g > 0.05 and peak_g < 0.95:
            pattern = "ENAQT PEAK"
        elif max_eff == g0:
            pattern = "monotone_q"
        elif max_eff == g100:
            pattern = "monotone_c"
        else:
            pattern = "flat/unk"

        row = (f"{name:<15} {result['num_atoms']:>4} "
               f"{g0:>8.4f} {g25:>8.4f} {g50:>8.4f} {g75:>8.4f} {g100:>8.4f} "
               f"{peak_g:>7.2f}  {pattern}")
        print(row)

    # Save
    def make_serializable(obj):
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(v) for v in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj) if isinstance(obj, np.floating) else int(obj)
        return obj

    with open(args.output, "w") as f:
        json.dump(make_serializable(all_results), f, indent=2)
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()

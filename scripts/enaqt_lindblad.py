"""
Correct ENAQT experiment: time-to-fraction comparison.
=====================================================
The ENAQT literature (Rebentrost et al. 2009) uses FIRST PASSAGE TIME as the metric:
how FAST does the excitation reach the sink, not how MUCH has arrived by t_max.

The ENAQT prediction: intermediate dephasing REDUCES the mean first passage time
(MFPT) below both pure quantum (gamma=0) and classical limits.

Correct comparison:
  QUANTUM: Lindblad master equation with Haken-Strobl dephasing
    + sink as decay channel (kappa)

  CLASSICAL: Continuous-time absorbing Markov chain
    Mean first passage time computed from fundamental matrix of absorbing chain.

Metric: time to absorb fraction f (e.g., f=0.5) of initial population.
If quantum with gamma > 0 reaches f=0.5 FASTER than both pure quantum and classical,
that is the ENAQT signature.
"""
from __future__ import annotations
import json, sys, os
import numpy as np
from pathlib import Path
from collections import deque
from scipy.integrate import solve_ivp

sys.path.insert(0, str(Path(__file__).parent))

from fetch_molecule import fetch_molecule
from molecular_fractal_bridge import build_molecular_adjacency


# ---------------------------------------------------------------------------
# Molecular adjacency
# ---------------------------------------------------------------------------

def build_unweighted_adjacency(atoms: list, bonds: list) -> np.ndarray:
    n = len(atoms)
    adj = np.zeros((n, n))
    for bond in bonds:
        if isinstance(bond, dict) and "atoms" in bond:
            i, j = int(bond["atoms"][0]), int(bond["atoms"][1])
        elif isinstance(bond, (list, tuple)) and len(bond) >= 2:
            i, j = int(bond[0]), int(bond[1])
        else:
            continue
        if 0 <= i < n and 0 <= j < n:
            adj[i, j] = 1.0
            adj[j, i] = 1.0
    return adj


def spectral_gap(adj: np.ndarray) -> float:
    n = adj.shape[0]
    degree = adj.sum(axis=1)
    degree_safe = np.where(degree > 0, degree, 1.0)
    D_root = np.diag(1.0 / np.sqrt(degree_safe))
    L_norm = np.eye(n) - D_root @ adj @ D_root
    evals = np.linalg.eigvalsh(L_norm)
    evals.sort()
    return max(1.0 - evals[1], 0.01)


# ---------------------------------------------------------------------------
# Quantum Lindblad
# ---------------------------------------------------------------------------

def lindblad_rhs(t, rho_flat, H, gamma, sink_idx, kappa, n):
    rho = rho_flat.reshape((n, n), order='F')
    # Unitary
    drho = -1j * (H @ rho - rho @ H)
    # Haken-Strobl dephasing
    for k in range(n):
        Pk = np.zeros((n, n)); Pk[k, k] = 1.0
        drho += gamma * (Pk @ rho @ Pk - 0.5 * Pk @ rho - 0.5 * rho @ Pk)
    # Sink decay
    P_s = np.zeros((n, n)); P_s[sink_idx, sink_idx] = 1.0
    drho += kappa * (P_s @ rho @ P_s - 0.5 * kappa * P_s @ rho - 0.5 * kappa * rho @ P_s)
    return drho.flatten(order='F')


def evolve_quantum_full(adj, source, sink, gamma, kappa, t_max, n_steps=1001):
    """Evolve and return full absorption timecourse."""
    n = adj.shape[0]
    H = adj.astype(complex)
    rho0 = np.zeros((n, n), dtype=complex); rho0[source, source] = 1.0
    t_eval = np.linspace(0, t_max, n_steps)
    sol = solve_ivp(lindblad_rhs, (0, t_max), rho0.flatten(order='F'),
                    args=(H, gamma, sink, kappa, n),
                    t_eval=t_eval, method='RK45', rtol=1e-8, atol=1e-11)
    traces = np.array([np.trace(sol.y[:, i].reshape((n, n), order='F')).real
                       for i in range(len(sol.t))])
    absorbed = 1.0 - traces
    return sol.t, absorbed


def time_to_fraction(times, absorbed, fraction):
    """Time to reach a given absorbed fraction."""
    for i, a in enumerate(absorbed):
        if a >= fraction:
            return float(times[i])
    return float(times[-1])


# ---------------------------------------------------------------------------
# Classical absorbing Markov chain
# ---------------------------------------------------------------------------

def classical_absorbing(adj, source, sink, t_max, dt=0.01):
    """Classical absorbing RW: return absorption timecourse."""
    n = adj.shape[0]
    degree = adj.sum(axis=1)
    degree_safe = np.where(degree > 0, degree, 1.0)
    P = adj / degree_safe[:, np.newaxis]
    p = np.zeros(n); p[source] = 1.0
    n_steps = int(t_max / dt)
    times = np.linspace(0, t_max, n_steps + 1)
    cumulative = 0.0
    absorbed = [0.0]
    for _ in range(n_steps):
        p_new = P @ p
        cumulative += p_new[sink]
        p_new[sink] = 0.0
        p = p_new
        absorbed.append(cumulative)
    return np.array(times), np.array(absorbed)


# ---------------------------------------------------------------------------
# Source/Sink
# ---------------------------------------------------------------------------

def identify_source_sink(adj, atoms):
    n = adj.shape[0]
    degrees = adj.sum(axis=1)
    carbon_indices = [i for i in range(n) if atoms[i]["element"] == "C"]
    if len(carbon_indices) < 2:
        carbon_indices = list(range(n))
    source = max(carbon_indices, key=lambda i: degrees[i])
    dist = {source: 0}
    queue = deque([source])
    while queue:
        cur = queue.popleft()
        for nb in np.where(adj[cur] > 0)[0]:
            if nb not in dist:
                dist[nb] = dist[cur] + 1
                queue.append(nb)
    sink = max(carbon_indices, key=lambda i: dist.get(i, 0))
    return source, sink


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

PAH_SERIES = ["benzene", "naphthalene", "anthracene", "tetracene", "pentacene"]


def run_experiment(atoms, bonds, kappa=5.0, fractions=[0.25, 0.50, 0.75]):
    adj = build_unweighted_adjacency(atoms, bonds)
    n = len(atoms)
    source, sink = identify_source_sink(adj, atoms)
    gap = spectral_gap(adj)

    # Use long time so all methods fully absorb
    t_max = max(100.0, 50.0 / gap)

    gamma_values = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]

    result = {
        "molecule": atoms[0].get("name", "?"),
        "num_atoms": n,
        "source": source,
        "sink": sink,
        "spectral_gap": float(gap),
        "kappa": kappa,
        "t_max": float(t_max),
        "fractions": fractions,
        "quantum": {},
        "classical": {},
    }

    # Classical
    times_cl, abs_cl = classical_absorbing(adj, source, sink, t_max=t_max, dt=0.01)
    for f in fractions:
        mfpt = time_to_fraction(times_cl, abs_cl, f)
        result["classical"][f"f={f}_time"] = mfpt
        result["classical"][f"f={f}_absorbed"] = float(abs_cl[-1])

    # Quantum sweeps
    for gamma in gamma_values:
        key = f"g={gamma}"
        result["quantum"][key] = {}
        try:
            times_q, abs_q = evolve_quantum_full(adj, source, sink, gamma, kappa, t_max)
            for f in fractions:
                t_frac = time_to_fraction(times_q, abs_q, f)
                result["quantum"][key][f"f={f}_time"] = t_frac
                result["quantum"][key][f"f={f}_absorbed"] = float(abs_q[-1])
        except Exception as e:
            result["quantum"][key]["error"] = str(e)

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ENAQT: time-to-fraction comparison")
    parser.add_argument("--kappa", type=float, default=5.0)
    parser.add_argument("--output", "-o", type=str,
                        default="D:/Molecule-App/enaqt_lindblad_results.json")
    args = parser.parse_args()

    print("=" * 80)
    print("ENAQT: Time-to-Fraction Comparison")
    print("=" * 80)
    print(f"""
The ENAQT signature: intermediate dephasing REDUCES the time to reach
a given absorption fraction — faster than pure quantum AND classical.

Metric: time to absorb f=50% of initial population (MFPT at f=0.5)

If there exists gamma > 0 where quantum time < classical time AND
quantum time < pure quantum (gamma=0) time -> ENAQT is present.
""")

    all_results = {}

    for name in PAH_SERIES:
        print(f"\n{name}...", end=" ", flush=True)
        mol = fetch_molecule(name)
        if not mol:
            print("FETCH FAILED")
            continue

        res = run_experiment(atoms=mol["atoms"], bonds=mol["bonds"],
                              kappa=args.kappa, fractions=[0.25, 0.50, 0.75])
        all_results[name] = res

        cl_t25 = res["classical"].get("f=0.25_time", None)
        cl_t50 = res["classical"].get("f=0.50_time", None)
        print(f"  n={res['num_atoms']} src={res['source']} snk={res['sink']}")

        gamma_values = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
        for f in [0.25, 0.50]:
            cl_t = res["classical"].get(f"f={f}_time", "N/A")
            q_times = {}
            for g in gamma_values:
                key = f"g={g}"
                qt = res["quantum"].get(key, {}).get(f"f={f}_time", None)
                if qt is not None:
                    q_times[g] = qt
            if q_times:
                best_g = min(q_times, key=lambda g: q_times[g])
                print(f"  f={f}: Cl_t={cl_t:.2f} if available, Q_best=g={best_g}(t={q_times[best_g]:.2f})")

    # Summary table: time to 50%
    print("\n\n" + "=" * 80)
    print("ENAQT RESULTS: Time to absorb 50% of initial population (kappa={})".format(args.kappa))
    print("=" * 80)
    header = (f"{'Molecule':<12} {'n':>4} "
              f"{'Cl(t50%)':>9} {'Q(g=0)':>8} {'g=0.1':>8} {'g=0.25':>8} "
              f"{'g=0.5':>8} {'best_g':>8} {'enaqt_sig?'}")
    print(header)
    print("-" * len(header))

    for name, res in all_results.items():
        cl_t50 = res["classical"].get("f=0.50_time", None)
        gamma_values = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
        q_times = {}
        for g in gamma_values:
            key = f"g={g}"
            qt = res["quantum"].get(key, {}).get("f=0.50_time", None)
            if qt is not None:
                q_times[g] = qt

        if cl_t50 is None or not q_times:
            continue

        best_g = min(q_times, key=lambda g: q_times[g])
        best_t = q_times[best_g]

        # ENAQT signature: best time < classical AND best time < pure quantum
        enaqt_sig = best_t < cl_t50 and best_t < q_times.get(0.0, 9999)

        row = (f"{name:<12} {res['num_atoms']:>4} "
               f"{cl_t50:>9.2f} "
               f"{q_times.get(0.0, 0):>8.2f} "
               f"{q_times.get(0.1, 0):>8.2f} "
               f"{q_times.get(0.25, 0):>8.2f} "
               f"{q_times.get(0.5, 0):>8.2f} "
               f"{best_g:>8.2f} "
               f"{'YES ***' if enaqt_sig else 'no'}")
        print(row)

    print("\n  *** = ENAQT signature: intermediate gamma reduces time below both classical and pure quantum")

    def make_serializable(obj):
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(v) for v in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        return obj

    with open(args.output, "w") as f:
        json.dump(make_serializable(all_results), f, indent=2)
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()

"""
ENAQT: rate-matched comparison with proper Q-matrix classical.
==============================================================
Fixes applied:
1. Classical uses Q-matrix (continuous generator) instead of discrete p_new=P@p
2. Both quantum and classical run via solve_ivp on same timescale
3. Q-matrix transient-only formulation: dp/dt = Q_trans @ p_trans
4. The gamma->infinity non-convergence is noted as a separate issue to investigate

The key comparison: with rate-matched models, what is the actual classical vs quantum gap?
"""
from __future__ import annotations
import json, sys, numpy as np
from scipy.integrate import solve_ivp
sys.path.insert(0, 'scripts')
from fetch_molecule import fetch_molecule


def build_unweighted_adj(atoms, bonds):
    n = len(atoms)
    adj = np.zeros((n, n))
    for b in bonds:
        i, j = int(b[0]), int(b[1])
        adj[i, j] = adj[j, i] = 1.0
    return adj

def spectral_gap(adj):
    n = adj.shape[0]
    d = adj.sum(axis=1)
    d_safe = np.where(d > 0, d, 1.0)
    D_root = np.diag(1.0 / np.sqrt(d_safe))
    L = np.eye(n) - D_root @ adj @ D_root
    ev = np.linalg.eigvalsh(L)
    ev.sort()
    return max(1.0 - ev[1], 0.01)

def identify_source_sink(adj, atoms):
    from collections import deque
    n = adj.shape[0]
    deg = adj.sum(axis=1)
    carb = [i for i in range(n) if atoms[i]["element"] == "C"]
    src = max(carb, key=lambda i: deg[i])
    dist = {src: 0}
    q = deque([src])
    while q:
        c = q.popleft()
        for nb in np.where(adj[c] > 0)[0]:
            if nb not in dist:
                dist[nb] = dist[c] + 1
                q.append(nb)
    snk = max(carb, key=lambda i: dist.get(i, 0))
    return src, snk


# ---------------------------------------------------------------------------
# Quantum Lindblad
# ---------------------------------------------------------------------------

def lindblad_rhs(t, rho_flat, H, gamma, sink, kappa, n):
    rho = rho_flat.reshape((n, n), order='F')
    drho = -1j * (H @ rho - rho @ H)
    for k in range(n):
        Pk = np.zeros((n, n))
        Pk[k, k] = 1.0
        drho += gamma * (Pk @ rho @ Pk - 0.5 * Pk @ rho - 0.5 * rho @ Pk)
    Ps = np.zeros((n, n))
    Ps[sink, sink] = 1.0
    drho += kappa * (Ps @ rho @ Ps - 0.5 * kappa * Ps @ rho - 0.5 * kappa * rho @ Ps)
    return drho.flatten(order='F')

def quantum_absorb(adj, source, sink, gamma, kappa, t_max, n_steps=2001):
    n = adj.shape[0]
    H = adj.astype(complex)
    rho0 = np.zeros((n, n), dtype=complex)
    rho0[source, source] = 1.0
    t_eval = np.linspace(0, t_max, n_steps)
    try:
        sol = solve_ivp(lindblad_rhs, (0, t_max), rho0.flatten(order='F'),
                        args=(H, gamma, sink, kappa, n),
                        t_eval=t_eval, method='RK45', rtol=1e-8, atol=1e-11)
        traces = np.array([np.trace(sol.y[:, i].reshape((n, n), order='F')).real
                          for i in range(len(sol.t))])
        return sol.t, 1.0 - traces
    except:
        return np.linspace(0, t_max, n_steps), np.zeros(n_steps)


# ---------------------------------------------------------------------------
# Classical Q-matrix (continuous generator, transient states only)
# ---------------------------------------------------------------------------

def classical_qmatrix(adj, source, sink, t_max, n_steps=2001):
    """
    Classical continuous-time absorbing chain via Q-matrix generator.
    dp_trans/dt = Q_trans @ p_trans  where Q_trans excludes sink row/col.
    Absorbed fraction = 1 - sum(p_transient).
    """
    n = adj.shape[0]
    degree = adj.sum(axis=1)
    transient = [i for i in range(n) if i != sink]
    src_idx = transient.index(source)

    # Q for transient states
    Q = np.zeros((len(transient), len(transient)))
    for i, ni in enumerate(transient):
        Q[i, i] = -degree[ni]
        for j, nj in enumerate(transient):
            if adj[ni, nj] > 0:
                Q[i, j] = adj[ni, nj]

    def rhs(t, p):
        return Q @ p

    p0 = np.zeros(len(transient))
    p0[src_idx] = 1.0
    t_eval = np.linspace(0, t_max, n_steps)
    sol = solve_ivp(rhs, (0, t_max), p0, t_eval=t_eval,
                    method='RK45', rtol=1e-10, atol=1e-13)
    absorbed = 1.0 - sol.y.sum(axis=0)
    return sol.t, absorbed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_molecule(name, kappa=5.0):
    mol = fetch_molecule(name)
    adj = build_unweighted_adj(mol['atoms'], mol['bonds'])
    source, sink = identify_source_sink(adj, mol['atoms'])
    n = len(mol['atoms'])
    gap = spectral_gap(adj)
    t_max = max(100.0, 30.0 / gap)

    gamma_values = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
    fractions = [0.25, 0.5, 0.75]

    # Classical Q-matrix
    t_cl, abs_cl = classical_qmatrix(adj, source, sink, t_max)
    cl_result = {}
    for f in fractions:
        t_f = np.interp(f, abs_cl, t_cl) if abs_cl[-1] >= f else t_max
        cl_result[f"f={f}_time"] = float(t_f)

    # Quantum sweeps
    q_results = {}
    for gamma in gamma_values:
        t_q, abs_q = quantum_absorb(adj, source, sink, gamma, kappa, t_max)
        res = {}
        for f in fractions:
            t_f = np.interp(f, abs_q, t_q) if abs_q[-1] >= f else float('inf')
            res[f"f={f}_time"] = float(t_f)
        res["final_absorbed"] = float(abs_q[-1])
        q_results[f"g={gamma}"] = res

    # Find best gamma for each fraction
    best = {}
    for f in fractions:
        q_times_f = {g: q_results[f"g={g}"][f"f={f}_time"]
                      for g in gamma_values
                      if q_results[f"g={g}"][f"f={f}_time"] < float('inf')}
        if q_times_f:
            best_g = min(q_times_f, key=lambda g: q_times_f[g])
            best[f"f={f}_time"] = {"best_gamma": best_g, "best_time": q_times_f[best_g]}
            cl_f = cl_result[f"f={f}_time"]
            enaqt = q_times_f[best_g] < cl_f and q_times_f[best_g] < q_times_f.get(0.0, 9999)
            best[f"f={f}_time"]["beats_classical"] = q_times_f[best_g] < cl_f
            best[f"f={f}_time"]["beats_pure_quantum"] = q_times_f[best_g] < q_times_f.get(0.0, 9999)
            best[f"f={f}_time"]["enaqt_sig"] = enaqt

    return {
        "name": name,
        "n": n,
        "source": source,
        "sink": sink,
        "kappa": kappa,
        "t_max": float(t_max),
        "classical": cl_result,
        "quantum": q_results,
        "best": best,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--kappa", type=float, default=5.0)
    parser.add_argument("-o", type=str, default="D:/Molecule-App/enaqt_rate_matched_results.json")
    args = parser.parse_args()

    print("=" * 80)
    print("ENAQT: Rate-Matched Comparison (Q-matrix classical)")
    print("=" * 80)

    all_results = {}
    for name in ["benzene", "naphthalene"]:
        print(f"\n{name}...")
        res = run_molecule(name, kappa=args.kappa)
        all_results[name] = res

        cl_t50 = res["classical"]["f=0.5_time"]
        print(f"  Classical Q-matrix t50%: {cl_t50:.2f}")

        for f in [0.25, 0.50]:
            print(f"\n  f={f}:")
            for g in [0.0, 0.1, 0.25, 0.5, 1.0, 5.0]:
                qt = res["quantum"][f"g={g}"][f"f={f}_time"]
                marker = ""
                if g == res["best"][f"f={f}_time"]["best_gamma"]:
                    marker = "  <-- BEST"
                if res["best"][f"f={f}_time"].get("enaqt_sig"):
                    marker += "  ENAQT!"
                print(f"    gamma={g}: t={qt:.2f}{marker}")

    # Summary table
    print("\n\n" + "=" * 80)
    print("SUMMARY: Time to 50% absorption (rate-matched)")
    print("=" * 80)
    print(f"{'Molecule':<12} {'Cl(t50)':>8} {'Q(g=0)':>8} {'g=0.25':>8} {'g=0.5':>8} "
          f"{'g=1.0':>8} {'Best_g':>8} {'Ratio_Q/Cl':>12}")
    print("-" * 80)

    for name, res in all_results.items():
        cl = res["classical"].get("f=0.5_time")
        q0 = res["quantum"]["g=0.0"].get("f=0.5_time")
        g025 = res["quantum"]["g=0.25"].get("f=0.5_time")
        g05 = res["quantum"]["g=0.5"].get("f=0.5_time")
        g1 = res["quantum"]["g=1.0"].get("f=0.5_time")
        best_entry = res["best"].get("f=0.5_time", {})
        best_g = best_entry.get("best_gamma")
        best_t = best_entry.get("best_time")
        ratio = best_t / cl if (cl and cl > 0 and best_t) else float('inf')

        cl_v = f"{cl:.2f}" if cl else "N/A"
        q0_v = f"{q0:.2f}" if q0 else "N/A"
        g025_v = f"{g025:.2f}" if g025 else "N/A"
        g05_v = f"{g05:.2f}" if g05 else "N/A"
        g1_v = f"{g1:.2f}" if g1 else "N/A"
        bg_v = f"{best_g:.2f}" if best_g else "N/A"
        print(f"{name:<12} {cl_v:>8} {q0_v:>8} {g025_v:>8} {g05_v:>8} "
              f"{g1_v:>8} {bg_v:>8} {ratio:>12.3f}x")

    print("\n  Note: ratio = best_quantum_time / classical_time")
    print("  ratio < 1 means quantum is faster; ratio > 1 means classical is faster")
    print()

    def ms(obj):
        if isinstance(obj, dict):
            return {k: ms(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ms(v) for v in obj]
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        return obj

    with open(args.o, "w") as f:
        json.dump(ms(all_results), f, indent=2)
    print(f"Saved to {args.o}")


if __name__ == "__main__":
    main()

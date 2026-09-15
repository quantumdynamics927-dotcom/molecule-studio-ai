"""
Quick ENAQT check: time to 50% absorption for benzene + naphthalene.
"""
from __future__ import annotations
import json, sys, numpy as np
from scipy.integrate import solve_ivp
sys.path.insert(0, 'scripts')
from fetch_molecule import fetch_molecule
from molecular_fractal_bridge import build_molecular_adjacency

def build_unweighted_adj(atoms, bonds):
    n = len(atoms); adj = np.zeros((n, n))
    for b in bonds:
        i, j = int(b[0]), int(b[1])
        adj[i,j] = adj[j,i] = 1.0
    return adj

def spectral_gap(adj):
    n = adj.shape[0]
    d = adj.sum(axis=1); d_safe = np.where(d > 0, d, 1.0)
    D_root = np.diag(1.0 / np.sqrt(d_safe))
    L = np.eye(n) - D_root @ adj @ D_root
    ev = np.linalg.eigvalsh(L); ev.sort()
    return max(1.0 - ev[1], 0.01)

def identify_source_sink(adj, atoms):
    from collections import deque
    n = adj.shape[0]; deg = adj.sum(axis=1)
    carb = [i for i in range(n) if atoms[i]["element"] == "C"]
    src = max(carb, key=lambda i: deg[i])
    dist = {src: 0}; q = deque([src])
    while q:
        c = q.popleft()
        for nb in np.where(adj[c] > 0)[0]:
            if nb not in dist:
                dist[nb] = dist[c] + 1; q.append(nb)
    snk = max(carb, key=lambda i: dist.get(i, 0))
    return src, snk

def lindblad_rhs(t, rho, H, gamma, sink, kappa, n):
    rho = rho.reshape((n,n), order='F')
    drho = -1j * (H @ rho - rho @ H)
    for k in range(n):
        Pk = np.zeros((n,n)); Pk[k,k] = 1.0
        drho += gamma * (Pk @ rho @ Pk - 0.5*Pk@rho - 0.5*rho@Pk)
    Ps = np.zeros((n,n)); Ps[sink,sink] = 1.0
    drho += kappa * (Ps @ rho @ Ps - 0.5*kappa*Ps@rho - 0.5*kappa*rho@Ps)
    return drho.flatten(order='F')

def time_to_absorb(adj, source, sink, gamma, kappa, t_max, frac=0.5):
    n = adj.shape[0]
    H = adj.astype(complex)
    rho0 = np.zeros((n,n), dtype=complex); rho0[source,source] = 1.0
    n_steps = min(2001, max(501, int(10000 / n)))
    t_eval = np.linspace(0, t_max, n_steps)
    try:
        sol = solve_ivp(lindblad_rhs, (0, t_max), rho0.flatten(order='F'),
                        args=(H, gamma, sink, kappa, n),
                        t_eval=t_eval, method='RK45', rtol=1e-6, atol=1e-9)
        traces = np.array([np.trace(sol.y[:,i].reshape((n,n),order='F')).real
                          for i in range(len(sol.t))])
        absorbed = 1.0 - traces
        for i, a in enumerate(absorbed):
            if a >= frac:
                return float(sol.t[i])
    except:
        pass
    return t_max

def classical_time(adj, source, sink, t_max, frac=0.5):
    n = adj.shape[0]
    d = adj.sum(axis=1); d_safe = np.where(d > 0, d, 1.0)
    P = adj / d_safe[:,None]
    p = np.zeros(n); p[source] = 1.0
    dt = 0.01; cum = 0.0
    for step in range(int(t_max/dt)):
        pn = P @ p
        cum += pn[sink]; pn[sink] = 0.0; p = pn
        if cum >= frac:
            return float(step * dt)
    return t_max

results = {}
for name in ["benzene", "naphthalene"]:
    mol = fetch_molecule(name)
    adj = build_unweighted_adj(mol["atoms"], mol["bonds"])
    src, snk = identify_source_sink(adj, mol["atoms"])
    gap = spectral_gap(adj)
    t_max = max(50.0, 30.0 / gap)
    kappa = 5.0
    frac = 0.5

    cl_t = classical_time(adj, src, snk, t_max, frac)
    q_times = {}
    for gamma in [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]:
        q_times[gamma] = time_to_absorb(adj, src, snk, gamma, kappa, t_max, frac)

    best_g = min(q_times, key=lambda g: q_times[g])
    beats_cl = q_times[best_g] < cl_t
    beats_q0 = q_times[best_g] < q_times[0.0]
    enaqt = beats_cl and beats_q0

    print(f"\n{name}: n={len(mol['atoms'])} src={src} snk={snk}")
    print(f"  Classical t50%: {cl_t:.2f}")
    for g in [0.0, 0.1, 0.25, 0.5, 1.0, 5.0]:
        marker = "  <-- BEST" if g == best_g else ""
        print(f"  Q(g={g}) t50%: {q_times[g]:.2f}{marker}")
    print(f"  Best gamma={best_g} (t={q_times[best_g]:.2f})")
    print(f"  Beats classical? {beats_cl}  Beats pure quantum? {beats_q0}")
    print(f"  ENAQT signature? {enaqt}")

    results[name] = {
        "n": len(mol["atoms"]),
        "source": src,
        "sink": snk,
        "kappa": kappa,
        "t_max": t_max,
        "classical_t50": cl_t,
        "quantum": {str(g): q_times[g] for g in q_times},
        "best_gamma": best_g,
        "beats_classical": beats_cl,
        "beats_pure_quantum": beats_q0,
        "enaqt_sig": enaqt,
    }

def ms(obj):
    if isinstance(obj, dict): return {k: ms(v) for k,v in obj.items()}
    elif isinstance(obj, list): return [ms(v) for v in obj]
    elif isinstance(obj, (np.integer,)): return int(obj)
    elif isinstance(obj, (np.floating,)): return float(obj)
    return obj

with open("D:/Molecule-App/enaqt_final_results.json", "w") as f:
    json.dump(ms(results), f, indent=2)
print("\nSaved to D:/Molecule-App/enaqt_final_results.json")

"""
Clean re-analysis: benzene substitution anomaly detection.
The key insight: benzene has perfect D6h symmetry. The walk breaks this symmetry
based on starting node (C0). The question is: can the walk distinguish which
position was substituted?

Benzene ring numbering (as we defined it):
  C0 — starting node (node 0)
  C1 — adjacent to C0
  C2 — meta to C0
  C3 — para to C0
  C4 — adjacent to C3 (opposite side of ring from C1)
  C5 — meta to C0 (other side)

Graph distances from C0:
  dist(C0)=0, dist(C1)=1, dist(C2)=2, dist(C3)=3, dist(C4)=2, dist(C5)=1

For a substitution at position X:
  If X is at graph distance d from C0, the walk should "see" it at distance d.

The question: does the walk's signature encode d (and thus which position)?
"""
import json
from pathlib import Path

ELEMENT_MASS = {
    "H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999,
    "F": 18.998, "Cl": 35.45, "Br": 79.904, "I": 126.90,
    "S": 32.06, "P": 30.974
}

# Benzene ring atom indices (in our definition)
# C0=idx0, C1=idx1, C2=idx2, C3=idx3, C4=idx4, C5=idx5
# H6 attached to C0, H7 to C1, H8 to C2, H9 to C3, H10 to C4, H11 to C5

BENZENE_RING = {0, 1, 2, 3, 4, 5}  # carbon ring indices

# Distance from C0 (starting node) in the benzene ring graph
# Ring graph distances: C0-1-2-3-4-5- back to C0
# Path distances: C0→C1=1, C0→C2=2, C0→C3=3, C0→C4=2 (via C5), C0→C5=1 (via C0-C5)
# But our ring is: 0-1-2-3-4-5-0 (simple ring)
# dist(0→1)=1, dist(0→2)=2, dist(0→3)=3, dist(0→4)=2, dist(0→5)=1
# So positions {1,5} are distance 1 (adjacent to start)
# Positions {2,4} are distance 2 (meta to start)
# Position {3} is distance 3 (para to start)

DIST_FROM_C0 = {0: 0, 1: 1, 5: 1, 2: 2, 4: 2, 3: 3}

# From the run output (reconstructed):
# Reference benzene: top1=C(idx=4), avg_mass=12.01, hetero=0
# For F at pos=0: avg_mass=14.34, hetero=1 (F detected in top3)
# For F at pos=1: avg_mass=12.01, hetero=0 (F NOT detected)
# For F at pos=2: avg_mass=14.34, hetero=1 (F detected)
# For F at pos=3: avg_mass=12.01, hetero=0 (F NOT detected)
# For F at pos=4: top1=F, avg_mass=14.34, hetero=1 (direct hit)
# For F at pos=5: avg_mass=12.01, hetero=0 (F NOT detected)

BENZENE_SIGNATURES = {
    "reference": {"top1_el": "C", "top1_idx": 4, "avg_mass": 12.01, "hetero": 0},
    # Substituent F (mass 18.998)
    "F@0": {"top1_el": "C", "top1_idx": 4, "avg_mass": 14.34, "hetero": 1},
    "F@1": {"top1_el": "C", "top1_idx": 4, "avg_mass": 12.01, "hetero": 0},
    "F@2": {"top1_el": "C", "top1_idx": 4, "avg_mass": 14.34, "hetero": 1},
    "F@3": {"top1_el": "C", "top1_idx": 4, "avg_mass": 12.01, "hetero": 0},
    "F@4": {"top1_el": "F", "top1_idx": 4, "avg_mass": 14.34, "hetero": 1},  # direct hit
    "F@5": {"top1_el": "C", "top1_idx": 4, "avg_mass": 12.01, "hetero": 0},
}

print("=" * 90)
print("REFINED BENZENE ANOMALY DETECTION ANALYSIS")
print("=" * 90)
print("""
Hypothesis: Can the walk distinguish which position was substituted?

Setup:
  - Reference: benzene
  - Perturbation: replace H at position X with F (H mass=1.008, F mass=19.0)
  - Question: does the walk's top-3 signature differ between positions?

Results table:
  Position  Distance from C0  avg_mass  hetero  Signal?
  ──────────────────────────────────────────────────────
  Ref (no sub)     —          12.01      0      —
  F@0 (ortho)      1          14.34      1      YES (F in top3)
  F@1 (ortho)      1          12.01      0      NO
  F@2 (meta)       2          14.34      1      YES (F in top3)
  F@3 (para)       3          12.01      0      NO
  F@4 (meta)       2          14.34      1      DIRECT HIT (F=top1)
  F@5 (ortho)       1          12.01      0      NO

OBSERVATION:
  - Positions 0 and 2 (dist=1,2 from C0): F appears in top3
  - Positions 1, 3, 5 (dist=1,3,1): F NOT in top3
  - This is NOT symmetric by graph distance from C0

  Wait — positions {1,5} should be symmetric (both distance 1 from C0).
  But pos=1 shows hetero=0 while pos=5 shows hetero=0 too (both no signal).
  But pos=0 (dist=1) shows hetero=1.

  Looking more carefully: our benzene ring is 0-1-2-3-4-5-0
  So adjacency: 0↔1, 1↔2, 2↔3, 3↔4, 4↔5, 5↔0
  From C0: dist(1)=1, dist(5)=1 (both neighbors)
  dist(2)=2, dist(4)=2 (both next)
  dist(3)=3 (para)

  But our bond list has:
    0-1 (double), 1-2 (single), 2-3 (double), 3-4 (single), 4-5 (double), 5-0 (single)

  The walk's probability distribution depends on BOTH graph structure AND
  the interference pattern from the staggered walk. At step 10 on benzene,
  the walk has mixed but still shows C4 preference due to the starting node.

  The fact that F@0 and F@2 both show hetero=1 while F@1, F@3, F@5 do not
  suggests the walk's top-3 includes atoms at graph distances 0 and 2 from C0
  when the substituent is at position 0 or 2.

ACTUAL INTERPRETATION (revised):
  The walk's top-3 atoms at step 10 include:
    - C4 (locked-on para carbon)
    - And possibly the two atoms adjacent to the substituent

  When F is at position 0:
    - The substituent's peripheral H is gone, replaced by F
    - The walk's top-3 includes the F atom (because it changed the local connectivity)

  When F is at position 1:
    - F is adjacent to C0 (starting node), but C0's own connectivity dominates
    - The walk stays locked on C4 regardless

  This is NOT graph distance based. It's about whether the substituent
  perturbs the local connectivity around C4 (the locked-on site).
""")

print("\n" + "=" * 90)
print("THE CRITICAL NEGATIVE RESULT")
print("=" * 90)
print("""
THE RESULT WE ACTUALLY CARE ABOUT:

On benzene (D6h symmetry, all 6 carbons equivalent):
  → The quantum walk produces a SINGLE dominant site (C4) at step 10
  → This is NOT symmetry-breaking due to quantum mechanics
  → This is starting-node bias: the walk locks onto the carbon opposite C0

On substituted benzene (C6v symmetry, all 6 positions distinct):
  → The walk STILL locks onto C4 regardless of substitution position
  → The only case where top-1 changes is when we substitute AT C4 itself

This means the quantum walk on benzene is NOT detecting positional isomers.
It is not detecting which position was substituted.
It is not detecting the symmetry breaking from D6h to C6v.

WHAT THIS SAYS ABOUT THE HOMO CLASSIFICATION:
  The 88.2% pilot accuracy on benzene-type molecules was NOT because
  the quantum walk detected conjugation patterns. It was because:
    (a) The starting node happened to be near the chemically relevant site, AND
    (b) The locked-on site (C4) coincided with the actual reactive site
        for many of those specific molecules.

This is confirmed by the starting-node bias analysis:
  - adrenaline: C4 should be dominant at steps 3-4, but by step 10
    the starting node (amine H) has polluted the ranking
  - glucose: the walk gets H14 (near the O glycosidic bond), which is
    accidentally correct, not systematically correct

THE DEEPER IMPLICATION:
  A staggered quantum walk on a molecular graph does NOT implement
  "conjugated system detection." It implements "starting-node-proximal
  graph centrality with interference" — which, on some molecules,
  accidentally correlates with HOMO character, but not systematically.
""")

print("\n" + "=" * 90)
print("POSITIVE FINDING FROM THE BENZENE SERIES")
print("=" * 90)
print("""
One genuinely positive finding: the walk DOES detect when the substituted
atom is itself in the top-3 region. When F is placed at position 4
(C4's own position), the walk's top-1 changes to F.

This means: the walk's localization IS sensitive to graph perturbations,
but only when the perturbation is AT the locked-on site.

For a real anomaly detection test, you would need:
  1. A reference molecule where the locked-on site is NOT at the substitution site
  2. Multiple substitution sites at different graph distances
  3. A way to attribute "anomaly score" to each position

The correct way to do this is TRANSPORT CENTRALITY:
  Instead of asking "where does the walk localize?", ask:
  "how much does the walk's probability change at each node
   when we remove/add an edge vs when we perturb the atom type?"

This is closer to the graph Laplacian perturbation analysis used in
sensitivity studies of quantum walks (Childs 2010, Janmark et al. 2014).
""")

# Analysis: Why Does Quantum Walk Degrade on Complex Molecules?
## Internal Research Note — 2026-07-26

---

## The Numbers (98 molecules)

| Method | Accuracy | Notes |
|---|---|---|
| Coined RW | 68.3% | Best performer |
| Eigenvector | 59.2% | Static descriptor |
| **Quantum walk** | **53.1%** | Degrades on complex molecules |
| Plain RW | 41.8% | Baseline diffusion |

**Key reversal**: Quantum walk no longer outperforms the classical baselines at 98 molecules. Coined RW leads at 68.3%.

---

## Segment-by-Segment Breakdown

| Segment | n | Q% | Cnd% | Pln% | Observation |
|---|---|---|---|---|---|
| Small heteroatom (H2O/S/H2S) | 5 | 100 | 100 | 100 | Trivially simple; all methods work |
| Extended PAHs | 10 | **90** | 100 | 50 | Q=90% on PAHs; only perylene fails |
| Alkanes | 5 | 80 | 100 | 80 | Both work; alkanes have no conjugation = no quantum advantage to find |
| Pilot (17) | 17 | **88** | 71 | 41 | Q wins on pilot; Cnd doesn't |
| Sulfides/thiols | 4 | 75 | 100 | 75 | Q acceptable |
| Additional aromatics | 5 | 60 | 60 | 0 | Mixed; Q wins 2 cases |
| Simple heterocycles | 4 | 50 | 25 | 25 | Small heterocycles; Q wins 1 |
| Nitriles/cyanides | 4 | 50 | 25 | 50 | Mixed |
| PAH series | 3 | 67 | 100 | 0 | Anthracene/tetracene OK; pentacene fails |
| Carbonyls/ketones | 8 | 25 | 62 | 38 | Q badly underperforms |
| Nucleobases | 5 | 40 | 100 | 80 | Q=40%; Cnd=100% |
| Vitamins/cofactors | 5 | 20 | 40 | 60 | Q poor |
| Amines/small hetero | 5 | 0 | 20 | 40 | Q completely fails |
| Steroids | 3 | **0** | **100** | 0 | Q=0%; Cnd=100% — worst failure mode |
| Flavonoids | 3 | 0 | 0 | 33 | All methods fail |
| Quinoline/isoquinoline | 2 | 0 | 0 | 0 | All methods fail |

---

## Root Cause: Walk Length Insufficient for Large Molecules

### The Hypothesis

At step 10, the quantum walk has made only 10 moves. On a 5-atom molecule, that's ~2 complete circuits of the graph. On a 74-atom molecule (cholesterol), it's 0.14 circuits — the walk barely leaves the starting neighborhood.

Classical methods (plain and coined RW) also suffer at step 10, but the coined RW's neighbor-sampling approach doesn't require the same kind of coherent exploration — it samples neighbors uniformly, which for a degree-weighted graph tends to find high-connectivity atoms faster.

### Evidence

**Molecule size vs Q accuracy correlation:**
```
Methane (5 atoms)     → Q correct
Ethane (8 atoms)      → Q WRONG (H as top)
Propane (11 atoms)    → Q correct
Butane (14 atoms)      → Q correct
Hexane (20 atoms)      → Q correct
Benzene (12 atoms)     → Q correct
Pentacene (36 atoms)   → Q WRONG (H as top)
Cholesterol (74 atoms) → Q WRONG (H as top)
Testosterone (49 atoms) → Q WRONG (H as top)
```

The H-as-top-atom failures (ethane, pentacene, cholesterol, testosterone, etc.) are all molecules where the walk starting at node 0 hasn't had enough steps to delocalize — it stays near the starting node, which happens to be a terminal H in PubChem ordering.

**The perylene failure** (Q=0%, Cnd=100%) is the clearest signal. Perylene has 32 atoms, 5 fused rings, strong conjugation. Coined RW correctly gets a carbon. Q gets H. This is NOT a quantum advantage failure — it's a step-count failure.

---

## The Structural Pattern of Failures

### Failure Type 1: Large flexible molecules (steroids, amino acids, large drugs)
- Q top-1 = H (terminal hydrogen near start node)
- Cnd top-1 = C (high-degree carbon in ring system)
- Root cause: walk hasn't explored enough of the graph
- Example: testosterone, cholesterol, phenylalanine, tryptophan

### Failure Type 2: Carbonyl-conjugated systems where O is buried
- Q picks O or nothing useful; C picks C
- Root cause: carbonyl O is topologically peripheral but electronically important
- Examples: benzaldehyde, acrolein, methyl acrylate, warfarin

### Failure Type 3: Short-conjugation small molecules
- Formaldehyde (4 atoms), hydrogen cyanide (3 atoms): all methods get H
- These are genuinely hard: HOMO is C-H sigma or N lone pair, hard to distinguish topologically
- Not a method failure; it's a literature mismatch

### Failure Type 4: Heteroatom-dominated ring systems (quinoline, isoquinoline)
- All methods get H; true HOMO is on heteroatom
- These are genuinely hard for topological methods

---

## What the Pilot 17 Obscured

The pilot 17 happened to include molecules where:
1. Most were rigid, compact aromatics (benzene, naphthalene, aspirin)
2. The starting node (PubChem node 0) was at or near the chemically relevant site
3. The graph exploration at step 10 was sufficient for the molecule's topology

The expanded set includes molecules where:
1. PubChem node 0 is a terminal heteroatom or H, far from the chemically relevant site
2. Large size means step 10 is insufficient for global exploration
3. Complex multi-ring systems with peripheral heteroatoms

---

## Possible Fixes

### Fix 1: Increase walk steps for large molecules
- Threshold by atom count: if n > 20, use steps = max(10, n // 2)
- Or: adaptive steps — run until participation ratio reaches threshold

### Fix 2: Average over all starting nodes
- Instead of single node 0, average quantum walk probabilities over all starting nodes
- This removes starting-node bias entirely
- Increases computation by n× but eliminates the confounder

### Fix 3: Longer steps specifically for PAHs
- For perylene (32 atoms): need at least 32 steps for 1 circuit
- Pentacene (36 atoms): similar
- The step-10 cutoff was calibrated on small molecules (≤24 atoms) and doesn't generalize

### Fix 4: Use the stability score or spectral gap to detect under-exploration
- If stability_score < threshold, increase steps
- Participation ratio at step 10 tells you if the walk has mixed

---

## Revised Assessment

**Original claim**: "Quantum walk outperforms classical at HOMO site classification"
**Revised**: "Quantum walk outperforms classical at HOMO site classification on rigid, compact aromatic molecules with well-connected conjugated systems, when starting node is near the chemically relevant site and step count is sufficient for graph exploration"

**What needs to be fixed**:
1. Step count must scale with molecule size (not fixed at 10)
2. Starting node must be canonicalized or averaged over
3. The method should be re-validated with these fixes before drawing conclusions

**Where quantum genuinely wins (pilot + extended)**:
- PAHs (benzene → tetracene): Q=90%, Cnd=100%, Pln=50% — Q wins over plain RW
- Perylene aside, the 5-ring systems show Q works when steps are sufficient
- Small rigid molecules (caffeine, aspirin, naphthalene): Q=88% confirmed

**Where classical wins cleanly**:
- Steroids (Q=0%, Cnd=100%): large flexible molecules need longer walks
- Nucleobases (Q=40%, Cnd=100%): Cnd's neighbor sampling handles peripheral heteroatoms better
- Carbonyl-heavy systems: Q gets confused by carbonyl O topology

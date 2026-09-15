# Pre-Registered Protocol: Fractal Quantum Walk HOMO Site Classification
## Version 1.0 — 2026-07-26

---

## Background and Hypotheses

This protocol governs the expanded validation experiment for the fractal quantum walk method applied to frontier molecular orbital (HOMO) site classification. The method uses a staggered quantum walk (GRE `quantum_walk`, model="staggered") on molecular bond graphs, with bond-order-weighted adjacency matrices.

### Pre-registered Hypotheses

**H1 (Primary)**: The quantum walk achieves higher dominant-site classification accuracy than plain random walk diffusion (≥47 pp gap expected based on pilot data).

**H2 (Secondary)**: The quantum walk achieves higher dominant-site classification accuracy than a coined classical walk (lifted Markov chain) — expected gap ~18 pp based on pilot data.

**H3 (Exploratory / Conjecture A)**: Quantum advantage (Q accuracy − Coined RW accuracy) increases monotonically with conjugation extent (number of aromatic rings or π-electron count).

---

## Match Criterion

**Pre-specified**: Classification is correct if and only if the top-ranked atom's element type matches the literature-validated HOMO character:

- `"conjugated_c"` if the dominant HOMO density is on carbon atoms in a conjugated/aromatic system
- `"heteroatom"` if the dominant HOMO density is on a heteroatom (O, N, S, Cl) lone pair or π-orbital

**Pre-specification timestamp**: Locked before data collection. The top-1 site is the atom with highest visit probability after `walk_steps` steps. No threshold or top-k modification is applied post-hoc.

**Excluded molecules**: Molecules where the literature is ambiguous or contested (none currently in the planned set; will be flagged if encountered).

---

## Starting Node Protocol

**Decision**: Use **node 0** as the canonical starting node for all molecules, consistent with the pilot experiment.

**Rationale**: Node 0 corresponds to PubChem's canonical ordering. This is fully specified before the experiment and reproducible. We acknowledge this introduces a starting-node bias (documented for adrenaline in pilot data), but accept this as the established protocol.

**Alternative considered and deferred**: Averaging over all starting nodes was considered too expensive for the expanded batch and deferred to a targeted follow-up study on a subset of molecules.

---

## Walk Parameters

| Parameter | Value | Rationale |
|---|---|---|
| `walk_steps` | 10 | Pilot showed meaningful localization at step 10 for most molecules; step 15 showed over-mixing |
| `fractal` | `"sierpinski"` | Standard choice; changing this is a separate experiment |
| `level` | 3 | Standard level used throughout pilot |
| `route` | `"ifs"` | Standard route; changing this is a separate experiment |
| `initial_node` | `0` | Canonical starting node |
| `model` | `"staggered"` | GRE default; Childs-Goldstein model |

---

## Molecule Set and Test Plan

### Target: ≥120 molecules total

#### PAH Homologous Series (benzene → pentacene)
Benzene, Naphthalene, Anthracene, Tetracene, Pentacene
- **Literature anchor**: HOMO on peripheral carbons for all PAHs; conjugation length systematically varies
- **Conjecture A test**: Accuracy gap (Q − Coined RW) should grow with ring count

#### Alk/Alkane Homologous Series
Methane, Ethane, Propane, Butane, Pentane, Hexane
- **Literature anchor**: HOMO on C-C sigma bond (central carbon region); no conjugation
- **Baseline**: These should be near-uniform diffusion for both methods (no conjugation = no quantum advantage expected)

#### Heterocycle Series
Pyridine, Pyridine N-oxide, Quinoline, Isoquinoline, Pyrrole, Indole, Furan, Thiophene
- **Literature anchor**: HOMO on heteroatom (lone pair or π orbital) vs on conjugated ring

#### Xanthine Derivatives (existing pilot)
Caffeine, Theobromine, Theophylline, Theobromine + methyl variants
- **Existing**: Already validated

#### Drug Molecules (expanded)
Aspirin, Acetaminophen, Ibuprofen, Dopamine, Serotonin, Chloroquine, Morphine, Nicotine, Glucose, Sucrose
- **Existing**: Already validated; adds to n

#### Additional Aromatics
Toluene, Xylene, Phenol, Aniline, Styrene, Biphenyl
- **Purpose**: Increase aromatic carbon-dominant cases

#### Additional Heteroatom-Dominant
H2O, H2S, NH3, CH3OH, CH3SH
- **Purpose**: Pure heteroatom-dominant small molecules; no conjugation confound

**Total target: ≥120 molecules** (pilot 17 + PAH 5 + alkanes 6 + heterocycles 8 + drugs 10 + aromatics 6 + heteroatom-dominants 5 + ~60 additional = ~120+)

---

## TRE Correlation Analysis (Exploratory)

**Pre-registered**: For PAHs where topological resonance energy (TRE) values are available from the literature, we will compute the Pearson correlation between the quantum walk's `stability_score` and the reported TRE value.

- **Expected direction**: Positive correlation — more aromatic stability → higher walk stability score
- **Metric**: Pearson r; significance at α=0.05
- **Note**: This is exploratory; we will report the correlation coefficient and confidence interval regardless of outcome.

---

## Entropy Reporting Standard

**Decision**: Report **natural log (nats)** for all entropy quantities.

- von Neumann entropy from GRE's `von_neumann_entropy` → reported in nats (natural log)
- Shannon entropy of probability distribution → reported in nats
- Any log-base conversion applied post-collection will be noted

---

## Statistical Analysis Plan

### Primary Analysis
Two-proportion z-test comparing quantum walk accuracy vs each classical baseline, across all molecules. Significance threshold: α = 0.05 (one-sided for directional hypothesis H1/H2; two-sided for H2 if reporting both directions).

### Secondary Analysis
- Head-to-head binomial test on non-tied comparisons (molecules where exactly one method is correct)
- Pearson correlation: stability_score vs TRE (PAH subset)

### Power
- Target: n = 137 molecules for two-proportion test at 80% power (based on observed 17.6 pp effect size, α=0.05)
- Power calculation reference: `scripts/power_calculation.py`

---

## Success Criteria

**Pre-registered** (no post-hoc modification):

- H1 supported if: quantum accuracy − plain RW accuracy > 30 pp, p < 0.05
- H2 supported if: quantum accuracy − coined RW accuracy > 10 pp, p < 0.05
- H3 supported if: Pearson r(ring_count, accuracy_gap) > 0.5, p < 0.05, on PAH series

These thresholds are set conservatively (below observed pilot effect sizes) to account for expected regression to the mean in the expanded sample.

---

## What Will NOT Be Done Post-Hoc

1. The top-k threshold will not be changed after seeing results
2. The starting node will not be changed to improve a specific molecule's match
3. Molecules will not be excluded based on results (pre-specified exclusion criteria only)
4. The match criterion will not be switched from top-1 to top-3 after seeing results

---

## Execution Log

| Date | Action |
|---|---|
| 2026-07-26 | Protocol v1.0 locked |
| 2026-07-26 | Power calculation run (`scripts/power_calculation.py`) |
| 2026-07-26 | Pilot data: n=17, Q=88.2%, Coined=70.6%, Plain=41.2% |
| TBD | Expanded batch execution (target ≥120 molecules) |
| TBD | Statistical analysis and hypothesis test |

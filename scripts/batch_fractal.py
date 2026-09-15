"""
Batch fractal quantum walk analysis across multiple molecules.
Fetches each molecule from PubChem, runs the walk, and produces
a comparison scorecard.

Usage:
    python batch_fractal.py "Caffeine, Aspirin, Adrenaline, Benzene, Glucose"
    python batch_fractal.py --list --  # reads from stdin
"""

from __future__ import annotations

import json
import sys
import time
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

# ---------------------------------------------------------------------------
# Add scripts dir to path
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))

from fetch_molecule import fetch_molecule
from molecular_fractal_bridge import run_fractal_analysis, MoleculeInput


# ---------------------------------------------------------------------------
# Molecule list — diverse chemical classes for rigorous testing
# ---------------------------------------------------------------------------
BATCH_MOLECULES = [
    # --- Aromatic / heterocyclic ---
    "caffeine",        # fused heterocycles — already done
    "theobromine",     # caffeine relative, methylxanthine
    "theophylline",    # another methylxanthine
    # --- Benzene derivatives ---
    "aspirin",         # benzene + ester/carboxylic acid — already done
    "acetaminophen",    # analgesic, amide on benzene
    "benzene",         # pure aromatic — symmetry control
    "naphthalene",     # fused PAH
    # --- Catecholamines ---
    "adrenaline",      # catechol + amine — already done
    "dopamine",        # simpler catecholamine
    "serotonin",       # indole + hydroxyl
    # --- Sugars / aliphatic ---
    "glucose",         # aliphatic, ring
    "sucrose",         # disaccharide
    # --- Drug-like ---
    "chloroquine",     # quinoline-based antimalarial
    "morphine",        # complex alkaloid
    "nicotine",        # pyridine + pyrrolidine
    # --- Small / control ---
    "methane",         # simplest alkane
    "ethene",          # double bond control
]


@dataclass
class MoleculeResult:
    name: str
    formula: str
    num_atoms: int
    num_bonds: int
    walk_steps: int
    position_entropy: float
    shannon_entropy: float
    von_neumann_entropy: float
    participation_ratio: float
    stability_score: float
    top_site_1: tuple[str, int, float]   # (element, index, probability)
    top_site_2: tuple[str, int, float]
    top_site_3: tuple[str, int, float]
    has_c4_in_top3: bool               # Does C4 appear in top 3?
    error: str | None


def run_molecule(
    name: str,
    walk_steps: int = 10,
    initial_node: int = 0,
) -> MoleculeResult:
    """Fetch and analyze a single molecule."""
    print(f"  Fetching {name}...", end=" ", flush=True)
    try:
        raw = fetch_molecule(name)
        if raw is None:
            return MoleculeResult(name=name, formula="?", num_atoms=0, num_bonds=0,
                                 walk_steps=walk_steps, position_entropy=0.0,
                                 shannon_entropy=0.0, von_neumann_entropy=0.0,
                                 participation_ratio=0.0, stability_score=0.0,
                                 top_site_1=("?", -1, 0.0), top_site_2=("?", -1, 0.0),
                                 top_site_3=("?", -1, 0.0), has_c4_in_top3=False,
                                 error="fetch_failed")
        mol = MoleculeInput(
            name=raw.get("name", name.title()),
            formula=raw.get("formula", ""),
            atoms=raw.get("atoms", []),
            bonds=raw.get("bonds", []),
        )
        print(f"{len(mol.atoms)} atoms, {len(mol.bonds)} bonds — running walk...", end=" ", flush=True)

        result = run_fractal_analysis(
            molecule_data=mol,
            fractal="sierpinski",
            level=3,
            route="ifs",
            walk_steps=walk_steps,
            initial_node=initial_node,
        )

        loc = result.localization
        top1 = loc[0] if len(loc) > 0 else None
        top2 = loc[1] if len(loc) > 1 else None
        top3 = loc[2] if len(loc) > 2 else None

        # Check if C4 is in top 3
        c4_in_top3 = any(
            loc_item.atom_index == 4 and loc_item.element in ("C", "c")
            for loc_item in (top1, top2, top3)
        )

        print("OK")
        return MoleculeResult(
            name=result.molecule_name,
            formula=result.formula,
            num_atoms=result.num_atoms,
            num_bonds=result.num_bonds,
            walk_steps=walk_steps,
            position_entropy=result.position_entropy,
            shannon_entropy=result.shannon_entropy,
            von_neumann_entropy=result.von_neumann_entropy,
            participation_ratio=result.participation_ratio,
            stability_score=result.stability_score,
            top_site_1=(top1.element, top1.atom_index, top1.visit_probability) if top1 else ("?", -1, 0.0),
            top_site_2=(top2.element, top2.atom_index, top2.visit_probability) if top2 else ("?", -1, 0.0),
            top_site_3=(top3.element, top3.atom_index, top3.visit_probability) if top3 else ("?", -1, 0.0),
            has_c4_in_top3=c4_in_top3,
            error=result.error,
        )

    except Exception as e:
        print(f"ERROR: {e}")
        return MoleculeResult(
            name=name, formula="?", num_atoms=0, num_bonds=0,
            walk_steps=walk_steps, position_entropy=0.0,
            shannon_entropy=0.0, von_neumann_entropy=0.0,
            participation_ratio=0.0, stability_score=0.0,
            top_site_1=("?", -1, 0.0), top_site_2=("?", -1, 0.0),
            top_site_3=("?", -1, 0.0), has_c4_in_top3=False,
            error=str(e),
        )


def print_scorecard(results: list[MoleculeResult]):
    """Print a formatted comparison table."""
    print("\n" + "=" * 110)
    print("FRACTAL WALK SCORECARD — C4 IN TOP-3 SITES")
    print("=" * 110)
    print(f"{'Molecule':<20} {'Formula':<12} {'Atoms':>5} {'Top1':>10} {'p1':>8} "
          f"{'Top2':>10} {'p2':>8} {'Top3':>10} {'p3':>8} {'C4?':>5}")
    print("-" * 110)

    hits = 0
    total = 0
    for r in results:
        if r.error:
            print(f"{r.name:<20} {'ERROR':<12} {r.error[:30]}")
            continue
        total += 1
        c4_mark = "✓" if r.has_c4_in_top3 else "✗"
        if r.has_c4_in_top3:
            hits += 1

        def fmt(el, idx, p):
            return f"{el}{idx}"

        print(
            f"{r.name:<20} {r.formula:<12} {r.num_atoms:>5} "
            f"{fmt(*r.top_site_1):>10} {r.top_site_1[2]:>8.4f} "
            f"{fmt(*r.top_site_2):>10} {r.top_site_2[2]:>8.4f} "
            f"{fmt(*r.top_site_3):>10} {r.top_site_3[2]:>8.4f} "
            f"{c4_mark:>5}"
        )

    print("-" * 110)
    print(f"Hits: {hits}/{total} ({100*hits/max(total,1):.1f}%)")
    print("=" * 110)
    print()

    # Also print: how often is C4 the #1 site?
    c4_num1 = sum(1 for r in results if not r.error and r.top_site_1[1] == 4 and r.top_site_1[0] in ("C", "c"))
    print(f"C4 as #1 site: {c4_num1}/{total}")
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch fractal walk analysis")
    parser.add_argument("molecules", nargs="*", default=None,
                         help="Molecule names (default: BATCH_MOLECULES list)")
    parser.add_argument("--steps", "-s", type=int, default=10,
                         help="Number of walk steps (default: 10)")
    parser.add_argument("--node", "-n", type=int, default=0,
                         help="Initial node (default: 0)")
    parser.add_argument("--output", "-o", type=str, default=None,
                         help="Write results JSON to this file")
    parser.add_argument("--resume", "-r", type=str, default=None,
                         help="Resume from a previous results JSON")
    args = parser.parse_args()

    molecules = args.molecules if args.molecules else BATCH_MOLECULES
    print(f"Batch analysis: {len(molecules)} molecules")
    print(f"Walk steps: {args.steps}, initial_node: {args.node}")

    # Load previous results if resuming
    completed: dict[str, MoleculeResult] = {}
    if args.resume:
        with open(args.resume) as f:
            prev = json.load(f)
        for r in prev:
            if isinstance(r, dict) and "name" in r:
                completed[r["name"]] = _dict_to_result(r)
        print(f"Resuming with {len(completed)} existing results")

    results = []
    for name in molecules:
        if name in completed:
            print(f"  Skipping {name} (already done)")
            results.append(completed[name])
            continue

        print(f"\n[{len(results)+1}/{len(molecules)}] {name}")
        r = run_molecule(name, walk_steps=args.steps, initial_node=args.node)
        results.append(r)
        completed[name] = r

        # Save checkpoint
        if args.output:
            with open(args.output + ".tmp", "w") as f:
                json.dump([_result_to_dict(r) for r in results], f)
            os.replace(args.output + ".tmp", args.output)

        # Small delay to be nice to PubChem
        time.sleep(0.3)

    print_scorecard(results)

    if args.output:
        with open(args.output, "w") as f:
            json.dump([_result_to_dict(r) for r in results], f, indent=2)
        print(f"Results saved to {args.output}")


def _result_to_dict(r: MoleculeResult) -> dict:
    d = asdict(r)
    d["top_site_1"] = list(r.top_site_1)
    d["top_site_2"] = list(r.top_site_2)
    d["top_site_3"] = list(r.top_site_3)
    return d


def _dict_to_result(d: dict) -> MoleculeResult:
    d = dict(d)
    d["top_site_1"] = tuple(d.pop("top_site_1"))
    d["top_site_2"] = tuple(d.pop("top_site_2"))
    d["top_site_3"] = tuple(d.pop("top_site_3"))
    return MoleculeResult(**d)


if __name__ == "__main__":
    main()

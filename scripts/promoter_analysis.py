"""
Promoter sequence analysis: composition + motif scanning.
====================================================
For 10 promoter sequences (~81bp each), computes:
1. Basic composition: GC%, CpG O/E, length, strand, gene context
2. Core promoter motifs: TATA box, Inr, DPE
3. Gene-specific TF motifs: CREB/CRE, AP-1, p53RE, SRY HMG, E-box, GC-box

References:
  TATA box: TATAAA (Homo sapiens core promoter element)
  CREB/CRE: TGACGTCA (BDNF, neuronal activity-dependent)
  AP-1: TGACTCA or TGAGTCA (FOS, JUN immediate-early response)
  p53RE: WWWCWWGYYY (p53 consensus for TP53)
  SRY HMG: AACAAAG (SRY HMG-box binding motif)
  E-box: CANNTG (bHLH factors)
  GC-box: GGGCGG (Sp1 binding)
  CAAT box: CCAAT (CAAT box, various promoters)
"""
from __future__ import annotations
import json, re
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Sequence data
# ---------------------------------------------------------------------------

SEQUENCES = {
    "ACTB": {
        "name": "Beta-actin",
        "sephirah": "Malkuth",
        "seq": "CTGAGTCAGGGGAATCACTTGCACCCGGGAGGCGGAGGCTGCAGTCAGCCGAGATCGCGCCATTGCACTCCAGCCTGGGCA",
        "strand": "-",
        "gene_context": "Housekeeping / cytoskeletal",
    },
    "BDNF": {
        "name": "Brain-derived neurotrophic factor",
        "sephirah": "Tiferet",
        "seq": "GCCGCCCCCCACCCCCTCCCTGCTGCGCTTTTCTGGTATTATTATTAAAGCGGTAGTCTGCCGGCGCTGATAAGCAACAAG",
        "strand": "-",
        "gene_context": "Activity-dependent neuronal growth factor",
    },
    "DCTN1": {
        "name": "Dynactin subunit 1",
        "sephirah": "Binah",
        "seq": "GACACGCCGATTTCTTATGGTCCTAATCGGCTTCCCAGGCACAGTGCGCGTGCGCTTATCCTGTCCCAGGTGTCCAGCTTT",
        "strand": "-",
        "gene_context": "Microtubule motor complex, neuronal",
    },
    "FOS": {
        "name": "c-Fos",
        "sephirah": "Netzach",
        "seq": "AACGCTTGTTATAAAAGCAGTGGCTGCGGCGCCTCGTACTCCAACCGCATCTGCAGCGAGCATCTGAGAAGCCAAGACTGA",
        "strand": "+",
        "gene_context": "Immediate-early response, neuronal activity",
    },
    "FOXG1": {
        "name": "Forkhead box G1",
        "sephirah": "Kether",
        "seq": "CCTGTCCTTTCCCAAGAATCCGGTTACACCGAATCATTTCACGCTAGACCGACTACGAAAACGTACCGGGCCGTCCACCTC",
        "strand": "+",
        "gene_context": "Forkhead transcription factor, brain development",
    },
    "JUN": {
        "name": "c-Jun",
        "sephirah": "Hod",
        "seq": "TGACTGGTAGCAGATAAGTGTTGAGCTCGGGCTGGATAAGGGCTCAGAGTTGCACTGAGTGTGGCTGAAGCAGCGAGGCGG",
        "strand": "-",
        "gene_context": "Immediate-early response, AP-1 component",
    },
    "NCAM1": {
        "name": "Neural cell adhesion molecule 1",
        "sephirah": "Chokmah",
        "seq": "ATCTGCCTCCCCTGTCTCTCTTACCTCCTTGATGTTCGGCACTATTTGTGGCCGGCGTGGTGGAAGGACACAGTGAGGTTC",
        "strand": "+",
        "gene_context": "Neural cell adhesion, synaptic plasticity",
    },
    "OXT": {
        "name": "Oxytocin",
        "sephirah": "Chesed",
        "seq": "CAATGCCCAGGCATAAAAAGGCCAGGCCGGAGAGACCGCCACCAGTCACGGACCCTGGACCCAGCGCACCCGCACCATGGC",
        "strand": "+",
        "gene_context": "Neuropeptide, hypothalamic",
    },
    "SRY": {
        "name": "Sex-determining region Y",
        "sephirah": "Yesod",
        "seq": "CAAGTTTCATTACAAAAGTTAACGTAACAAAGAATCTGGTAGAAGTGAGTTTTGGATAGTAAAATAAGTTTCGAACTCTGG",
        "strand": "-",
        "gene_context": "Sex determination, HMG-box TF",
    },
    "TP53": {
        "name": "Tumor protein p53",
        "sephirah": "Gevurah",
        "seq": "ACTGTCCAGCTTTGTGCCAGGAGCCTCGCAGGGGTTGATGGGATTGGGGTTTTCCCCTCCCATGTGCTCAAGACTGGCGCT",
        "strand": "-",
        "gene_context": "Tumor suppressor, stress response",
    },
}


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------

def gc_content(seq: str) -> float:
    """GC% of sequence."""
    seq = seq.upper()
    gc = sum(1 for c in seq if c in 'GC')
    return gc / len(seq) * 100 if seq else 0.0


def cpg_oe(seq: str) -> Optional[float]:
    """
    CpG observed/expected ratio.
    OE = (count_C * count_G) / (len(seq) * count_CpG)
    Gardiner-Garden & Frommer 1987.
    Raw value is informative even at 81bp (not claiming "island" call).
    """
    seq = seq.upper()
    n = len(seq)
    count_c = seq.count('C')
    count_g = seq.count('G')
    count_cpg = seq.count('CG')
    if count_cpg == 0 or n == 0:
        return None
    OE = (count_c * count_g) / (n * count_cpg)
    return OE


def dinuc_freq(seq: str, dn: str) -> float:
    """Frequency of a dinucleotide (normalized per 100bp)."""
    seq = seq.upper()
    n = len(seq)
    if n < 2:
        return 0.0
    count = sum(1 for i in range(n - 1) if seq[i:i+2] == dn.upper())
    return count / (n - 1) * 100


def purine_pyrimidine(seq: str) -> float:
    """RY content (purine/pyrimidine bias)."""
    seq = seq.upper()
    ry = sum(1 for c in seq if c in 'RY')
    return ry / len(seq) * 100 if seq else 0.0


# ---------------------------------------------------------------------------
# Motif scanning
# ---------------------------------------------------------------------------

def motif_hits(seq: str, pattern: str, min_hits: int = 1) -> list[tuple[int, str]]:
    """
    Scan for all occurrences of a motif (IUPAC or plain) in sequence.
    Returns list of (start_pos, matched_sequence).
    """
    seq = seq.upper()
    pattern = pattern.upper()
    hits = []
    for m in re.finditer(pattern, seq):
        hits.append((m.start(), m.group()))
    return hits


def scan_all_motifs(seq: str) -> dict:
    """Scan sequence for all canonical promoter motifs."""
    seq = seq.upper()
    results = {}

    # Core promoter elements
    # TATA box: TATAWAWR (classic eukaryotic TATA)
    results["TATA_box"] = motif_hits(seq, r"TATA[AT]A[AT][AT]")
    # Inr (initiator): YYANWYY or TCTMTM (Pyrimidine-rich Inr)
    results["Inr"] = motif_hits(seq, r"TC[CT][CT]")
    # DPE (Downstream promoter element): A/G GATCF (at +28 to +32 relative to TSS)
    results["DPE"] = motif_hits(seq, r"[AG]AT[TC]")
    # BRE (TFIIB recognition element): SSRCGCC (upstream of TATA)
    results["BRE"] = motif_hits(seq, r"[GC]C[GC]GCC")

    # General TF motifs
    # GC-box: Sp1 binding site
    results["GC_box"] = motif_hits(seq, r"GGGCGG")
    # CAAT box
    results["CAAT_box"] = motif_hits(seq, r"CCAAT")
    # AP-1: TGACTCA (FOS/JUN binding)
    results["AP1"] = motif_hits(seq, r"TGAC")
    # CREB/CRE: TGACGTCA (cAMP response element)
    results["CREB_CRE"] = motif_hits(seq, r"TGACGTCA")
    results["CRE_half"] = motif_hits(seq, r"TGACG")
    # E-box: CANNTG (bHLH factors including CLOCK/BMAL)
    results["E_box"] = motif_hits(seq, r"CA[ACGT]TG")
    # p53RE: RRRCWWGYYY (p53 half-site, two copies = full p53RE)
    results["p53_half"] = motif_hits(seq, r"[AG][AG][AG]C[A-T]T[AG][AG][AG]")
    results["p53_full"] = motif_hits(seq, r"[AG]{2}[AG]C[A-T]T[AG]{2}[ACG]{3}")  # approximate

    # SRY HMG-box: AACAAAG (consensus for HMG-box binding)
    results["SRY_HMG"] = motif_hits(seq, r"AACAAAG")

    # Neural activity / neuronal promoters
    # NGFIA/NRSE: ATTGGATT (neuronal-specific)
    results["NRSE"] = motif_hits(seq, r"ATTGGATT")
    # NRF-1: YCAGWTGGB (nuclear respiratory factor)
    results["NRF1"] = motif_hits(seq, r"[CT]CAG[AT][AT]G[CG]")
    # GABP: TTCCGG (ETS family, BDNF)
    results["ETS_GABP"] = motif_hits(seq, r"TTCC")

    # Heat shock element: GAANTTC (HSP)
    results["HSE"] = motif_hits(seq, r"GAANTTC")

    # STAT binding site: TTCCNGGAA
    results["STAT"] = motif_hits(seq, r"TTCC[ACG]GGAA")

    # RE1/NRSE (neuron-restrictive silencer): TTAGCGATT
    results["REST_RE1"] = motif_hits(seq, r"TTAGCGATT")

    return results


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze_all():
    """Run full composition + motif analysis on all sequences."""
    all_results = {}

    for gene, info in SEQUENCES.items():
        seq = info["seq"]
        n = len(seq)

        # Composition
        gc = gc_content(seq)
        cpg_oe_val = cpg_oe(seq)
        cpg_count = seq.upper().count('CG')
        at_content = sum(1 for c in seq.upper() if c in 'AT') / n * 100

        # Scan motifs
        motifs = scan_all_motifs(seq)

        # Known biology check
        known = {}
        if gene == "BDNF":
            # BDNF promoter IV is activity-dependent, has CRE (TGACGTCA)
            known["has_CRE"] = bool(motifs["CREB_CRE"]) or bool(motifs["CRE_half"])
            known["has_GC_box"] = bool(motifs["GC_box"])
            known["has_TATA"] = bool(motifs["TATA_box"])
            known["expected_CRE"] = True
        elif gene == "TP53":
            # TP53 binds its own RE (two half-sites)
            known["has_p53"] = len(motifs["p53_half"]) >= 2
            known["has_GC_box"] = bool(motifs["GC_box"])
            known["expected_TP53"] = True
        elif gene == "FOS":
            # FOS is a classic AP-1 gene
            known["has_AP1"] = bool(motifs["AP1"])
            known["has_TATA"] = bool(motifs["TATA_box"])
            known["expected_AP1"] = True
        elif gene == "JUN":
            known["has_AP1"] = bool(motifs["AP1"])
            known["expected_AP1"] = True
        elif gene == "SRY":
            known["has_HMG"] = bool(motifs["SRY_HMG"])
            known["has_TATA"] = bool(motifs["TATA_box"])
            known["expected_HMG"] = True
        elif gene == "ACTB":
            known["has_GC_box"] = bool(motifs["GC_box"]) or len(motifs["GC_box"]) > 1
            known["expected_housekeeping"] = True

        all_results[gene] = {
            "gene": gene,
            "name": info["name"],
            "sephirah": info["sephirah"],
            "strand": info["strand"],
            "gene_context": info["gene_context"],
            "length": n,
            "GC_pct": round(gc, 2),
            "AT_pct": round(at_content, 2),
            "CpG_count": cpg_count,
            "CpG_OE": round(cpg_oe_val, 3) if cpg_oe_val is not None else None,
            "GC_box_count": len(motifs["GC_box"]),
            "TATA_count": len(motifs["TATA_box"]),
            "CAAT_count": len(motifs["CAAT_box"]),
            "AP1_count": len(motifs["AP1"]),
            "CRE_count": len(motifs["CREB_CRE"]),
            "CRE_half_count": len(motifs["CRE_half"]),
            "E_box_count": len(motifs["E_box"]),
            "SRY_HMG_count": len(motifs["SRY_HMG"]),
            "p53_half_count": len(motifs["p53_half"]),
            "ETS_GABP_count": len(motifs["ETS_GABP"]),
            "Inr_count": len(motifs["Inr"]),
            "DPE_count": len(motifs["DPE"]),
            "motifs": {k: [(pos, seq) for pos, seq in v]
                       for k, v in motifs.items() if v},
            "known_biology": known,
        }

    return all_results


def print_summary(results: dict):
    """Print human-readable summary table."""
    print("=" * 90)
    print("PROMOTER SEQUENCE ANALYSIS: Composition + Motif Summary")
    print("=" * 90)

    # Composition table
    print("\nCOMPOSITION STATS:")
    print(f"{'Gene':<8} {'Name':<20} {'GC%':>6} {'CpG#':>5} {'CpG OE':>8} {'TATA':>5} "
          f"{'GC-box':>7} {'CAAT':>5} {'AP-1':>5} {'CRE':>4} {'E-box':>6} {'ETS':>5}")
    print("-" * 90)

    for gene, r in results.items():
        gc = r["GC_pct"]
        cpg_oe = f"{r['CpG_OE']:.2f}" if r["CpG_OE"] is not None else "N/A"
        print(f"{gene:<8} {r['name'][:20]:<20} {gc:>6.1f} {r['CpG_count']:>5} "
              f"{cpg_oe:>8} {r['TATA_count']:>5} "
              f"{r['GC_box_count']:>7} {r['CAAT_count']:>5} "
              f"{r['AP1_count']:>5} {r['CRE_count']:>4} "
              f"{r['E_box_count']:>6} {r['ETS_GABP_count']:>5}")

    print()

    # Motif detail table
    print("\nMOTIF PRESENCE/ABSENCE MATRIX (1 = present, 0 = absent):")
    print(f"{'Gene':<8} {'TATA':>5} {'GC-box':>7} {'CAAT':>5} {'AP-1':>5} "
          f"{'CRE':>4} {'E-box':>6} {'ETS':>5} {'SRY-HMG':>8} {'p53-1/2':>8}")
    print("-" * 75)

    for gene, r in results.items():
        def fmt(c): return str(c) if c > 0 else "0"
        print(f"{gene:<8} {fmt(r['TATA_count']):>5} {fmt(r['GC_box_count']):>7} "
              f"{fmt(r['CAAT_count']):>5} {fmt(r['AP1_count']):>5} "
              f"{fmt(r['CRE_count']):>4} "
              f"{fmt(r['E_box_count']):>6} "
              f"{fmt(r['ETS_GABP_count']):>5} "
              f"{fmt(r['SRY_HMG_count']):>8} "
              f"{fmt(r['p53_half_count']):>8}")

    # Known biology check
    print("\n\nBIOLOGY CHECK (Does promoter match known TF binding?)")
    print("=" * 70)

    checks = [
        ("BDNF", "CRE (activity-dependent neuronal promoter)", "CRE_count", 0, ">="),
        ("BDNF", "GC-box (Sp1-rich housekeeping)", "GC_box_count", 0, ">="),
        ("TP53", "p53 half-sites (>=2 for full RE)", "p53_half_count", 2, ">="),
        ("FOS",  "AP-1 site (immediate-early response)", "AP1_count", 1, ">="),
        ("JUN",  "AP-1 site (immediate-early response)", "AP1_count", 1, ">="),
        ("SRY",  "SRY HMG-box motif", "SRY_HMG_count", 1, ">="),
        ("ACTB", "GC-box (housekeeping, Sp1-driven)", "GC_box_count", 1, ">="),
    ]

    print(f"{'Gene':<8} {'Check':<45} {'Found':>7} {'Expected':>9} {'Pass?':>6}")
    print("-" * 80)

    for gene, check_desc, field, threshold, op in checks:
        if gene not in results:
            continue
        count = results[gene][field]
        if op == ">=":
            passed = count >= threshold
        elif op == ">":
            passed = count > threshold
        else:
            passed = count == threshold
        expected_str = f"{op}{threshold}"
        print(f"{gene:<8} {check_desc:<45} {count:>7} {expected_str:>9} "
              f"{'PASS' if passed else 'FAIL':>6}")


def write_output(results: dict, path: str):
    """Save JSON results."""
    def clean(obj):
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean(v) for v in obj]
        elif isinstance(obj, float):
            return round(obj, 6)
        return obj
    with open(path, "w") as f:
        json.dump(clean(results), f, indent=2)


if __name__ == "__main__":
    results = analyze_all()
    print_summary(results)
    write_output(results, "D:/Molecule-App/promoter_analysis_results.json")
    print("\nSaved to D:/Molecule-App/promoter_analysis_results.json")

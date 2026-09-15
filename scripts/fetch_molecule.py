"""
Fetch molecule data from PubChem and save as JSON for the fractal bridge.
Usage: python fetch_molecule.py <name> [output.json]
"""

from __future__ import annotations

import sys
import json
import requests
from collections import Counter

# PubChem element codes
ELEMENT_CODES = {
    1: "H", 2: "He", 3: "Li", 4: "Be", 5: "B", 6: "C",
    7: "N", 8: "O", 9: "F", 10: "Ne", 11: "Na", 12: "Mg",
    13: "Al", 14: "Si", 15: "P", 16: "S", 17: "Cl", 18: "Ar",
    19: "K", 20: "Ca", 26: "Fe", 35: "Br", 53: "I",
}


def fetch_molecule(name: str) -> dict | None:
    """Fetch compound by name, return 3D coordinates + bonds."""
    # Resolve name to CID
    r = requests.get(
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/cids/JSON",
        timeout=30,
    )
    if r.status_code != 200:
        return None
    cid = r.json()["IdentifierList"]["CID"][0]

    # Fetch 3D/2D record
    r = requests.get(
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/record/JSON?heading=3D+Conformer",
        timeout=30,
    )
    if r.status_code != 200:
        return None

    return _parse_record(r.json(), name.title(), cid)


def _parse_record(data: dict, name: str, cid: int) -> dict:
    """Parse PubChem record into our MoleculeData format."""
    compound = data["PC_Compounds"][0]

    # --- Atoms ---
    atom_aids = compound["atoms"]["aid"]           # 1-indexed
    atom_elements_raw = compound["atoms"]["element"]  # element codes
    elements = [ELEMENT_CODES.get(int(e), "?") for e in atom_elements_raw]

    n_atoms = len(atom_aids)
    if n_atoms == 0:
        return None

    # --- Bonds (1-indexed, convert to 0-indexed) ---
    bonds_raw = compound["bonds"]
    bond_aid1 = bonds_raw["aid1"]   # 1-indexed atom IDs
    bond_aid2 = bonds_raw["aid2"]
    bond_order = bonds_raw["order"]  # 1=single, 2=double, 3=triple

    # Build atom-index → position map (aid is 1-indexed)
    aid_to_idx = {aid: idx for idx, aid in enumerate(atom_aids)}

    bonds = []
    bond_weights = []
    for a1, a2, order in zip(bond_aid1, bond_aid2, bond_order):
        if a1 in aid_to_idx and a2 in aid_to_idx:
            bonds.append([aid_to_idx[a1], aid_to_idx[a2]])
            # Weight by bond order (higher order = higher hopping amplitude)
            bond_weights.append(float(order))
        else:
            print(f"Warning: bond references unknown aid {a1} or {a2}", file=sys.stderr)

    # --- Coordinates ---
    conformers = compound["coords"][0]["conformers"]
    conf = conformers[0]
    x_coords = conf.get("x", [])
    y_coords = conf.get("y", [])
    z_coords = conf.get("z", [])

    atoms = []
    for i in range(n_atoms):
        xi = float(x_coords[i]) if i < len(x_coords) else 0.0
        yi = float(y_coords[i]) if i < len(y_coords) else 0.0
        zi = float(z_coords[i]) if i < len(z_coords) else 0.0
        atoms.append({
            "element": elements[i],
            "x": xi,
            "y": yi,
            "z": zi,
        })

    formula = _elements_to_formula(elements)

    return {
        "name": name,
        "formula": formula,
        "description": f"{name} (CID {cid}) — PubChem record",
        "category": "Organic Compound",
        "atoms": atoms,
        "bonds": bonds,
        "_bond_weights": bond_weights,  # for bridge use
    }


def _elements_to_formula(elements: list[str]) -> str:
    counts = Counter(elements)
    order = ["C", "H", "N", "O", "S", "P", "F", "Cl", "Br", "I"]
    parts = []
    for el in order:
        if el in counts:
            n = counts[el]
            parts.append(el + (str(n) if n > 1 else ""))
    return "".join(parts)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_molecule.py <name> [output.json]")
        sys.exit(1)

    name = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else f"{name.lower().replace(' ', '_')}.json"

    print(f"Fetching {name} from PubChem...", file=sys.stderr)
    result = fetch_molecule(name)

    if result is None:
        print(f"Failed to fetch {name}", file=sys.stderr)
        sys.exit(1)

    # Remove internal fields before saving
    result_clean = {k: v for k, v in result.items() if not k.startswith("_")}
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result_clean, f, indent=2)

    print(f"Saved {len(result['atoms'])} atoms, {len(result['bonds'])} bonds to {output}",
          file=sys.stderr)

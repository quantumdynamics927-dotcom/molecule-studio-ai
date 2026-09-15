import { sanitizeMolecule } from "./geometry";
import type { MoleculeData, PubChemHit } from "./types";

const ATOM_Z: Record<number, string> = {
  1: "H",
  6: "C",
  7: "N",
  8: "O",
  9: "F",
  11: "Na",
  12: "Mg",
  15: "P",
  16: "S",
  17: "Cl",
  19: "K",
  20: "Ca",
  26: "Fe",
  29: "Cu",
  30: "Zn",
  35: "Br",
  53: "I",
};

const PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug";

export async function searchPubChem(query: string): Promise<PubChemHit[]> {
  const q = query.trim();
  if (!q) return [];
  const url = `${PUG}/compound/name/${encodeURIComponent(q)}/property/Title,MolecularFormula,MolecularWeight,IUPACName,CanonicalSMILES/JSON`;
  const res = await fetch(url);
  if (!res.ok) return [];
  const json = (await res.json()) as {
    PropertyTable?: {
      Properties?: Array<{
        CID: number;
        Title?: string;
        MolecularFormula?: string;
        MolecularWeight?: number | string;
        IUPACName?: string;
        CanonicalSMILES?: string;
      }>;
    };
  };
  return (json.PropertyTable?.Properties ?? []).map((p) => ({
    cid: p.CID,
    name: p.Title || q,
    formula: p.MolecularFormula,
    weight: typeof p.MolecularWeight === "string" ? Number(p.MolecularWeight) : p.MolecularWeight,
    iupac: p.IUPACName,
    smiles: p.CanonicalSMILES,
  }));
}

export async function loadPubChem3D(nameOrCid: string | number): Promise<MoleculeData> {
  const isCid = typeof nameOrCid === "number" || /^\d+$/.test(String(nameOrCid));
  const path = isCid
    ? `compound/cid/${nameOrCid}`
    : `compound/name/${encodeURIComponent(String(nameOrCid))}`;
  const url = `${PUG}/${path}/record/JSON/?record_type=3d`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("No 3D conformer in PubChem for this compound.");
  }
  const json = await res.json();
  return parsePubChemRecord(json, String(nameOrCid));
}

function parsePubChemRecord(json: unknown, fallbackName: string): MoleculeData {
  const root = json as {
    PC_Compounds?: Array<{
      id?: { id?: { cid?: number } };
      atoms?: { element?: number[] };
      bonds?: { aid1?: number[]; aid2?: number[]; order?: number[] };
      coords?: Array<{ conformers?: Array<{ x: number[]; y: number[]; z: number[] }> }>;
      props?: Array<{ urn?: { label?: string }; value?: { sval?: string } }>;
    }>;
  };
  const c = root.PC_Compounds?.[0];
  if (!c?.atoms?.element || !c.coords?.[0]?.conformers?.[0]) {
    throw new Error("Incomplete PubChem 3D record.");
  }
  const conf = c.coords[0].conformers[0];
  const atoms = c.atoms.element.map((z, i) => ({
    element: ATOM_Z[z] ?? "C",
    x: conf.x[i],
    y: conf.y[i],
    z: conf.z[i],
  }));
  const bonds = (c.bonds?.aid1 ?? []).map((aid, i) => ({
    a: aid - 1,
    b: (c.bonds?.aid2?.[i] ?? 1) - 1,
    order: c.bonds?.order?.[i] ?? 1,
  }));
  let name = fallbackName;
  let formula = "";
  for (const p of c.props ?? []) {
    if (p.urn?.label === "IUPAC Name" && p.value?.sval) name = p.value.sval;
    if (p.urn?.label === "Molecular Formula" && p.value?.sval) formula = p.value.sval;
  }
  const cid = c.id?.id?.cid;
  return sanitizeMolecule({
    name: prettyName(fallbackName, name),
    formula,
    description: cid
      ? `PubChem CID ${cid}. Experimental 3D conformer from the PubChem compound database.`
      : "3D conformer from PubChem.",
    category: "PubChem",
    atoms,
    bonds,
    source: cid ? `pubchem:${cid}` : "pubchem",
  });
}

function prettyName(query: string, iupac: string) {
  if (!/^\d+$/.test(query) && query.length < 40) {
    return query.replace(/\b\w/g, (c) => c.toUpperCase());
  }
  return iupac.length > 48 ? iupac.slice(0, 46) + "…" : iupac;
}

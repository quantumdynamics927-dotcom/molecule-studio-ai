// PubChem PUG REST API integration

const PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug";

export interface PubChemCompound {
  cid: number;
  name: string;
  iupacName?: string;
  molecularFormula?: string;
  molecularWeight?: number;
  canonicalSMILES?: string;
  isomericSMILES?: string;
  2dImageUrl?: string;
}

export async function searchMolecule(name: string): Promise<PubChemCompound[]> {
  try {
    const prop = "MolecularFormula,MolecularWeight,CanonicalSMILES,IUPACName";
    const url = `${PUBCHEM_BASE}/compound/name/${encodeURIComponent(name)}/property/${prop}/JSON`;
    const res = await fetch(url);
    if (!res.ok) return [];
    const data = await res.json();
    return (data.PropertyTable?.Properties || []).map((p: any) => ({
      cid: p.CID,
      name: name,
      iupacName: p.IUPACName,
      molecularFormula: p.MolecularFormula,
      molecularWeight: p.MolecularWeight,
      canonicalSMILES: p.CanonicalSMILES,
      isomericSMILES: p.IsomericSMILES,
      2dImageUrl: `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${p.CID}/PNG`
    }));
  } catch {
    return [];
  }
}

export async function getMolecule2D(name: string): Promise<string | null> {
  const compounds = await searchMolecule(name);
  return compounds[0]?.2dImageUrl || null;
}

export async function getMoleculeProperties(name: string): Promise<PubChemCompound | null> {
  const compounds = await searchMolecule(name);
  return compounds[0] || null;
}

export async function getCID(name: string): Promise<number | null> {
  try {
    const url = `${PUBCHEM_BASE}/compound/name/${encodeURIComponent(name)}/cids/JSON`;
    const res = await fetch(url);
    if (!res.ok) return null;
    const data = await res.json();
    return data.IdentifierList?.CID?.[0] || null;
  } catch {
    return null;
  }
}

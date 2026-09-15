export interface Atom {
  element: string;
  x: number;
  y: number;
  z: number;
}

export interface Bond {
  a: number;
  b: number;
  order: number;
}

export interface MoleculeData {
  id?: string;
  name: string;
  formula: string;
  description: string;
  category: string;
  atoms: Atom[];
  bonds: Bond[];
  source?: string;
}

export type ViewStyle = "ball-stick" | "spacefill" | "sticks";
export type TabId = "viewer" | "analysis" | "notebooks" | "database";
export type ExportFormat = "pdb" | "xyz" | "mol" | "json";
export type AnalysisId =
  | "properties"
  | "bonds"
  | "optimizer"
  | "compare"
  | "reaction"
  | "pdb";

export interface Notebook {
  id: string;
  title: string;
  notes: string;
  molecule: MoleculeData | null;
  createdAt: number;
  updatedAt: number;
}

export interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

export interface PubChemHit {
  cid: number;
  name: string;
  formula?: string;
  weight?: number;
  iupac?: string;
  smiles?: string;
}


export interface Atom {
  element: string;
  x: number;
  y: number;
  z: number;
}

export interface MoleculeData {
  name: string;
  formula: string;
  description: string;
  atoms: Atom[];
  bonds: [number, number][]; // Tuple of atom indices
  category: string;
}

export enum AppStatus {
  IDLE = 'IDLE',
  LOADING = 'LOADING',
  ERROR = 'ERROR',
  SUCCESS = 'SUCCESS'
}

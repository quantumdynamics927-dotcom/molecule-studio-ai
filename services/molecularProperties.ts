// Molecular property calculations

export interface Atom {
  element: string;
  x: number;
  y: number;
  z: number;
}

export interface MolecularProperties {
  molecularWeight: number;
  formula: string;
  atomCount: Record<string, number>;
  bondCount: number;
  bondStats: { min: number; max: number; avg: number };
  centerOfMass: { x: number; y: number; z: number };
}

const ATOMIC_MASSES: Record<string, number> = {
  H: 1.008, He: 4.003, Li: 6.941, Be: 9.012, B: 10.81, C: 12.01, N: 14.01,
  O: 16.00, F: 19.00, Ne: 20.18, Na: 22.99, Mg: 24.31, Al: 26.98, Si: 28.09,
  P: 30.97, S: 32.07, Cl: 35.45, Ar: 39.95, K: 39.10, Ca: 40.08, Fe: 55.85,
  Cu: 63.55, Zn: 65.38, Br: 79.90, I: 126.90
};

export function calculateMolecularWeight(atoms: Atom[]): number {
  return atoms.reduce((sum, atom) => sum + (ATOMIC_MASSES[atom.element] || 0), 0);
}

export function calculateFormula(atoms: Atom[]): string {
  const counts: Record<string, number> = {};
  atoms.forEach(a => { counts[a.element] = (counts[a.element] || 0) + 1; });

  const order = ["C", "H", "N", "O", "S", "P", "F", "Cl", "Br", "I", "Si", "B", "Na", "Ca", "Fe", "Mg", "K", "Zn", "Cu"];
  let formula = "";
  order.forEach(el => {
    if (counts[el]) {
      formula += el + (counts[el] > 1 ? counts[el] : "");
      delete counts[el];
    }
  });
  Object.entries(counts).sort().forEach(([el, n]) => {
    formula += el + (n > 1 ? n : "");
  });
  return formula;
}

export function calculateBondStats(atoms: Atom[], bonds: number[][]): { min: number; max: number; avg: number } {
  if (bonds.length === 0) return { min: 0, max: 0, avg: 0 };
  const distances = bonds.map(b => {
    const a = atoms[b[0]], c = atoms[b[1]];
    return Math.sqrt((a.x - c.x) ** 2 + (a.y - c.y) ** 2 + (a.z - c.z) ** 2);
  });
  return {
    min: Math.min(...distances),
    max: Math.max(...distances),
    avg: distances.reduce((a, b) => a + b, 0) / distances.length
  };
}

export function calculateCenterOfMass(atoms: Atom[]): { x: number; y: number; z: number } {
  if (atoms.length === 0) return { x: 0, y: 0, z: 0 };
  const total = atoms.reduce((acc, a) => ({ x: acc.x + a.x, y: acc.y + a.y, z: acc.z + a.z }), { x: 0, y: 0, z: 0 });
  return { x: total.x / atoms.length, y: total.y / atoms.length, z: total.z / atoms.length };
}

export function getMolecularProperties(atoms: Atom[], bonds: number[][]): MolecularProperties {
  return {
    molecularWeight: calculateMolecularWeight(atoms),
    formula: calculateFormula(atoms),
    atomCount: atoms.reduce((acc: Record<string, number>, a) => { acc[a.element] = (acc[a.element] || 0) + 1; return acc; }, {}),
    bondCount: bonds.length,
    bondStats: calculateBondStats(atoms, bonds),
    centerOfMass: calculateCenterOfMass(atoms)
  };
}

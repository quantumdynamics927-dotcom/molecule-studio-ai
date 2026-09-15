import { atomicMass } from "./constants";
import type { Atom, Bond } from "./types";

function dist(a: Atom, b: Atom) {
  return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
}

export function calculateFormula(atoms: Atom[]): string {
  const counts: Record<string, number> = {};
  for (const a of atoms) {
    const el = a.element;
    counts[el] = (counts[el] ?? 0) + 1;
  }
  const order = ["C", "H", "N", "O", "S", "P", "F", "Cl", "Br", "I", "Si", "B", "Na", "K", "Ca", "Mg", "Fe", "Zn"];
  let formula = "";
  for (const el of order) {
    if (counts[el]) {
      formula += el + (counts[el] > 1 ? String(counts[el]) : "");
      delete counts[el];
    }
  }
  for (const el of Object.keys(counts).sort()) {
    formula += el + (counts[el] > 1 ? String(counts[el]) : "");
  }
  return formula || "—";
}

export function molecularWeight(atoms: Atom[]) {
  return atoms.reduce((sum, a) => sum + atomicMass(a.element), 0);
}

export function atomCounts(atoms: Atom[]) {
  const counts: Record<string, number> = {};
  for (const a of atoms) counts[a.element] = (counts[a.element] ?? 0) + 1;
  return counts;
}

export function bondStats(atoms: Atom[], bonds: Bond[]) {
  if (bonds.length === 0) return { min: 0, max: 0, avg: 0 };
  const lengths = bonds.map((b) => dist(atoms[b.a], atoms[b.b]));
  const sum = lengths.reduce((s, n) => s + n, 0);
  return {
    min: Math.min(...lengths),
    max: Math.max(...lengths),
    avg: sum / lengths.length,
  };
}

export function heavyAtomCount(atoms: Atom[]) {
  return atoms.filter((a) => a.element.toUpperCase() !== "H").length;
}

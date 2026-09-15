import { covalentRadius } from "./constants";
import { calculateFormula } from "./properties";
import type { Atom, Bond, MoleculeData } from "./types";

export function dist(a: Atom, b: Atom) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  const dz = a.z - b.z;
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

export function bondAngle(a: Atom, vertex: Atom, c: Atom) {
  const v1 = { x: a.x - vertex.x, y: a.y - vertex.y, z: a.z - vertex.z };
  const v2 = { x: c.x - vertex.x, y: c.y - vertex.y, z: c.z - vertex.z };
  const mag1 = Math.hypot(v1.x, v1.y, v1.z);
  const mag2 = Math.hypot(v2.x, v2.y, v2.z);
  if (mag1 < 1e-8 || mag2 < 1e-8) return 0;
  const cos = (v1.x * v2.x + v1.y * v2.y + v1.z * v2.z) / (mag1 * mag2);
  return (Math.acos(Math.max(-1, Math.min(1, cos))) * 180) / Math.PI;
}

export function centerOfMass(atoms: Atom[]) {
  if (atoms.length === 0) return { x: 0, y: 0, z: 0 };
  const t = atoms.reduce(
    (acc, a) => ({ x: acc.x + a.x, y: acc.y + a.y, z: acc.z + a.z }),
    { x: 0, y: 0, z: 0 },
  );
  const n = atoms.length;
  return { x: t.x / n, y: t.y / n, z: t.z / n };
}

export function centerAtoms(atoms: Atom[]): Atom[] {
  const c = centerOfMass(atoms);
  return atoms.map((a) => ({
    ...a,
    x: a.x - c.x,
    y: a.y - c.y,
    z: a.z - c.z,
  }));
}

export function inferBonds(atoms: Atom[]): Bond[] {
  const bonds: Bond[] = [];
  for (let i = 0; i < atoms.length; i++) {
    for (let j = i + 1; j < atoms.length; j++) {
      const d = dist(atoms[i], atoms[j]);
      const max = (covalentRadius(atoms[i].element) + covalentRadius(atoms[j].element)) * 1.25;
      if (d > 0.35 && d < max) {
        let order = 1;
        if (d < max * 0.62) order = 3;
        else if (d < max * 0.78) order = 2;
        bonds.push({ a: i, b: j, order });
      }
    }
  }
  return bonds;
}

export function normalizeBonds(raw: unknown, atoms: Atom[]): Bond[] {
  if (!Array.isArray(raw) || raw.length === 0) return inferBonds(atoms);
  const bonds: Bond[] = [];
  for (const item of raw) {
    if (Array.isArray(item) && item.length >= 2) {
      const a = Number(item[0]);
      const b = Number(item[1]);
      const order = Number(item[2] ?? 1) || 1;
      if (Number.isInteger(a) && Number.isInteger(b) && a >= 0 && b >= 0 && a < atoms.length && b < atoms.length && a !== b) {
        bonds.push({ a, b, order: Math.min(3, Math.max(1, order)) });
      }
    } else if (item && typeof item === "object") {
      const rec = item as { a?: number; b?: number; order?: number };
      const a = Number(rec.a);
      const b = Number(rec.b);
      if (Number.isInteger(a) && Number.isInteger(b) && a >= 0 && b >= 0 && a < atoms.length && b < atoms.length && a !== b) {
        bonds.push({ a, b, order: Math.min(3, Math.max(1, Number(rec.order) || 1)) });
      }
    }
  }
  return bonds.length ? bonds : inferBonds(atoms);
}

export function rmsd(a: Atom[], b: Atom[]) {
  const n = Math.min(a.length, b.length);
  if (n === 0) return 0;
  let sum = 0;
  for (let i = 0; i < n; i++) {
    const dx = a[i].x - b[i].x;
    const dy = a[i].y - b[i].y;
    const dz = a[i].z - b[i].z;
    sum += dx * dx + dy * dy + dz * dz;
  }
  return Math.sqrt(sum / n);
}

export function moleculeExtent(atoms: Atom[]) {
  if (atoms.length === 0) return 4;
  let max = 0;
  for (const a of atoms) {
    max = Math.max(max, Math.hypot(a.x, a.y, a.z));
  }
  return Math.max(3, max);
}

export function sanitizeMolecule(raw: Partial<MoleculeData> & { bonds?: unknown }): MoleculeData {
  const atoms = (raw.atoms ?? []).map((a) => ({
    element: String(a.element || "C").replace(/[^A-Za-z]/g, "").slice(0, 2) || "C",
    x: Number(a.x) || 0,
    y: Number(a.y) || 0,
    z: Number(a.z) || 0,
  }));
  const centered = centerAtoms(atoms);
  const bonds = normalizeBonds(raw.bonds, centered);
  return {
    id: raw.id,
    name: raw.name?.trim() || "Untitled",
    formula: raw.formula?.trim() || calculateFormula(centered),
    description: raw.description?.trim() || "Generated structure.",
    category: raw.category?.trim() || "Organic Compound",
    atoms: centered,
    bonds,
    source: raw.source,
  };
}

export type BondRow = {
  index: number;
  a: number;
  b: number;
  order: number;
  length: number;
  label: string;
};

export function bondRows(atoms: Atom[], bonds: Bond[]): BondRow[] {
  return bonds.map((bond, index) => ({
    index,
    a: bond.a,
    b: bond.b,
    order: bond.order,
    length: dist(atoms[bond.a], atoms[bond.b]),
    label: `${atoms[bond.a]?.element ?? "?"}–${atoms[bond.b]?.element ?? "?"}`,
  }));
}

export type AngleRow = {
  key: string;
  vertex: number;
  left: number;
  right: number;
  degrees: number;
  label: string;
};

export function angleRows(atoms: Atom[], bonds: Bond[]): AngleRow[] {
  const adj: number[][] = atoms.map(() => []);
  for (const bond of bonds) {
    adj[bond.a]?.push(bond.b);
    adj[bond.b]?.push(bond.a);
  }
  const rows: AngleRow[] = [];
  for (let v = 0; v < atoms.length; v++) {
    const n = adj[v];
    for (let i = 0; i < n.length; i++) {
      for (let j = i + 1; j < n.length; j++) {
        const left = n[i];
        const right = n[j];
        rows.push({
          key: `${left}-${v}-${right}`,
          vertex: v,
          left,
          right,
          degrees: bondAngle(atoms[left], atoms[v], atoms[right]),
          label: `${atoms[left].element}–${atoms[v].element}–${atoms[right].element}`,
        });
      }
    }
  }
  return rows.sort((a, b) => a.degrees - b.degrees);
}

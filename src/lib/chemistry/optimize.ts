import { dist } from "./geometry";
import type { Atom, Bond } from "./types";

const IDEAL: Record<string, number> = {
  "C-C": 1.54,
  "C-H": 1.09,
  "C-O": 1.43,
  "C-N": 1.47,
  "C=C": 1.34,
  "C=O": 1.23,
  "C=N": 1.29,
  "O-H": 0.96,
  "N-H": 1.01,
  "O-O": 1.48,
  "N-N": 1.45,
  "C-S": 1.82,
  "S-H": 1.34,
};

function pairKey(el1: string, el2: string, order: number) {
  const [a, b] = [el1, el2].sort();
  const bond = order >= 2 ? `${a}=${b}` : `${a}-${b}`;
  return bond;
}

export function idealLength(el1: string, el2: string, order: number) {
  return IDEAL[pairKey(el1, el2, order)] ?? (order >= 2 ? 1.32 : 1.5);
}

export function optimizeGeometry(atoms: Atom[], bonds: Bond[], steps = 80, rate = 0.08) {
  const current = atoms.map((a) => ({ ...a }));
  const history: number[] = [];

  for (let iter = 0; iter < steps; iter++) {
    let energy = 0;
    for (const bond of bonds) {
      const i = bond.a;
      const j = bond.b;
      const ai = current[i];
      const aj = current[j];
      const ideal = idealLength(ai.element, aj.element, bond.order);
      const d = dist(ai, aj);
      const err = d - ideal;
      energy += err * err;
      const force = err * rate;
      const dx = aj.x - ai.x;
      const dy = aj.y - ai.y;
      const dz = aj.z - ai.z;
      const len = Math.hypot(dx, dy, dz) || 1;
      const fx = (dx / len) * force * 0.5;
      const fy = (dy / len) * force * 0.5;
      const fz = (dz / len) * force * 0.5;
      ai.x += fx;
      ai.y += fy;
      ai.z += fz;
      aj.x -= fx;
      aj.y -= fy;
      aj.z -= fz;
    }
    history.push(energy);
  }

  return { atoms: current, history };
}

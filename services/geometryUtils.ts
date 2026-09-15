// 3D geometry utilities

export interface Vec3 { x: number; y: number; z: number; }

export function calculateBondLength(a: Vec3, b: Vec3): number {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2);
}

export function calculateBondAngle(a: Vec3, b: Vec3, c: Vec3): number {
  const v1 = { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z };
  const v2 = { x: c.x - b.x, y: c.y - b.y, z: c.z - b.z };
  const dot = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;
  const mag1 = Math.sqrt(v1.x ** 2 + v1.y ** 2 + v1.z ** 2);
  const mag2 = Math.sqrt(v2.x ** 2 + v2.y ** 2 + v2.z ** 2);
  return Math.acos(Math.max(-1, Math.min(1, dot / (mag1 * mag2)))) * (180 / Math.PI);
}

export function calculateDihedralAngle(a: Vec3, b: Vec3, c: Vec3, d: Vec3): number {
  const v1 = { x: b.x - a.x, y: b.y - a.y, z: b.z - a.z };
  const v2 = { x: c.x - b.x, y: c.y - b.y, z: c.z - b.z };
  const v3 = { x: d.x - c.x, y: d.y - c.y, z: d.z - c.z };

  const n1 = { x: v1.y * v2.z - v1.z * v2.y, y: v1.z * v2.x - v1.x * v2.z, z: v1.x * v2.y - v1.y * v2.x };
  const n2 = { x: v2.y * v3.z - v2.z * v3.y, y: v2.z * v3.x - v2.x * v3.z, z: v2.x * v3.y - v2.y * v3.x };

  const dot = n1.x * n2.x + n1.y * n2.y + n1.z * n2.z;
  const mag1 = Math.sqrt(n1.x ** 2 + n1.y ** 2 + n1.z ** 2);
  const mag2 = Math.sqrt(n2.x ** 2 + n2.y ** 2 + n2.z ** 2);

  return Math.acos(Math.max(-1, Math.min(1, dot / (mag1 * mag2)))) * (180 / Math.PI);
}

export function calculateRMSD(atoms1: Vec3[], atoms2: Vec3[]): number {
  if (atoms1.length !== atoms2.length) return -1;
  if (atoms1.length === 0) return 0;
  const sum = atoms1.reduce((acc, a, i) => {
    const b = atoms2[i];
    return acc + (a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2;
  }, 0);
  return Math.sqrt(sum / atoms1.length);
}

export function translateAtoms(atoms: Vec3[], dx: number, dy: number, dz: number): Vec3[] {
  return atoms.map(a => ({ x: a.x + dx, y: a.y + dy, z: a.z + dz }));
}

export function centerAtOrigin(atoms: Vec3[]): Vec3[] {
  if (atoms.length === 0) return atoms;
  const com = calculateCenterOfMass(atoms);
  return translateAtoms(atoms, -com.x, -com.y, -com.z);
}

export function calculateCenterOfMass(atoms: Vec3[]): Vec3 {
  if (atoms.length === 0) return { x: 0, y: 0, z: 0 };
  const total = atoms.reduce((acc, a) => ({ x: acc.x + a.x, y: acc.y + a.y, z: acc.z + a.z }), { x: 0, y: 0, z: 0 });
  return { x: total.x / atoms.length, y: total.y / atoms.length, z: total.z / atoms.length };
}

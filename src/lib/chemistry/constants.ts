/** CPK / Jmol element colors — used only in the 3D canvas, not UI chrome. */
export const CPK_COLORS: Record<string, string> = {
  H: "#f0f0f2",
  C: "#2a2e32",
  O: "#d94a4a",
  N: "#3d6fd8",
  S: "#e0c040",
  P: "#e08a2a",
  F: "#62c46a",
  CL: "#3cbf3c",
  BR: "#a44a3a",
  I: "#8a3c8a",
  FE: "#d06a3a",
  MG: "#3cbf6a",
  NA: "#3c5ad0",
  CA: "#7a7a88",
  K: "#8a4ad0",
  ZN: "#7a8a8a",
  DEFAULT: "#c070c0",
};

/** Display radii for ball-and-stick (Å, scaled for the viewer). */
export const BALL_RADII: Record<string, number> = {
  H: 0.28,
  C: 0.52,
  O: 0.48,
  N: 0.5,
  S: 0.64,
  P: 0.64,
  F: 0.42,
  CL: 0.6,
  BR: 0.68,
  I: 0.78,
  DEFAULT: 0.48,
};

/** van der Waals radii (Å) for space-filling. */
export const VDW_RADII: Record<string, number> = {
  H: 1.2,
  C: 1.7,
  N: 1.55,
  O: 1.52,
  F: 1.47,
  P: 1.8,
  S: 1.8,
  CL: 1.75,
  BR: 1.85,
  I: 1.98,
  FE: 2.05,
  DEFAULT: 1.5,
};

export const COVALENT_RADII: Record<string, number> = {
  H: 0.31,
  C: 0.76,
  N: 0.71,
  O: 0.66,
  F: 0.57,
  P: 1.07,
  S: 1.05,
  CL: 1.02,
  BR: 1.2,
  I: 1.39,
  DEFAULT: 0.77,
};

export const ATOMIC_MASSES: Record<string, number> = {
  H: 1.008,
  He: 4.003,
  Li: 6.941,
  Be: 9.012,
  B: 10.81,
  C: 12.011,
  N: 14.007,
  O: 15.999,
  F: 18.998,
  Ne: 20.18,
  Na: 22.99,
  Mg: 24.305,
  Al: 26.982,
  Si: 28.085,
  P: 30.974,
  S: 32.06,
  Cl: 35.45,
  Ar: 39.948,
  K: 39.098,
  Ca: 40.078,
  Fe: 55.845,
  Cu: 63.546,
  Zn: 65.38,
  Br: 79.904,
  I: 126.9,
};

export const ELEMENT_NAMES: Record<string, string> = {
  H: "Hydrogen",
  C: "Carbon",
  N: "Nitrogen",
  O: "Oxygen",
  F: "Fluorine",
  P: "Phosphorus",
  S: "Sulfur",
  CL: "Chlorine",
  BR: "Bromine",
  I: "Iodine",
  NA: "Sodium",
  MG: "Magnesium",
  FE: "Iron",
  CA: "Calcium",
  K: "Potassium",
  ZN: "Zinc",
};

export function cpkColor(element: string) {
  return CPK_COLORS[element.toUpperCase()] ?? CPK_COLORS.DEFAULT;
}

export function ballRadius(element: string) {
  return BALL_RADII[element.toUpperCase()] ?? BALL_RADII.DEFAULT;
}

export function vdwRadius(element: string) {
  return VDW_RADII[element.toUpperCase()] ?? VDW_RADII.DEFAULT;
}

export function covalentRadius(element: string) {
  return COVALENT_RADII[element.toUpperCase()] ?? COVALENT_RADII.DEFAULT;
}

export function atomicMass(element: string) {
  const key = element.length === 1
    ? element.toUpperCase()
    : element[0].toUpperCase() + element.slice(1).toLowerCase();
  return ATOMIC_MASSES[key] ?? ATOMIC_MASSES[element] ?? 0;
}

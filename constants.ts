
export const CPK_COLORS: Record<string, string> = {
  H: "#FFFFFF",  // Hydrogen
  C: "#222222",  // Carbon (Darker for better contrast)
  O: "#EE0000",  // Oxygen
  N: "#3050F8",  // Nitrogen
  S: "#FFFF30",  // Sulfur
  P: "#FFA500",  // Phosphorus
  CL: "#1FF01F", // Chlorine
  BR: "#A62929", // Bromine
  F: "#90E050",  // Fluorine
  I: "#940094",  // Iodine
  FE: "#E06633", // Iron
  MG: "#00FF00", // Magnesium
  NA: "#0000FF", // Sodium
  CA: "#808090", // Calcium
  DEFAULT: "#FF00FF" // Pink for unknown
};

export const ATOM_RADII: Record<string, number> = {
  H: 0.35,
  C: 0.65,
  O: 0.60,
  N: 0.62,
  S: 0.8,
  P: 0.8,
  CL: 0.75,
  DEFAULT: 0.6
};

export const PRESET_MOLECULES = [
  "Caffeine",
  "Adrenaline",
  "Aspirin",
  "Glucose",
  "Serotonin",
  "DNA Base Pair",
  "Methane",
  "Ethanol"
];

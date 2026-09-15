import type { ExportFormat, MoleculeData } from "./types";

export function exportMolecule(data: MoleculeData, format: ExportFormat): string {
  switch (format) {
    case "xyz":
      return toXYZ(data);
    case "pdb":
      return toPDB(data);
    case "mol":
      return toMOL(data);
    case "json":
      return JSON.stringify(data, null, 2);
  }
}

function toXYZ(data: MoleculeData) {
  const lines = [
    String(data.atoms.length),
    `${data.name} | ${data.formula} | Molecule Studio`,
  ];
  for (const a of data.atoms) {
    lines.push(`${a.element.padEnd(2)} ${fmt(a.x, 6)} ${fmt(a.y, 6)} ${fmt(a.z, 6)}`);
  }
  return lines.join("\n");
}

function toPDB(data: MoleculeData) {
  const lines = [
    `HEADER    ${data.name.toUpperCase().slice(0, 40)}`,
    `TITLE     ${data.name}`,
    `COMPND    ${data.formula}`,
    `AUTHOR    Molecule Studio`,
  ];
  data.atoms.forEach((atom, i) => {
    const n = String(i + 1).padStart(5);
    const el = atom.element.padEnd(2);
    lines.push(
      `HETATM${n}  ${el.padEnd(3)} MOL A   1    ${padCoord(atom.x)}${padCoord(atom.y)}${padCoord(atom.z)}  1.00  0.00          ${el}`,
    );
  });
  data.bonds.forEach((bond) => {
    lines.push(`CONECT${String(bond.a + 1).padStart(5)}${String(bond.b + 1).padStart(5)}`);
  });
  lines.push("END");
  return lines.join("\n");
}

function toMOL(data: MoleculeData) {
  const lines = [
    data.name,
    "  Molecule-Studio  3D",
    "",
    `${pad3(data.atoms.length)}${pad3(data.bonds.length)}  0  0  0  0  0  0  0  0999 V2000`,
  ];
  for (const atom of data.atoms) {
    lines.push(
      `${pad10(atom.x)}${pad10(atom.y)}${pad10(atom.z)} ${atom.element.padEnd(3)} 0  0  0  0  0  0  0  0  0  0  0  0`,
    );
  }
  for (const bond of data.bonds) {
    lines.push(`${pad3(bond.a + 1)}${pad3(bond.b + 1)}${pad3(bond.order)}  0  0  0  0`);
  }
  lines.push("M  END");
  return lines.join("\n");
}

export function downloadText(content: string, filename: string, mime = "text/plain") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function filenameFor(data: MoleculeData, format: ExportFormat) {
  const base = data.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "molecule";
  return `${base}.${format}`;
}

function fmt(n: number, digits: number) {
  return n.toFixed(digits);
}
function padCoord(n: number) {
  return n.toFixed(3).padStart(8);
}
function pad3(n: number) {
  return String(n).padStart(3);
}
function pad10(n: number) {
  return n.toFixed(4).padStart(10);
}

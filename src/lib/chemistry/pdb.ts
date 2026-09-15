import { createServerFn } from "@tanstack/react-start";
import { inferBonds, sanitizeMolecule } from "./geometry";
import type { Atom, MoleculeData } from "./types";

const MAX_ATOMS = 280;

export const fetchPdbStructure = createServerFn({ method: "POST" })
  .validator((input: { pdbId: string }) => input)
  .handler(async ({ data }) => {
    const id = data.pdbId.trim().toUpperCase();
    if (!/^[0-9][A-Z0-9]{3}$/.test(id)) {
      return { ok: false as const, error: "PDB IDs look like 1CRN or 4HHB." };
    }
    const res = await fetch(`https://files.rcsb.org/download/${id}.pdb`);
    if (!res.ok) {
      return { ok: false as const, error: `RCSB returned ${res.status} for ${id}.` };
    }
    const text = await res.text();
    try {
      const molecule = parsePdb(text, id);
      return { ok: true as const, molecule };
    } catch (err) {
      return {
        ok: false as const,
        error: err instanceof Error ? err.message : "Failed to parse PDB.",
      };
    }
  });

export function parsePdb(text: string, id: string): MoleculeData {
  const atoms: Atom[] = [];
  const serialToIndex = new Map<number, number>();
  const conect: Array<[number, number]> = [];
  let title = id;
  let caOnly = false;

  const atomLines = text.split(/\r?\n/).filter((l) => l.startsWith("ATOM  ") || l.startsWith("HETATM"));
  const proteinLike = atomLines.length > MAX_ATOMS;
  caOnly = proteinLike;

  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith("TITLE")) {
      title = line.slice(10).trim() || title;
    }
    if (line.startsWith("ATOM  ") || line.startsWith("HETATM")) {
      const name = line.slice(12, 16).trim();
      if (caOnly && name !== "CA") continue;
      const serial = Number(line.slice(6, 11));
      const element = (line.slice(76, 78).trim() || name.replace(/[^A-Za-z]/g, "").slice(0, 2) || "C");
      const atom: Atom = {
        element: normalizeElement(element),
        x: Number(line.slice(30, 38)),
        y: Number(line.slice(38, 46)),
        z: Number(line.slice(46, 54)),
      };
      serialToIndex.set(serial, atoms.length);
      atoms.push(atom);
      if (atoms.length >= MAX_ATOMS) break;
    }
    if (line.startsWith("CONECT")) {
      const nums = line.slice(6).trim().split(/\s+/).map(Number).filter((n) => Number.isFinite(n));
      const origin = nums[0];
      for (const t of nums.slice(1)) conect.push([origin, t]);
    }
  }

  if (atoms.length === 0) throw new Error("No atoms found in this PDB file.");

  const bonds = conect
    .map(([a, b]) => {
      const ia = serialToIndex.get(a);
      const ib = serialToIndex.get(b);
      if (ia == null || ib == null || ia === ib) return null;
      return { a: Math.min(ia, ib), b: Math.max(ia, ib), order: 1 };
    })
    .filter((b): b is { a: number; b: number; order: number } => b !== null);

  const unique = new Map<string, { a: number; b: number; order: number }>();
  for (const b of bonds) unique.set(`${b.a}-${b.b}`, b);

  return sanitizeMolecule({
    name: title.length > 48 ? title.slice(0, 46) + "…" : title,
    formula: "",
    description: caOnly
      ? `PDB ${id} — Cα trace (${atoms.length} residues shown; full file exceeds the viewer atom cap).`
      : `PDB ${id} from the RCSB Protein Data Bank.`,
    category: "Macromolecule",
    atoms,
    bonds: unique.size ? [...unique.values()] : inferBonds(atoms),
    source: `pdb:${id}`,
  });
}

function normalizeElement(el: string) {
  const cleaned = el.replace(/[^A-Za-z]/g, "");
  if (!cleaned) return "C";
  return cleaned[0].toUpperCase() + cleaned.slice(1).toLowerCase();
}

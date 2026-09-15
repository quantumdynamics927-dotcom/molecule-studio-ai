import { generateMolecule } from "@/lib/ai/generate-molecule";
import { PRESETS, PRESET_LIST } from "@/lib/chemistry/presets";
import { loadPubChem3D } from "@/lib/chemistry/pubchem";
import type { MoleculeData } from "@/lib/chemistry/types";
import { useStudio } from "@/lib/store";

export async function resolveMolecule(query: string): Promise<MoleculeData> {
  const q = query.trim();
  if (!q) throw new Error("Enter a name, formula, or CID.");

  const key = q.toLowerCase().replace(/[^a-z0-9]+/g, "");
  const preset =
    PRESETS[key] ??
    PRESET_LIST.find(
      (p) =>
        p.name.toLowerCase() === q.toLowerCase() ||
        p.formula.toLowerCase() === q.toLowerCase() ||
        p.name.toLowerCase().replace(/[^a-z0-9]+/g, "") === key,
    );
  if (preset) return preset;

  try {
    return await loadPubChem3D(q);
  } catch {
    /* fall through to AI */
  }

  const ai = await generateMolecule({ data: { query: q } });
  if (!ai.ok) throw new Error(ai.error);
  return ai.molecule;
}

export async function loadQuery(query: string) {
  const { setStatus, setMolecule, toast } = useStudio.getState();
  setStatus("loading");
  try {
    const molecule = await resolveMolecule(query);
    setMolecule(molecule);
    toast(`Loaded ${molecule.name}`, "success");
  } catch (err) {
    const message = err instanceof Error ? err.message : "Could not load molecule.";
    setStatus("error", message);
    toast(message, "error");
  }
}

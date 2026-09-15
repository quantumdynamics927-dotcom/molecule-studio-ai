import { createServerFn } from "@tanstack/react-start";
import { sanitizeMolecule } from "@/lib/chemistry/geometry";
import type { MoleculeData } from "@/lib/chemistry/types";

const SYSTEM = `You are a computational chemist. Return ONLY valid JSON (no markdown) for a 3D molecular geometry in Ångströms.

Schema:
{"name":"string","formula":"string","description":"1-2 sentences","category":"string","atoms":[{"element":"C","x":0,"y":0,"z":0}],"bonds":[[0,1,1]]}

Rules:
- atoms[].element is a chemical symbol (C, H, N, O, S, P, F, Cl, Br, I, …)
- bonds are [atomIndexA, atomIndexB, order] with 0-based indices; order is 1, 2, or 3
- Use realistic VSEPR / experimental bond lengths and angles
- Include hydrogens
- Center the structure near the origin
- Keep the molecule under 60 atoms
- Never invent impossible valences`;

export const generateMolecule = createServerFn({ method: "POST" })
  .validator((input: { query: string }) => input)
  .handler(async ({ data }) => {
    const apiKey = process.env.XAI_API_KEY;
    if (!apiKey) {
      return { ok: false as const, error: "AI generation is unavailable in this environment." };
    }
    const query = data.query.trim().slice(0, 200);
    if (!query) return { ok: false as const, error: "Enter a molecule name or formula." };

    const res = await fetch("https://api.x.ai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "grok-4.5",
        temperature: 0.2,
        max_tokens: 2500,
        messages: [
          { role: "system", content: SYSTEM },
          { role: "user", content: `Generate a 3D structural model for: ${query}` },
        ],
      }),
    });

    if (!res.ok) {
      return { ok: false as const, error: `Model request failed (${res.status}).` };
    }

    const body = (await res.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const content = body.choices?.[0]?.message?.content ?? "";
    const parsed = extractJson(content);
    if (!parsed) {
      return { ok: false as const, error: "The model did not return a usable structure." };
    }

    const molecule: MoleculeData = sanitizeMolecule({
      ...parsed,
      source: "grok",
    });
    if (molecule.atoms.length === 0) {
      return { ok: false as const, error: "Empty structure returned." };
    }
    return { ok: true as const, molecule };
  });

function extractJson(text: string): Partial<MoleculeData> | null {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  const candidate = fenced?.[1] ?? text;
  const start = candidate.indexOf("{");
  const end = candidate.lastIndexOf("}");
  if (start < 0 || end <= start) return null;
  try {
    return JSON.parse(candidate.slice(start, end + 1)) as Partial<MoleculeData>;
  } catch {
    return null;
  }
}

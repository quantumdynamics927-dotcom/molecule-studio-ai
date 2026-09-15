import { createServerFn } from "@tanstack/react-start";
import { sanitizeMolecule } from "@/lib/chemistry/geometry";
import type { MoleculeData } from "@/lib/chemistry/types";

export const simulateReaction = createServerFn({ method: "POST" })
  .validator((input: { reactants: string }) => input)
  .handler(async ({ data }) => {
    const apiKey = process.env.XAI_API_KEY;
    if (!apiKey) {
      return { ok: false as const, error: "AI is unavailable in this environment." };
    }
    const reactants = data.reactants.trim().slice(0, 240);
    if (!reactants) return { ok: false as const, error: "Describe the reactants." };

    const res = await fetch("https://api.x.ai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "grok-4.5",
        temperature: 0.25,
        max_tokens: 2200,
        messages: [
          {
            role: "system",
            content: `Return ONLY JSON:
{"summary":"plain language of the major product and why","name":"","formula":"","description":"","category":"Product","atoms":[{"element":"C","x":0,"y":0,"z":0}],"bonds":[[0,1,1]]}
The atoms/bonds describe the MAJOR organic product in 3D Ångströms with hydrogens, VSEPR geometry, under 50 atoms.`,
          },
          { role: "user", content: `Reaction / reactants: ${reactants}` },
        ],
      }),
    });
    if (!res.ok) return { ok: false as const, error: `Model request failed (${res.status}).` };
    const body = (await res.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const content = body.choices?.[0]?.message?.content ?? "";
    const start = content.indexOf("{");
    const end = content.lastIndexOf("}");
    if (start < 0 || end <= start) {
      return { ok: false as const, error: "The model did not return a product structure." };
    }
    try {
      const parsed = JSON.parse(content.slice(start, end + 1)) as Partial<MoleculeData> & { summary?: string };
      const molecule = sanitizeMolecule({ ...parsed, source: "reaction" });
      return { ok: true as const, molecule, summary: parsed.summary ?? molecule.description };
    } catch {
      return { ok: false as const, error: "Could not parse the predicted product." };
    }
  });

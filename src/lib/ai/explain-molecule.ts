import { createServerFn } from "@tanstack/react-start";

export const explainMolecule = createServerFn({ method: "POST" })
  .validator((input: { name: string; formula: string; question?: string }) => input)
  .handler(async ({ data }) => {
    const apiKey = process.env.XAI_API_KEY;
    if (!apiKey) {
      return { ok: false as const, error: "AI is unavailable in this environment." };
    }
    const question = (data.question ?? "Summarize structure, notable properties, and common uses.").slice(0, 400);
    const res = await fetch("https://api.x.ai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "grok-4.5",
        temperature: 0.4,
        max_tokens: 450,
        messages: [
          {
            role: "system",
            content:
              "You are a concise chemistry lecturer. Write 2 short paragraphs of accurate, non-speculative science. No markdown headings. No bullet lists unless listing functional groups.",
          },
          {
            role: "user",
            content: `Molecule: ${data.name} (${data.formula}). ${question}`,
          },
        ],
      }),
    });
    if (!res.ok) return { ok: false as const, error: `Model request failed (${res.status}).` };
    const body = (await res.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const text = body.choices?.[0]?.message?.content?.trim() ?? "";
    if (!text) return { ok: false as const, error: "Empty response." };
    return { ok: true as const, text };
  });

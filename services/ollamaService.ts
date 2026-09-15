
import { MoleculeData } from "../types";

const OLLAMA_API_KEY = "9db26354b39a4fceb14d73b7d3d6f5dc.ieMUvdkBOIYwcwKiIv5ILjeP";
const OLLAMA_API_URL = "https://api.ollama.cloud/v1/chat/completions";
const MODEL = "minimax-m2.7:cloud";

export class OllamaError extends Error {
  constructor(message: string, public statusCode?: number) {
    super(message);
    this.name = "OllamaError";
  }
}

export async function connectOllama(): Promise<boolean> {
  try {
    const response = await fetch(OLLAMA_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${OLLAMA_API_KEY}` },
      body: JSON.stringify({ model: MODEL, messages: [{ role: "user", content: "hi" }], temperature: 0.1, max_tokens: 5 })
    });
    return response.ok;
  } catch { return false; }
}

export async function generateMolecule(query: string): Promise<MoleculeData> {
  const response = await fetch(OLLAMA_API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${OLLAMA_API_KEY}` },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        { role: "system", content: `You are a chemistry expert. Return ONLY valid JSON: {"name":"","formula":"","description":"","category":"","atoms":[{"element":"C","x":0,"y":0,"z":0}],"bonds":[[0,1]]}. Center at [0,0,0]. Use VSEPR geometry.` },
        { role: "user", content: `Generate a 3D structural model for: ${query}` }
      ],
      temperature: 0.3, max_tokens: 4096
    })
  });

  if (!response.ok) throw new OllamaError(`API error (${response.status})`, response.status);
  const result = await response.json();
  const content = result.choices?.[0]?.message?.content || "";
  const jsonMatch = content.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new OllamaError("No JSON in response");
  try { return JSON.parse(jsonMatch[0]); } catch { throw new OllamaError("Invalid JSON"); }
}

export async function chatWithOllama(message: string): Promise<string> {
  const response = await fetch(OLLAMA_API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${OLLAMA_API_KEY}` },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: "system", content: "You are a helpful chemistry assistant." }, { role: "user", content: message }],
      temperature: 0.4, max_tokens: 2048
    })
  });
  if (!response.ok) throw new OllamaError(`API error (${response.status})`, response.status);
  const result = await response.json();
  return result.choices?.[0]?.message?.content || "";
}

// Legacy export for backwards compatibility
export async function fetchMoleculeData(query: string): Promise<MoleculeData> {
  return generateMolecule(query);
}

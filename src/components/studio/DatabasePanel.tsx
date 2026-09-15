import { ExternalLink, Loader2, Search } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { searchPubChem } from "@/lib/chemistry/pubchem";
import type { PubChemHit } from "@/lib/chemistry/types";
import { loadQuery } from "@/lib/load-molecule";
import { useStudio } from "@/lib/store";
import { Formula } from "./Formula";

export function DatabasePanel() {
  const [q, setQ] = useState("penicillin");
  const [hits, setHits] = useState<PubChemHit[]>([]);
  const [busy, setBusy] = useState(false);
  const toast = useStudio((s) => s.toast);

  async function search() {
    setBusy(true);
    try {
      const results = await searchPubChem(q);
      setHits(results);
      toast(results.length ? `${results.length} PubChem hit${results.length === 1 ? "" : "s"}` : "No PubChem match", "info");
    } catch {
      toast("PubChem search failed", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-display text-xl font-semibold tracking-tight">Library</h2>
        <p className="mt-1 text-sm text-muted">Search PubChem and load experimental 3D conformers.</p>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void search();
        }}
        className="flex gap-2"
      >
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Name or formula" />
        <Button type="submit" size="icon" aria-label="Search" disabled={busy}>
          {busy ? <Loader2 className="animate-spin" /> : <Search />}
        </Button>
      </form>
      <div className="space-y-1.5">
        {hits.map((h) => (
          <button
            key={h.cid}
            onClick={() => void loadQuery(String(h.cid))}
            className="w-full rounded-xl border border-border bg-elevated p-3 text-left hover:border-border-strong"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium text-fg">{h.name}</p>
              <ExternalLink className="size-3.5 shrink-0 text-subtle" />
            </div>
            <p className="mt-1 text-xs text-muted">
              {h.formula ? <Formula value={h.formula} /> : null}
              {h.weight ? <span className="ml-2 tabular-nums">{Number(h.weight).toFixed(1)} g/mol</span> : null}
            </p>
            <p className="mt-1 font-mono text-[10px] text-subtle">CID {h.cid}</p>
          </button>
        ))}
      </div>
    </div>
  );
}

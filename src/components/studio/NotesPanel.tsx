import { Plus, Trash2 } from "lucide-react";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { hydrateNotebooks, useStudio } from "@/lib/store";
import { cn } from "@/lib/utils";

export function NotesList() {
  const notebooks = useStudio((s) => s.notebooks);
  const active = useStudio((s) => s.activeNotebook);
  const createNotebook = useStudio((s) => s.createNotebook);
  const selectNotebook = useStudio((s) => s.selectNotebook);
  const deleteNotebook = useStudio((s) => s.deleteNotebook);

  useEffect(() => {
    hydrateNotebooks();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold tracking-tight">Notes</h2>
          <p className="text-sm text-muted">Saved on this device.</p>
        </div>
        <Button size="sm" onClick={createNotebook}>
          <Plus /> New
        </Button>
      </div>
      {notebooks.length === 0 ? (
        <p className="rounded-xl border border-dashed border-border px-3 py-6 text-center text-sm text-muted">
          Snapshot the current molecule into a lab note.
        </p>
      ) : (
        <div className="space-y-1.5">
          {notebooks.map((nb) => (
            <div
              key={nb.id}
              className={cn(
                "group flex items-center gap-2 rounded-xl border px-3 py-2.5",
                active === nb.id ? "border-fg/20 bg-elevated" : "border-border",
              )}
            >
              <button className="min-w-0 flex-1 text-left" onClick={() => selectNotebook(nb.id)}>
                <p className="truncate text-sm font-medium text-fg">{nb.title}</p>
                <p className="text-[11px] text-subtle">
                  {nb.molecule?.name ?? "No structure"} ·{" "}
                  {new Date(nb.updatedAt).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                </p>
              </button>
              <button
                className="rounded-md p-1.5 text-subtle opacity-0 hover:bg-surface hover:text-danger group-hover:opacity-100"
                onClick={() => deleteNotebook(nb.id)}
                aria-label="Delete note"
              >
                <Trash2 className="size-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function NotesEditor() {
  const id = useStudio((s) => s.activeNotebook);
  const notebooks = useStudio((s) => s.notebooks);
  const updateNotebook = useStudio((s) => s.updateNotebook);
  const nb = notebooks.find((n) => n.id === id);
  if (!nb) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-sm text-muted">
        Select or create a note to write alongside the structure.
      </div>
    );
  }
  return (
    <div className="flex h-full flex-col bg-surface">
      <input
        value={nb.title}
        onChange={(e) => updateNotebook(nb.id, { title: e.target.value })}
        className="border-b border-border bg-transparent px-5 py-3 font-display text-lg font-semibold text-fg outline-none"
      />
      <textarea
        value={nb.notes}
        onChange={(e) => updateNotebook(nb.id, { notes: e.target.value })}
        className="min-h-0 flex-1 resize-none bg-transparent px-5 py-4 font-mono text-sm leading-relaxed text-muted outline-none"
        placeholder="Observations, assay notes, next experiments…"
      />
    </div>
  );
}

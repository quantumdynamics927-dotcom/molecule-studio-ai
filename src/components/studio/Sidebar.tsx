import { Info, X } from "lucide-react";
import { Formula } from "@/components/studio/Formula";
import { Button } from "@/components/ui/button";
import { CPK_COLORS } from "@/lib/chemistry/constants";
import { atomCounts, heavyAtomCount, molecularWeight } from "@/lib/chemistry/properties";
import { PRESET_LIST } from "@/lib/chemistry/presets";
import type { ViewStyle } from "@/lib/chemistry/types";
import { loadQuery } from "@/lib/load-molecule";
import { useStudio } from "@/lib/store";
import { cn } from "@/lib/utils";
import { AnalysisList } from "./AnalysisPanel";
import { DatabasePanel } from "./DatabasePanel";
import { NotesList } from "./NotesPanel";

export function Sidebar() {
  const tab = useStudio((s) => s.tab);
  const sidebarOpen = useStudio((s) => s.sidebarOpen);
  const setSidebarOpen = useStudio((s) => s.setSidebarOpen);

  return (
    <>
      {sidebarOpen && (
        <button
          className="fixed inset-0 z-30 bg-bg/60 backdrop-blur-sm lg:hidden"
          aria-label="Close panel"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside
        className={cn(
          "z-40 flex w-[min(100%,20.5rem)] shrink-0 flex-col overflow-y-auto border-border bg-surface",
          "fixed inset-y-0 left-0 border-r transition-transform duration-200",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
          "lg:relative lg:translate-x-0",
        )}
      >
        <div className="flex items-center justify-between border-b border-border px-4 py-3 lg:hidden">
          <span className="text-sm font-medium">Panel</span>
          <Button variant="ghost" size="icon-sm" onClick={() => setSidebarOpen(false)} aria-label="Close">
            <X />
          </Button>
        </div>
        <div className="flex-1 p-4">
          {tab === "viewer" && <ViewerPanel />}
          {tab === "analysis" && <AnalysisList />}
          {tab === "notebooks" && <NotesList />}
          {tab === "database" && <DatabasePanel />}
        </div>
      </aside>
    </>
  );
}

function ViewerPanel() {
  const molecule = useStudio((s) => s.molecule);
  const error = useStudio((s) => s.error);
  const viewStyle = useStudio((s) => s.viewStyle);
  const setViewStyle = useStudio((s) => s.setViewStyle);
  const dynamics = useStudio((s) => s.dynamics);
  const setDynamics = useStudio((s) => s.setDynamics);
  const density = useStudio((s) => s.density);
  const setDensity = useStudio((s) => s.setDensity);
  const mw = molecularWeight(molecule.atoms);
  const counts = atomCounts(molecule.atoms);
  const styles: { id: ViewStyle; label: string }[] = [
    { id: "ball-stick", label: "Ball" },
    { id: "sticks", label: "Stick" },
    { id: "spacefill", label: "Space" },
  ];

  return (
    <div className="space-y-5">
      <section>
        <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-subtle">{molecule.category}</p>
        <h2 className="mt-1 font-display text-2xl font-semibold tracking-tight text-fg text-balance">
          {molecule.name}
        </h2>
        <Formula value={molecule.formula} className="mt-1 text-sm text-muted" />
      </section>

      {error && (
        <p className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-xs text-danger">{error}</p>
      )}

      <section className="rounded-xl border border-border bg-elevated p-4">
        <h3 className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-widest text-subtle">
          <Info className="size-3" /> About
        </h3>
        <p className="text-sm leading-relaxed text-muted text-pretty">{molecule.description}</p>
      </section>

      <section className="grid grid-cols-3 gap-2">
        <Stat label="Atoms" value={String(molecule.atoms.length)} />
        <Stat label="Bonds" value={String(molecule.bonds.length)} />
        <Stat label="Heavy" value={String(heavyAtomCount(molecule.atoms))} />
        <Stat label="MW" value={mw.toFixed(2)} className="col-span-3" suffix="g/mol" />
      </section>

      <section>
        <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-subtle">Composition</h3>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(counts).map(([el, n]) => (
            <span
              key={el}
              className="inline-flex items-center gap-1.5 rounded-md border border-border bg-elevated px-2 py-1 text-xs"
            >
              <span
                className="size-2 rounded-full"
                style={{ background: CPK_COLORS[el.toUpperCase()] ?? CPK_COLORS.DEFAULT }}
              />
              <span className="font-mono text-fg">{el}</span>
              <span className="tabular-nums text-muted">{n}</span>
            </span>
          ))}
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-subtle">Representation</h3>
        <div className="flex rounded-lg bg-elevated p-1">
          {styles.map((s) => (
            <button
              key={s.id}
              onClick={() => setViewStyle(s.id)}
              className={cn(
                "flex-1 rounded-md py-1.5 text-xs font-medium",
                viewStyle === s.id ? "bg-surface text-fg" : "text-muted hover:text-fg",
              )}
            >
              {s.label}
            </button>
          ))}
        </div>
        <div className="mt-2 flex gap-2">
          <Toggle pressed={dynamics} onPressed={() => setDynamics(!dynamics)} label="Thermal" />
          <Toggle pressed={density} onPressed={() => setDensity(!density)} label="Density" />
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-subtle">Library</h3>
        <div className="grid grid-cols-2 gap-1.5">
          {PRESET_LIST.map((m) => (
            <button
              key={m.id ?? m.name}
              onClick={() => void loadQuery(m.name)}
              className={cn(
                "truncate rounded-lg border px-2.5 py-2 text-left text-xs transition-colors",
                molecule.name === m.name
                  ? "border-fg/20 bg-elevated text-fg"
                  : "border-border text-muted hover:border-border-strong hover:text-fg",
              )}
            >
              {m.name}
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

function Stat({
  label,
  value,
  suffix,
  className,
}: {
  label: string;
  value: string;
  suffix?: string;
  className?: string;
}) {
  return (
    <div className={cn("rounded-lg border border-border bg-elevated px-3 py-2", className)}>
      <p className="text-[10px] uppercase tracking-wider text-subtle">{label}</p>
      <p className="font-mono text-sm tabular-nums text-fg">
        {value}
        {suffix ? <span className="ml-1 text-[10px] text-muted">{suffix}</span> : null}
      </p>
    </div>
  );
}

function Toggle({ pressed, onPressed, label }: { pressed: boolean; onPressed: () => void; label: string }) {
  return (
    <button
      onClick={onPressed}
      className={cn(
        "flex-1 rounded-lg border py-2 text-xs font-medium",
        pressed ? "border-accent/40 bg-accent/10 text-accent" : "border-border text-muted hover:text-fg",
      )}
    >
      {label}
    </button>
  );
}

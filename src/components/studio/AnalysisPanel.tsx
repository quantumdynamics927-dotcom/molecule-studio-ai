import {
  Activity,
  Binary,
  Box,
  GitBranch,
  Loader2,
  Scale,
  Sparkles,
} from "lucide-react";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import { Line, LineChart, ResponsiveContainer, YAxis } from "recharts";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { simulateReaction } from "@/lib/ai/simulate-reaction";
import { angleRows, bondRows, rmsd } from "@/lib/chemistry/geometry";
import { optimizeGeometry } from "@/lib/chemistry/optimize";
import { fetchPdbStructure } from "@/lib/chemistry/pdb";
import { PRESET_LIST } from "@/lib/chemistry/presets";
import {
  atomCounts,
  bondStats,
  calculateFormula,
  molecularWeight,
} from "@/lib/chemistry/properties";
import type { AnalysisId } from "@/lib/chemistry/types";
import { useStudio } from "@/lib/store";
import { cn } from "@/lib/utils";
import { Formula } from "./Formula";

const MODULES: { id: AnalysisId; name: string; blurb: string; icon: typeof Scale }[] = [
  { id: "properties", name: "Properties", blurb: "Mass, formula, composition", icon: Scale },
  { id: "bonds", name: "Bond analysis", blurb: "Lengths, orders, angles", icon: GitBranch },
  { id: "optimizer", name: "Geometry", blurb: "Relax bond-length strain", icon: Activity },
  { id: "compare", name: "Compare", blurb: "RMSD against a second structure", icon: Binary },
  { id: "reaction", name: "Reaction", blurb: "Predict a major product", icon: Sparkles },
  { id: "pdb", name: "PDB explorer", blurb: "Load an RCSB structure", icon: Box },
];

export function AnalysisList() {
  const analysis = useStudio((s) => s.analysis);
  const setAnalysis = useStudio((s) => s.setAnalysis);
  return (
    <div className="space-y-3">
      <div>
        <h2 className="font-display text-xl font-semibold tracking-tight">Analysis</h2>
        <p className="mt-1 text-sm text-muted">Measurements run on the loaded molecule.</p>
      </div>
      <div className="grid gap-1.5">
        {MODULES.map((m) => (
          <button
            key={m.id}
            onClick={() => setAnalysis(m.id)}
            className={cn(
              "flex items-start gap-3 rounded-xl border px-3 py-3 text-left transition-colors",
              analysis === m.id
                ? "border-fg/20 bg-elevated"
                : "border-border hover:border-border-strong hover:bg-elevated/50",
            )}
          >
            <m.icon className="mt-0.5 size-4 text-accent" />
            <span>
              <span className="block text-sm font-medium text-fg">{m.name}</span>
              <span className="text-xs text-muted">{m.blurb}</span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function AnalysisStage() {
  const analysis = useStudio((s) => s.analysis);
  return (
    <div className="absolute inset-x-0 bottom-0 z-10 max-h-[46%] overflow-y-auto border-t border-border bg-surface/95 p-4 backdrop-blur-md md:max-h-[42%]">
      {analysis === "properties" && <PropertiesView />}
      {analysis === "bonds" && <BondsView />}
      {analysis === "optimizer" && <OptimizerView />}
      {analysis === "compare" && <CompareView />}
      {analysis === "reaction" && <ReactionView />}
      {analysis === "pdb" && <PdbView />}
    </div>
  );
}

function PropertiesView() {
  const mol = useStudio((s) => s.molecule);
  const mw = molecularWeight(mol.atoms);
  const stats = bondStats(mol.atoms, mol.bonds);
  const counts = atomCounts(mol.atoms);
  return (
    <div>
      <h3 className="text-sm font-semibold text-fg">Molecular properties</h3>
      <div className="mt-3 grid grid-cols-2 gap-2 md:grid-cols-4">
        <Metric label="Formula" value={<Formula value={calculateFormula(mol.atoms)} />} />
        <Metric label="Mol. weight" value={`${mw.toFixed(3)} g/mol`} />
        <Metric label="Avg bond" value={`${stats.avg.toFixed(3)} Å`} />
        <Metric label="Range" value={`${stats.min.toFixed(3)}–${stats.max.toFixed(3)} Å`} />
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {Object.entries(counts).map(([el, n]) => (
          <span key={el} className="rounded-md bg-elevated px-2 py-1 font-mono text-xs text-muted">
            {el} {n} · {((n / mol.atoms.length) * 100).toFixed(0)}%
          </span>
        ))}
      </div>
    </div>
  );
}

function BondsView() {
  const mol = useStudio((s) => s.molecule);
  const setHovered = useStudio((s) => s.setHovered);
  const rows = useMemo(() => bondRows(mol.atoms, mol.bonds), [mol]);
  const angles = useMemo(() => angleRows(mol.atoms, mol.bonds).slice(0, 12), [mol]);
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div>
        <h3 className="text-sm font-semibold">Bonds</h3>
        <div className="mt-2 max-h-40 overflow-y-auto">
          {rows.map((r) => (
            <button
              key={r.index}
              className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-xs hover:bg-elevated"
              onMouseEnter={() => setHovered(r.a)}
              onMouseLeave={() => setHovered(null)}
            >
              <span className="font-mono text-fg">
                {r.label}
                <span className="ml-2 text-subtle">{r.order === 3 ? "triple" : r.order === 2 ? "double" : "single"}</span>
              </span>
              <span className="font-mono tabular-nums text-muted">{r.length.toFixed(3)} Å</span>
            </button>
          ))}
        </div>
      </div>
      <div>
        <h3 className="text-sm font-semibold">Valence angles</h3>
        <div className="mt-2 max-h-40 overflow-y-auto">
          {angles.map((a) => (
            <div key={a.key} className="flex items-center justify-between px-2 py-1.5 text-xs">
              <span className="font-mono text-fg">{a.label}</span>
              <span className="font-mono tabular-nums text-muted">{a.degrees.toFixed(1)}°</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function OptimizerView() {
  const mol = useStudio((s) => s.molecule);
  const setMolecule = useStudio((s) => s.setMolecule);
  const toast = useStudio((s) => s.toast);
  const [history, setHistory] = useState<number[]>([]);
  const [running, setRunning] = useState(false);

  function run() {
    setRunning(true);
    const result = optimizeGeometry(mol.atoms, mol.bonds, 90, 0.1);
    setHistory(result.history);
    setMolecule({ ...mol, atoms: result.atoms, source: mol.source });
    toast("Geometry relaxed", "success");
    setRunning(false);
  }

  const chart = history.map((e, i) => ({ i, e }));

  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">Geometry optimizer</h3>
          <p className="text-xs text-muted">Gradient steps toward ideal covalent lengths.</p>
        </div>
        <Button size="sm" onClick={run} disabled={running}>
          {running ? "Running…" : "Relax"}
        </Button>
      </div>
      {chart.length > 0 && (
        <div className="mt-3 h-24">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chart}>
              <YAxis hide domain={["auto", "auto"]} />
              <Line type="monotone" dataKey="e" stroke="var(--color-accent)" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <p className="mt-1 text-right font-mono text-[11px] text-muted">
            Strain {history[history.length - 1]?.toFixed(3)}
          </p>
        </div>
      )}
    </div>
  );
}

function CompareView() {
  const mol = useStudio((s) => s.molecule);
  const compare = useStudio((s) => s.compare);
  const setCompare = useStudio((s) => s.setCompare);
  const value = compare ? rmsd(mol.atoms, compare.atoms) : null;
  return (
    <div>
      <h3 className="text-sm font-semibold">Structure compare</h3>
      <p className="text-xs text-muted">Naive index-aligned RMSD after both are centered.</p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {PRESET_LIST.map((p) => (
          <button
            key={p.id}
            onClick={() => setCompare(p)}
            className={cn(
              "rounded-md border px-2 py-1 text-xs",
              compare?.name === p.name ? "border-accent/40 bg-accent/10 text-accent" : "border-border text-muted",
            )}
          >
            {p.name}
          </button>
        ))}
      </div>
      {compare && (
        <p className="mt-3 font-mono text-sm text-fg">
          RMSD vs {compare.name}:{" "}
          <span className="tabular-nums">{value?.toFixed(3)} Å</span>
          <span className="ml-2 text-xs text-muted">
            ({Math.min(mol.atoms.length, compare.atoms.length)} atoms paired)
          </span>
        </p>
      )}
    </div>
  );
}

function ReactionView() {
  const setMolecule = useStudio((s) => s.setMolecule);
  const toast = useStudio((s) => s.toast);
  const [q, setQ] = useState("ethanol + acetic acid → ester");
  const [busy, setBusy] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setSummary(null);
    const res = await simulateReaction({ data: { reactants: q } });
    setBusy(false);
    if (!res.ok) {
      toast(res.error, "error");
      return;
    }
    setMolecule(res.molecule);
    setSummary(res.summary);
    toast(`Product: ${res.molecule.name}`, "success");
  }

  return (
    <div>
      <h3 className="text-sm font-semibold">Reaction sketch</h3>
      <p className="text-xs text-muted">Describes a plausible major product and loads its 3D model.</p>
      <div className="mt-2 flex gap-2">
        <Input value={q} onChange={(e) => setQ(e.target.value)} />
        <Button size="sm" onClick={() => void run()} disabled={busy}>
          {busy ? <Loader2 className="animate-spin" /> : "Predict"}
        </Button>
      </div>
      {summary && <p className="mt-3 text-sm leading-relaxed text-muted text-pretty">{summary}</p>}
    </div>
  );
}

function PdbView() {
  const setMolecule = useStudio((s) => s.setMolecule);
  const toast = useStudio((s) => s.toast);
  const [id, setId] = useState("1CRN");
  const [busy, setBusy] = useState(false);

  async function run() {
    setBusy(true);
    const res = await fetchPdbStructure({ data: { pdbId: id } });
    setBusy(false);
    if (!res.ok) {
      toast(res.error, "error");
      return;
    }
    setMolecule(res.molecule);
    toast(`Loaded ${id.toUpperCase()}`, "success");
  }

  return (
    <div>
      <h3 className="text-sm font-semibold">PDB explorer</h3>
      <p className="text-xs text-muted">Fetch from RCSB. Large proteins load as a Cα trace.</p>
      <div className="mt-2 flex gap-2">
        <Input
          value={id}
          onChange={(e) => setId(e.target.value)}
          className="max-w-[8rem] font-mono uppercase"
          maxLength={4}
        />
        <Button size="sm" onClick={() => void run()} disabled={busy}>
          {busy ? <Loader2 className="animate-spin" /> : "Fetch"}
        </Button>
        {["1CRN", "4HHB", "1CBS"].map((ex) => (
          <button
            key={ex}
            onClick={() => setId(ex)}
            className="rounded-md px-2 font-mono text-xs text-muted hover:text-fg"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-elevated px-3 py-2">
      <p className="text-[10px] uppercase tracking-wider text-subtle">{label}</p>
      <div className="mt-0.5 font-mono text-sm text-fg">{value}</div>
    </div>
  );
}



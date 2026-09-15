import {
  Beaker,
  Box,
  Download,
  Eye,
  FileText,
  Loader2,
  Menu,
  RotateCw,
  Search,
} from "lucide-react";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { downloadText, exportMolecule, filenameFor } from "@/lib/chemistry/export";
import type { ExportFormat, TabId } from "@/lib/chemistry/types";
import { loadQuery } from "@/lib/load-molecule";
import { useStudio } from "@/lib/store";
import { cn } from "@/lib/utils";

const TABS: { id: TabId; label: string; icon: typeof Eye }[] = [
  { id: "viewer", label: "Viewer", icon: Eye },
  { id: "analysis", label: "Analysis", icon: Box },
  { id: "notebooks", label: "Notes", icon: FileText },
  { id: "database", label: "Library", icon: Search },
];

const FORMATS: ExportFormat[] = ["pdb", "xyz", "mol", "json"];

export function Header() {
  const tab = useStudio((s) => s.tab);
  const setTab = useStudio((s) => s.setTab);
  const molecule = useStudio((s) => s.molecule);
  const status = useStudio((s) => s.status);
  const rotating = useStudio((s) => s.rotating);
  const setRotating = useStudio((s) => s.setRotating);
  const setSidebarOpen = useStudio((s) => s.setSidebarOpen);
  const toast = useStudio((s) => s.toast);
  const [query, setQuery] = useState("");
  const [exportOpen, setExportOpen] = useState(false);
  const exportRef = useRef<HTMLDivElement>(null);

  function onSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    void loadQuery(query);
  }

  function onExport(format: ExportFormat) {
    const content = exportMolecule(molecule, format);
    downloadText(content, filenameFor(molecule, format));
    toast(`Exported ${format.toUpperCase()}`, "success");
    setExportOpen(false);
  }

  return (
    <header className="z-20 flex items-center gap-3 border-b border-border bg-surface/80 px-3 py-2.5 backdrop-blur-md md:px-5">
      <Button
        variant="ghost"
        size="icon-sm"
        className="lg:hidden"
        onClick={() => setSidebarOpen(true)}
        aria-label="Open panel"
      >
        <Menu />
      </Button>

      <div className="flex items-center gap-2.5">
        <div className="flex size-9 items-center justify-center rounded-lg bg-elevated text-accent">
          <Beaker className="size-5" />
        </div>
        <div className="hidden leading-tight sm:block">
          <p className="font-display text-[15px] font-semibold tracking-tight text-fg">Molecule Studio</p>
          <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-subtle">Structure lab</p>
        </div>
      </div>

      <nav className="ml-2 hidden items-center rounded-lg bg-elevated p-1 md:flex">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
              tab === t.id ? "bg-surface text-fg shadow-sm" : "text-muted hover:text-fg",
            )}
          >
            <t.icon className="size-3.5" />
            {t.label}
          </button>
        ))}
      </nav>

      <form onSubmit={onSearch} className="ml-auto flex min-w-0 flex-1 items-center gap-2 md:max-w-sm">
        <div className="relative w-full">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-subtle" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Caffeine, C9H8O4, CID…"
            className="h-9 pl-9"
          />
        </div>
        <Button type="submit" size="sm" disabled={status === "loading"} className="shrink-0">
          {status === "loading" ? <Loader2 className="animate-spin" /> : "Load"}
        </Button>
      </form>

      <div className="hidden items-center gap-1 sm:flex">
        <Button
          variant={rotating ? "solid" : "ghost"}
          size="icon-sm"
          onClick={() => setRotating(!rotating)}
          aria-label="Toggle rotation"
        >
          <RotateCw className={rotating ? "animate-spin-slow" : ""} />
        </Button>
        <div className="relative" ref={exportRef}>
          <Button variant="outline" size="sm" onClick={() => setExportOpen((v) => !v)}>
            <Download />
            <span className="hidden lg:inline">Export</span>
          </Button>
          {exportOpen && (
            <div className="absolute right-0 top-full z-30 mt-1 w-36 overflow-hidden rounded-lg border border-border bg-elevated py-1 shadow-lg">
              {FORMATS.map((f) => (
                <button
                  key={f}
                  onClick={() => onExport(f)}
                  className="block w-full px-3 py-2 text-left text-xs uppercase tracking-wide text-fg hover:bg-surface"
                >
                  {f}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

import { Box, Eye, FileText, Search } from "lucide-react";
import { AnalysisStage } from "@/components/studio/AnalysisPanel";
import { Header } from "@/components/studio/Header";
import { NotesEditor } from "@/components/studio/NotesPanel";
import { Sidebar } from "@/components/studio/Sidebar";
import { Toasts } from "@/components/studio/Toasts";
import { Viewport } from "@/components/studio/Viewport";
import type { TabId } from "@/lib/chemistry/types";
import { useStudio } from "@/lib/store";
import { cn } from "@/lib/utils";

const MOBILE_TABS: { id: TabId; icon: typeof Eye; label: string }[] = [
  { id: "viewer", icon: Eye, label: "View" },
  { id: "analysis", icon: Box, label: "Analyze" },
  { id: "notebooks", icon: FileText, label: "Notes" },
  { id: "database", icon: Search, label: "Library" },
];

export function StudioApp() {
  const tab = useStudio((s) => s.tab);
  const setTab = useStudio((s) => s.setTab);

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-bg text-fg">
      <Header />
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <main className="relative flex min-w-0 flex-1 flex-col">
          {tab === "notebooks" ? (
            <div className="grid min-h-0 flex-1 md:grid-cols-[1.1fr_0.9fr]">
              <Viewport />
              <NotesEditor />
            </div>
          ) : (
            <>
              <Viewport />
              {tab === "analysis" && <AnalysisStage />}
            </>
          )}
          <p className="pointer-events-none absolute bottom-16 right-4 hidden text-[10px] uppercase tracking-[0.18em] text-subtle md:bottom-4 md:block">
            Drag to orbit · scroll to zoom
          </p>
        </main>
      </div>
      <nav className="flex border-t border-border bg-surface md:hidden">
        {MOBILE_TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "flex h-14 flex-1 flex-col items-center justify-center gap-0.5 text-[10px] font-medium",
              tab === t.id ? "text-fg" : "text-muted",
            )}
          >
            <t.icon className="size-4" />
            {t.label}
          </button>
        ))}
      </nav>
      <Toasts />
    </div>
  );
}

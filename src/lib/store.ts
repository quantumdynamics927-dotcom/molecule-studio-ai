import { create } from "zustand";
import { PRESETS } from "@/lib/chemistry/presets";
import type {
  AnalysisId,
  MoleculeData,
  Notebook,
  TabId,
  Toast,
  ViewStyle,
} from "@/lib/chemistry/types";
import { uid } from "@/lib/utils";

const NB_KEY = "molecule-studio.notebooks";

function loadNotebooks(): Notebook[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(NB_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Notebook[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveNotebooks(list: Notebook[]) {
  try {
    localStorage.setItem(NB_KEY, JSON.stringify(list));
  } catch {
    /* quota */
  }
}

export type LoadStatus = "idle" | "loading" | "error";

interface StudioState {
  molecule: MoleculeData;
  compare: MoleculeData | null;
  status: LoadStatus;
  error: string | null;
  tab: TabId;
  analysis: AnalysisId;
  viewStyle: ViewStyle;
  rotating: boolean;
  dynamics: boolean;
  density: boolean;
  hovered: number | null;
  selected: number | null;
  notebooks: Notebook[];
  activeNotebook: string | null;
  toasts: Toast[];
  sidebarOpen: boolean;
  setTab: (tab: TabId) => void;
  setAnalysis: (id: AnalysisId) => void;
  setViewStyle: (s: ViewStyle) => void;
  setRotating: (v: boolean) => void;
  setDynamics: (v: boolean) => void;
  setDensity: (v: boolean) => void;
  setHovered: (i: number | null) => void;
  setSelected: (i: number | null) => void;
  setSidebarOpen: (v: boolean) => void;
  setMolecule: (m: MoleculeData) => void;
  setCompare: (m: MoleculeData | null) => void;
  setStatus: (s: LoadStatus, error?: string | null) => void;
  toast: (message: string, type?: Toast["type"]) => void;
  dismissToast: (id: string) => void;
  createNotebook: () => void;
  selectNotebook: (id: string | null) => void;
  updateNotebook: (id: string, patch: Partial<Notebook>) => void;
  deleteNotebook: (id: string) => void;
}

export const useStudio = create<StudioState>((set, get) => ({
  molecule: PRESETS.caffeine,
  compare: null,
  status: "idle",
  error: null,
  tab: "viewer",
  analysis: "properties",
  viewStyle: "ball-stick",
  rotating: true,
  dynamics: false,
  density: false,
  hovered: null,
  selected: null,
  notebooks: [],
  activeNotebook: null,
  toasts: [],
  sidebarOpen: false,
  setTab: (tab) => set({ tab, sidebarOpen: false }),
  setAnalysis: (analysis) => set({ analysis, tab: "analysis" }),
  setViewStyle: (viewStyle) => set({ viewStyle }),
  setRotating: (rotating) => set({ rotating }),
  setDynamics: (dynamics) => set({ dynamics }),
  setDensity: (density) => set({ density }),
  setHovered: (hovered) => set({ hovered }),
  setSelected: (selected) => set({ selected }),
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  setMolecule: (molecule) =>
    set({ molecule, status: "idle", error: null, hovered: null, selected: null }),
  setCompare: (compare) => set({ compare }),
  setStatus: (status, error = null) => set({ status, error }),
  toast: (message, type = "info") => {
    const id = uid();
    set((s) => ({ toasts: [...s.toasts.slice(-4), { id, message, type }] }));
  },
  dismissToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  createNotebook: () => {
    const { molecule } = get();
    const nb: Notebook = {
      id: uid(),
      title: `${molecule.name} notes`,
      notes: `# ${molecule.name}\n\nFormula: ${molecule.formula}\n\n${molecule.description}\n`,
      molecule,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    set((s) => {
      const notebooks = [nb, ...s.notebooks];
      saveNotebooks(notebooks);
      return { notebooks, activeNotebook: nb.id, tab: "notebooks" };
    });
  },
  selectNotebook: (id) => {
    const nb = get().notebooks.find((n) => n.id === id);
    if (nb?.molecule) get().setMolecule(nb.molecule);
    set({ activeNotebook: id, tab: "notebooks" });
  },
  updateNotebook: (id, patch) => {
    set((s) => {
      const notebooks = s.notebooks.map((n) =>
        n.id === id ? { ...n, ...patch, updatedAt: Date.now() } : n,
      );
      saveNotebooks(notebooks);
      return { notebooks };
    });
  },
  deleteNotebook: (id) => {
    set((s) => {
      const notebooks = s.notebooks.filter((n) => n.id !== id);
      saveNotebooks(notebooks);
      return {
        notebooks,
        activeNotebook: s.activeNotebook === id ? null : s.activeNotebook,
      };
    });
  },
}));

export function hydrateNotebooks() {
  const list = loadNotebooks();
  useStudio.setState({ notebooks: list });
}

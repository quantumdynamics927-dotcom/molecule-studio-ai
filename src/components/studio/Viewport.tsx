import { Beaker } from "lucide-react";
import { useEffect, useState } from "react";
import MoleculeCanvas from "@/components/studio/MoleculeCanvas";
import { ELEMENT_NAMES } from "@/lib/chemistry/constants";
import { useStudio } from "@/lib/store";

export function Viewport() {
  const [ready, setReady] = useState(false);
  const molecule = useStudio((s) => s.molecule);
  const rotating = useStudio((s) => s.rotating);
  const viewStyle = useStudio((s) => s.viewStyle);
  const dynamics = useStudio((s) => s.dynamics);
  const density = useStudio((s) => s.density);
  const hovered = useStudio((s) => s.hovered);
  const selected = useStudio((s) => s.selected);
  const status = useStudio((s) => s.status);
  const setHovered = useStudio((s) => s.setHovered);
  const setSelected = useStudio((s) => s.setSelected);

  useEffect(() => setReady(true), []);

  const focus = selected ?? hovered;
  const atom = focus != null ? molecule.atoms[focus] : null;

  return (
    <div className="relative h-full min-h-0 flex-1 overflow-hidden bg-bg">
      {ready ? (
          <MoleculeCanvas
            data={molecule}
            rotating={rotating}
            viewStyle={viewStyle}
            dynamics={dynamics}
            density={density}
            hovered={hovered}
            selected={selected}
            onHover={setHovered}
            onSelect={setSelected}
          />
      ) : (
        <CanvasFallback />
      )}

      {status === "loading" && (
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-3 bg-bg/55 backdrop-blur-sm">
          <div className="relative size-14">
            <div className="absolute inset-0 animate-spin rounded-full border-2 border-border border-t-accent" />
            <Beaker className="absolute inset-0 m-auto size-5 text-accent" />
          </div>
          <p className="text-sm font-medium text-fg">Resolving structure</p>
          <p className="text-xs text-muted">PubChem 3D, then model generation if needed</p>
        </div>
      )}

      {atom && (
        <div className="pointer-events-none absolute left-4 top-4 rounded-lg border border-border bg-surface/90 px-3 py-2 backdrop-blur-sm">
          <p className="font-mono text-sm text-fg">
            {atom.element}
            <span className="ml-2 text-muted">{ELEMENT_NAMES[atom.element.toUpperCase()] ?? "Element"}</span>
          </p>
          <p className="font-mono text-[11px] tabular-nums text-subtle">
            {atom.x.toFixed(3)}, {atom.y.toFixed(3)}, {atom.z.toFixed(3)} Å
          </p>
        </div>
      )}
    </div>
  );
}

function CanvasFallback() {
  return (
    <div className="flex h-full w-full items-center justify-center bg-bg text-sm text-muted">
      Preparing viewer
    </div>
  );
}

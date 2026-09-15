import { Check, Info, X } from "lucide-react";
import { useEffect } from "react";
import { useStudio } from "@/lib/store";
import { cn } from "@/lib/utils";

export function Toasts() {
  const toasts = useStudio((s) => s.toasts);
  const dismiss = useStudio((s) => s.dismissToast);
  return (
    <div className="pointer-events-none fixed right-4 top-16 z-50 flex w-[min(100%-2rem,20rem)] flex-col gap-2">
      {toasts.map((t) => (
        <ToastItem key={t.id} id={t.id} message={t.message} type={t.type} onDone={dismiss} />
      ))}
    </div>
  );
}

function ToastItem({
  id,
  message,
  type,
  onDone,
}: {
  id: string;
  message: string;
  type: "success" | "error" | "info";
  onDone: (id: string) => void;
}) {
  useEffect(() => {
    const t = setTimeout(() => onDone(id), 3800);
    return () => clearTimeout(t);
  }, [id, onDone]);
  const Icon = type === "success" ? Check : type === "error" ? X : Info;
  return (
    <div
      className={cn(
        "pointer-events-auto flex items-start gap-2 rounded-lg border bg-elevated px-3 py-2.5 text-sm shadow-lg",
        type === "error" ? "border-danger/30 text-danger" : "border-border text-fg",
      )}
    >
      <Icon className="mt-0.5 size-4 shrink-0" />
      <p className="flex-1 leading-snug">{message}</p>
      <button onClick={() => onDone(id)} className="text-subtle hover:text-fg" aria-label="Dismiss">
        <X className="size-3.5" />
      </button>
    </div>
  );
}

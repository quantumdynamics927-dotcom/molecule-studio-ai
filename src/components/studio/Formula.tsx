export function Formula({ value, className = "" }: { value: string; className?: string }) {
  const parts = value.split(/(\d+)/);
  return (
    <span className={`font-mono ${className}`}>
      {parts.map((part, i) =>
        /^\d+$/.test(part) ? (
          <sub key={i} className="text-[0.7em]">
            {part}
          </sub>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </span>
  );
}

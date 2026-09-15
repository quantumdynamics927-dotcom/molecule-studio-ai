import React, { useState } from 'react';
import { Link } from 'lucide-react';

interface Atom { element: string; x: number; y: number; z: number; }
interface Props { atoms: Atom[]; bonds: number[][]; onAtomHover?: (index: number | null) => void; }

function distance(a: Atom, b: Atom) {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2);
}

function getBondType(length: number): { label: string; color: string } {
  if (length < 1.2) return { label: "Triple", color: "text-red-600" };
  if (length < 1.5) return { label: "Double", color: "text-orange-500" };
  return { label: "Single", color: "text-stone-600" };
}

export default function BondAnalyzer({ atoms, bonds, onAtomHover }: Props) {
  const [sortBy, setSortBy] = useState<"length" | "type">("length");

  const bondData = bonds.map(([a, b], i) => ({
    index: i,
    atom1: atoms[a],
    atom2: atoms[b],
    length: distance(atoms[a], atoms[b]),
    type: getBondType(distance(atoms[a], atoms[b]))
  })).sort((a, b) => sortBy === "length" ? a.length - b.length : a.type.label.localeCompare(b.type.label));

  return (
    <div className="bg-white rounded-2xl border border-stone-200 p-5">
      <div className="flex items-center gap-2 mb-4">
        <Link size={18} className="text-stone-700" />
        <h3 className="font-bold text-stone-900">Bond Analyzer</h3>
      </div>

      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setSortBy("length")}
          className={`px-3 py-1 text-xs rounded-lg ${sortBy === "length" ? "bg-stone-900 text-white" : "bg-stone-100 text-stone-600"}`}
        >By Length</button>
        <button
          onClick={() => setSortBy("type")}
          className={`px-3 py-1 text-xs rounded-lg ${sortBy === "type" ? "bg-stone-900 text-white" : "bg-stone-100 text-stone-600"}`}
        >By Type</button>
      </div>

      <div className="max-h-64 overflow-y-auto space-y-1">
        {bondData.map(bond => (
          <div
            key={bond.index}
            className="flex items-center justify-between py-2 px-3 bg-stone-50 rounded-lg hover:bg-stone-100 cursor-pointer"
            onMouseEnter={() => { onAtomHover?.(bond.index); }}
            onMouseLeave={() => onAtomHover?.(null)}
          >
            <span className="text-xs font-mono">
              <span className="text-blue-600">{bond.atom1.element}</span>
              <span className="text-stone-400">—</span>
              <span className="text-blue-600">{bond.atom2.element}</span>
            </span>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-medium ${bond.type.color}`}>{bond.type.label}</span>
              <span className="text-xs text-stone-400">{bond.length.toFixed(3)} Å</span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-stone-100 grid grid-cols-3 gap-2 text-center">
        <div className="text-xs">
          <div className="text-stone-400">Min</div>
          <div className="font-medium">{Math.min(...bondData.map(b => b.length)).toFixed(3)} Å</div>
        </div>
        <div className="text-xs">
          <div className="text-stone-400">Avg</div>
          <div className="font-medium">{(bondData.reduce((s, b) => s + b.length, 0) / bondData.length).toFixed(3)} Å</div>
        </div>
        <div className="text-xs">
          <div className="text-stone-400">Max</div>
          <div className="font-medium">{Math.max(...bondData.map(b => b.length)).toFixed(3)} Å</div>
        </div>
      </div>
    </div>
  );
}

import React from 'react';
import { Scale, FlaskConical, Atom as AtomIcon } from 'lucide-react';
import { Atom, calculateMolecularWeight, calculateFormula } from '../services/molecularProperties';

interface Props { atoms: Atom[]; bonds: number[][]; }

export default function PropertyCalculator({ atoms, bonds }: Props) {
  const mw = calculateMolecularWeight(atoms);
  const formula = calculateFormula(atoms);
  const atomCounts = atoms.reduce((acc: Record<string, number>, a) => {
    acc[a.element] = (acc[a.element] || 0) + 1;
    return acc;
  }, {});

  const properties = [
    { icon: Scale, label: "Molecular Weight", value: `${mw.toFixed(3)} g/mol`, sub: null },
    { icon: FlaskConical, label: "Chemical Formula", value: formula, sub: null },
    { icon: AtomIcon, label: "Total Atoms", value: atoms.length.toString(), sub: "atoms" },
    { icon: AtomIcon, label: "Total Bonds", value: bonds.length.toString(), sub: "bonds" }
  ];

  return (
    <div className="bg-white rounded-2xl border border-stone-200 p-5">
      <h3 className="font-bold text-stone-900 mb-4">Molecular Properties</h3>

      <div className="grid grid-cols-2 gap-3 mb-4">
        {properties.map((p, i) => (
          <div key={i} className="bg-stone-50 rounded-xl p-3">
            <div className="flex items-center gap-1 mb-1">
              <p.icon size={12} className="text-stone-400" />
              <span className="text-[10px] text-stone-400 uppercase">{p.label}</span>
            </div>
            <div className="font-bold text-stone-900">{p.value}</div>
            {p.sub && <div className="text-xs text-stone-400">{p.sub}</div>}
          </div>
        ))}
      </div>

      <div>
        <h4 className="text-xs font-bold text-stone-400 uppercase mb-2">Composition</h4>
        <div className="flex flex-wrap gap-2">
          {Object.entries(atomCounts).map(([el, count]) => (
            <span key={el} className="px-2 py-1 bg-stone-100 rounded-lg text-xs">
              <span className="font-bold">{el}</span>
              <span className="text-stone-400 ml-1">{count}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

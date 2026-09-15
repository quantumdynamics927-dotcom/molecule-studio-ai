import React, { useState } from 'react';
import { Beaker } from 'lucide-react';

interface Atom { element: string; x: number; y: number; z: number; }
interface Props { atoms: Atom[]; bonds: number[][]; onOptimized?: (atoms: Atom[]) => void; }

const ITERATION_COUNT = 50;
const LEARNING_RATE = 0.01;

function distance(a: Atom, b: Atom) {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2);
}

const BOND_LENGTHS: Record<string, Record<string, number>> = {
  C: { C: 1.54, H: 1.09, O: 1.43, N: 1.47 },
  O: { C: 1.43, H: 0.96, O: 1.48, N: 1.43 },
  N: { C: 1.47, H: 1.01, O: 1.43, N: 1.45 },
  H: { C: 1.09, O: 0.96, N: 1.01, H: 0.74 }
};

function getIdealLength(el1: string, el2: string): number {
  return BOND_LENGTHS[el1]?.[el2] || BOND_LENGTHS[el2]?.[el1] || 1.5;
}

export default function GeometryOptimizer({ atoms, bonds, onOptimized }: Props) {
  const [optimizedAtoms, setOptimizedAtoms] = useState<Atom[] | null>(null);
  const [energyHistory, setEnergyHistory] = useState<number[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const optimize = async () => {
    setIsRunning(true);
    const current = atoms.map(a => ({ ...a }));
    const history: number[] = [];

    for (let iter = 0; iter < ITERATION_COUNT; iter++) {
      let totalEnergy = 0;

      bonds.forEach(([i, j]) => {
        const ideal = getIdealLength(current[i].element, current[j].element);
        const dist = distance(current[i], current[j]);
        const force = (dist - ideal) * LEARNING_RATE;
        totalEnergy += Math.abs(dist - ideal);

        const dx = current[j].x - current[i].x;
        const dy = current[j].y - current[i].y;
        const dz = current[j].z - current[i].z;
        const len = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;

        current[i].x += (dx / len) * force * 0.5;
        current[i].y += (dy / len) * force * 0.5;
        current[i].z += (dz / len) * force * 0.5;
        current[j].x -= (dx / len) * force * 0.5;
        current[j].y -= (dy / len) * force * 0.5;
        current[j].z -= (dz / len) * force * 0.5;
      });

      history.push(totalEnergy);
      if (iter % 10 === 0) {
        setEnergyHistory([...history]);
        setOptimizedAtoms(current.map(a => ({ ...a })));
        await new Promise(r => setTimeout(r, 0));
      }
    }

    setEnergyHistory(history);
    setOptimizedAtoms(current.map(a => ({ ...a })));
    onOptimized?.(current.map(a => ({ ...a })));
    setIsRunning(false);
  };

  return (
    <div className="bg-white rounded-2xl border border-stone-200 p-5">
      <div className="flex items-center gap-2 mb-4">
        <Beaker size={18} className="text-stone-700" />
        <h3 className="font-bold text-stone-900">Geometry Optimizer</h3>
      </div>
      <p className="text-sm text-stone-500 mb-4">Minimize bond length violations using gradient descent.</p>

      <button
        onClick={optimize}
        disabled={isRunning || atoms.length === 0}
        className="w-full bg-stone-900 text-white py-2 rounded-xl font-medium hover:bg-stone-800 disabled:opacity-50 mb-4"
      >
        {isRunning ? "Optimizing..." : "Start Optimization"}
      </button>

      {energyHistory.length > 0 && (
        <div className="space-y-3">
          <div className="text-xs text-stone-400">Energy vs Iteration</div>
          <svg viewBox="0 0 200 60" className="w-full h-16 bg-stone-50 rounded-lg">
            <polyline
              fill="none"
              stroke="#1c1917"
              strokeWidth="1.5"
              points={energyHistory.map((e, i) => {
                const maxE = Math.max(...energyHistory, 0.001);
                const x = (i / (energyHistory.length - 1 || 1)) * 200;
                const y = 60 - (e / maxE) * 50;
                return `${x},${y}`;
              }).join(" ")}
            />
          </svg>
          <div className="flex justify-between text-xs text-stone-400">
            <span>0</span>
            <span>Iterations: {energyHistory.length}</span>
            <span>Energy: {energyHistory[energyHistory.length - 1]?.toFixed(3)}</span>
          </div>
        </div>
      )}
    </div>
  );
}

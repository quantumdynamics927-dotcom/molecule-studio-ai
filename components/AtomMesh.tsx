
import React from 'react';
import * as THREE from 'three';
import { Atom } from '../types';
import { CPK_COLORS, ATOM_RADII } from '../constants';

interface AtomMeshProps {
  atom: Atom;
  index: number;
}

const AtomMesh: React.FC<AtomMeshProps> = ({ atom }) => {
  const color = CPK_COLORS[atom.element.toUpperCase()] || CPK_COLORS.DEFAULT;
  const radius = ATOM_RADII[atom.element.toUpperCase()] || ATOM_RADII.DEFAULT;

  return (
    <mesh position={[atom.x, atom.y, atom.z]}>
      <sphereGeometry args={[radius, 32, 32]} />
      <meshStandardMaterial 
        color={color} 
        roughness={0.15} 
        metalness={0.2}
        emissive={color}
        emissiveIntensity={0.05}
      />
    </mesh>
  );
};

export default AtomMesh;

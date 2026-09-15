
import React, { useMemo } from 'react';
import * as THREE from 'three';

interface BondMeshProps {
  start: [number, number, number];
  end: [number, number, number];
}

const BondMesh: React.FC<BondMeshProps> = ({ start, end }) => {
  const { position, quaternion, length } = useMemo(() => {
    const s = new THREE.Vector3(...start);
    const e = new THREE.Vector3(...end);
    
    const direction = new THREE.Vector3().subVectors(e, s);
    const len = direction.length();
    const pos = new THREE.Vector3().addVectors(s, e).multiplyScalar(0.5);
    
    const quat = new THREE.Quaternion();
    quat.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.clone().normalize());
    
    return { position: pos, quaternion: quat, length: len };
  }, [start, end]);

  return (
    <mesh position={position} quaternion={quaternion}>
      <cylinderGeometry args={[0.12, 0.12, length, 12]} />
      <meshStandardMaterial 
        color="#888888" 
        roughness={0.3} 
        metalness={0.1} 
      />
    </mesh>
  );
};

export default BondMesh;

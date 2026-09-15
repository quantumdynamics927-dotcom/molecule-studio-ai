
import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stage, Float, ContactShadows, Environment, Center } from '@react-three/drei';
import { MoleculeData } from '../types';
import AtomMesh from './AtomMesh';
import BondMesh from './BondMesh';

interface MoleculeCanvasProps {
  data: MoleculeData | null;
  isRotating: boolean;
}

const MoleculeCanvas: React.FC<MoleculeCanvasProps> = ({ data, isRotating }) => {
  if (!data) return null;

  return (
    <Canvas shadows camera={{ position: [0, 0, 10], fov: 45 }}>
      <Suspense fallback={null}>
        <Stage environment="city" intensity={0.5} contactShadow={false}>
          <Float speed={1.5} rotationIntensity={0.5} floatIntensity={0.5}>
            <Center top>
              <group>
                {/* Atoms */}
                {data.atoms.map((atom, idx) => (
                  <AtomMesh key={`atom-${idx}`} atom={atom} index={idx} />
                ))}

                {/* Bonds */}
                {data.bonds.map((bond, idx) => {
                  const atomA = data.atoms[bond[0]];
                  const atomB = data.atoms[bond[1]];
                  if (!atomA || !atomB) return null;
                  return (
                    <BondMesh 
                      key={`bond-${idx}`} 
                      start={[atomA.x, atomA.y, atomA.z]} 
                      end={[atomB.x, atomB.y, atomB.z]} 
                    />
                  );
                })}
              </group>
            </Center>
          </Float>
        </Stage>
        <ContactShadows 
          position={[0, -4, 0]} 
          opacity={0.4} 
          scale={20} 
          blur={2} 
          far={10} 
        />
        <OrbitControls 
          enablePan={false} 
          autoRotate={isRotating} 
          autoRotateSpeed={0.5} 
          minDistance={5} 
          maxDistance={30} 
        />
        <Environment preset="city" />
      </Suspense>
    </Canvas>
  );
};

export default MoleculeCanvas;

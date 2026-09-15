import { OrbitControls } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { ballRadius, cpkColor, vdwRadius } from "@/lib/chemistry/constants";
import { moleculeExtent } from "@/lib/chemistry/geometry";
import type { Atom, Bond, MoleculeData, ViewStyle } from "@/lib/chemistry/types";

interface Props {
  data: MoleculeData;
  rotating: boolean;
  viewStyle: ViewStyle;
  dynamics: boolean;
  density: boolean;
  hovered: number | null;
  selected: number | null;
  onHover: (i: number | null) => void;
  onSelect: (i: number | null) => void;
}

export default function MoleculeCanvas(props: Props) {
  const extent = Math.max(4, moleculeExtent(props.data.atoms));
  return (
    <Canvas
      dpr={[1, 2]}
      camera={{ position: [0, extent * 0.35, Math.max(8, extent * 2.45)], fov: 42, near: 0.1, far: 200 }}
      gl={{ antialias: true, alpha: false, preserveDrawingBuffer: true }}
      onPointerMissed={() => props.onSelect(null)}
      onCreated={({ camera, gl }) => {
        camera.lookAt(0, 0, 0);
        gl.setClearColor("#0b0d0f", 1);
      }}
      className="absolute inset-0 h-full w-full"
    >
      <color attach="background" args={["#0b0d0f"]} />
      <hemisphereLight args={["#e8eef4", "#2a241c", 0.85]} />
      <ambientLight intensity={0.45} />
      <directionalLight position={[6, 10, 8]} intensity={1.4} />
      <directionalLight position={[-6, -2, -4]} intensity={0.4} color="#9ec4d4" />
      <Recenter extent={extent} />
      <MoleculeGroup {...props} />
      <OrbitControls
        makeDefault
        enableDamping
        dampingFactor={0.08}
        autoRotate={props.rotating}
        autoRotateSpeed={0.55}
        minDistance={Math.max(3, extent * 0.9)}
        maxDistance={Math.max(18, extent * 6)}
        enablePan={false}
      />
    </Canvas>
  );
}

function Recenter({ extent }: { extent: number }) {
  const { camera, controls } = useThree();
  useEffect(() => {
    camera.position.set(0, extent * 0.35, Math.max(8, extent * 2.45));
    camera.lookAt(0, 0, 0);
    const orbit = controls as { target?: THREE.Vector3; update?: () => void } | null;
    orbit?.target?.set(0, 0, 0);
    orbit?.update?.();
  }, [camera, controls, extent]);
  return null;
}

function MoleculeGroup(props: Props) {
  const group = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    if (!group.current) return;
    if (!props.dynamics) {
      group.current.rotation.x = 0;
      group.current.position.y = 0;
      return;
    }
    const t = clock.elapsedTime;
    group.current.rotation.x = Math.sin(t * 1.15) * 0.03;
    group.current.position.y = Math.sin(t * 0.9) * 0.05;
  });

  const showBonds = props.viewStyle !== "spacefill";

  return (
    <group ref={group}>
      {props.data.atoms.map((atom, i) => (
        <AtomMesh
          key={`a-${i}-${atom.element}`}
          atom={atom}
          index={i}
          viewStyle={props.viewStyle}
          density={props.density}
          active={props.hovered === i || props.selected === i}
          onHover={props.onHover}
          onSelect={props.onSelect}
        />
      ))}
      {showBonds &&
        props.data.bonds.map((bond, i) => {
          const a = props.data.atoms[bond.a];
          const b = props.data.atoms[bond.b];
          if (!a || !b) return null;
          return <BondMesh key={`b-${i}`} a={a} b={b} order={bond.order} />;
        })}
    </group>
  );
}

function AtomMesh({
  atom,
  index,
  viewStyle,
  density,
  active,
  onHover,
  onSelect,
}: {
  atom: Atom;
  index: number;
  viewStyle: ViewStyle;
  density: boolean;
  active: boolean;
  onHover: (i: number | null) => void;
  onSelect: (i: number | null) => void;
}) {
  const color = cpkColor(atom.element);
  const radius =
    viewStyle === "spacefill"
      ? vdwRadius(atom.element) * 0.52
      : viewStyle === "sticks"
        ? 0.12
        : ballRadius(atom.element);

  return (
    <group position={[atom.x, atom.y, atom.z]}>
      <mesh
        scale={active ? 1.12 : 1}
        onPointerOver={(e) => {
          e.stopPropagation();
          onHover(index);
          document.body.style.cursor = "pointer";
        }}
        onPointerOut={() => {
          onHover(null);
          document.body.style.cursor = "";
        }}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(index);
        }}
      >
        <sphereGeometry args={[radius, 32, 32]} />
        <meshStandardMaterial
          color={color}
          roughness={0.28}
          metalness={atom.element === "C" ? 0.08 : 0.18}
          emissive={color}
          emissiveIntensity={active ? 0.22 : 0.04}
        />
      </mesh>
      {density && (
        <mesh>
          <sphereGeometry args={[radius * 1.85, 16, 16]} />
          <meshStandardMaterial
            color={color}
            transparent
            opacity={0.08}
            roughness={1}
            depthWrite={false}
          />
        </mesh>
      )}
    </group>
  );
}

function BondMesh({ a, b, order }: { a: Atom; b: Atom; order: number }) {
  const start = [a.x, a.y, a.z] as [number, number, number];
  const end = [b.x, b.y, b.z] as [number, number, number];
  const mid: [number, number, number] = [(a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2];
  const perp = useMemo(() => {
    const dir = new THREE.Vector3(b.x - a.x, b.y - a.y, b.z - a.z);
    const up = Math.abs(dir.y) < 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
    return new THREE.Vector3().crossVectors(dir, up).normalize();
  }, [a.x, a.y, a.z, b.x, b.y, b.z]);

  const radius = order >= 2 ? 0.055 : 0.09;
  const offsets = order === 3 ? [-0.13, 0, 0.13] : order === 2 ? [-0.09, 0.09] : [0];
  const colorA = cpkColor(a.element);
  const colorB = cpkColor(b.element);

  return (
    <group>
      {offsets.map((off) => {
        const shift = perp.clone().multiplyScalar(off);
        return (
          <group key={off}>
            <HalfBond from={start} to={mid} offset={shift} color={colorA} radius={radius} />
            <HalfBond from={mid} to={end} offset={shift} color={colorB} radius={radius} />
          </group>
        );
      })}
    </group>
  );
}

function HalfBond({
  from,
  to,
  offset,
  color,
  radius,
}: {
  from: [number, number, number];
  to: [number, number, number];
  offset: THREE.Vector3;
  color: string;
  radius: number;
}) {
  const { position, quaternion, length } = useMemo(() => {
    const s = new THREE.Vector3(...from).add(offset);
    const e = new THREE.Vector3(...to).add(offset);
    const direction = new THREE.Vector3().subVectors(e, s);
    const length = direction.length();
    const position = new THREE.Vector3().addVectors(s, e).multiplyScalar(0.5);
    const quaternion = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      direction.clone().normalize(),
    );
    return { position, quaternion, length };
  }, [from, to, offset]);

  return (
    <mesh position={position} quaternion={quaternion}>
      <cylinderGeometry args={[radius, radius, Math.max(0.02, length), 10]} />
      <meshStandardMaterial color={color} roughness={0.35} metalness={0.12} />
    </mesh>
  );
}

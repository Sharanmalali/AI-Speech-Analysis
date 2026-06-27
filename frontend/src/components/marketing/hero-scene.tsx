"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type { Mesh, Points } from "three";

function Knot() {
  const mesh = useRef<Mesh>(null);
  useFrame((_, delta) => {
    if (mesh.current) {
      mesh.current.rotation.x += delta * 0.15;
      mesh.current.rotation.y += delta * 0.2;
    }
  });
  return (
    <mesh ref={mesh} scale={1.6}>
      <icosahedronGeometry args={[1, 1]} />
      <meshStandardMaterial
        color="#6366F1"
        wireframe
        emissive="#8B5CF6"
        emissiveIntensity={0.4}
        roughness={0.3}
      />
    </mesh>
  );
}

function StarField() {
  const points = useRef<Points>(null);
  const positions = new Float32Array(600 * 3).map(() => (Math.random() - 0.5) * 14);
  useFrame((_, delta) => {
    if (points.current) points.current.rotation.y += delta * 0.03;
  });
  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.04} color="#EC4899" transparent opacity={0.7} />
    </points>
  );
}

/** Lightweight React-Three-Fiber hero scene (rendered client-side only). */
export default function HeroScene() {
  return (
    <Canvas camera={{ position: [0, 0, 5], fov: 50 }} dpr={[1, 2]}>
      <ambientLight intensity={0.6} />
      <directionalLight position={[3, 3, 5]} intensity={1.2} />
      <pointLight position={[-4, -2, -3]} intensity={2} color="#EC4899" />
      <Knot />
      <StarField />
    </Canvas>
  );
}
